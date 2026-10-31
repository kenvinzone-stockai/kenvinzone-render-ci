from __future__ import annotations

import json
import re
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .config import read_social_config, write_social_config
from .http import http_form_request, http_get_request
from .metadata import (
    build_upload_metadata,
    final_video_path_for_project,
    first_url_from_source,
    require_slide_project,
    upload_paragraphs,
)


def facebook_config(config: dict | None = None) -> dict:
    config = read_social_config() if config is None else config
    facebook = config.get("facebook", {}) if isinstance(config, dict) else {}
    if not isinstance(facebook, dict):
        facebook = {}
    return facebook


def facebook_graph_version(facebook: dict) -> str:
    version = str(facebook.get("graph_version") or "v25.0").strip()
    return version if version.startswith("v") else f"v{version}"


def facebook_pages(facebook: dict) -> list[dict]:
    raw_pages = facebook.get("pages")
    pages = raw_pages if isinstance(raw_pages, list) else []
    normalized = []
    seen = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_id = str(page.get("id") or page.get("page_id") or "").strip()
        page_access_token = str(page.get("page_access_token") or page.get("access_token") or "").strip()
        if not page_id or not page_access_token or page_id in seen:
            continue
        seen.add(page_id)
        normalized.append({
            "id": page_id,
            "page_access_token": page_access_token,
            "name": str(page.get("name") or "").strip(),
            "thumbnail": str(page.get("thumbnail") or "").strip(),
        })
    legacy_page_id = str(facebook.get("page_id") or "").strip()
    legacy_page_access_token = str(facebook.get("page_access_token") or "").strip()
    if legacy_page_id and legacy_page_access_token and legacy_page_id not in seen:
        normalized.append({
            "id": legacy_page_id,
            "page_access_token": legacy_page_access_token,
            "name": str(facebook.get("page_name") or "").strip(),
            "thumbnail": str(facebook.get("page_thumbnail") or "").strip(),
        })
    return normalized


def facebook_active_page_id(facebook: dict) -> str:
    active_page_id = str(facebook.get("active_page_id") or facebook.get("page_id") or "").strip()
    if active_page_id:
        return active_page_id
    pages = facebook_pages(facebook)
    return str(pages[0].get("id") or "") if pages else ""


def facebook_active_page(facebook: dict) -> dict:
    pages = facebook_pages(facebook)
    active_page_id = facebook_active_page_id(facebook)
    for page in pages:
        if page.get("id") == active_page_id:
            return page
    return pages[0] if pages else {}


def facebook_page_id(facebook: dict) -> str:
    return str(facebook_active_page(facebook).get("id") or "").strip()


def facebook_page_access_token(facebook: dict) -> str:
    return str(facebook_active_page(facebook).get("page_access_token") or "").strip()


def facebook_is_configured(facebook: dict) -> bool:
    return bool(facebook_page_id(facebook) and facebook_page_access_token(facebook))


def facebook_config_hint() -> str:
    return (
        "Fill facebook.pages[].id, facebook.pages[].page_access_token, and facebook.active_page_id in config/social-upload.json. "
        "The Page token needs pages_show_list, pages_read_engagement, pages_manage_posts, and video publishing permissions."
    )


def facebook_reels_url(facebook: dict) -> str:
    page_id = facebook_page_id(facebook)
    return f"https://graph.facebook.com/{facebook_graph_version(facebook)}/{quote(page_id, safe='')}/video_reels"


def facebook_post_comment_url(facebook: dict, post_id: str) -> str:
    return f"https://graph.facebook.com/{facebook_graph_version(facebook)}/{quote(post_id, safe='')}/comments"


def facebook_full_post_id(facebook: dict, object_id: str) -> str:
    object_id = str(object_id or "").strip()
    if not object_id or "_" in object_id:
        return object_id
    page_id = facebook_page_id(facebook)
    return f"{page_id}_{object_id}" if page_id else object_id


