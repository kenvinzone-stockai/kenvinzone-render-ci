#!/usr/bin/env python3
"""BỘ NÃO VNINDEX: 2 email báo cáo (sáng 11:01 + chiều 15:01) -> deck vnindex-daily-hf hoàn chỉnh.

Chạy trên GitHub Actions (cần GEMINI_API_KEY). KHÔNG chạy trong container Cowork/device_bash.

   python build_vnindex_deck.py --am-file <am.txt> --pm-file <pm.txt> [--date DD/MM/YYYY]

Dữ liệu SỐ (điểm, mốc EMA/swing, giá, %) lấy TRỰC TIẾP từ email — Gemini chỉ sắp xếp lại đúng schema
và viết phần kể chuyện (cover, script 10 dòng, mô tả). Tiêu đề/thứ/metadata tính tất định ở assemble.

In ra PROJECT=<tên thư mục> ở dòng cuối để workflow lấy.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from build_deck_from_url import gemini, resolve_model, normalize_names  # tái dùng

BGM_REL = "preview-assets/bgm/20260624-151812_Write_You.mp3"
WEEKDAYS = {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"}

# Mẫu schema đầy đủ (deck 30/10) — Gemini bám đúng cấu trúc này, chỉ thay dữ liệu theo ngày mới.
SCHEMA_EXAMPLE = r"""
{
  "score": 48, "score_am": 46, "status": "WATCHLIST — THEO DÕI", "status_pct": "55%",
  "cover": {
    "eyebrow": "Chứng khoán hôm nay",
    "title_lines": ["Hồi lên 1742", "chưa qua EMA20"],
    "sub_html": "Hồi hơn <b>7</b> điểm từ sáng, còn <b>5,5</b> điểm tới EMA20",
    "chips": [{"icon":"📈","label":"VNI","value":"1742"},{"icon":"◎","label":"Score","value":"48"},{"icon":"⚡","label":"EMA20","value":"−5,5","hot":true}],
    "cta": "Hồi thật hay bẫy tăng giá?"
  },
  "compare": [
    {"label":"Score","am":"46","pm":"48","delta":"+2","tone":"up"},
    {"label":"Giá VNI","am":"1735","pm":"1742,31","delta":"+7,31","tone":"up"},
    {"label":"Vol ratio","am":"0,78","pm":"0","delta":"ghi bằng 0","tone":"flat"}
  ],
  "range_pill": "BIÊN 1730,93 – 1747,78 · thủng 1730,93 → về 1715–1720",
  "journey": {
    "axis": [1722, 1758],
    "path": [{"label":"Tham chiếu","price":1755.61},{"label":"11:01","price":1735},{"label":"15:01","price":1742.31}],
    "resistance": {"price":1747.78,"label":"Cản · EMA20 D1 1747,78"},
    "zone": {"lo":1729.2,"hi":1734.63,"label":"Mốc sáng 1729,2 · low phiên 1734,63"},
    "am_card": {"time":"11:01 · SÁNG","meta":"Score 46 · Vol ×0,78","text":"Giá <b>1735</b> sát swing low 1729,2, dưới cả EMA20/50/200"},
    "warn_card": "Báo cáo sáng: thủng <b>1729,2</b> kèm volume tăng mạnh thì vô hiệu",
    "pm_card": {"time":"15:01 · CHIỀU","meta":"Score 48 · Vol ghi 0","text":"Chốt <b>1742,31</b> — low phiên 1734,63 trên mốc, chưa lấy lại EMA20"},
    "twist": "Mốc 1729,2 còn nguyên, giá hồi hơn 7 điểm nhưng vẫn dưới EMA20 1747,78"
  },
  "subscores": [
    {"label":"Kỹ thuật","am":12,"pm":14,"max":30},{"label":"Timing","am":8,"pm":8,"max":20},
    {"label":"Dòng tiền","am":10,"pm":9,"max":20},{"label":"Sector","am":7,"pm":7,"max":15},{"label":"Rủi ro","am":9,"pm":10,"max":15}
  ],
  "subscore_note": "Kỹ thuật +2, Rủi ro +1, Dòng tiền −1 → tổng +2",
  "timeframes": [
    {"tf":"W1","name":"Tuần","trend":"bullish","badge":"Bullish","detail":"EMA Full Bullish · MACD bearish"},
    {"tf":"3D","name":"3 ngày","trend":"bullish","badge":"Bullish","detail":"EMA Mixed · MACD bearish"},
    {"tf":"D1","name":"Ngày","trend":"bearish","badge":"Bearish","detail":"RSI <b>45,36 → 47,06</b> · MACD hist 5,19 → 5,59"},
    {"tf":"M15","name":"15 phút","trend":"neutral","badge":"Doji","detail":"Range · doji volume thấp"}
  ],
  "timeframe_note": "Khối lượng chiều ghi bằng 0 nên tín hiệu M15 chưa kiểm chứng",
  "levels": {
    "axis": [1726, 1766], "price": 1742.31, "price_label": "Giá chốt 1.742,31",
    "items": [
      {"price":1761.44,"label":"EMA50 D1","kind":"res"},{"price":1755.84,"label":"EMA200 D1","kind":"res"},
      {"price":1747.78,"label":"EMA20 D1","kind":"res"},{"price":1742.9,"label":"High 20 nến","kind":"res"},
      {"price":1734.63,"label":"Low phiên","kind":"sup"},{"price":1730.93,"label":"Swing low","kind":"sup","key":true}
    ],
    "up": "Đóng D1 trên 1747,78 + thanh khoản tăng", "down": "Thủng 1730,93 → về 1715–1720"
  },
  "scenarios": [
    {"pct":45,"tone":"down","name":"Hồi thất bại, dò đáy","desc":"Thủng <b>1730,93</b> → <b>1715–1720</b>"},
    {"pct":35,"tone":"flat","name":"Đi ngang tích lũy","desc":"Biên <b>1730–1748</b>, thanh khoản cải thiện dần"},
    {"pct":20,"tone":"up","name":"Lấy lại EMA20 D1 (suy luận)","desc":"Đóng trên <b>1747,78</b> kèm thanh khoản tăng đột biến"}
  ],
  "actions": [
    {"tone":"urgent","title":"Chưa mở vị thế mới","desc":"Chờ D1 lấy lại <b>1747,78</b> kèm thanh khoản"},
    {"tone":"positive","title":"Đang nắm giữ","desc":"Có thể giữ, dừng lỗ chặt dưới <b>1730,93</b>, không bình quân giá xuống"},
    {"tone":"urgent","title":"Margin","desc":"Nên giảm tỷ trọng, ưu tiên bảo toàn vốn"}
  ],
  "outro": {"up":"D1 đóng vững trên 1747,78 kèm thanh khoản đột biến","down":"Thủng 1730,93 kèm volume — thesis vô hiệu","promise":"Hẹn anh em bản tin tổng hợp thứ Hai tuần sau","follow_handle":"@kenvinzone"},
  "script_lines": ["... đúng 10 dòng ..."],
  "yt_description": "mô tả YouTube dài, có emoji, các mục HÀNH TRÌNH/5 THÀNH PHẦN/ĐA KHUNG/VÙNG GIÁ/KỊCH BẢN/KẾ HOẠCH + disclaimer",
  "yt_tags": ["vnindex","chứng khoán","..."]
}
"""

SPEC = """Bạn là biên tập viên bản tin VNINDEX hằng ngày của kênh "Kể Chuyện Chứng Khoán" (KenvinZone Analytics). Nhiệm vụ: đọc HAI báo cáo kỹ thuật tự động (SÁNG 11:01 và CHIỀU 15:01) của CÙNG một ngày, rồi xuất ra MỘT object JSON đúng schema deck "vnindex-daily-hf" để dựng video dọc 9:16.

