from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote, unquote

REPO_ROOT = Path(__file__).resolve().parents[1]
SLIDE_ROOT = REPO_ROOT / "slide"


def sanitize_and_truncate_for_youtube(text: str, max_code_units: int) -> str:
    if not text:
        return ""
    # YouTube API does not allow '<' and '>' in title/description/tags.
    # Replace '<' with Unicode full-width '＜' (U+FF1C) and '>' with Unicode full-width '＞' (U+FF1E).
    text = text.replace("<", "＜").replace(">", "＞")
    
    # Remove control characters except newline, carriage return, and tab.
    text = "".join(ch for ch in text if ch >= " " or ch in "\n\r\t")
    
    # Truncate to maximum UTF-16 code units (YouTube character limit).
    # UTF-16-LE encodes each code unit as 2 bytes.
    encoded = text.encode("utf-16-le")
    if len(encoded) <= max_code_units * 2:
        return text
        
    limit = max_code_units * 2
    if limit >= 2:
        # Check value of the last 16-bit word to avoid slicing in the middle of a surrogate pair.
        val = int.from_bytes(encoded[limit-2:limit], byteorder="little")
        if 0xD800 <= val <= 0xDBFF:
            limit -= 2
            
    return encoded[:limit].decode("utf-16-le", errors="ignore")


def validate_project_name(project: str) -> str:
    project = unquote(str(project or "")).strip()
    if not project or project in {".", ".."} or "/" in project or "\\" in project or "\x00" in project:
        raise ValueError("Invalid project name.")
    return project


