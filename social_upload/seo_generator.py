"""AI-powered SEO metadata generator for video uploads.

Uses Gemini API (same key as TTS) to generate optimized titles, descriptions,
tags, and hashtags for YouTube, TikTok, Facebook Reels, and Instagram Reels.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Master Prompt — channel identity & SEO rules
# ---------------------------------------------------------------------------
MASTER_PROMPT = r"""Bạn là Chuyên gia SEO Video chứng khoán Việt Nam.

## THÔNG TIN KÊNH
- Tên kênh: Kể Chuyện Chứng Khoán - KenvinZone
- Handle: @kechuyen.chungkhoan
- Brand watermark: KenvinZone Analytics
- Audience: Nhà đầu tư F0 Việt Nam, 25-45 tuổi
- Tone: Anh hàng xóm kể chuyện — thân thiện, ví von đời thường, xen số liệu cụ thể

## CÁC LOẠI VIDEO
1. vnindex-story: VNINDEX Daily (Shorts 60-90s) — phân tích phiên sáng/chiều
2. giai-ma-tin-tuc: Giải Mã Tin Tức (Shorts 60-90s) — tin vĩ mô ảnh hưởng CK
3. vnindex-weekly-report: Tổng Kết Tuần (Shorts 60-90s) — tổng hợp 5 phiên
4. giai-ma-nganh: Giải Mã Ngành (Long-form 3-5 phút) — phân tích chuyên sâu ngành
5. explainer: Bài Học F0 (Long-form 3-8 phút) — kiến thức nền tảng, bẫy tâm lý

## QUY TẮC TIÊU ĐỀ YOUTUBE (≤100 ký tự)
- Công thức: [HOOK CẢM XÚC] + [CHỦ ĐỀ CỤ THỂ] + [CON SỐ/KẾT QUẢ]
- Ưu tiên con số cụ thể (+85%, top 5, 3 bước...)
- VIẾT HOA chọn lọc chỉ 1-2 từ quan trọng
- KHÔNG clickbait lố, KHÔNG hứa lợi nhuận

## QUY TẮC TIKTOK TITLE (≤150 ký tự, kèm hashtag)
- Hook 1 câu viral + hashtag trực tiếp

## QUY TẮC MÔ TẢ YOUTUBE (≤5000 ký tự)
- Hook 1-2 câu (KHÔNG copy tiêu đề)
- 📌 Nội dung video: 3-5 bullet points
- 🔔 CTA đăng ký kênh
- ⚠️ Disclaimer: "Nội dung mang tính giáo dục, không phải khuyến nghị đầu tư"
- Hashtag cuối: LUÔN bắt đầu bằng 3 hashtag mặc định #giaimachungkhoan #kechuyenchungkhoan #xuhuongchungkhoan + 3-5 hashtag nội dung
- TUYỆT ĐỐI KHÔNG dùng hashtag #Escbase hay #escbase trong bất kỳ nền tảng nào

## TAGS YOUTUBE (tối đa 15)
5 cố định: Kể Chuyện Chứng Khoán, KenvinZone, chứng khoán, VN-Index, F0 chứng khoán
+ 10 tags động theo nội dung (tên cổ phiếu, nhóm ngành, khái niệm, trending, search intent)

## CAPTION FACEBOOK REELS (<500 ký tự)
- Hook 1 câu + 2-3 câu tóm tắt + CTA YouTube + hashtag

## CAPTION INSTAGRAM REELS (<2200 ký tự)
- Giống FB nhưng dài hơn, 10-15 hashtag

## LƯU Ý
- LUÔN kèm disclaimer giáo dục
- Hashtag mặc định #giaimachungkhoan #kechuyenchungkhoan #xuhuongchungkhoan LUÔN xuất hiện đầu khối hashtag
- KHÔNG BAO GIỜ dùng #Escbase
- KHÔNG đưa ra khuyến nghị mua/bán cụ thể"""

# ---------------------------------------------------------------------------
# Gemini API call
# ---------------------------------------------------------------------------

def _gemini_api_key() -> str:
    """Resolve Gemini API key from env or config file."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    config_path = REPO_ROOT / "config" / "tts.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            key = str((data.get("gemini") or {}).get("api_key") or "").strip()
        except (json.JSONDecodeError, OSError):
            pass
    if not key:
        raise ValueError("Missing Gemini API key. Set GEMINI_API_KEY env var or add to config/tts.json.")
    return key


