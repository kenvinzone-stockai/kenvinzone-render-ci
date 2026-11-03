#!/usr/bin/env python3
"""BỘ NÃO CHỨNG KHOÁN MỸ: SPX + NASDAQ (Bias định lượng) -> deck equity-bias-hf.

Gộp 2 chỉ số vào 1 video (khối S&P 500 -> khối Nasdaq -> so sánh & phân kỳ).
Dữ liệu SỐ lấy TẤT ĐỊNH từ bias-web/data/latest.json (assets.SPX + assets.NASDAQ);
Gemini chỉ viết kịch bản (script 7 dòng), 3 kịch bản thị trường, nhãn phân kỳ, mô tả YouTube.

   python build_equity_deck.py --data <latest.json> [--frame daily|weekly] [--date DD/MM/YYYY]
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from build_deck_from_url import gemini, resolve_model, normalize_names

CAT_LABEL = {
    "rates": "Lãi suất / Fed", "usd": "Đồng USD", "flows": "Dòng tiền",
    "positioning": "Vị thế", "risk": "Khẩu vị rủi ro", "options": "Quyền chọn",
    "liquidity": "Thanh khoản", "breadth": "Độ rộng",
}
WARM = ["#ef4444", "#f87171", "#fb923c"]
COOL = ["#4ade80", "#38bdf8", "#22d3ee"]
REGIME_VN = {"bullish": "TĂNG", "bearish": "GIẢM", "neutral": "TRUNG LẬP",
             "strong bullish": "TĂNG MẠNH", "strong bearish": "GIẢM MẠNH",
             "slightly bullish": "HƠI TĂNG", "slightly bearish": "HƠI GIẢM"}
SCEN_COLOR = {"base": "#fbbf24", "down": "#f87171", "up": "#4ade80"}
INDEX_META = {"SPX": {"key": "spx", "name": "S&P 500", "ticker": "SPX"},
              "NASDAQ": {"key": "nas", "name": "Nasdaq 100", "ticker": "NASDAQ"}}


def regime_vn(s):
    return REGIME_VN.get(str(s or "").strip().lower(), str(s or "TRUNG LẬP").upper())


def build_forces(cats):
    """Top-6 nhóm theo |đóng góp|, màu theo dấu."""
    rows = sorted(cats, key=lambda c: -abs(float(c.get("contribution", 0.0))))[:6]
    out = []
    wi = ci = 0
    for c in rows:
        val = round(float(c.get("contribution", 0.0)), 2)
        if val < 0:
            color = WARM[wi % len(WARM)]; wi += 1
        else:
            color = COOL[ci % len(COOL)]; ci += 1
        out.append({"label": CAT_LABEL.get(c.get("key"), c.get("key")), "value": val, "color": color})
    return out


def build_gamma(g):
    return {
        "underlying": g.get("underlying", ""),
        "net_gex_m": round(float(g.get("netGex", 0.0)) / 1e6, 0),
        "expected_move": round(float(g.get("expectedMove", 0.0)), 1),
        "spot": g.get("spot"), "put": g.get("putWall"), "flip": g.get("gammaFlip"), "call": g.get("callWall"),
    }


def build_index(asset, frame):
    fr = asset.get(frame) or {}
    meta = INDEX_META[asset_symbol(asset)]
    g = build_gamma(asset.get("gamma") or {})
    return {
        "key": meta["key"], "name": meta["name"], "ticker": meta["ticker"],
        "score": round(float(fr.get("score", 0.0)), 1),
        "day_score": round(float((asset.get("daily") or {}).get("score", fr.get("score", 0.0))), 1),
        "week_score": round(float((asset.get("weekly") or {}).get("score", fr.get("score", 0.0))), 1),
        "regime": regime_vn(fr.get("regime")),
        "score_change": round(float(fr.get("scoreChange", 0.0)), 1),
        "forces": build_forces(fr.get("categories") or []),
        "gamma": g,
        "divergence": asset.get("divergence") or {},
    }


_SYM = {}
def asset_symbol(asset):
    return _SYM[id(asset)]


def divergence_fallback(spx, nas):
    bits = []
    for ix in (spx, nas):
        dv = ix["divergence"]
        if str(dv.get("status")).upper() == "DIVERGENCE":
            bits.append(f'{ix["ticker"]} <b>phân kỳ</b> (tuần {dv.get("weeklyScore")} · ngày {dv.get("dailyScore")})')
    if not bits:
        return "Cả hai chỉ số <b>đồng pha</b> tuần và ngày — xu hướng nhất quán."
    return " · ".join(bits) + " — cần thận trọng khi 2 khung lệch nhau."


SCHEMA = r"""
{
  "divergence_tag": "Câu ngắn nêu phân kỳ tuần/ngày của 2 chỉ số (có thể dùng <b></b>)",
  "scenarios": [
    {"tone":"base","pct":55,"name":"Đi ngang giằng co"},
    {"tone":"down","pct":25,"name":"Rủi ro điều chỉnh"},
    {"tone":"up","pct":20,"name":"Hồi phục kỹ thuật"}
  ],
  "script_lines": ["... đúng 7 dòng ..."],
  "cover_title": "Tiêu đề YouTube ngắn (≤80 ký tự): S&P 500 & Nasdaq + bias + khung ngày/tuần",
  "yt_description": "mô tả dài nhiều emoji + disclaimer",
  "yt_tags": ["sp500","nasdaq","chứng khoán mỹ","..."]
}
"""

SPEC = """Bạn là biên tập viên bản tin "Phân tích định lượng Chứng khoán Mỹ" của KenvinZone Analytics. Nhận CÁC CON SỐ đã tính sẵn cho S&P 500 và Nasdaq (điểm Bias, các lực, cấu trúc Gamma trên SPY/QQQ, phân kỳ tuần/ngày) rồi viết PHẦN KỂ CHUYỆN cho 1 video dọc gộp 2 chỉ số, xuất ra MỘT object JSON đúng schema.

