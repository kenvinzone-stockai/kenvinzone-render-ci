#!/usr/bin/env python3
"""KHUNG MẪU — BRAIN KIỂU B: SỐ LIỆU ĐỊNH LƯỢNG (JSON) -> DECK.

Khác kiểu A: SỐ LIỆU lấy TẤT ĐỊNH từ nguồn (không để AI bịa). Gemini CHỈ viết phần KỂ CHUYỆN
(kịch bản, nhãn đọc, mô tả). An toàn & ổn định hơn cho báo cáo định kỳ.

CÁCH DÙNG:
  1) Copy thành  build_<loại>_deck.py  ở gốc repo.
  2) Sửa các chỗ  # >>> SỬA:
        - TEMPLATE_NAME, STYLE_PRESET
        - hàm pick_data()  : rút đúng số liệu bạn cần từ JSON nguồn
        - hàm build_scenes(): map số liệu -> các khối hf-data (s1..s7)
        - SPEC_STORY       : prompt cho Gemini CHỈ viết phần chữ (script, scenarios, mô tả)
  3) Gọi:  python build_<loại>_deck.py --data <nguồn.json> --frame daily|weekly [--date DD/MM/YYYY]
  In ra  PROJECT=<tên>  ở DÒNG CUỐI.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from build_deck_from_url import gemini, resolve_model, normalize_names  # tái dùng

TEMPLATE_NAME = "gold-daily-bias-hf"   # >>> SỬA
STYLE_PRESET = "giai-ma-nganh"         # >>> SỬA (+ thêm vào STYLE_PRESET của ci_build_video.py)
BGM_REL = "preview-assets/bgm/20260624-151812_Write_You.mp3"


def today_vn():
    return datetime.now(timezone(timedelta(hours=7)))


# >>> SỬA: rút số liệu TẤT ĐỊNH từ JSON nguồn. Trả về dict số liệu sạch để dựng cảnh.
def pick_data(raw: dict, frame: str) -> dict:
    asset = raw["assets"]["GOLD"][frame]          # ví dụ: điểm Bias khung ngày/tuần
    return {
        "score": asset["score"],
        "regime": asset.get("regime", "neutral"),
        "categories": asset.get("categories", []), # mỗi cái có contribution (âm/dương)
        "gamma": asset.get("gamma", {}),
        # ... thêm field bạn cần
    }


# >>> SỬA: biến số liệu thành các khối hiển thị (hf-data s1..s7). KHÔNG gọi Gemini ở đây.
def build_scenes(d: dict) -> dict:
    return {
        "s1": {"score": d["score"], "regime": d["regime"]},
        "s2": {"forces": [{"label": c.get("key"), "value": c.get("contribution")} for c in d["categories"]]},
        # ... s3..s7 tùy template
    }


# >>> SỬA: Gemini CHỈ viết phần CHỮ. Cho nó SỐ LIỆU ĐÃ CHỐT, yêu cầu trả JSON phần kể chuyện.
SPEC_STORY = """Bạn là biên tập viên bản tin phân tích định lượng. Dưới đây là SỐ LIỆU ĐÃ CHỐT (không được đổi số).
Hãy viết PHẦN KỂ CHUYỆN cho video dọc 9 cảnh, dựa đúng vào số liệu.

QUY TẮC:
- script_lines ĐÚNG 9 dòng; số câu/dòng = [1,3,3,3,4,4,3,3,3].
- Tổng 480–560 từ, TUYỆT ĐỐI ≤ 640 (video < 3 phút). Số trong lời đọc viết thành chữ.
- Tên/chỉ số tiếng Anh viết chuẩn (Dow Jones, S&P 500, Nasdaq, VN-Index). KHÔNG từ cấm.
- "góc nhìn tham khảo, không phải khuyến nghị đầu tư".