def _call_gemini(prompt: str, user_message: str) -> str:
    """Call Gemini API for text generation (not TTS)."""
    import urllib.request
    import urllib.error

    api_key = _gemini_api_key()
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    body = json.dumps({
        "contents": [
            {"role": "user", "parts": [{"text": user_message}]}
        ],
        "systemInstruction": {"parts": [{"text": prompt}]},
        "generationConfig": {
            "temperature": 0.8,
            "responseMimeType": "application/json",
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST",
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"Gemini API error {exc.code}: {error_body[:500]}") from exc

    # Extract text from Gemini response
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {json.dumps(result, ensure_ascii=False)[:500]}") from exc

    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_template_type(project_dir: Path) -> str:
    """Detect template type from project directory name or TEMPLATE_RULES.md."""
    name = project_dir.name.lower()
    rules_file = project_dir / "TEMPLATE_RULES.md"
    if rules_file.exists():
        content = rules_file.read_text(encoding="utf-8", errors="replace")[:500]
        for tpl in ("giai-ma-nganh", "giai-ma-tin-tuc", "vnindex-weekly-report", "vnindex-story", "explainer"):
            if tpl in content.lower():
                return tpl

    if "giai-ma-nganh" in name or "nganh" in name:
        return "giai-ma-nganh"
    if "giai-ma-tin" in name or "msci" in name or "tin-tuc" in name:
        return "giai-ma-tin-tuc"
    if "weekly" in name or "tong-ket" in name:
        return "vnindex-weekly-report"
    if "explainer" in name or "bai-hoc" in name or "f0" in name:
        return "explainer"
    return "vnindex-story"


def generate_seo_metadata(project: str, script_lines: list[str] | None = None) -> dict:
    """Generate AI-optimized SEO metadata for all platforms.

    Args:
        project: Project directory name under slide/
        script_lines: TTS script lines. If None, reads from script-90s.txt.

    Returns:
        Dict with youtube, tiktok, facebook, instagram sections.
    """
    from .metadata import require_slide_project, read_script_lines

    project_dir = require_slide_project(project)
    if script_lines is None:
        script_lines = read_script_lines(project_dir)

    if not script_lines:
        raise ValueError("No script content found. Write script-90s.txt first.")

    template_type = detect_template_type(project_dir)
    script_text = "\n".join(script_lines)

    user_message = f"""Tạo SEO metadata cho video sau:

**Loại video:** {template_type}
**Project:** {project}

**Nội dung script (giọng đọc TTS):**
{script_text}

Trả về JSON với cấu trúc chính xác sau (KHÔNG thêm field nào khác):
{{
  "youtube": {{
    "title": "Tiêu đề ≤100 ký tự",
    "title_variants": ["Phương án 2", "Phương án 3"],
    "description": "Mô tả YouTube đầy đủ với emoji, CTA, disclaimer, hashtag",
    "tags": ["tag1", "tag2", "... tối đa 15 tags"],
    "privacyStatus": "public"
  }},
  "tiktok": {{
    "title": "Title ≤150 ký tự kèm hashtag",
    "upload_mode": "inbox",
    "privacy_level": "PUBLIC_TO_EVERYONE"
  }},
  "facebook": {{
    "caption": "Caption <500 ký tự với emoji + hashtag",
    "videoState": "PUBLISHED"
  }},
  "instagram": {{
    "caption": "Caption <2200 ký tự với hashtag"
  }}
}}"""

    raw = _call_gemini(MASTER_PROMPT, user_message)

    # Parse JSON from response
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
        else:
            raise ValueError(f"Gemini did not return valid JSON: {raw[:500]}")

    # Validate structure
    for key in ("youtube", "tiktok", "facebook"):
        if key not in result or not isinstance(result[key], dict):
            raise ValueError(f"Missing or invalid '{key}' section in SEO output.")

    # Enforce title length
    yt = result.get("youtube", {})
    if yt.get("title") and len(yt["title"]) > 100:
        yt["title"] = yt["title"][:97].rstrip(" .,;:-") + "..."

    return result


def apply_seo_to_upload_metadata(project: str, seo: dict) -> dict:
    """Merge AI-generated SEO into upload-metadata.json and save.

    Returns the merged metadata.
    """
    from .metadata import (
        require_slide_project,
        read_project_upload_metadata,
        write_project_upload_metadata,
        read_script_lines,
        generated_upload_metadata,
        merge_upload_metadata,
    )

    project_dir = require_slide_project(project)
    existing = read_project_upload_metadata(project_dir)

    # Build base metadata
    script_lines = read_script_lines(project_dir)
    base = generated_upload_metadata(project_dir, script_lines, existing)

    # Overlay AI SEO onto base
    yt_seo = seo.get("youtube", {})
    if yt_seo:
        base.setdefault("youtube", {}).update({
            k: v for k, v in yt_seo.items() if v is not None
        })

    fb_seo = seo.get("facebook", {})
    if fb_seo:
        base.setdefault("facebook", {}).update({
            k: v for k, v in fb_seo.items() if v is not None
        })

    tk_seo = seo.get("tiktok", {})
    if tk_seo:
        base["tiktok"] = tk_seo

    ig_seo = seo.get("instagram", {})
    if ig_seo:
        base["instagram"] = ig_seo

    # Store title variants for reference
    if yt_seo.get("title_variants"):
        base["youtube"]["title_variants"] = yt_seo["title_variants"]

    # Mark as AI-generated
    base["seo_generated"] = True

    write_project_upload_metadata(project_dir, base)
    return base