def facebook_page_profile(facebook: dict, page: dict | None = None) -> dict:
    active_page = page or facebook_active_page(facebook)
    page_id = str(active_page.get("id") or "").strip()
    access_token = str(active_page.get("page_access_token") or "").strip()
    profile = {
        "id": page_id,
        "name": str(active_page.get("name") or "").strip(),
        "thumbnail": str(active_page.get("thumbnail") or "").strip(),
    }
    if not page_id or not access_token:
        return profile
    try:
        data = http_get_request(
            f"https://graph.facebook.com/{facebook_graph_version(facebook)}/{quote(page_id, safe='')}",
            {
                "fields": "id,name,picture{url}",
                "access_token": access_token,
            },
        )
    except RuntimeError as exc:
        profile["error"] = str(exc)
        return profile
    picture = data.get("picture", {}) if isinstance(data.get("picture"), dict) else {}
    picture_data = picture.get("data", {}) if isinstance(picture.get("data"), dict) else {}
    profile.update({
        "id": str(data.get("id") or page_id),
        "name": str(data.get("name") or profile["name"]),
        "thumbnail": str(picture_data.get("url") or profile["thumbnail"]),
    })
    return profile


def facebook_pages_status(facebook: dict) -> list[dict]:
    active_page_id = facebook_active_page_id(facebook)
    result = []
    for page in facebook_pages(facebook):
        profile = facebook_page_profile(facebook, page)
        profile["active"] = profile.get("id") == active_page_id
        result.append(profile)
    return result


def set_facebook_active_page(page_id: str) -> dict:
    page_id = str(page_id or "").strip()
    if not page_id:
        raise ValueError("Missing Facebook page id.")
    config = read_social_config()
    facebook = facebook_config(config)
    pages = facebook_pages(facebook)
    if not any(page.get("id") == page_id for page in pages):
        raise ValueError("Facebook page id is not configured in facebook.pages.")
    facebook["active_page_id"] = page_id
    config["facebook"] = facebook
    write_social_config(config)
    return {"ok": True, "active_page_id": page_id}


def facebook_graph_object_url(facebook: dict, object_id: str) -> str:
    return f"https://graph.facebook.com/{facebook_graph_version(facebook)}/{quote(object_id, safe='')}"


def facebook_object_metadata(facebook: dict, object_id: str, access_token: str, fields: str = "id") -> dict:
    if not object_id:
        return {}
    return http_get_request(
        facebook_graph_object_url(facebook, object_id),
        {
            "fields": fields,
            "access_token": access_token,
        },
    )


def wait_for_facebook_object_ready(
    facebook: dict,
    object_id: str,
    access_token: str,
    attempts: int = 8,
    delay_seconds: float = 4.0,
) -> tuple[dict, str]:
    last_error = ""
    for attempt in range(attempts):
        try:
            data = facebook_object_metadata(facebook, object_id, access_token)
            if str(data.get("id") or "").strip():
                return data, ""
            last_error = f"Facebook object response did not include an id: {data}"
        except RuntimeError as exc:
            last_error = str(exc)
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    return {}, last_error


def post_facebook_source_comment(facebook: dict, object_id: str, message: str, access_token: str) -> tuple[str, str]:
    last_error = ""
    for attempt in range(4):
        try:
            comment_data = http_form_request(
                facebook_post_comment_url(facebook, object_id),
                {
                    "message": message,
                    "access_token": access_token,
                },
            )
            comment_id = str(comment_data.get("id") or "").strip()
            if comment_id:
                return comment_id, ""
            last_error = f"Facebook comment response did not include an id: {comment_data}"
        except RuntimeError as exc:
            last_error = str(exc)
        if attempt < 3:
            time.sleep(3)
    return "", last_error


