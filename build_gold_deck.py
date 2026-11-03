#!/usr/bin/env python3
"""BỘ NÃO VÀNG: báo cáo Bias định lượng (bias-web/data/latest.json) -> deck gold-daily-bias-hf.

Chạy trên GitHub Actions (cần GEMINI_API_KEY). Dữ liệu SỐ (điểm Bias, 6 lực kéo, cấu trúc
Gamma GLD + XAUUSD, lịch sử 3 phiên) lấy TRỰC TIẾP & TẤT ĐỊNH từ latest.json — Gemini CHỈ
viết phần kể chuyện (3 kịch bản, 3 hành động, script 6 dòng, nhãn đọc, ghi chú tín dụng, mô tả YouTube).

   python build_gold_deck.py --data <latest.json> [--date DD/MM/YYYY] [--history ci-state/gold-history.json]

In ra PROJECT=<tên thư mục> ở dòng cuối để workflow lấy.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
from datetime import datetime, timedelta

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from build_deck_from_url import gemini, resolve_model, normalize_names  # tái dùng

BGM_REL = "preview-assets/bgm/20260624-151812_Write_You.mp3"

# 6 lực kéo cố định của template (key template -> nhãn VN + category nguồn trong latest.json).
# Màu gán theo DẤU (âm = ấm/đỏ, dương = lạnh/xanh) nên trái = kéo xuống, phải = đỡ giá luôn đúng.
FORCE_MAP = [
    ("usd",       "Áp lực USD",            "usd"),
    ("flows",     "Dòng tiền & xu hướng",  "flows"),
    ("gold_spec", "Yếu tố riêng của Vàng", "gold_specific"),
    ("rates",     "Lãi suất thực",         "rates"),
    ("m2",        "Thanh khoản M2",        "liquidity"),
    ("risk",      "Khẩu vị rủi ro",        "risk"),
]
WARM = ["#ef4444", "#f87171", "#fb923c"]   # cho lực ÂM (kéo giá xuống)
COOL = ["#4ade80", "#38bdf8", "#c084fc"]   # cho lực DƯƠNG (đỡ giá)

REGIME_VN = {
    "bullish": "TĂNG GIÁ", "bearish": "GIẢM GIÁ", "neutral": "TRUNG LẬP",
    "strong bullish": "TĂNG MẠNH", "strong bearish": "GIẢM MẠNH",
    "slightly bullish": "HƠI TĂNG", "slightly bearish": "HƠI GIẢM",
}
SCEN_COLOR = {"base": "#fbbf24", "down": "#f87171", "up": "#4ade80"}
ACTION_STYLE = {"neutral": ("⇆", "#fbbf24"), "buy": ("▲", "#4ade80"), "risk": ("▼", "#f87171")}

SFX_TICKS = ["usd", "flows", "gold_spec", "rates", "m2", "risk", "spot", "flip", "put", "call", "s_base", "s_down", "s_up"]
SFX_IMPACTS = ["score", "gex"]


def regime_vn(s: str) -> str:
    return REGIME_VN.get(str(s or "").strip().lower(), str(s or "TRUNG LẬP").upper())


def cat_contrib(cats: list, key: str) -> float:
    for c in cats:
        if c.get("key") == key:
            return round(float(c.get("contribution", 0.0)), 2)
    return 0.0


def cat_raw(cats: list, key: str):
    for c in cats:
        if c.get("key") == key:
            return c.get("rawScore")
    return None


def build_forces(cats: list) -> list:
    forces = []
    wi = ci = 0
    for key, label, src in FORCE_MAP:
        val = cat_contrib(cats, src)
        if val < 0:
            color = WARM[wi % len(WARM)]; wi += 1
        else:
            color = COOL[ci % len(COOL)]; ci += 1
        forces.append({"key": key, "label": label, "value": val, "color": color})
    return forces


def build_gamma(g: dict) -> dict:
    gld = {k: g.get(k) for k in ("putWall", "callWall", "gammaFlip", "spot")}
    xau = g.get("spotAsset", {}) or {}
    vals = [v for v in (gld["putWall"], gld["callWall"], gld["gammaFlip"], gld["spot"]) if v is not None]
    lo = (int(min(vals) // 5) * 5) - 5
    hi = (int(-(-max(vals) // 5)) * 5) + 5
    net_m = round(float(g.get("netGex", 0.0)) / 1e6, 1)
    return {
        "axis": [lo, hi],
        "net_gex_m": net_m,
        "call": {"gld": gld["callWall"], "xau": round(float(xau.get("callWall")), 0) if xau.get("callWall") else None},
        "flip": {"gld": gld["gammaFlip"], "xau": round(float(xau.get("gammaFlip")), 0) if xau.get("gammaFlip") else None},
        "spot": {"gld": gld["spot"], "xau": round(float(xau.get("spot")), 1) if xau.get("spot") else None},
        "put":  {"gld": gld["putWall"], "xau": round(float(xau.get("putWall")), 0) if xau.get("putWall") else None},
    }


def roll_history(hist_path: Path, date_full: str, score: float, prev_score) -> list:
    """Lịch sử 3 phiên gần nhất [[DD/MM, score], ...]. Tự tích luỹ theo ngày trong ci-state."""
    dd_mm = "/".join(date_full.split("/")[:2])
    try:
        items = json.loads(hist_path.read_text(encoding="utf-8")) if hist_path.exists() else []
    except Exception:
        items = []
    if not isinstance(items, list):
        items = []
    # seed điểm phiên trước ở lần chạy đầu (để đường xu hướng có độ dốc ngay)
    if not items and prev_score is not None:
        try:
            y = (datetime.strptime(date_full, "%d/%m/%Y") - timedelta(days=1))
            items.append({"full": y.strftime("%d/%m/%Y"), "d": y.strftime("%d/%m"), "score": round(float(prev_score), 2)})
        except Exception:
            pass
    items = [it for it in items if it.get("full") != date_full]            # upsert hôm nay
    items.append({"full": date_full, "d": dd_mm, "score": round(float(score), 2)})
    items = items[-30:]
    try:
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        hist_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  [history] cảnh báo: không ghi được {hist_path}: {e}", flush=True)
    disp = items[-3:]
    # pad trái đủ 3 điểm (ngày đầu) bằng cách lùi ngày, giữ giá trị cũ nhất
    while len(disp) < 3:
        first = disp[0]
        try:
            pd = datetime.strptime(first["full"], "%d/%m/%Y") - timedelta(days=1)
            disp.insert(0, {"full": pd.strftime("%d/%m/%Y"), "d": pd.strftime("%d/%m"), "score": first["score"]})
        except Exception:
            disp.insert(0, dict(first))
    return [[it["d"], it["score"]] for it in disp]


def trend_tag(history: list, score_change) -> str:
    vals = [v for _, v in history]
    if len(set(vals)) == 1:
        return "Đi ngang quanh mốc hiện tại"
    d1 = vals[1] - vals[0]
    d2 = vals[2] - vals[1]
    if d1 > 0 and d2 > 0:
        return "Cải thiện 3 phiên liên tiếp"
    if d1 < 0 and d2 < 0:
        return "3 phiên liên tiếp xấu đi"
    if (score_change or 0) > 0:
        return "Nhích lên so với phiên trước"
    if (score_change or 0) < 0:
        return "Giảm nhẹ so với phiên trước"
    return "Dao động, chưa có xu hướng rõ"


SCHEMA_EXAMPLE = r"""
{
  "stress": "Khẩu vị rủi ro ổn định · tín dụng chưa căng",
  "stress_note_html": "✅ Khẩu vị rủi ro còn <b>dương</b>, chưa có dấu hiệu căng thẳng tín dụng ép dòng tiền rời Vàng",
  "scenarios": [
    {"key":"s_base","tone":"base","pct":60,"name":"Giằng co trong biên","desc":"Dao động giữa Put Wall <b>360</b> (≈<b>3.897</b>) và Call Wall <b>375</b> (≈<b>4.060</b>)"},
    {"key":"s_down","tone":"down","pct":22,"name":"Phá vỡ giảm","desc":"USD &amp; lãi suất bật lại, thủng <b>360</b> (≈<b>3.897</b>) → test sâu hơn"},
    {"key":"s_up","tone":"up","pct":18,"name":"Bứt phá trú ẩn","desc":"Vượt Call Wall <b>375</b> (≈<b>4.060</b>) khi rủi ro tăng"}
  ],
  "actions": [
    {"key":"neutral","title":"Giữ trung tính trong biên","desc":"<b>360–375</b> GLD · ≈ <b>3.897–4.060</b> XAUUSD"},
    {"key":"buy","title":"Điều kiện mua lại","desc":"Đóng cửa vững trên Gamma Flip <b>365</b> (≈ <b>3.951</b>)"},
    {"key":"risk","title":"Rủi ro cần tránh","desc":"Thủng Put Wall <b>360</b> (≈ <b>3.897</b>) → áp lực bán"}
  ],
  "anchors": {
    "score":"không phẩy bảy","trend":"đi ngang","neutral":"Trung Lập",
    "usd":"âm ba phẩy chín","flows":"âm ba phẩy tám","gold_spec":"âm hai phẩy năm",
    "counterweight":"Đối trọng","rates":"dương chín","m2":"dương một phẩy bảy","risk":"dương một phẩy tám","stress":"tín dụng",
    "gex":"Net GEX","gex_value":"dương hai phẩy năm","spot":"Giá GLD","spot_xau":"ba chín tám","flip":"mốc đảo chiều",
    "put":"Put Wall","call":"Call Wall","vol":"kìm nén",
    "s_base":"sáu mươi phần","s_down":"hai mươi hai phần","s_up":"mười tám phần",
    "act_neutral":"giữ trung tính","act_buy":"đóng cửa","aurora":"AURORA","follow":"Hãy follow"
  },
  "script_lines": ["... đúng 6 dòng ..."],
  "cover_title": "Tiêu đề YouTube ngắn, nêu rõ Vàng + bias + ngày",
  "yt_description": "mô tả YouTube dài, có emoji, các mục BIAS/LỰC KÉO/GAMMA/KỊCH BẢN/HÀNH ĐỘNG + disclaimer",
  "yt_tags": ["vàng","gold","xauusd","..."]
}
"""

SPEC = """Bạn là biên tập viên bản tin "Phân tích định lượng VÀNG" hằng ngày của KenvinZone Analytics (kênh Chuyện Chứng Khoán & KenvinZone). Nhiệm vụ: nhận các CON SỐ đã tính sẵn từ nền tảng Market Bias (điểm bias, 6 lực kéo, cấu trúc Gamma GLD + XAUUSD, lịch sử 3 phiên) rồi viết PHẦN KỂ CHUYỆN cho video dọc 9:16, xuất ra MỘT object JSON đúng schema bên dưới.

