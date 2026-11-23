#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐÓNG GÓI bài Promo Coupon Prop Futures -> slide project cho ci_build_video.py.

Dùng:
    python make_prop_promo.py lessons/prop-promo/e2t-blackweek-2026.json --force
In dòng cuối: PROJECT=<tên thư mục slide>
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
TEMPLATE = "prop-promo-hf"
MAX_WORDS = 260


def slugify(s: str, maxlen: int = 44) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:maxlen].strip("-") or "prop-promo"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Dùng: python make_prop_promo.py <promo.json> [--force]")
    src = Path(sys.argv[1])
    if not src.is_absolute():
        src = REPO / src
    data = json.loads(src.read_text(encoding="utf-8"))

    script = data.pop("script", None)
    upload = data.pop("upload", None)
    proj_name = data.pop("project", None)

    errs = []
    if not isinstance(script, list) or len(script) != 5:
        errs.append(f"script phải có đúng 5 dòng (s0..s4), đang có {len(script) if isinstance(script, list) else 0}")
    else:
        words = sum(len(l.split()) for l in script)
        if words > MAX_WORDS:
            errs.append(f"script promo {words} từ > trần {MAX_WORDS} (nên giữ gọn 30–50 giây)")
        print(f"  [prop-promo] {words} từ ≈ {words/4.1 + 4:.0f}s video")
    if not isinstance(upload, dict) or not (upload.get("youtube") or {}).get("title"):
        errs.append("thiếu upload.youtube.title")
    if errs:
        for e in errs:
            print("  [LỖI]", e)
        sys.exit("Promo JSON chưa đạt chuẩn.")

    data["template"] = TEMPLATE
    today_slug = datetime.now().strftime("%d-%m")
    data["date"] = datetime.now().strftime("%d/%m/%Y")
    if not proj_name:
        base = data.get("coupon_id") or data.get("firm") or "promo"
        proj_name = f"prop-promo-{slugify(base)}-{today_slug}"

    out = REPO / "slide" / proj_name
    if out.exists() and "--force" not in sys.argv[2:]:
        sys.exit(f"slide/{proj_name} đã tồn tại — thêm --force để ghi đè.")
    out.mkdir(parents=True, exist_ok=True)

    (out / "hf-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "script-90s.txt").write_text("\n".join(l.strip() for l in script) + "\n", encoding="utf-8")
    (out / "upload-metadata.json").write_text(json.dumps(upload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PROJECT={proj_name}")


if __name__ == "__main__":
    main()