NGUYÊN TẮC SỐ LIỆU (quan trọng nhất):
- MỌI con số (điểm tổng, 5 điểm thành phần, giá, EMA20/50/200, RSI, MACD hist, swing low/high, vùng hỗ trợ/kháng cự, % kịch bản, vol ratio) PHẢI lấy ĐÚNG từ báo cáo — KHÔNG được bịa, làm tròn sai, hay đổi số. Lấy số CHỐT NGÀY (báo cáo CHIỀU) cho các trường "pm"/chính; số SÁNG cho "am"/"score_am".
- Dùng dấu phẩy thập phân kiểu Việt khi HIỂN THỊ (1742,31) nhưng trong JSON các field "price" là SỐ thực (1742.31). Các field chuỗi (compare.am/pm, labels, desc) dùng dấu phẩy Việt.
- % các kịch bản (scenarios) lấy từ "Ma trận kịch bản" (KB1/KB2/KB3). Nếu báo cáo chỉ có 2 kịch bản, suy luận kịch bản thứ 3 hợp lý và ghi "(suy luận)" trong name, tổng 3 % ≈ 100.

SCRIPT ĐỌC (script_lines) — ĐÚNG 10 DÒNG, mỗi dòng 1 câu trọn ý, tổng ~150–210 từ:
1. Hook: diễn biến chốt ngày (giá chốt, bật/giảm bao nhiêu điểm, khựng/qua mốc nào).
2. Thứ + ngày DD/MM, điểm KenvinZone từ <sáng> lên/xuống <chiều>, nhãn đổi thế nào.
3. Buổi sáng: giá, biến động so đỉnh, thanh khoản (vol ratio), mốc hỗ trợ sát.
4. Ranh giới then chốt báo cáo sáng đặt ra + điều kiện vô hiệu/giữ vững.
5. Buổi chiều: mốc ấy còn/mất, đáy phiên, giá so EMA20.
6. Thay đổi 5 điểm thành phần (vd "Kỹ thuật cộng hai, rủi ro cộng một, dòng tiền trừ một...") → tổng.
7. RSI, MACD hist, vị trí so EMA; nền W1/3D.
8. M15 (doji/pin bar/volume), mốc swing low quan trọng nhất cần canh.
9. Kịch bản phiên tới kèm % (vd "45% ... ; 35% ... ; 20% ...").
10. Khuyến nghị hành động ngắn (chưa mở mới / giảm margin) + lời hẹn.
LƯU Ý SCRIPT:
- Mốc giá/chỉ số GIỮ dạng số (1742,31 ; 1747,78 ; 1730,93) để đọc chính xác; còn số đếm nhỏ viết chữ ("bảy điểm", "cộng hai").
- Dòng 10: nếu ngày làm là THỨ SÁU thì hẹn "bản tin tổng hợp THỨ HAI tuần sau" (nghỉ T7/CN); các ngày khác hẹn "bản tin ngày mai".
- KHÔNG dùng: "chắc chắn tăng/giảm", "cam kết lãi", "x2/x3 tài khoản", "mua ngay", "bán ngay", "all in", "làm giàu nhanh", "bí mật nội bộ", "thao túng", "lãi đảm bảo". Giọng: "góc nhìn tham khảo", "kịch bản", "cần canh/theo dõi".