NGUYÊN TẮC SỐ LIỆU: tuyệt đối không bịa số; chỉ dùng số được cung cấp. Điểm Bias thang -100..100 (gần 0 = trung lập).

BỐ CỤC VIDEO = TUẦN TỰ: hook (cả 2 chỉ số) -> khối S&P 500 -> khối Nasdaq -> so sánh & phân kỳ -> CTA.

SCRIPT (script_lines) — ĐÚNG 7 DÒNG, mỗi dòng 1 câu, tổng ~140–200 TỪ (video DƯỚI 3 phút). THỨ TỰ CỐ ĐỊNH:
1. Hook: điểm Bias của CẢ S&P 500 và Nasdaq + trạng thái, một ý về phân kỳ/đồng pha chung.
2. S&P 500 — điểm Bias + 2–3 lực chi phối mạnh nhất (theo số đóng góp).
3. S&P 500 — cấu trúc Gamma: Net GEX dương/âm, giá SPY so Gamma Flip, kẹp giữa Put Wall – Call Wall, biến động kỳ vọng.
4. Nasdaq — điểm Bias + 2–3 lực chính.
5. Nasdaq — cấu trúc Gamma (QQQ) tương tự.
6. So sánh 2 chỉ số + phân kỳ TUẦN/NGÀY + hàm ý; nêu nhanh 3 kịch bản kèm % (vd "năm mươi lăm phần trăm ...").
7. Khuyến nghị quan sát + mời follow KenvinZone và AURORA.

LƯU Ý:
- Thuật ngữ tiếng Anh GIỮ tiếng Anh: S&P 500, Nasdaq, SPY, QQQ, Gamma, Net GEX, Put Wall, Call Wall, Gamma Flip, Fed. KHÔNG phiên âm.
- Mốc giá/điểm để dạng số để đọc đúng; số đếm nhỏ & % viết chữ.
- KHÔNG hô hào "mua ngay/bán ngay/chắc chắn/all in". Giọng tham khảo, định lượng.

