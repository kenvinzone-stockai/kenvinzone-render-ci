from __future__ import annotations

import json
import secrets
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import read_social_config, write_social_config
from .metadata import build_upload_metadata, final_video_path_for_project, require_slide_project

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
TIKTOK_CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
TIKTOK_DIRECT_POST_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_INBOX_POST_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
TIKTOK_POST_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

OAUTH_STATES: dict[str, dict] = {}
OAUTH_STATES_LOCK = threading.Lock()


def tiktok_config(config: dict | None = None) -> dict:
    config = read_social_config() if config is None else config
    tiktok = config.get("tiktok", {}) if isinstance(config, dict) else {}
    if not isinstance(tiktok, dict):
        tiktok = {}
    return tiktok


def tiktok_redirect_uri(tiktok: dict) -> str:
    return str(tiktok.get("redirect_uri") or "http://localhost:8765/api/social/tiktok/callback")


def tiktok_is_configured(tiktok: dict) -> bool:
    return bool(str(tiktok.get("client_key") or "").strip() and str(tiktok.get("client_secret") or "").strip())


def tiktok_is_connected(tiktok: dict) -> bool:
    tokens = tiktok_tokens(tiktok)
    return bool(tokens.get("access_token") and tokens.get("open_id"))


def tiktok_tokens(tiktok: dict) -> dict:
    tokens = tiktok.get("tokens", {}) if isinstance(tiktok.get("tokens"), dict) else {}
    return tokens


def tiktok_config_hint() -> str:
    return (
        'Add tiktok.client_key and tiktok.client_secret to config/social-upload.json. '
        'Get these from https://developers.tiktok.com/'
    )


def tiktok_public_account(tiktok: dict) -> dict:
    tokens = tiktok_tokens(tiktok)
    return {
        "open_id": str(tokens.get("open_id") or ""),
        "username": str(tokens.get("username") or ""),
        "avatar": str(tokens.get("avatar") or ""),
        "display_name": str(tokens.get("display_name") or ""),
    }


# --- OAuth ---

def start_tiktok_oauth(project: str) -> str:
    config = read_social_config()
    tiktok = tiktok_config(config)
    if not tiktok_is_configured(tiktok):
        raise ValueError(tiktok_config_hint())
    require_slide_project(project)
    state = f"{project}:{secrets.token_urlsafe(18)}"
    with OAUTH_STATES_LOCK:
        OAUTH_STATES[state] = {"project": project, "created_at": time.time()}
    # Also persist state in config for cross-restart recovery
    config["_tiktok_oauth_state"] = state
    write_social_config(config)
    params = {
        "client_key": tiktok["client_key"],
        "redirect_uri": tiktok_redirect_uri(tiktok),
        "response_type": "code",
        "scope": "user.info.basic,video.publish,video.upload",
        "state": state,
    }
    return TIKTOK_AUTH_URL + "?" + urlencode(params)


def finish_tiktok_oauth(query: dict[str, list[str]]) -> str:
    error = (query.get("error") or [""])[0]
    if error:
        error_desc = (query.get("error_description") or [""])[0]
        raise RuntimeError(f"TikTok OAuth cancelled: {error} — {error_desc}")
    code = (query.get("code") or [""])[0]
    state = (query.get("state") or [""])[0]
    if not code or not state:
        raise ValueError("Missing TikTok OAuth code/state.")
    with OAUTH_STATES_LOCK:
        state_data = OAUTH_STATES.pop(state, None)
    if not state_data:
        # Try recovering from config
        config = read_social_config()
        saved_state = config.get("_tiktok_oauth_state")
        if saved_state == state:
            project = state.split(":")[0] if ":" in state else ""
            state_data = {"project": project}
        else:
            raise ValueError("TikTok OAuth state is invalid or expired. Try connecting again.")

    config = read_social_config()
    tiktok = tiktok_config(config)
    if not tiktok_is_configured(tiktok):
        raise ValueError(tiktok_config_hint())

    # Exchange code for tokens
    token_data = tiktok_exchange_code(code, tiktok)
    access_token = token_data.get("access_token", "")
    open_id = token_data.get("open_id", "")

    # Try to get user info for display
    username = ""
    display_name = ""
    avatar = ""
    try:
        user_info = tiktok_query_creator_info(access_token)
        username = user_info.get("creator_username", "")
        display_name = user_info.get("creator_nickname", "")
        avatar = user_info.get("creator_avatar_url", "")
    except Exception:
        pass

    tokens = {
        "access_token": access_token,
        "refresh_token": token_data.get("refresh_token", ""),
        "open_id": open_id,
        "expires_at": time.time() + float(token_data.get("expires_in") or 86400),
        "refresh_expires_at": time.time() + float(token_data.get("refresh_expires_in") or 86400 * 365),
        "scope": token_data.get("scope", ""),
        "token_type": token_data.get("token_type", "Bearer"),
        "username": username,
        "display_name": display_name,
        "avatar": avatar,
    }
    tiktok["tokens"] = tokens
    config["tiktok"] = tiktok
    config.pop("_tiktok_oauth_state", None)
    write_social_config(config)
    return str(state_data.get("project") or "")