def require_slide_project(project: str) -> Path:
    project = validate_project_name(project)
    project_dir = (SLIDE_ROOT / project).resolve()
    try:
        project_dir.relative_to(SLIDE_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Invalid project path.") from exc
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Project '{project}' not found.")
    return project_dir


def final_video_url(project: str) -> str:
    return f"/slide/{quote(project)}/output/final_video.mp4"


def final_video_path_for_project(project: str) -> Path:
    project_dir = require_slide_project(project)
    video_path = (project_dir / "output" / "final_video.mp4").resolve()
    try:
        video_path.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid video path.") from exc
    if not video_path.is_file():
        raise FileNotFoundError(f"final_video.mp4 not found for project '{project_dir.name}'.")
    return video_path


def first_url_from_source(project_dir: Path) -> str:
    links = project_dir / "source" / "links.txt"
    if links.exists():
        for line in links.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("http"):
                return stripped
    source = project_dir / "source" / "source.md"
    if source.exists():
        match = re.search(r"https?://\S+", source.read_text(encoding="utf-8", errors="replace"))
        if match:
            return match.group(0).rstrip(").,")
    return ""


def upload_metadata_path(project_dir: Path) -> Path:
    return project_dir / "upload-metadata.json"


def read_script_lines(project_dir: Path) -> list[str]:
    script_path = project_dir / "script-90s.txt"
    if not script_path.exists():
        return []
    return [line.strip() for line in script_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def upload_paragraphs(lines: list[str]) -> str:
    icons = ["🎬", "🔎", "💡", "🧠", "⚡", "✅", "📌"]
    paragraphs = []
    for index, line in enumerate(lines):
        text = re.sub(r"\s+", " ", line).strip()
        if text:
            paragraphs.append(f"{icons[index % len(icons)]} {text}")
    return "\n\n".join(paragraphs)


def limit_youtube_title(value: str) -> str:
    title = re.sub(r"\s+", " ", str(value or "")).strip()
    return title if len(title) <= 100 else title[:97].rstrip(" .,;:-") + "..."


def read_project_upload_metadata(project_dir: Path) -> dict:
    metadata_path = upload_metadata_path(project_dir)
    if not metadata_path.exists():
        return {}
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"upload-metadata.json is invalid JSON: {metadata_path}") from exc
    return data if isinstance(data, dict) else {}


# Default channel hashtags (used when a project has no trailing hashtag block).
DEFAULT_HASHTAGS = "#giaimachungkhoan #kechuyenchungkhoan #xuhuongchungkhoan"


def _strip_banned_hashtags(line: str) -> str:
    """Remove disallowed hashtags (e.g. #Escbase) from a hashtag line."""
    tokens = [t for t in str(line).split() if t.lower() != "#escbase"]
    return " ".join(tokens)


def trailing_hashtag_block(value: str, fallback: str = DEFAULT_HASHTAGS) -> str:
    lines = [line.strip() for line in str(value or "").splitlines()]
    trailing = []
    for line in reversed(lines):
        if not line:
            if trailing:
                continue
            continue
        if line.startswith("#"):
            trailing.append(line)
            continue
        break
    trailing.reverse()
    block = "\n".join(trailing) if trailing else fallback
    block = "\n".join(_strip_banned_hashtags(line) for line in block.splitlines())
    block = "\n".join(line for line in block.splitlines() if line.strip()).strip()
    return block or fallback


def merge_upload_metadata(defaults: dict, custom: dict) -> dict:
    if not custom:
        return defaults
    result = json.loads(json.dumps(defaults, ensure_ascii=False))
    for section in ("youtube", "facebook", "facebook_post", "tiktok", "instagram"):
        if isinstance(custom.get(section), dict):
            result.setdefault(section, {}).update(custom[section])
    for key, value in custom.items():
        if key not in {"youtube", "facebook", "facebook_post", "tiktok", "instagram"}:
            result[key] = value
    return result


def generated_upload_metadata(project_dir: Path, script_lines: list[str], existing: dict | None = None) -> dict:
    existing = existing if isinstance(existing, dict) else {}
    first_line = script_lines[0] if script_lines else project_dir.name.replace("-", " ").title()
    title = sanitize_and_truncate_for_youtube(limit_youtube_title(first_line), 100)
    source_url = first_url_from_source(project_dir)
    script_text = upload_paragraphs(script_lines).strip() or first_line
    existing_youtube = existing.get("youtube", {}) if isinstance(existing.get("youtube"), dict) else {}
    existing_facebook = existing.get("facebook", {}) if isinstance(existing.get("facebook"), dict) else {}
    existing_facebook_post = existing.get("facebook_post", {}) if isinstance(existing.get("facebook_post"), dict) else {}
    youtube_hashtags = trailing_hashtag_block(str(existing_youtube.get("description") or ""), DEFAULT_HASHTAGS)
    facebook_hashtags = trailing_hashtag_block(str(existing_facebook.get("caption") or ""), youtube_hashtags)
    youtube_description_parts = [script_text or first_line]
    if source_url:
        youtube_description_parts.append(f"Nguồn: {source_url}")
    youtube_description_parts.append(youtube_hashtags)
    facebook_caption_parts = [script_text or first_line, facebook_hashtags]
    youtube_description = sanitize_and_truncate_for_youtube("\n\n".join(youtube_description_parts), 5000)
    facebook_caption = "\n\n".join(facebook_caption_parts)
    raw_tags = existing_youtube.get("tags") if isinstance(existing_youtube.get("tags"), list) else ["Kể Chuyện Chứng Khoán", "KenvinZone", "chứng khoán", "VN-Index", "F0 chứng khoán"]
    youtube_tags = [sanitize_and_truncate_for_youtube(str(t), 100) for t in raw_tags] if raw_tags else []
    
    facebook_post_message = str(existing_facebook_post.get("message") or facebook_caption)
    facebook_post_link = str(existing_facebook_post.get("link") or "")
    
    return {
        "version": int(existing.get("version") or 1) if isinstance(existing.get("version", 1), int) else 1,
        "youtube": {
            "title": title,
            "description": youtube_description,
            "privacyStatus": str(existing_youtube.get("privacyStatus") or "private"),
            "tags": youtube_tags,
        },
        "facebook": {
            "caption": facebook_caption,
            "videoState": str(existing_facebook.get("videoState") or "DRAFT").upper(),
            "sourceComment": str(existing_facebook.get("sourceComment") or (f"Nguồn: {source_url}" if source_url else "")),
        },
        "facebook_post": {
            "message": facebook_post_message,
            "link": facebook_post_link,
        },
    }


def write_project_upload_metadata(project_dir: Path, metadata: dict) -> None:
    encoded = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
    if len(encoded) > 200_000:
        raise ValueError("upload-metadata.json is too large.")
    upload_metadata_path(project_dir).write_bytes(encoded + b"\n")


def sync_upload_metadata_from_script(project: str, script_lines: list[str] | None = None) -> dict:
    project_dir = require_slide_project(project)
    lines = script_lines if script_lines is not None else read_script_lines(project_dir)
    existing = read_project_upload_metadata(project_dir)
    metadata = generated_upload_metadata(project_dir, lines, existing)
    write_project_upload_metadata(project_dir, metadata)
    return metadata


def build_upload_metadata(project: str) -> dict:
    project_dir = require_slide_project(project)
    script_lines = read_script_lines(project_dir)
    defaults = generated_upload_metadata(project_dir, script_lines, {})
    metadata = merge_upload_metadata(defaults, read_project_upload_metadata(project_dir))
    source_url = first_url_from_source(project_dir)
    youtube = metadata.get("youtube", {}) if isinstance(metadata.get("youtube"), dict) else {}
    facebook = metadata.get("facebook", {}) if isinstance(metadata.get("facebook"), dict) else {}
    default_youtube = defaults.get("youtube", {})
    default_facebook = defaults.get("facebook", {})
    facebook_post = metadata.get("facebook_post", {}) if isinstance(metadata.get("facebook_post"), dict) else {}
    default_facebook_post = defaults.get("facebook_post", {}) if isinstance(defaults.get("facebook_post"), dict) else {}
    tiktok = metadata.get("tiktok", {}) if isinstance(metadata.get("tiktok"), dict) else {}
    raw_tags = youtube.get("tags") if isinstance(youtube.get("tags"), list) else ["Kể Chuyện Chứng Khoán", "KenvinZone", "chứng khoán", "VN-Index", "F0 chứng khoán"]
    youtube_tags = [sanitize_and_truncate_for_youtube(str(t), 100) for t in raw_tags] if raw_tags else []
    return {
        "project": project_dir.name,
        "title": sanitize_and_truncate_for_youtube(limit_youtube_title(str(youtube.get("title") or default_youtube.get("title") or project_dir.name)), 100),
        "description": sanitize_and_truncate_for_youtube(str(youtube.get("description") or default_youtube.get("description") or ""), 5000),
        "youtubeDescription": sanitize_and_truncate_for_youtube(str(youtube.get("description") or default_youtube.get("description") or ""), 5000),
        "facebookCaption": str(facebook.get("caption") or default_facebook.get("caption") or ""),
        "facebookVideoState": str(facebook.get("videoState") or "DRAFT").upper(),
        "facebookSourceComment": str(facebook.get("sourceComment") or (f"Nguồn: {source_url}" if source_url else "")),
        "facebookPostMessage": str(facebook_post.get("message") or default_facebook_post.get("message") or ""),
        "facebookPostLink": str(facebook_post.get("link") or default_facebook_post.get("link") or ""),
        "tiktokTitle": str(tiktok.get("title") or ""),
        "source_url": source_url,
        "privacyStatus": str(youtube.get("privacyStatus") or "private"),
        "tags": youtube_tags,
        "education_seo": youtube.get("education_seo") if isinstance(youtube.get("education_seo"), dict) else None,
        "seo_generated": bool(metadata.get("seo_generated")),
        "upload_metadata_url": f"/slide/{quote(project_dir.name)}/upload-metadata.json",
        "upload_metadata_exists": upload_metadata_path(project_dir).exists(),
        "video_url": final_video_url(project_dir.name),
    }