scenarios: đúng 3, tone base/down/up, tổng pct = 100 (số nguyên). name ngắn (≤22 ký tự).
divergence_tag: 1 câu ngắn nêu phân kỳ hoặc đồng pha của 2 chỉ số.
cover_title ≤80 ký tự. yt_description nhiều emoji + "KHÔNG phải lời khuyên đầu tư" + hashtag (#sp500 #nasdaq #chungkhoanmy #gamma #kenvinzone). yt_tags 12–15 tag không #.

ĐẦU RA: CHỈ một object JSON đúng schema sau:
""" + SCHEMA


def build_prompt(frame_note, spx, nas):
    def desc(ix):
        g = ix["gamma"]
        fl = "; ".join(f'{f["label"]} {f["value"]:+.2f}' for f in ix["forces"])
        dv = ix["divergence"]
        return (f'{ix["name"]} ({ix["ticker"]}): điểm {ix["score"]:+.1f} ({ix["regime"]}), tuần {ix["week_score"]:+.1f}. '
                f'Lực chính: {fl}. '
                f'Gamma {ix["gamma"]["underlying"]}: Net GEX {g["net_gex_m"]:+.0f} triệu ({"ÂM" if g["net_gex_m"]<0 else "DƯƠNG"}), '
                f'Spot {g["spot"]} ({"trên" if g["spot"]>=g["flip"] else "dưới"} Flip {g["flip"]}), Put Wall {g["put"]}, Call Wall {g["call"]}, biến động kỳ vọng ±{g["expected_move"]}. '
                f'Phân kỳ: {dv.get("status")} (tuần {dv.get("weeklyScore")} · ngày {dv.get("dailyScore")}).')
    return f"{frame_note}\n\n=== DỮ LIỆU (dùng đúng số) ===\n- {desc(spx)}\n\n- {desc(nas)}\n"


def validate(deck):
    errs = []
    sl = deck.get("script_lines", [])
    if len(sl) != 7:
        errs.append(f"script_lines phải ĐÚNG 7 dòng (đang {len(sl)})")
    words = len(re.findall(r"\w+", " ".join(str(x) for x in sl)))
    if words > 260:
        errs.append(f"script {words} từ — QUÁ DÀI; cắt còn ≤ 190 từ")
    sc = deck.get("scenarios", [])
    if len(sc) != 3:
        errs.append(f"scenarios phải 3 (đang {len(sc)})")
    else:
        tot = sum(int(x.get("pct", 0)) for x in sc)
        if not (95 <= tot <= 105):
            errs.append(f"tổng % kịch bản = {tot}, cần ≈100")
    return errs


def finalize(deck, spx, nas, det):
    scen = []
    for s in deck.get("scenarios", []):
        tone = s.get("tone", "base")
        scen.append({"pct": int(s.get("pct", 0)), "color": SCEN_COLOR.get(tone, "#fbbf24"), "name": s.get("name", "")})
    return {
        "template": "equity-bias-hf",
        "date": det["date"],
        "eyebrow": det["eyebrow"],
        "title_html": det["title_html"],
        "date_prefix": det["date_prefix"],
        "cadence_word": det["cadence_word"],
        "indices": [spx, nas],
        "divergence_tag": deck.get("divergence_tag") or divergence_fallback(spx, nas),
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
    title = deck.get("cover_title") or f"Bias định lượng S&P 500 & Nasdaq — cấu trúc Gamma · {dd}/{mm}"
    meta = {"youtube": {"title": title[:98], "description": deck.get("yt_description", ""),
                        "tags": deck.get("yt_tags", []), "privacyStatus": "private",
                        "categoryId": "25", "madeForKids": False},
            "source": {"kind": "equity-bias", "date": date_full}}
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    ps = {"subtitles": {"enabled": True, "color": "#7dd3fc", "fontSize": 18, "bottom": 60, "maxLines": 1},
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
    ap.add_argument("--frame", default="daily", choices=["daily", "weekly"])
    ap.add_argument("--date")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    blob = json.loads(Path(a.data).read_text(encoding="utf-8"))
    assets = blob.get("assets") or {}
    spx_a, nas_a = assets.get("SPX"), assets.get("NASDAQ")
    if not spx_a or not nas_a:
        sys.exit("Thiếu assets.SPX hoặc assets.NASDAQ")
    _SYM[id(spx_a)] = "SPX"; _SYM[id(nas_a)] = "NASDAQ"
    weekly = a.frame == "weekly"
    spx = build_index(spx_a, a.frame)
    nas = build_index(nas_a, a.frame)

    fr0 = spx_a.get(a.frame) or {}
    date_full = a.date or _as_ddmmyyyy(fr0.get("asOf")) or datetime.now().strftime("%d/%m/%Y")
    if weekly:
        frame_note = "ĐÂY LÀ BẢN TIN THEO TUẦN (khung tuần). Giọng tổng quan cả tuần; dòng 6 nói 'tuần tới'."
        det = {"date": date_full, "eyebrow": "⚡ WEEKLY BIAS · CHỨNG KHOÁN MỸ",
               "title_html": "BIAS ĐỊNH LƯỢNG<br/>CHỨNG KHOÁN MỸ · TUẦN",
               "date_prefix": "TUẦN · dữ liệu đến", "cadence_word": "tuần"}
        proj = "equity-us-week-{}{}{}".format(*date_full.split("/"))
    else:
        frame_note = "ĐÂY LÀ BẢN TIN THEO NGÀY. Dòng 6 nói 'phiên tới'."
        det = {"date": date_full, "eyebrow": "⚡ DAILY BIAS · CHỨNG KHOÁN MỸ",
               "title_html": "BIAS ĐỊNH LƯỢNG<br/>CHỨNG KHOÁN MỸ",
               "date_prefix": "PHIÊN", "cadence_word": "phiên"}
        proj = "equity-us-{}{}{}".format(*date_full.split("/"))

    model = resolve_model(key)
    print(f"=== [1/2] Gemini viết kịch bản CK Mỹ [{a.frame}] {date_full} | SPX {spx['score']:+.1f} {spx['regime']} · NAS {nas['score']:+.1f} {nas['regime']} | model={model} ===", flush=True)
    base = build_prompt(frame_note, spx, nas)
    last_err = ""
    for attempt in range(1, 4):
        prompt = base if attempt == 1 else base + f"\n\nLƯU Ý: lần trước lỗi:\n{last_err}\nSửa đúng schema + đủ 7 dòng."
        raw = normalize_names(gemini(SPEC, prompt, key, model))
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON lỗi: {e}"; print("  " + last_err, flush=True); continue
        errs = validate(deck)
        if errs:
            last_err = "; ".join(errs); print("  validate: " + last_err, flush=True); continue
        hf = finalize(deck, spx, nas, det)
        out_dir = REPO / "slide" / proj
        assemble(hf, deck, date_full, out_dir)
        print(f"=== [2/2] Đã dựng {proj} ===", flush=True)
        print(f"PROJECT={proj}")
        return
    sys.exit(f"Không dựng được deck CK Mỹ sau 3 lượt. Lỗi cuối: {last_err}")


if __name__ == "__main__":
    main()
