#!/usr/bin/env python3
"""BỘ NÃO LIÊN THỊ TRƯỜNG (tuần): gộp GOLD + SPX + NASDAQ (bias-web weekly) -> deck intermarket-weekly-hf.

Bản tổng kết tuần sáng Chủ Nhật: điểm composite liên thị trường (= trung bình 3 điểm),
các lực VĨ MÔ chung (trung bình đóng góp theo nhóm), điểm mạnh/yếu từng tài sản, dòng tiền
luân chuyển, 3 kịch bản. Số TẤT ĐỊNH; Gemini chỉ viết script 8 dòng + 3 kịch bản + nhãn.

   python build_intermarket_deck.py --data <latest.json> [--date DD/MM/YYYY]
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from build_deck_from_url import gemini, resolve_model, normalize_names

CAT_LABEL = {
    "rates": "Lãi suất thực", "usd": "Đồng USD", "flows": "Dòng tiền",
    "positioning": "Vị thế", "risk": "Khẩu vị rủi ro", "options": "Quyền chọn",
    "liquidity": "Thanh khoản M2", "breadth": "Độ rộng TT", "gold_specific": "Yếu tố riêng Vàng",
}
SHARED = ["rates", "usd", "flows", "risk", "liquidity", "breadth", "positioning", "options"]
WARM = ["#ef4444", "#f87171", "#fb923c"]
COOL = ["#4ade80", "#38bdf8", "#22d3ee"]
SCEN_COLOR = {"base": "#fbbf24", "down": "#f87171", "up": "#4ade80"}
# thứ tự hiển thị 3 tài sản (như mẫu cũ): S&P 500 -> Nasdaq -> Vàng
ASSETS = [("SPX", "spx", "S&P 500", "SPX", "#38bdf8"),
          ("NASDAQ", "nas", "Nasdaq 100", "NASDAQ", "#a78bfa"),
          ("GOLD", "gold", "Vàng", "XAUUSD", "#fbbf24")]


def regime_vn(score):
    return "TĂNG" if score > 3 else ("GIẢM" if score < -3 else "TRUNG LẬP")


def cat_val(cats, key):
    for c in cats:
        if c.get("key") == key:
            return round(float(c.get("contribution", 0.0)), 2)
    return 0.0


def build_macro(weeklies):
    """6 lực vĩ mô chung = trung bình đóng góp theo nhóm trên 3 tài sản, chọn top 6 theo |trung bình|."""
    means = []
    for key in SHARED:
        vals = [cat_val(w["categories"], key) for w in weeklies]
        means.append((key, round(sum(vals) / len(vals), 2)))
    means.sort(key=lambda kv: -abs(kv[1]))
    out = []
    wi = ci = 0
    for key, v in means[:6]:
        if v < 0:
            color = WARM[wi % len(WARM)]; wi += 1
        else:
            color = COOL[ci % len(COOL)]; ci += 1
        out.append({"label": CAT_LABEL.get(key, key), "value": v, "color": color})
    return out


def build_asset(sym, key, name, ticker, accent, asset):
    w = asset.get("weekly") or {}
    cats = w.get("categories") or []
    g = asset.get("gamma") or {}
    score = round(float(w.get("score", 0.0)), 1)
    # lực chi phối mạnh nhất (theo |đóng góp|) và lực đỡ lớn nhất
    ranked = sorted(cats, key=lambda c: -abs(float(c.get("contribution", 0.0))))
    top = ranked[0] if ranked else {}
    pos = max(cats, key=lambda c: float(c.get("contribution", 0.0)), default={})
    neg = min(cats, key=lambda c: float(c.get("contribution", 0.0)), default={})
    return {
        "key": key, "name": name, "ticker": ticker, "accent": accent,
        "score": score, "regime": regime_vn(score),
        "top": {"label": CAT_LABEL.get(top.get("key"), top.get("key", "")), "value": round(float(top.get("contribution", 0.0)), 2)},
        "support": {"label": CAT_LABEL.get(pos.get("key"), pos.get("key", "")), "value": round(float(pos.get("contribution", 0.0)), 2)},
        "drag": {"label": CAT_LABEL.get(neg.get("key"), neg.get("key", "")), "value": round(float(neg.get("contribution", 0.0)), 2)},
        "gamma_neg": float(g.get("netGex", 0.0)) < 0,
        "expected_move": round(float(g["expectedMove"]), 1) if g.get("expectedMove") else None,
    }


SCHEMA = r"""
{
  "scenarios": [
    {"tone":"base","pct":50,"name":"Giằng co biên hẹp"},
    {"tone":"down","pct":30,"name":"Biến động trái phiếu"},
    {"tone":"up","pct":20,"name":"USD hạ nhiệt"}
  ],
  "rotation_tag": "1 câu ngắn về dòng tiền luân chuyển giữa các nhóm/tài sản (có thể dùng <b></b>)",
  "script_lines": ["... đúng 8 dòng ..."],
  "cover_title": "Tiêu đề YouTube ≤80 ký tự: Tổng kết liên thị trường tuần + bias chung",
  "yt_description": "mô tả dài nhiều emoji + disclaimer",
  "yt_tags": ["liên thị trường","market bias","vàng","sp500","nasdaq","..."]
}
"""

SPEC = """Bạn là biên tập viên bản tin "Phân tích định lượng LIÊN THỊ TRƯỜNG" hằng tuần của KenvinZone Analytics (bản tổng kết sáng Chủ Nhật). Nhận các CON SỐ đã tính sẵn: điểm Bias tuần của S&P 500, Nasdaq, Vàng; điểm composite liên thị trường (trung bình 3); các lực VĨ MÔ chung; điểm mạnh/yếu từng tài sản. Viết phần kể chuyện, xuất ra MỘT object JSON đúng schema.