def facebook_caption_for_project(project: str, fallback_caption: str) -> tuple[str, str]:
    project_dir = require_slide_project(project)
    script_path = project_dir / "script-90s.txt"
    script_lines = [line.strip() for line in script_path.read_text(encoding="utf-8").splitlines() if line.strip()] if script_path.exists() else []
    source_url = first_url_from_source(project_dir)
    caption = str(fallback_caption or "").strip() or upload_paragraphs(script_lines).strip()
    caption = re.sub(r"(?im)^\s*Nguồn:\s*https?://\S+\s*$", "", caption)
    if source_url:
        caption = caption.replace(source_url, "")
    caption = re.sub(r"\n{3,}", "\n\n", caption).strip() or upload_paragraphs(script_lines).strip()
    # Strip the disallowed #Escbase hashtag; convert any plain-text "Escbase" brand mention.
    caption = re.sub(r"#Escbase\b\s*", "", caption, flags=re.IGNORECASE)
    caption = re.sub(r"\bEscbase\b", "KenvinZone", caption, flags=re.IGNORECASE)
    if "#kechuyenchungkhoan" not in caption.lower():
        caption = f"{caption}\n\n#kechuyenchungkhoan".strip()
    return caption[:5000], source_url


def facebook_upload_video(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    video_path = final_video_path_for_project(project)
    metadata = build_upload_metadata(project)
    caption, source_url = facebook_caption_for_project(
        project,
        str(payload.get("facebookCaption") or metadata["facebookCaption"]),
    )

    config = read_social_config()
    facebook = facebook_config(config)
    if not facebook_is_configured(facebook):
        raise ValueError(facebook_config_hint())

    access_token = facebook_page_access_token(facebook)
    video_state = str(payload.get("facebookVideoState") or facebook.get("video_state") or "DRAFT").strip().upper()
    if video_state not in {"DRAFT", "PUBLISHED"}:
        raise ValueError("facebook.video_state must be DRAFT or PUBLISHED.")

    reels_url = facebook_reels_url(facebook)
    start_data = http_form_request(
        reels_url,
        {
            "upload_phase": "start",
            "access_token": access_token,
        },
    )
    video_id = str(start_data.get("video_id") or "").strip()
    if not video_id:
        raise RuntimeError(f"Facebook upload start did not return a video_id: {start_data}")
    upload_url = str(start_data.get("upload_url") or "").strip()
    if not upload_url:
        upload_url = f"https://rupload.facebook.com/video-upload/{facebook_graph_version(facebook)}/{quote(video_id, safe='')}"

    file_size = video_path.stat().st_size
    upload_request = Request(
        upload_url,
        data=video_path.read_bytes(),
        headers={
            "Authorization": f"OAuth {access_token}",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(file_size),
            "offset": "0",
            "file_size": str(file_size),
        },
        method="POST",
    )
    try:
        with urlopen(upload_request, timeout=600) as response:
            upload_text = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Facebook video upload failed: HTTP {exc.code}: {detail}") from exc
    upload_data = json.loads(upload_text) if upload_text.strip() else {}
    if upload_data.get("success") is False:
        raise RuntimeError(f"Facebook video upload failed: {upload_data}")

    finish_fields = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": video_state,
        "description": caption,
        "access_token": access_token,
    }
    finish_data = http_form_request(reels_url, finish_fields)
    if finish_data.get("success") is False:
        raise RuntimeError(f"Facebook upload finish failed: {finish_data}")

    post_id = str(finish_data.get("post_id") or finish_data.get("id") or "").strip()
    comment_target_id = facebook_full_post_id(facebook, post_id or video_id)
    permalink_url = str(finish_data.get("permalink_url") or "").strip()

    reel_url = permalink_url or (f"https://www.facebook.com/reel/{video_id}" if video_id and video_state == "PUBLISHED" else "")
    return {
        "ok": True,
        "platform": "facebook",
        "project": project,
        "page_id": facebook_page_id(facebook),
        "video_id": video_id,
        "post_id": post_id,
        "url": reel_url,
        "source_url": source_url,
        "source_comment_target_id": comment_target_id if video_state == "PUBLISHED" else "",
        "source_comment_id": "",
        "source_comment_error": "",
        "video_state": video_state,
        "message": (
            f"Uploaded to Facebook Reels as {video_state}. Use Comment source after publish to add the source link." if video_state == "PUBLISHED" else
            f"Uploaded to Facebook Reels as {video_state}. Review in Meta Business Suite/Page before publishing if needed."
        ),
    }