ĐẦU RA: CHỈ một object JSON:
{
  "hook": {"title_lines":["≤20 ký tự","≤20 ký tự"],"sub":"","chips":[{...3 chip...}]},
  "scenarios": [{"type":"base","text":""},{"type":"down","text":""},{"type":"up","text":""}],
  "actions": [{"type":"neutral","text":""}, ...],
  "outro": {"tag":"","closing":"","cta":""},
  "script_lines": ["...9 dòng..."],
  "youtube": {"title":"≤90","description":"...disclaimer + hashtag","tags":["..."]}
}
"""


def assemble(story: dict, scenes: dict, meta_src: dict, proj: str, date_full: str, frame: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    hf = {"template": TEMPLATE_NAME, "date": date_full, "frame": frame,
          "audio_offset": 1.0, "outro_hold": 3.6,
          "hook": story.get("hook", {}), "outro": story.get("outro", {}),
          "source": meta_src}
    hf.update(scenes)  # s1..s7 từ số liệu
    # (tùy template) nhét scenarios/actions vào đúng cảnh
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [str(x).strip() for x in story.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    y = story.get("youtube", {})
    meta = {"youtube": {"title": y.get("title", "")[:100], "description": y.get("description", ""),
                        "tags": y.get("tags", []), "privacyStatus": "private",
                        "categoryId": "25", "madeForKids": False}, "source": meta_src}
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "preview-settings.json").write_text(json.dumps(
        {"scriptLines": lines, "bgm": {"mode": "custom", "volume": 0.2,
         "custom": {"path": BGM_REL, "url": f"/slide/{proj}/{BGM_REL}"}},
         "subtitles": {"enabled": True}}, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="đường dẫn JSON nguồn (vd bias-web/data/latest.json)")
    ap.add_argument("--frame", default="daily", choices=["daily", "weekly"])
    ap.add_argument("--date", help="DD/MM/YYYY (bỏ trống = lấy theo báo cáo/hôm nay)")
    a = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    raw = json.loads(Path(a.data).read_text(encoding="utf-8"))
    d = pick_data(raw, a.frame)
    scenes = build_scenes(d)

    date_full = a.date or today_vn().strftime("%d/%m/%Y")
    dd, mm, yyyy = date_full.split("/")[0].zfill(2), date_full.split("/")[1].zfill(2), date_full.split("/")[2]
    proj = f"<loại>-{dd}{mm}{yyyy}" + ("-week" if a.frame == "weekly" else "")  # >>> SỬA tên

    model = resolve_model(key)
    # đưa SỐ LIỆU ĐÃ CHỐT cho Gemini viết chữ:
    user = "SỐ LIỆU ĐÃ CHỐT (không đổi số):\n" + json.dumps({**d, **scenes}, ensure_ascii=False)
    last_err = ""
    for attempt in range(1, 4):
        push = ""
        if attempt > 1 and "QUÁ DÀI" in last_err:
            push = f"\n\n⚠️ Lần trước QUÁ DÀI — viết lại ~520 từ, giữ số câu mỗi dòng [1,3,3,3,4,4,3,3,3]."
        prompt = user if attempt == 1 else user + f"\n\nSỬA lỗi:\n{last_err}" + push
        story = json.loads(normalize_names(gemini(SPEC_STORY, prompt, key, model)))
        out_dir = REPO / "slide" / proj
        assemble(story, scenes, {"site": "<Nguồn>", "headline": "<tiêu đề>", "date": date_full, "url": ""},
                 proj, date_full, a.frame, out_dir)
        r = subprocess.run([sys.executable, str(REPO / "check_deck_cloud.py"), str(out_dir)],
                           capture_output=True, text=True)
        print(r.stdout, flush=True)
        if r.returncode == 0:
            print(f"PROJECT={proj}"); return
        last_err = "\n".join(l for l in r.stdout.splitlines() if "LỖI:" in l)
    sys.exit(f"Không đạt sau 3 lượt:\n{last_err}")


if __name__ == "__main__":
    main()