NGUYÊN TẮC SỐ LIỆU: tuyệt đối không bịa số; chỉ dùng số được cung cấp. Thang điểm -100..100 (gần 0 = trung lập).

SCRIPT (script_lines) — ĐÚNG 8 DÒNG, mỗi dòng 1 câu, tổng ~150–200 TỪ (video DƯỚI 3 phút). THỨ TỰ CỐ ĐỊNH, bám sát để KHỚP hình:
1. Hook: cả 3 tài sản cốt lõi (S&P 500, Nasdaq, Vàng) tuần qua ở trạng thái nào + điểm composite liên thị trường + 1 câu hỏi/nhận định.
2. Bức tranh VĨ MÔ chung: lãi suất thực, thanh khoản M2, USD — lực nào mạnh nhất trên toàn thị trường tuần này.
3. S&P 500 (DÒNG NÀY CHỈ NÓI VỀ S&P 500, MỞ ĐẦU bằng "S&P 500"): điểm tuần + lực đỡ/cản nổi bật nhất của nó.
4. Nasdaq (DÒNG NÀY CHỈ NÓI VỀ NASDAQ, MỞ ĐẦU bằng "Nasdaq"): điểm tuần + lực đỡ/cản nổi bật.
5. Vàng (DÒNG NÀY CHỈ NÓI VỀ VÀNG, MỞ ĐẦU bằng "Vàng"): điểm tuần + giằng co nâng đỡ (M2/trú ẩn) vs kìm hãm (lãi suất thực/USD).
6. Dòng tiền luân chuyển giữa các nhóm tài sản (tấn công ➜ phòng thủ, chờ tín hiệu USD).
7. Ba kịch bản tuần tới kèm % (vd "năm mươi phần trăm ...; ba mươi phần trăm ...; hai mươi phần trăm ...").
8. Chiến lược tổng (bảo toàn vốn/giao dịch biên độ) + mời follow KenvinZone và AURORA.
QUAN TRỌNG: dòng 3,4,5 mỗi dòng CHỈ nói đúng 1 tài sản theo thứ tự S&P 500 → Nasdaq → Vàng (để phụ đề khớp với từng dòng hiện trên màn hình).