TÊN RIÊNG / CHỈ SỐ / THUẬT NGỮ: luôn viết chuẩn: VNINDEX (hoặc VN-Index), EMA20/EMA50/EMA200, RSI, MACD, KenvinZone, Dow Jones, S&P 500, Nasdaq. KHÔNG phiên âm tiếng Việt kiểu "Đao Giôn", "Ét pi", "Vi-En In-đéc".

cover.title_lines: 2 dòng ngắn (≤18 ký tự/dòng), nêu ý chính của ngày (vd "Hồi lên 1742" / "chưa qua EMA20"). status: ánh xạ nhãn báo cáo → chữ in hoa: "Watchlist"→"WATCHLIST — THEO DÕI"; "Avoid New Entry"→"TRÁNH VÀO MỚI"; "Buy/Accumulate"→"MUA/TÍCH LŨY"; "Sell/Reduce"→"BÁN/GIẢM"; giữ status_pct đúng % độ tin cậy trong báo cáo.

yt_description: mô tả YouTube dài, nhiều emoji, gồm các mục: HÀNH TRÌNH CẢ NGÀY (sáng/chiều), 5 THÀNH PHẦN ĐIỂM SỐ, PHÂN TÍCH ĐA KHUNG, VÙNG GIÁ CHỐT NGÀY (hỗ trợ/kháng cự), KỊCH BẢN PHIÊN TỚI, KẾ HOẠCH HÀNH ĐỘNG, rồi disclaimer "KHÔNG phải lời khuyên đầu tư", kết bằng lời hẹn + hashtag (#giaimachungkhoan #kechuyenchungkhoan #xuhuongchungkhoan #vnindex #chungkhoan #phantichkythuat). yt_tags: 12–15 tag không có #.

ĐẦU RA: CHỈ một object JSON đúng schema dưới đây (không văn bản thừa), đúng kiểu dữ liệu, số liệu khớp báo cáo:
""" + SCHEMA_EXAMPLE


def viet_weekday(d: datetime) -> str:
    return WEEKDAYS[d.weekday()]


def build_prompt(am_text: str, pm_text: str, date_full: str, weekday: str) -> str:
    return (f"NGÀY LÀM: {date_full} ({weekday}). "
            f"{'HÔM NAY LÀ THỨ SÁU — dòng 10 phải hẹn bản tin THỨ HAI tuần sau.' if weekday=='Thứ Sáu' else 'Dòng 10 hẹn bản tin ngày mai.'}\n\n"
            f"=== BÁO CÁO SÁNG (11:01) ===\n{am_text[:7000]}\n\n"
            f"=== BÁO CÁO CHIỀU (15:01) — lấy số CHỐT NGÀY từ đây ===\n{pm_text[:8000]}")


def yt_title(date_full: str) -> str:
    dd, mm = date_full.split("/")[0], date_full.split("/")[1]
    return f"Nhìn lại chỉ số kỹ thuật, dòng tiền và kịch bản hướng đi chỉ số chứng khoán VNINDEX ngày {dd}/{mm}"


def assemble(deck: dict, date_full: str, weekday: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # hf-data.json: trường tất định + phần Gemini sinh
    hf = {"template": "vnindex-daily-hf", "date": date_full, "weekday": weekday, "handle": "@Kechuyen.Chungkhoan"}
    for k in ["score", "score_am", "status", "status_pct", "cover", "compare", "range_pill",
              "journey", "subscores", "subscore_note", "timeframes", "timeframe_note",
              "levels", "scenarios", "actions", "outro"]:
        if k in deck:
            hf[k] = deck[k]
    hf["audio_offset"] = 1.0
    hf["outro_hold"] = 3.6
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [str(x).strip() for x in deck.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    title = yt_title(date_full)
    meta = {
        "youtube": {"title": title, "description": deck.get("yt_description", ""),
                    "tags": deck.get("yt_tags", []), "privacyStatus": "private",
                    "categoryId": "25", "madeForKids": False},
        "source": {"kind": "vnindex-daily", "date": date_full},
    }
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    proj = out_dir.name
    ps = {
        "subtitles": {"enabled": True, "color": "#92f93e", "fontSize": 18, "bottom": 60, "maxLines": 1},
        "backgroundFx": "candlestick",
        "bgm": {"mode": "custom", "preset": "ambient", "volume": 0.2,
                "custom": {"name": "Write_You.mp3", "path": BGM_REL, "url": f"/slide/{proj}/{BGM_REL}"}},
        "scriptLines": lines,
        "slides": {"deletedIds": [], "scriptLines": lines},
        "visuals": {"colorMode": "dark", "backgroundColor": "#07030d", "gridEnabled": False,
                    "backgroundFx": "candlestick-diag"},
    }
    (out_dir / "preview-settings.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2), encoding="utf-8")

    # bgm
    canon = REPO / "assets" / "bgm" / "20260624-151812_Write_You.mp3"
    dst = out_dir / BGM_REL
    if canon.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(canon.read_bytes())


def validate(deck: dict) -> list[str]:
    errs = []
    sl = deck.get("script_lines", [])
    if len(sl) != 10:
        errs.append(f"script_lines phải đúng 10 dòng (đang {len(sl)})")
    sc = deck.get("scenarios", [])
    if len(sc) != 3:
        errs.append(f"scenarios phải 3 kịch bản (đang {len(sc)})")
    else:
        tot = sum(int(x.get("pct", 0)) for x in sc)
        if not (95 <= tot <= 105):
            errs.append(f"tổng % kịch bản = {tot}, cần ≈100")
    if not isinstance(deck.get("score"), int):
        errs.append("thiếu score (int)")
    if len(deck.get("subscores", [])) != 5:
        errs.append("subscores phải 5 nhóm")
    if not deck.get("cover", {}).get("title_lines"):
        errs.append("thiếu cover.title_lines")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--am-file", required=True)
    ap.add_argument("--pm-file", required=True)
    ap.add_argument("--date", help="DD/MM/YYYY (mặc định suy từ tên/nội dung file chiều hoặc hôm nay)")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    am_text = Path(a.am_file).read_text(encoding="utf-8", errors="replace") if Path(a.am_file).exists() else ""
    pm_text = Path(a.pm_file).read_text(encoding="utf-8", errors="replace")

    date_full = a.date
    if not date_full:
        m = re.search(r"VNINDEX\s+(\d{2})/(\d{2})/(\d{4})", pm_text)
        date_full = f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else datetime.now().strftime("%d/%m/%Y")
    d = datetime.strptime(date_full, "%d/%m/%Y")
    weekday = viet_weekday(d)
    dd, mm, yyyy = date_full.split("/")
    proj = f"vnindex-{dd}{mm}{yyyy}-ngay"

    model = resolve_model(key)
    print(f"=== [1/2] Gemini dựng deck VNINDEX {date_full} ({weekday}) | model={model} ===", flush=True)

    base = build_prompt(am_text, pm_text, date_full, weekday)
    last_err = ""
    for attempt in range(1, 4):
        prompt = base if attempt == 1 else base + f"\n\nLƯU Ý: lần trước lỗi:\n{last_err}\nSửa đúng schema + số liệu."
        raw = normalize_names(gemini(SPEC, prompt, key, model))
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON không hợp lệ: {e}"
            print("  " + last_err, flush=True)
            continue
        errs = validate(deck)
        if errs:
            last_err = "; ".join(errs)
            print("  lỗi validate: " + last_err, flush=True)
            continue
        out_dir = REPO / "slide" / proj
        assemble(deck, date_full, weekday, out_dir)
        print(f"=== [2/2] Đã dựng {proj} ===", flush=True)
        print(f"PROJECT={proj}")
        return
    sys.exit(f"Không dựng được deck VNINDEX sau 3 lượt. Lỗi cuối: {last_err}")


if __name__ == "__main__":
    main()
