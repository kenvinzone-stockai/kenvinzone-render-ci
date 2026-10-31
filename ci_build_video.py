#!/usr/bin/env python3
"""CI driver: TTS -> render HyperFrames -> upload YouTube for ONE slide project.

Runs in GitHub Actions (or any Linux box with Node 22+, ffmpeg, Chromium).
Reuses the channel's existing modules unchanged:
    generate_tts.py         -> output/voiceover_concat.mp3 + output/timing.json
    render_hyperframes.py   -> output/final_video.mp4   (frame-by-frame, mượt)
    social_upload/youtube   -> upload (headless, dùng refresh_token sẵn có)

Usage:
    python ci_build_video.py slide/<name> [--privacy private|unlisted|public] [--no-upload]

Secrets (env):
    GEMINI_API_KEY      Gemini TTS key (tts.gemini đọc trực tiếp từ env này)
    SOCIAL_UPLOAD_JSON  toàn bộ nội dung config/social-upload.json (client + channels + refresh_token)
    YT_CHANNEL_ID       (tùy chọn) id kênh YouTube muốn đăng; mặc định kênh active trong config
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

# Preset giọng đọc Gemini theo loại template (khớp style-preset trong tts/gemini.py)
STYLE_PRESET = {
    "giaima-tin-hf": "giai-ma-nganh",
    "vnindex-daily-hf": "ban-tin-vnindex",
    "gold-daily-bias-hf": "giai-ma-nganh",
    "aurora-explainer-hf": "giai-ma-nganh",
}


def restore_social_config() -> None:
    """Tái tạo config/social-upload.json từ secret SOCIAL_UPLOAD_JSON."""
    raw = os.environ.get("SOCIAL_UPLOAD_JSON", "").strip()
    if not raw:
        print("  [cảnh báo] Thiếu SOCIAL_UPLOAD_JSON — chỉ chạy được khi có --no-upload.")
        return
    try:
        json.loads(raw)  # validate
    except json.JSONDecodeError as exc:
        sys.exit(f"SOCIAL_UPLOAD_JSON không phải JSON hợp lệ: {exc}")
    cfg = REPO / "config" / "social-upload.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(raw, encoding="utf-8")
    try:
        os.chmod(cfg, 0o600)
    except OSError:
        pass
    print("  Đã tái tạo config/social-upload.json từ secret.")


def restore_tts_config() -> None:
    """Tái tạo config/tts.json từ secret TTS_CONFIG_JSON (giọng clone + style + api_key)."""
    raw = os.environ.get("TTS_CONFIG_JSON", "").strip()
    if not raw:
        print("  [cảnh báo] Thiếu TTS_CONFIG_JSON — sẽ dùng giọng mặc định, KHÔNG phải giọng clone.")
        return
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"TTS_CONFIG_JSON không phải JSON hợp lệ: {exc}")
    cfg = REPO / "config" / "tts.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(raw, encoding="utf-8")
    try:
        os.chmod(cfg, 0o600)
    except OSError:
        pass
    print("  Đã tái tạo config/tts.json (giọng clone).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slide_dir", help="vd: slide/giai-ma-tin-tuc-quangtramctck-27-10")
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--no-upload", action="store_true", help="Chỉ TTS + render, không upload")
    ap.add_argument("--engine", default="gemini", choices=["gemini", "edge", "elevenlabs"])
    args = ap.parse_args()

    slide = Path(args.slide_dir)
    if not slide.is_absolute():
        slide = REPO / slide
    slide = slide.resolve()
    if not (slide / "hf-data.json").exists():
        sys.exit(f"Không thấy hf-data.json trong {slide}")
    project = slide.name
    data = json.loads((slide / "hf-data.json").read_text(encoding="utf-8"))
    tpl = str(data.get("template") or "giaima-tin-hf")
    preset = str(data.get("style_preset") or STYLE_PRESET.get(tpl, "giai-ma-nganh"))

    print(f"=== DECK: {project} | template={tpl} | preset giọng={preset} ===", flush=True)

    restore_tts_config()
    if not args.no_upload:
        restore_social_config()

    # 1) TTS — giọng + style lấy từ config/tts.json (auto-clone). Chỉ ép style-preset nếu deck khai báo.
    print(f"=== [1/3] Tạo giọng đọc ({args.engine}) ===", flush=True)
    tts_cmd = [sys.executable, str(REPO / "generate_tts.py"), str(slide),
               "--engine", args.engine, "--gemini-mode", "full"]
    style_preset = data.get("style_preset")
    if style_preset:
        tts_cmd += ["--style-preset", str(style_preset)]
    tts = subprocess.run(tts_cmd, cwd=str(REPO))
    if tts.returncode != 0:
        sys.exit(f"TTS thất bại (exit {tts.returncode})")

    # 2) Render HyperFrames (mượt, từng khung)
    print("=== [2/3] Render HyperFrames (30fps đầy đủ) ===", flush=True)
    sys.path.insert(0, str(REPO))
    from render_hyperframes import render_hyperframes
    final = render_hyperframes(slide)
    print(f"  Video: {final}", flush=True)

    # 3) Upload YouTube
    if args.no_upload:
        print("=== [3/3] Bỏ qua upload (--no-upload). Xong. ===")
        return
    print(f"=== [3/3] Upload YouTube (privacy={args.privacy}) ===", flush=True)
    chan = os.environ.get("YT_CHANNEL_ID", "").strip()
    if chan:
        from social_upload.youtube import set_youtube_active_channel
        set_youtube_active_channel(chan)
    from social_upload.youtube import youtube_upload_video
    result = youtube_upload_video({"project": project, "privacyStatus": args.privacy})
    print(json.dumps(result, ensure_ascii=False), flush=True)
    (REPO / "upload-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Xong: {result.get('url')}")


if __name__ == "__main__":
    main()
