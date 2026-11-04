#!/usr/bin/env python3
"""KHUNG MẪU — BRAIN KIỂU A: 1 LINK BÀI BÁO -> DECK.

CÁCH DÙNG:
  1) Copy file này thành  build_<loại>_deck.py  ở gốc repo (vd build_crypto_deck.py).
  2) Sửa 3 chỗ đánh dấu  # >>> SỬA:
        - TEMPLATE_NAME : tên thư mục template dưới template/
        - SPEC          : prompt + schema JSON cho loại nội dung của bạn
        - (tùy chọn) quy tắc đặt tên project / style_preset
  3) Tái dùng gemini/resolve_model/normalize_names + check_deck_cloud.py sẵn có.
  4) Test bằng workflow build-deck.yml (chỉ brain, rẻ) trước khi render thật.

Yêu cầu: env GEMINI_API_KEY. In ra  PROJECT=<tên thư mục>  ở DÒNG CUỐI để workflow lấy.
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
# Tái dùng hạ tầng gọi Gemini đã có sẵn (có retry timeout, chọn model, lưới tên riêng):
from build_deck_from_url import gemini, resolve_model, normalize_names, fetch_article

BGM_REL = "preview-assets/bgm/20260624-151812_Write_You.mp3"

# >>> SỬA: tên thư mục template (phải tồn tại ở template/<TEMPLATE_NAME>/build.py)
TEMPLATE_NAME = "giaima-tin-hf"
# >>> SỬA: preset giọng — nhớ thêm dòng tương ứng vào STYLE_PRESET trong ci_build_video.py
STYLE_PRESET = "giai-ma-nganh"

# >>> SỬA: toàn bộ "luật chơi" cho Gemini. Giữ các ràng buộc BẤT BIẾN (xem Mục 7 của SOP):
#   - script ĐÚNG 9 dòng, số câu/dòng [1,3,3,3,4,4,3,3,3]
#   - tổng 480–560 từ, TUYỆT ĐỐI ≤ 640 (video < 3 phút)
#   - tên/chỉ số tiếng Anh viết chuẩn (Dow Jones, S&P 500, Nasdaq, VN-Index, KenvinZone)
#   - KHÔNG dùng từ cấm; luôn "góc nhìn tham khảo, không phải khuyến nghị đầu tư"
#   - đầu ra CHỈ một object JSON theo schema dưới
SPEC = """Bạn là biên tập viên kênh "<TÊN KÊNH>". Đọc MỘT bài báo và kể lại thành video dọc 9 cảnh, LUÔN dẫn nguồn, kèm góc nhìn cho người xem phổ thông. Diễn đạt LẠI, KHÔNG chép nguyên văn.

QUY TẮC BẤT BIẾN:
1. script_lines ĐÚNG 9 dòng; số câu mỗi dòng = [1,3,3,3,4,4,3,3,3]. Dòng 1 = 1 câu hook.
2. Dòng 3,4,5,7,8 mở đầu bằng câu hỏi dẫn. (Tùy biến theo template của bạn.)
3. Số trong lời đọc VIẾT THÀNH CHỮ; số hiển thị trên slide để nguyên chữ số.
4. Dòng 2 nêu nguồn (trang, tác giả, ngày). Dòng 9 = kết mở + mời theo dõi + disclaimer.
5. ĐỘ DÀI LÀ RÀNG BUỘC SỐ 1: tổng 480–560 TỪ, TUYỆT ĐỐI ≤ 640 — video BẮT BUỘC < 3 phút.
6. KHÔNG dùng: "thao túng","mua ngay","bán ngay","chắc chắn tăng/giảm","cam kết lãi","x2/x3 tài khoản","làm giàu nhanh","all in","lãi đảm bảo".
7. Tên/chỉ số tiếng Anh viết CHUẨN quốc tế, KHÔNG phiên âm.