def tiktok_exchange_code(code: str, tiktok: dict) -> dict:
    payload = urlencode({
        "client_key": tiktok["client_key"],
        "client_secret": tiktok["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": tiktok_redirect_uri(tiktok),
    }).encode("utf-8")
    request = Request(
        TIKTOK_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok OAuth token exchange failed: HTTP {exc.code}: {detail}") from exc


def tiktok_refresh_access_token(config: dict, tiktok: dict) -> str:
    tokens = tiktok_tokens(tiktok)
    access_token = str(tokens.get("access_token") or "")
    expires_at = float(tokens.get("expires_at") or 0)
    if access_token and expires_at > time.time() + 90:
        return access_token

    refresh_token = str(tokens.get("refresh_token") or "")
    if not refresh_token:
        raise RuntimeError("TikTok không có refresh token. Hãy kết nối lại TikTok.")

    payload = urlencode({
        "client_key": tiktok["client_key"],
        "client_secret": tiktok["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode("utf-8")
    request = Request(
        TIKTOK_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok token refresh failed: HTTP {exc.code}: {detail}") from exc

    new_access_token = data.get("access_token", "")
    if not new_access_token:
        raise RuntimeError(f"TikTok token refresh returned no access_token: {data}")

    tokens["access_token"] = new_access_token
    tokens["expires_at"] = time.time() + float(data.get("expires_in") or 86400)
    if data.get("refresh_token"):
        tokens["refresh_token"] = data["refresh_token"]
        tokens["refresh_expires_at"] = time.time() + float(data.get("refresh_expires_in") or 86400 * 365)
    tiktok["tokens"] = tokens
    config["tiktok"] = tiktok
    write_social_config(config)
    return new_access_token


# --- Creator Info ---

def tiktok_query_creator_info(access_token: str) -> dict:
    request = Request(
        TIKTOK_CREATOR_INFO_URL,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok creator info query failed: HTTP {exc.code}: {detail}") from exc
    error = result.get("error", {})
    if isinstance(error, dict) and error.get("code") != "ok":
        raise RuntimeError(f"TikTok creator info error: {error.get('message', error.get('code'))}")
    return result.get("data", {})


# --- Upload ---

def tiktok_upload_video(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    video_path = final_video_path_for_project(project)
    metadata = build_upload_metadata(project)
    title = str(payload.get("title") or metadata.get("title") or project).strip()[:150]
    privacy_level = str(payload.get("privacy_level") or "SELF_ONLY").strip()
    upload_mode = str(payload.get("mode") or "direct").strip().lower()

    config = read_social_config()
    tiktok = tiktok_config(config)
    if not tiktok_is_configured(tiktok):
        raise ValueError(tiktok_config_hint())
    if not tiktok_is_connected(tiktok):
        raise RuntimeError("TikTok chưa được kết nối. Hãy click 'Kết nối TikTok' trước.")
    access_token = tiktok_refresh_access_token(config, tiktok)

    video_size = video_path.stat().st_size
    if video_size == 0:
        raise ValueError("Video file is empty.")

    if upload_mode == "inbox":
        # Upload to TikTok Inbox/Draft
        init_payload = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            }
        }
        init_url = TIKTOK_INBOX_POST_URL
    else:
        # Direct Post
        init_payload = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            }
        }
        init_url = TIKTOK_DIRECT_POST_URL

    init_body = json.dumps(init_payload).encode("utf-8")
    init_request = Request(
        init_url,
        data=init_body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urlopen(init_request, timeout=60) as response:
            init_result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok upload init failed: HTTP {exc.code}: {detail}") from exc

    error = init_result.get("error", {})
    if isinstance(error, dict) and error.get("code") != "ok":
        raise RuntimeError(f"TikTok upload init error: {error.get('message', error.get('code'))}")

    data = init_result.get("data", {})
    publish_id = data.get("publish_id", "")
    upload_url = data.get("upload_url", "")

    if not upload_url:
        raise RuntimeError(f"TikTok upload init did not return an upload URL: {init_result}")

    # PUT video binary to upload_url
    video_bytes = video_path.read_bytes()
    last_byte = len(video_bytes) - 1
    upload_request = Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{last_byte}/{len(video_bytes)}",
        },
        method="PUT",
    )
    try:
        with urlopen(upload_request, timeout=600) as response:
            upload_result_text = response.read().decode("utf-8")
            upload_result = json.loads(upload_result_text) if upload_result_text.strip() else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok video upload failed: HTTP {exc.code}: {detail}") from exc

    mode_label = "TikTok Inbox/Draft" if upload_mode == "inbox" else "TikTok Direct Post"
    return {
        "ok": True,
        "platform": "tiktok",
        "project": project,
        "publish_id": publish_id,
        "mode": upload_mode,
        "privacy_level": privacy_level,
        "message": f"Video đã được upload lên {mode_label}. publish_id: {publish_id}",
    }


def tiktok_check_post_status(publish_id: str) -> dict:
    config = read_social_config()
    tiktok = tiktok_config(config)
    access_token = tiktok_refresh_access_token(config, tiktok)
    payload = json.dumps({"publish_id": publish_id}).encode("utf-8")
    request = Request(
        TIKTOK_POST_STATUS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok status check failed: HTTP {exc.code}: {detail}") from exc