NGUYÊN TẮC SỐ LIỆU (quan trọng nhất):
- TUYỆT ĐỐI không bịa số. Mọi mốc giá/điểm (score, giá trị 6 lực, Put Wall/Call Wall/Gamma Flip/Spot của GLD và XAUUSD, Net GEX, %) phải DÙNG ĐÚNG số được cung cấp ở phần DỮ LIỆU.
- Khi nhắc mốc XAUUSD dùng số làm tròn được cung cấp; GLD giữ nguyên.
- Ghi chú tín dụng/khẩu vị rủi ro (stress) phải PHẢN ÁNH ĐÚNG dấu của các lực "Khẩu vị rủi ro", "Thanh khoản M2": nếu các lực này DƯƠNG thì KHÔNG được nói "tín dụng căng thẳng" — phải nói rủi ro còn ổn định/hỗ trợ. Chỉ cảnh báo căng thẳng khi chúng ÂM rõ.

GAMMA (bám đúng chế độ hiện tại):
- Nếu Net GEX DƯƠNG (gamma dương): thị trường có xu hướng bị GHIM/kìm nén trong biên, dao động co lại; xác suất kịch bản "giằng co trong biên" nên CAO.
- Nếu Net GEX ÂM (gamma âm): biến động bị KHUẾCH ĐẠI, dễ phá biên; nêu rủi ro hai chiều.
- Spot nằm TRÊN Gamma Flip → đang ở vùng gamma dương; DƯỚI Flip → vùng gamma âm. Mô tả cho đúng.