ĐẦU RA: CHỈ một object JSON theo schema (không chữ thừa):
{
  "source": {"site":"","short":"","author":"","headline":"","date":"DD/MM/YYYY","url":""},
  "hook": {"eyebrow":"","title_lines":["≤20 ký tự","≤20 ký tự"],"sub":"","chips":[{"icon":"↘","text":"","tone":"down"},{"icon":"⑂","text":"","tone":"gold"},{"icon":"◆","text":"","tone":"blue"}]},
  "s1": {"...": "..."},  "s2": {"...": "..."},  "s3": {"...": "..."},
  "s4": {"...": "..."},  "s5": {"lights":[{"color":"green"},{"color":"yellow"},{"color":"red"}]},
  "s6": {"...": "..."},  "s7": {"...": "..."},
  "outro": {"tag":"","closing":"","cta":""},
  "script_lines": ["...9 dòng..."],
  "youtube": {"title":"≤90 ký tự","description":"... có link nguồn + 'không phải khuyến nghị đầu tư' + hashtag","tags":["..."]}
}
"""


def today_vn():
    return datetime.now(timezone(timedelta(hours=7)))


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "", s).lower()[:28] or "tin"


def assemble(deck, proj, date_full, out_dir):
    """Ghi deck ra đĩa. GIỮ cấu trúc hf-data chung để render dùng được."""
    out_dir.mkdir(parents=True, exist_ok=True)
    hf = {"template": TEMPLATE_NAME, "date": date_full, "handle": "@<handle>",
          "audio_offset": 1.0, "outro_hold": 3.6}
    for k in ["source", "hook", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "outro"]:
        hf[k] = deck.get(k, {})
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [str(x).strip() for x in deck.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    y = deck.get("youtube", {})
    title = str(y.get("title", "")).strip()
    if not title.startswith("[Giải mã]"):
        title = "[Giải mã] " + title
    meta = {"youtube": {"title": title[:100], "description": y.get("description", ""),
                        "tags": y.get("tags", []), "privacyStatus": "private",
                        "categoryId": "25", "madeForKids": False},
            "source": deck.get("source", {})}
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    ps = {"scriptLines": lines, "bgm": {"mode": "custom", "volume": 0.2,
          "custom": {"path": BGM_REL, "url": f"/slide/{proj}/{BGM_REL}"}},
          "subtitles": {"enabled": True}}
    (out_dir / "preview-settings.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2), encoding="utf-8")
    # (tùy chọn) copy nhạc nền từ assets/bgm/ vào out_dir/BGM_REL như build_deck_from_url.py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--date", help="DD/MM/YYYY")
    ap.add_argument("--slug")
    ap.add_argument("--title", help="tiêu đề cover ép (giữ nguyên văn)")
    a = ap.parse_args()

    import os
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    date_full = a.date or today_vn().strftime("%d/%m/%Y")
    dd, mm = date_full.split("/")[0].zfill(2), date_full.split("/")[1].zfill(2)

    print(f"=== [1/3] Đọc bài: {a.url} ===", flush=True)
    article = fetch_article(a.url)
    model = resolve_model(key)

    user = f"LINK: {a.url}\nNGÀY: {date_full}\n"
    if a.title:
        user += f"TIÊU ĐỀ COVER NGƯỜI DÙNG ÉP (giữ nguyên văn): {a.title}\n"
    user += f"\nNỘI DUNG BÀI:\n{article}"

    proj, last_err = None, ""
    for attempt in range(1, 4):
        print(f"=== [2/3] Gemini dựng deck (lượt {attempt}) ===", flush=True)
        push = ""
        if attempt > 1 and "QUÁ DÀI" in last_err:   # ép cắt định lượng khi quá dài
            tgt = {2: 540, 3: 500}.get(attempt, 520)
            push = (f"\n\n⚠️ ƯU TIÊN SỐ 1 LÀ ĐỘ DÀI: lần trước QUÁ DÀI. Viết lại chỉ ~{tgt} từ "
                    f"(≤620), giữ đúng số câu mỗi dòng [1,3,3,3,4,4,3,3,3] và giữ số liệu + nguồn.")
        prompt = user if attempt == 1 else user + f"\n\nSỬA các lỗi sau:\n{last_err}" + push

        raw = normalize_names(gemini(SPEC, prompt, key, model))
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON không hợp lệ: {e}"; print("  " + last_err, flush=True); continue

        if not proj:
            slug = a.slug or slugify(deck.get("source", {}).get("headline", "tin"))
            proj = f"giai-ma-tin-tuc-{slug}-{dd}-{mm}"   # >>> SỬA quy tắc đặt tên nếu muốn
        out_dir = REPO / "slide" / proj
        assemble(deck, proj, date_full, out_dir)

        print("=== [3/3] Kiểm tra deck ===", flush=True)
        import subprocess
        r = subprocess.run([sys.executable, str(REPO / "check_deck_cloud.py"), str(out_dir)],
                           capture_output=True, text=True)
        print(r.stdout, flush=True)
        if r.returncode == 0:
            print(f"PROJECT={proj}"); return
        last_err = "\n".join(l for l in r.stdout.splitlines() if "LỖI:" in l)

    sys.exit(f"Không dựng được deck đạt sau 3 lượt. Lỗi cuối:\n{last_err}")


if __name__ == "__main__":
    main()