def facebook_comment_source(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    metadata = build_upload_metadata(project) if project else {}
    source_comment = str(payload.get("facebookSourceComment") or metadata.get("facebookSourceComment") or "").strip()
    if not source_comment:
        raise ValueError("Source comment is empty.")

    target_id = str(
        payload.get("sourceCommentTargetId")
        or payload.get("source_comment_target_id")
        or payload.get("postId")
        or payload.get("post_id")
        or payload.get("videoId")
        or payload.get("video_id")
        or ""
    ).strip()
    if not target_id:
        raise ValueError("Missing Facebook Reel/Post id. Upload Facebook Reels as PUBLISHED first, then click Comment source.")

    config = read_social_config()
    facebook = facebook_config(config)
    if not facebook_is_configured(facebook):
        raise ValueError(facebook_config_hint())

    access_token = facebook_page_access_token(facebook)
    target_id = facebook_full_post_id(facebook, target_id)
    comment_id, comment_error = post_facebook_source_comment(facebook, target_id, source_comment, access_token)
    if not comment_id:
        raise RuntimeError(f"Facebook source comment failed: {comment_error}")

    return {
        "ok": True,
        "platform": "facebook",
        "project": project,
        "source_comment_target_id": target_id,
        "source_comment_id": comment_id,
        "message": "Source link was posted as a Facebook comment.",
    }


def http_multipart_post(url: str, fields: dict[str, str], files: dict[str, tuple[str, bytes, str]], timeout: int = 120) -> dict:
    boundary = f"----FormBoundary{uuid.uuid4().hex}"
    parts = []
    
    for name, value in fields.items():
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
        
    for name, (filename, content, mime_type) in files.items():
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode("utf-8"))
        parts.append(f"Content-Type: {mime_type}".encode("utf-8"))
        parts.append(b"")
        parts.append(content)
        
    parts.append(f"--{boundary}--".encode("utf-8"))
    parts.append(b"")
    
    body = b"\r\n".join(parts)
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        
    return json.loads(text) if text.strip() else {}


def facebook_upload_post(payload: dict) -> dict:
    project = str(payload.get("project") or "").strip()
    message = str(payload.get("facebookPostMessage") or "").strip()
    link = str(payload.get("facebookPostLink") or "").strip()
    image_base64 = str(payload.get("imageBase64") or "").strip()
    image_name = str(payload.get("imageName") or "image.jpg").strip()

    if not message:
        raise ValueError("Nội dung bài viết không được để trống.")

    config = read_social_config()
    facebook = facebook_config(config)
    if not facebook_is_configured(facebook):
        raise ValueError(facebook_config_hint())

    access_token = facebook_page_access_token(facebook)
    page_id = facebook_page_id(facebook)
    version = facebook_graph_version(facebook)

    if image_base64:
        import base64
        if "," in image_base64:
            header, encoded = image_base64.split(",", 1)
        else:
            encoded = image_base64
        image_bytes = base64.b64decode(encoded)

        ext = image_name.split(".")[-1].lower()
        mime_type = "image/jpeg"
        if ext == "png":
            mime_type = "image/png"
        elif ext == "gif":
            mime_type = "image/gif"
        elif ext == "webp":
            mime_type = "image/webp"

        photos_url = f"https://graph.facebook.com/{version}/{quote(page_id, safe='')}/photos"
        result = http_multipart_post(
            photos_url,
            {
                "caption": message,
                "access_token": access_token,
            },
            {
                "source": (image_name, image_bytes, mime_type)
            }
        )
        post_id = str(result.get("post_id") or result.get("id") or "").strip()
    else:
        feed_url = f"https://graph.facebook.com/{version}/{quote(page_id, safe='')}/feed"
        post_data = {
            "message": message,
            "access_token": access_token,
        }
        if link:
            post_data["link"] = link
        result = http_form_request(feed_url, post_data)
        post_id = str(result.get("id") or "").strip()

    if not post_id:
        raise RuntimeError(f"Facebook page post failed: {result}")

    return {
        "ok": True,
        "platform": "facebook-post",
        "project": project,
        "page_id": page_id,
        "post_id": post_id,
        "url": f"https://www.facebook.com/{post_id}",
        "message": "Đăng bài viết lên Facebook Page thành công.",
    }