3 KỊCH BẢN (scenarios): đúng 3, tone lần lượt gợi ý base/down/up, tổng pct = 100 (số nguyên). desc nêu mốc Put/Call/Flip thật (GLD và ≈XAUUSD), dùng thẻ <b></b> cho số.
3 HÀNH ĐỘNG (actions): đúng 3 với key "neutral" (giữ trung tính trong biên), "buy" (điều kiện mua lại), "risk" (rủi ro cần tránh) — mỗi cái nêu mốc cụ thể.

SCRIPT ĐỌC (script_lines) — ĐÚNG 6 DÒNG, mỗi dòng 1 câu trọn ý, tổng ~90–140 TỪ (video BẮT BUỘC DƯỚI 3 phút, càng gọn càng tốt). THỨ TỰ CỐ ĐỊNH (để khớp hình):
1. Hook: điểm Bias Vàng hôm nay + nhãn chế độ (TRUNG LẬP/TĂNG/GIẢM) + xu hướng mấy phiên.
2. Các lực KÉO GIÁ XUỐNG đang mạnh (nêu 2–3 lực âm lớn nhất: USD, dòng tiền, yếu tố riêng của Vàng...).
3. Các lực ĐỠ GIÁ / đối trọng (lãi suất thực, thanh khoản M2, khẩu vị rủi ro) + một câu về tín dụng/rủi ro cho đúng dấu.
4. Cấu trúc Gamma: Net GEX dương/âm, giá GLD so Gamma Flip, kẹp giữa Put Wall và Call Wall, hệ quả (kìm nén hay khuếch đại).
5. Ba kịch bản phiên tới kèm % (vd "sáu mươi phần trăm ... ; hai mươi hai phần trăm ... ; mười tám phần trăm ...").
6. Khuyến nghị: giữ trung tính trong biên / điều kiện mua lại / rủi ro cần tránh + lời mời follow KenvinZone và AURORA.

