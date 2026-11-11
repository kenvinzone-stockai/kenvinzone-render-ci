#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐÓNG GÓI bài học Explainer Trading -> slide project cho ci_build_video.py.

Đây là LỚP ĐÓNG GÓI tất định (không gọi AI). Bộ não sinh nội dung
(build_explainer_deck.py — Brain Type C của ANTI) sẽ xuất ra đúng định dạng
"lesson JSON" dưới đây rồi gọi lớp này; trước khi Brain sẵn sàng, bài học
viết tay / Claude soạn đặt trong lessons/explainer/*.json cũng chạy được ngay.

Lesson JSON = toàn bộ trường hf-data của template aurora-trading-explainer-hf
(template, header, chart_data, visual_events, telemetry, outro, bgm...)
CỘNG THÊM 2 khóa bị tách ra khi đóng gói:
    "script": [9 dòng thoại — mỗi dòng 1 cảnh s0..s8, nhịp câu 1-3-3-3-4-4-3-3-3]
    "upload": upload-metadata.json (youtube/tiktok/facebook_reels...)
Tùy chọn: "project" (tên thư mục; mặc định sinh từ topic_id + ngày).

Dùng:
    python make_explainer_project.py lessons/explainer/sample-sideway-b.json
In dòng cuối:  PROJECT=<tên thư mục slide>  (workflow grep lấy).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
TEMPLATE = "aurora-trading-explainer-hf"
SENT_PATTERN = [1, 3, 3, 3, 4, 4, 3, 3, 3]   # nhịp câu chuẩn 9 cảnh (đã chốt với ANTI)
MAX_WORDS = 720                               # trần ~3 phút (chuẩn Giải Mã < 3 min)


def slugify(s: str, maxlen: int = 44) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:maxlen].strip("-") or "bai-hoc"


def nsents(line: str) -> int:
    return len([x for x in re.split(r"(?<=[.!?…])\s+", line.strip()) if x])


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Dùng: python make_explainer_project.py <lesson.json> [--force]")
    src = Path(sys.argv[1])
    if not src.is_absolute():
        src = REPO / src
    lesson = json.loads(src.read_text(encoding="utf-8"))

    # --- tách script + upload ra khỏi phần hf-data -------------------------
    script = lesson.pop("script", None)
    upload = lesson.pop("upload", None)
    proj_name = lesson.pop("project", None)

    errs = []
    if not isinstance(script, list) or len(script) != 9:
        errs.append(f"script phải là 9 dòng (s0..s8), đang có {len(script) if isinstance(script, list) else 'không có'}")
    else:
        for i, (line, want) in enumerate(zip(script, SENT_PATTERN)):
            got = nsents(line)
            if got != want:
                errs.append(f"script dòng s{i}: cần {want} câu, đang có {got}")
        words = sum(len(l.split()) for l in script)
        if words > MAX_WORDS:
            errs.append(f"script {words} từ > trần {MAX_WORDS} (video sẽ vượt 3 phút)")

    lesson.setdefault("template", TEMPLATE)
    if lesson["template"] != TEMPLATE:
        errs.append(f"template phải là {TEMPLATE}, đang là {lesson['template']}")

    # contract v2 (ANTI): scenes.s0..s8, mỗi cảnh tự khai báo phần tử + telemetry
    scenes = lesson.get("scenes") or {}
    missing = [f"s{i}" for i in range(9) if f"s{i}" not in scenes]
    if missing:
        errs.append(f"scenes thiếu cảnh: {', '.join(missing)}")
    for cid, s in scenes.items():
        if not isinstance(s.get("telemetry"), dict):
            errs.append(f"scenes.{cid} thiếu telemetry {{left,right}}")
    s1, s3 = scenes.get("s1", {}), scenes.get("s3", {})
    if not s1.get("sideway_candles"):
        errs.append("scenes.s1.sideway_candles trống")
    if not (s3.get("volume_profile") or {}).get("bins"):
        errs.append("scenes.s3.volume_profile.bins trống")
    if not isinstance(upload, dict) or not (upload.get("youtube") or {}).get("title"):
        errs.append("upload.youtube.title trống (cần cho ci_build_video upload)")
    if errs:
        for e in errs:
            print("  [LỖI]", e)
        sys.exit("Lesson JSON chưa đạt chuẩn — sửa các lỗi trên rồi chạy lại.")

    # --- tên project -------------------------------------------------------
    today = datetime.now().strftime("%d-%m")
    if not proj_name:
        base = lesson.get("topic_id") or (lesson.get("header") or {}).get("title") or "explainer"
        proj_name = f"giai-ma-trading-{slugify(base)}-{today}"
    out = REPO / "slide" / proj_name
    if out.exists() and "--force" not in sys.argv[2:]:
        sys.exit(f"slide/{proj_name} đã tồn tại — thêm --force để ghi đè.")
    out.mkdir(parents=True, exist_ok=True)

    # --- ghi 3 file chuẩn slide project ------------------------------------
    (out / "hf-data.json").write_text(
        json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "script-90s.txt").write_text("\n".join(l.strip() for l in script) + "\n",
                                        encoding="utf-8")
    (out / "upload-metadata.json").write_text(
        json.dumps(upload, ensure_ascii=False, indent=2), encoding="utf-8")

    total_w = sum(len(l.split()) for l in script)
    bins = (s3.get("volume_profile") or {}).get("bins", [])
    print(f"  Đã đóng gói slide/{proj_name}: script 9 dòng / {total_w} từ, "
          f"9 cảnh scenes, VP {len(bins)} bins (POC @ {s3.get('volume_profile', {}).get('poc_price')}).")
    print(f"PROJECT={proj_name}")


if __name__ == "__main__":
    main()