LƯU Ý:
- Thuật ngữ tiếng Anh GIỮ tiếng Anh: S&P 500, Nasdaq, Gold, XAUUSD, Fed, USD, M2, Gamma, Net GEX. KHÔNG phiên âm.
- Mốc số để dạng số đọc đúng; số đếm nhỏ & % viết chữ.
- KHÔNG hô hào "mua ngay/bán ngay/chắc chắn/all in". Giọng tổng quan, định lượng, chuyên nghiệp.

scenarios: đúng 3, tone base/down/up, tổng pct = 100 (số nguyên). name ngắn (≤22 ký tự).
rotation_tag: 1 câu ngắn về dòng tiền luân chuyển.
cover_title ≤80 ký tự. yt_description nhiều emoji + "KHÔNG phải lời khuyên đầu tư" + hashtag (#lienthitruong #marketbias #vang #sp500 #nasdaq #kenvinzone). yt_tags 12–15 tag không #.

ĐẦU RA: CHỈ một object JSON đúng schema sau:
""" + SCHEMA


def build_prompt(date_full, composite, assets, macro):
    a_txt = "\n".join(
        f'- {a["name"]} ({a["ticker"]}): điểm tuần {a["score"]:+.1f} ({a["regime"]}); '
        f'lực đỡ lớn nhất {a["support"]["label"]} {a["support"]["value"]:+.2f}, '
        f'lực cản lớn nhất {a["drag"]["label"]} {a["drag"]["value"]:+.2f}; '
        f'Gamma {"ÂM" if a["gamma_neg"] else "DƯƠNG"}'
        + (f', biến động kỳ vọng ±{a["expected_move"]}' if a["expected_move"] else '')
        for a in assets)
    m_txt = "; ".join(f'{m["label"]} {m["value"]:+.2f}' for m in macro)
    return (
        f"TUẦN dữ liệu đến: {date_full}.\n\n"
        f"ĐIỂM COMPOSITE LIÊN THỊ TRƯỜNG (trung bình 3 tài sản): {composite:+.1f} / 100\n\n"
        f"TỪNG TÀI SẢN:\n{a_txt}\n\n"
        f"LỰC VĨ MÔ CHUNG (trung bình đóng góp trên 3 tài sản, + đỡ / − kéo): {m_txt}\n"
    )


def validate(deck):
    errs = []
    sl = deck.get("script_lines", [])
    if len(sl) != 8:
        errs.append(f"script_lines phải ĐÚNG 8 dòng (đang {len(sl)})")
    words = len(re.findall(r"\w+", " ".join(str(x) for x in sl)))
    if words > 280:
        errs.append(f"script {words} từ — QUÁ DÀI; cắt còn ≤ 200 từ")
    sc = deck.get("scenarios", [])
    if len(sc) != 3:
        errs.append(f"scenarios phải 3 (đang {len(sc)})")
    else:
        tot = sum(int(x.get("pct", 0)) for x in sc)
        if not (95 <= tot <= 105):
            errs.append(f"tổng % kịch bản = {tot}, cần ≈100")
    return errs


def finalize(deck, composite, assets, macro, det):
    scen = [{"pct": int(s.get("pct", 0)), "color": SCEN_COLOR.get(s.get("tone", "base"), "#fbbf24"), "name": s.get("name", "")}
            for s in deck.get("scenarios", [])]
    return {
        "template": "intermarket-weekly-hf",
        "date": det["date"],
        "eyebrow": "⚡ WEEKLY · LIÊN THỊ TRƯỜNG",
        "title_html": "TỔNG KẾT ĐỊNH LƯỢNG<br/>LIÊN THỊ TRƯỜNG",
        "date_prefix": "TUẦN · dữ liệu đến",
        "composite": {"score": composite, "regime": regime_vn(composite)},
        "assets": assets,
        "macro": macro,
        "rotation_tag": deck.get("rotation_tag", ""),
        "scenarios": scen,
        "audio_offset": 1.0,
        "outro_hold": 3.6,
    }


def assemble(hf, deck, date_full, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [str(x).strip() for x in deck.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dd, mm = date_full.split("/")[0], date_full.split("/")[1]
    title = deck.get("cover_title") or f"Tổng kết liên thị trường tuần — S&P 500, Nasdaq, Vàng · đến {dd}/{mm}"
    meta = {"youtube": {"title": title[:98], "description": deck.get("yt_description", ""),
                        "tags": deck.get("yt_tags", []), "privacyStatus": "private",
                        "categoryId": "25", "madeForKids": False},
            "source": {"kind": "intermarket-weekly", "date": date_full}}
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    ps = {"subtitles": {"enabled": True, "color": "#fde047", "fontSize": 18, "bottom": 60, "maxLines": 1},
          "backgroundFx": "candlestick", "bgm": {"mode": "preset", "preset": "ambient", "volume": 0.18},
          "scriptLines": lines, "slides": {"deletedIds": [], "scriptLines": lines},
          "visuals": {"colorMode": "dark", "backgroundColor": "#060a13", "gridEnabled": False, "backgroundFx": "candlestick-diag"}}
    (out_dir / "preview-settings.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2), encoding="utf-8")


def _as_ddmmyyyy(s):
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--date")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    blob = json.loads(Path(a.data).read_text(encoding="utf-8"))
    av = blob.get("assets") or {}
    for s in ("SPX", "NASDAQ", "GOLD"):
        if s not in av:
            sys.exit(f"Thiếu assets.{s}")
    weeklies = [av[s]["weekly"] for s in ("SPX", "NASDAQ", "GOLD")]
    assets = [build_asset(sym, key_, name, tk, acc, av[sym]) for (sym, key_, name, tk, acc) in ASSETS]
    composite = round(sum(a_["score"] for a_ in assets) / len(assets), 1)
    macro = build_macro(weeklies)

    date_full = a.date or _as_ddmmyyyy((av["SPX"].get("weekly") or {}).get("asOf")) or datetime.now().strftime("%d/%m/%Y")
    det = {"date": date_full}
    dd, mm, yyyy = date_full.split("/")
    proj = f"intermarket-week-{dd}{mm}{yyyy}"

    model = resolve_model(key)
    print(f"=== [1/2] Gemini viết tổng kết liên thị trường tuần {date_full} | composite {composite:+.1f} | SPX {assets[0]['score']:+.1f} NAS {assets[1]['score']:+.1f} GOLD {assets[2]['score']:+.1f} | model={model} ===", flush=True)
    base = build_prompt(date_full, composite, assets, macro)
    last_err = ""
    for attempt in range(1, 4):
        prompt = base if attempt == 1 else base + f"\n\nLƯU Ý: lần trước lỗi:\n{last_err}\nSửa đúng schema + đủ 8 dòng."
        raw = normalize_names(gemini(SPEC, prompt, key, model))
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON lỗi: {e}"; print("  " + last_err, flush=True); continue
        errs = validate(deck)
        if errs:
            last_err = "; ".join(errs); print("  validate: " + last_err, flush=True); continue
        hf = finalize(deck, composite, assets, macro, det)
        out_dir = REPO / "slide" / proj
        assemble(hf, deck, date_full, out_dir)
        print(f"=== [2/2] Đã dựng {proj} ===", flush=True)
        print(f"PROJECT={proj}")
        return
    sys.exit(f"Không dựng được deck liên thị trường sau 3 lượt. Lỗi cuối: {last_err}")


if __name__ == "__main__":
    main()