LƯU Ý SCRIPT:
- Thuật ngữ tiếng Anh GIỮ NGUYÊN tiếng Anh cả khi đọc: Gold, GLD, XAUUSD, Gamma, Net GEX, Put Wall, Call Wall, Gamma Flip, Fed, Dow Jones, S&P 500, Nasdaq. TUYỆT ĐỐI KHÔNG phiên âm kiểu "gô", "gam-ma", "pút oon".
- Mốc giá/điểm GIỮ dạng số để đọc chính xác (360 ; 375 ; 365 ; 3.981); số đếm nhỏ và % viết chữ ("sáu mươi phần trăm", "âm ba phẩy chín").
- KHÔNG dùng: "chắc chắn tăng/giảm", "cam kết lãi", "mua ngay", "bán ngay", "all in", "x2 tài khoản", "lãi đảm bảo". Giọng tham khảo: "kịch bản", "cần canh", "theo dõi".

anchors: với MỖI beat, ghi 1–3 TỪ đúng như sẽ đọc trong script_lines (để khớp animation). Nếu không chắc cứ ghi gần đúng — hệ thống có vị trí dự phòng.

cover_title: tiêu đề video ngắn (≤70 ký tự) nêu Vàng + chế độ bias + ngày.
yt_description: mô tả dài nhiều emoji: ĐIỂM BIAS, 6 LỰC KÉO, CẤU TRÚC GAMMA, 3 KỊCH BẢN, KẾ HOẠCH HÀNH ĐỘNG, rồi disclaimer "KHÔNG phải lời khuyên đầu tư", kết bằng hashtag (#vang #gold #xauusd #giavang #phantichdinhluong #kenvinzone). yt_tags: 12–15 tag không dấu #.

ĐẦU RA: CHỈ một object JSON đúng schema sau (không text thừa), đúng kiểu dữ liệu:
""" + SCHEMA_EXAMPLE


def build_prompt(date_full, weekday_note, regime, score, score_change, forces, gamma, hist) -> str:
    fl = "\n".join(f"  - {f['label']} ({f['key']}): {f['value']:+.2f} điểm" for f in forces)
    gld = gamma
    neg = gamma["net_gex_m"] < 0
    spot_above = (gamma["spot"]["gld"] or 0) >= (gamma["flip"]["gld"] or 0)
    g_txt = (
        f"  - Net GEX: {gamma['net_gex_m']:+.1f} triệu USD ({'ÂM → gamma âm, biến động khuếch đại' if neg else 'DƯƠNG → gamma dương, biến động kìm nén'})\n"
        f"  - Giá hiện tại: GLD {gld['spot']['gld']} · XAUUSD ≈ {gld['spot']['xau']}  ({'TRÊN' if spot_above else 'DƯỚI'} Gamma Flip → {'vùng gamma dương' if spot_above else 'vùng gamma âm'})\n"
        f"  - Gamma Flip: GLD {gld['flip']['gld']} · ≈ {gld['flip']['xau']}\n"
        f"  - Put Wall: GLD {gld['put']['gld']} · ≈ {gld['put']['xau']}\n"
        f"  - Call Wall: GLD {gld['call']['gld']} · ≈ {gld['call']['xau']}"
    )
    h_txt = " → ".join(f"{d}:{v:+.2f}" for d, v in hist)
    return (
        f"NGÀY: {date_full}. {weekday_note}\n\n"
        f"=== DỮ LIỆU BIAS VÀNG (đã tính sẵn — dùng đúng số) ===\n"
        f"ĐIỂM BIAS tổng: {score:+.2f} / 100 — chế độ: {regime} — thay đổi so phiên trước: {score_change:+.2f}\n"
        f"Lịch sử 3 phiên (điểm): {h_txt}\n\n"
        f"6 LỰC KÉO (đóng góp vào điểm, + là đỡ giá, − là kéo xuống):\n{fl}\n\n"
        f"CẤU TRÚC GAMMA:\n{g_txt}\n"
    )


def validate(deck: dict) -> list:
    errs = []
    sl = deck.get("script_lines", [])
    if len(sl) != 6:
        errs.append(f"script_lines phải ĐÚNG 6 dòng (đang {len(sl)})")
    words = len(re.findall(r"\w+", " ".join(str(x) for x in sl)))
    if words > 230:
        errs.append(f"script {words} từ — QUÁ DÀI cho video dưới 3 phút; cắt còn ≤ 160 từ")
    sc = deck.get("scenarios", [])
    if len(sc) != 3:
        errs.append(f"scenarios phải 3 kịch bản (đang {len(sc)})")
    else:
        tot = sum(int(x.get("pct", 0)) for x in sc)
        if not (95 <= tot <= 105):
            errs.append(f"tổng % kịch bản = {tot}, cần ≈100")
    if len(deck.get("actions", [])) != 3:
        errs.append("actions phải 3")
    return errs


def finalize(deck: dict, det: dict) -> dict:
    """Ghép phần Gemini (narrative) + phần tất định (số) thành hf-data.json hoàn chỉnh."""
    scen = []
    for s in deck.get("scenarios", []):
        tone = s.get("tone", "base")
        scen.append({"key": s.get("key") or f"s_{tone}", "pct": int(s.get("pct", 0)),
                     "color": SCEN_COLOR.get(tone, "#fbbf24"), "name": s.get("name", ""), "desc": s.get("desc", "")})
    acts = []
    for a in deck.get("actions", []):
        icon, color = ACTION_STYLE.get(a.get("key", "neutral"), ("•", "#fbbf24"))
        acts.append({"icon": icon, "color": color, "title": a.get("title", ""), "desc": a.get("desc", "")})
    hf = {
        "template": "gold-daily-bias-hf",
        "date": det["date"],
        "title_html": "BÁO CÁO NHANH VĨ MÔ<br/>&amp; BIAS NGÀY",
        "regime": det["regime"],
        "score": det["score"],
        "history": det["history"],
        "trend_tag": det["trend_tag"],
        "forces": det["forces"],
        "stress": deck.get("stress", ""),
        "gamma": det["gamma"],
        "scenarios": scen,
        "actions": acts,
        "anchors": deck.get("anchors", {}),
        "sfx_ticks": SFX_TICKS,
        "sfx_impacts": SFX_IMPACTS,
        "audio_offset": 1.0,
        "outro_hold": 3.6,
    }
    if deck.get("stress_note_html"):
        hf["stress_note_html"] = deck["stress_note_html"]
    return hf


def assemble(hf: dict, deck: dict, proj: str, date_full: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [str(x).strip() for x in deck.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dd, mm = date_full.split("/")[0], date_full.split("/")[1]
    title = deck.get("cover_title") or f"Phân tích định lượng Vàng (Gold/XAUUSD) — Bias & cấu trúc Gamma ngày {dd}/{mm}"
    meta = {
        "youtube": {"title": title[:98], "description": deck.get("yt_description", ""),
                    "tags": deck.get("yt_tags", []), "privacyStatus": "private",
                    "categoryId": "25", "madeForKids": False},
        "source": {"kind": "gold-daily-bias", "date": date_full},
    }
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    ps = {
        "subtitles": {"enabled": True, "color": "#fde047", "fontSize": 18, "bottom": 60, "maxLines": 1},
        "backgroundFx": "candlestick",
        "bgm": {"mode": "preset", "preset": "ambient", "volume": 0.18},
        "scriptLines": lines,
        "slides": {"deletedIds": [], "scriptLines": lines},
        "visuals": {"colorMode": "dark", "backgroundColor": "#060a13", "gridEnabled": False,
                    "backgroundFx": "candlestick-diag"},
    }
    (out_dir / "preview-settings.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="đường dẫn latest.json (bias-web/data/latest.json)")
    ap.add_argument("--date", help="DD/MM/YYYY (mặc định: daily.asOf hoặc hôm nay)")
    ap.add_argument("--history", default=str(REPO / "ci-state" / "gold-history.json"))
    ap.add_argument("--asset", default="GOLD")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")

    blob = json.loads(Path(a.data).read_text(encoding="utf-8"))
    asset = (blob.get("assets") or {}).get(a.asset)
    if not asset:
        sys.exit(f"Không thấy assets.{a.asset} trong {a.data}")
    daily = asset.get("daily") or {}
    gamma_raw = asset.get("gamma") or {}
    cats = daily.get("categories") or []

    date_full = a.date or (daily.get("asOf") and _as_ddmmyyyy(daily["asOf"])) or datetime.now().strftime("%d/%m/%Y")
    d = datetime.strptime(date_full, "%d/%m/%Y")
    weekday_note = "Bản tin buổi sáng." if True else ""
    score = round(float(daily.get("score", 0.0)), 2)
    prev = daily.get("prevScore")
    score_change = round(float(daily.get("scoreChange", 0.0)), 2)
    regime = regime_vn(daily.get("regime"))
    forces = build_forces(cats)
    gamma = build_gamma(gamma_raw)
    history = roll_history(Path(a.history), date_full, score, prev)
    det = {"date": date_full, "regime": regime, "score": score, "history": history,
           "trend_tag": trend_tag(history, score_change), "forces": forces, "gamma": gamma}

    dd, mm, yyyy = date_full.split("/")
    proj = f"gold-bias-{dd}{mm}{yyyy}"

    model = resolve_model(key)
    print(f"=== [1/2] Gemini viết kịch bản Vàng {date_full} | score={score:+.2f} {regime} | gamma={'DƯƠNG' if gamma['net_gex_m']>=0 else 'ÂM'} {gamma['net_gex_m']:+.1f}M | model={model} ===", flush=True)
    base = build_prompt(date_full, weekday_note, regime, score, score_change, forces, gamma, history)
    last_err = ""
    for attempt in range(1, 4):
        prompt = base if attempt == 1 else base + f"\n\nLƯU Ý: lần trước lỗi:\n{last_err}\nSửa đúng schema + đủ số dòng."
        raw = normalize_names(gemini(SPEC, prompt, key, model))
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON không hợp lệ: {e}"; print("  " + last_err, flush=True); continue
        errs = validate(deck)
        if errs:
            last_err = "; ".join(errs); print("  lỗi validate: " + last_err, flush=True); continue
        hf = finalize(deck, det)
        out_dir = REPO / "slide" / proj
        assemble(hf, deck, proj, date_full, out_dir)
        print(f"=== [2/2] Đã dựng {proj} ===", flush=True)
        print(f"PROJECT={proj}")
        return
    sys.exit(f"Không dựng được deck Vàng sau 3 lượt. Lỗi cuối: {last_err}")


def _as_ddmmyyyy(s: str) -> str:
    s = str(s).strip()[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
