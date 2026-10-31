#!/usr/bin/env python3
"""BỘ NÃO (Gemini): 1 link bài báo -> deck Giải Mã hoàn chỉnh cho pipeline cloud.

Chạy trên GitHub Actions (mạng mở, gọi được Gemini). KHÔNG chạy được trong container
Cowork hay device_bash (Gemini bị chặn ở đó).

   python build_deck_from_url.py --url <link> [--date DD/MM/YYYY] [--slug <chude>]

Tạo: slide/giai-ma-tin-tuc-<slug>-<ddmm>/  gồm hf-data.json, script-90s.txt,
upload-metadata.json, preview-settings.json, source/source.md
Rồi chạy check_deck_cloud.py; nếu lệch, gửi lỗi lại cho Gemini sửa (tối đa 3 lượt).
In ra PROJECT=<tên thư mục> ở dòng cuối để workflow lấy.

Env: GEMINI_API_KEY (bắt buộc).
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, unicodedata, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent
MODEL = os.environ.get("KZ_BRAIN_MODEL", "gemini-2.5-flash")
BGM_REL = "preview-assets/bgm/20260624-151812_Write_You.mp3"

SPEC = """Bạn là biên tập viên của kênh "Kể Chuyện Chứng Khoán" (KenvinZone). Nhiệm vụ: đọc MỘT bài báo chứng khoán/kinh tế tiếng Việt và kể lại thành một video dọc 9 cảnh "Giải Mã", LUÔN dẫn nguồn, kèm góc nhìn cho nhà đầu tư F0. Diễn đạt LẠI, KHÔNG chép nguyên văn; chỉ giữ số liệu, tên tổ chức/người, phát biểu (ghi rõ ai nói).

QUY TẮC BẤT BIẾN:
1. script_lines ĐÚNG 9 dòng. Số CÂU mỗi dòng (tách bằng . ! ?) phải đúng: [1,3,3,3,4,4,3,3,3]. Dòng 1 = đúng 1 câu hook.
2. Dòng 3,4,5,7,8 MỞ ĐẦU bằng câu hỏi dẫn ("Vậy ... ?"). Dòng 5 dạng "Thứ nhất... Thứ hai... Và thứ ba..." (3 câu). Dòng 6 dạng "Đèn xanh là... Đèn vàng là... Còn đèn đỏ là..." (nhưng vẫn đúng 4 câu: 1 câu hỏi + 3 câu đèn).
3. SỐ trong lời đọc (script_lines) viết THÀNH CHỮ để TTS đọc đúng: ví dụ "bốn mươi hai phần trăm", "mười một nghìn tỷ đồng", "năm phẩy sáu". Nhưng trong hf-data (hiện trên slide) để NGUYÊN CHỮ SỐ.
4. Dòng 2 nêu nguồn: "Câu chuyện hôm nay được kể lại từ bài viết trên <trang>, tác giả <tên>, đăng ngày <ngày>...". Nếu bài không có tác giả, bỏ phần tác giả.
5. Dòng 9 = cái kết mở + mời theo dõi KenvinZone + disclaimer "đây chỉ là góc nhìn tham khảo chứ không phải lời khuyên đầu tư".
6. TUYỆT ĐỐI KHÔNG dùng các từ: "thao túng" (thay bằng "giao dịch phối hợp"), "mua ngay", "bán ngay", "chắc chắn tăng/giảm", "cam kết lãi", "x2/x3 tài khoản", "làm giàu nhanh", "bí mật nội bộ", "all in", "lãi đảm bảo". Giọng: "góc nhìn tham khảo", "kịch bản", "cần theo dõi".
7. Tổng độ dài script ~560–650 TỪ (dưới 3 phút Shorts). Mỗi mặt lợi phải kèm mặt rủi ro.
8. Tin nước ngoài/vĩ mô (Fed, phố Wall...) thì cảnh s6 BẮT BUỘC liên hệ chứng khoán Việt Nam.
9. Báo cáo của công ty chứng khoán: nêu rõ "đây là quan điểm của <đơn vị>", không biến "TVS chọn 5 cổ phiếu" thành "nên mua".
10. Nếu người dùng đưa tiêu đề cover sẵn, GIỮ NGUYÊN VĂN (kể cả chữ "Cổ phiếu"), không rút gọn.

ĐẦU RA: CHỈ một đối tượng JSON (không văn bản thừa) theo đúng schema sau. Mỗi cảnh một ý; số liệu khớp bài.
{
  "source": {"site": "tên báo", "short": "viết tắt", "author": "tên tác giả hoặc ''", "headline": "tiêu đề gốc của bài", "date": "DD/MM/YYYY", "url": "url rút gọn"},
  "hook": {"eyebrow": "Chuyện Chứng Khoán", "title_lines": ["dòng 1 <=20 ký tự", "dòng 2 <=20 ký tự"], "sub": "1 câu phụ ngắn", "chips": [{"icon":"↘","text":"vd LNTT -42%","tone":"down"},{"icon":"⑂","text":"...","tone":"gold"},{"icon":"◆","text":"...","tone":"blue"}]},
  "s1": {"title": "Tin hôm nay ta giải mã", "summary_html": "1-2 câu, cụm cần nhấn bọc <mark>...</mark>"},
  "s2": {"title_lines": ["Bức tranh chung","ảm đạm đến đâu?"], "stats": [{"value": 11000, "decimals":0, "unit":"tỷ", "label":"...", "badge":"-42% YoY", "tone":"gold", "beat":1}], "note": "1 câu nền"},
  "s3": {"title_lines": ["Sự phân hóa","thể hiện ra sao?"], "lead": "Kẻ thắng — người thua", "bars": [{"label":"TCBS","display":"+6%","value":6,"beat":1},{"label":"VIX","display":"-92,9%","value":-92.9,"beat":2}], "callout": {"value":41,"suffix":"%","text":"...","beat":1}},
  "s4": {"title_lines": ["Dịch chuyển","giữa các mảng?"], "cards": [{"big":"12.300 tỷ","title":"...","text":"..."},{"big":"...","title":"...","text":"..."},{"big":"...","title":"...","text":"..."}]},
  "s5": {"title_lines": ["Ai thắng","ai thua?"], "lights": [{"color":"green","tag":"THẮNG THẾ","title":"...","text":"..."},{"color":"yellow","tag":"LƯU Ý","title":"...","text":"..."},{"color":"red","tag":"KHÓ KHĂN","title":"...","text":"..."}]},
  "s6": {"title_lines": ["Vì sao","phân hóa lớn vậy?"], "chain": [{"title":"...","text":"...","beat":1},{"title":"...","text":"...","beat":1},{"title":"...","text":"...","beat":2}]},
  "s7": {"title_lines": ["Nhà đầu tư","nên làm gì?"], "items": [{"icon":"check","title":"...","text":"...","beat":1},{"icon":"check","title":"...","text":"...","beat":1},{"icon":"warn","title":"...","text":"...","beat":2}]},
  "outro": {"tag": "Giải Mã Chứng Khoán", "closing": "1 câu kết đọng", "cta": "Theo dõi để giải mã tin tiếp theo"},
  "script_lines": ["... 9 dòng ..."],
  "youtube": {"title": "<trục chuyện> | Chuyện Chứng Khoán (<=90 ký tự, KHÔNG tự thêm [Giải mã])", "description": "icon + 1 câu giải mã + 'Trong video:' 4-5 gạch đầu dòng số liệu + 'Nguồn: <trang> — <tác giả>, <ngày>: <url>' + 'Tổng hợp & bình luận lại, KHÔNG phải khuyến nghị đầu tư.' + hashtag", "tags": ["khong dau #","..."]}
}
- "tone" của chip: up/down/gold/blue. "value" trong stats/bars là SỐ (âm cho giảm). "beat" = câu thứ mấy (đếm từ 0) trong dòng script tương ứng mà khối xuất hiện (câu hỏi dẫn là câu 0, nội dung thường beat 1 hoặc 2).
- description PHẢI có link url nguồn và câu disclaimer 'không phải khuyến nghị đầu tư'. hashtag gồm: #ChuyenChungKhoan #KenvinZone #giaimachungkhoan #kechuyenchungkhoan #xuhuongchungkhoan + vài tag theo bài.
"""


def today_vn():
    return datetime.now(timezone(timedelta(hours=7)))


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "", s).lower()
    return s[:28] or "tin"


def fetch_article(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KenvinZone bot)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        html = r.read().decode("utf-8", "replace")
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:12000]


def resolve_model(api_key):
    if os.environ.get("KZ_BRAIN_MODEL"):
        return os.environ["KZ_BRAIN_MODEL"]
    u = "https://generativelanguage.googleapis.com/v1beta/models"
    req = urllib.request.Request(u, headers={"x-goog-api-key": api_key})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    names = []
    for m in data.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            n = m["name"].split("/")[-1]
            if "tts" in n or "image" in n or "embedding" in n or "vision" in n:
                continue
            names.append(n)
    def score(n):
        s = 0
        if "2.5" in n: s += 100
        elif "2.0" in n: s += 50
        if "flash" in n: s += 20
        if "latest" in n: s += 5
        if "preview" in n or "exp" in n: s -= 3
        return s
    names.sort(key=score, reverse=True)
    if not names:
        raise RuntimeError("Khóa không truy cập được model generateContent nào.")
    print(f"  model khả dụng: {names[:6]}", flush=True)
    return names[0]


def gemini(system, user, api_key, model):
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6, "maxOutputTokens": 8192},
    }
    u = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    req = urllib.request.Request(u, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"Gemini HTTP {e.code} model={model}: {detail}")
    cand = (d.get("candidates") or [{}])[0]
    parts = (cand.get("content") or {}).get("parts") or [{}]
    return parts[0].get("text", "")


def assemble(deck, proj, date_full, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    hf = {"template": "giaima-tin-hf", "date": date_full, "handle": "@kechuyen.chungkhoan"}
    for k in ["source", "hook", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "outro"]:
        hf[k] = deck.get(k, {})
    hf["audio_offset"] = 1.0
    hf["outro_hold"] = 3.6
    (out_dir / "hf-data.json").write_text(json.dumps(hf, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [str(x).strip() for x in deck.get("script_lines", [])]
    (out_dir / "script-90s.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    y = deck.get("youtube", {})
    title = str(y.get("title", "")).strip()
    if not title.lstrip().startswith("[Giải mã]"):
        title = "[Giải mã] " + title
    title = title[:100]
    src = deck.get("source", {})
    meta = {
        "youtube": {"title": title, "description": y.get("description", ""), "tags": y.get("tags", []),
                    "privacyStatus": "private", "categoryId": "25", "madeForKids": False},
        "facebook_reels": {"caption": (deck.get("s1", {}).get("summary_html", "") or title).replace("<mark>", "").replace("</mark>", ""),
                           "videoState": "DRAFT", "sourceComment": f"Nguồn: {src.get('url','')} — {src.get('site','')}"},
        "tiktok": {"title": title.replace("[Giải mã] ", ""), "privacy": "SELF_ONLY"},
        "instagram": {"caption": title.replace("[Giải mã] ", ""), "privacy": "private"},
        "source": src,
    }
    (out_dir / "upload-metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    ps = {"scriptLines": lines, "slides": {"scriptLines": lines},
          "bgm": {"mode": "custom", "volume": 0.2, "custom": {"path": BGM_REL, "url": f"/slide/{proj}/{BGM_REL}"}},
          "subtitles": {"enabled": True}, "heroTitle": {"mode": "default"},
          "backgroundFx": "candlestick-diag", "visuals": {"backgroundFx": "candlestick-diag"}}
    (out_dir / "preview-settings.json").write_text(json.dumps(ps, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "source").mkdir(exist_ok=True)
    (out_dir / "source" / "source.md").write_text(
        f"# {src.get('headline','')}\n- Trang: {src.get('site','')}\n- Tác giả: {src.get('author','')}\n- Ngày: {src.get('date','')}\n- URL: {src.get('url','')}\n", encoding="utf-8")
    canon = REPO / "assets" / "bgm" / "20260624-151812_Write_You.mp3"
    dst = out_dir / BGM_REL
    if canon.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(canon.read_bytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--date", help="DD/MM/YYYY")
    ap.add_argument("--slug")
    ap.add_argument("--title")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY")
    now = today_vn()
    date_full = a.date or now.strftime("%d/%m/%Y")
    dd, mm = date_full.split("/")[0].zfill(2), date_full.split("/")[1].zfill(2)
    print(f"=== [1/3] Đọc bài: {a.url} ===", flush=True)
    article = fetch_article(a.url)
    print(f"  lấy được {len(article)} ký tự", flush=True)
    model = resolve_model(key)
    print(f"  dùng model: {model}", flush=True)
    user = f"LINK: {a.url}\n"
    if a.title:
        user += f"TIÊU ĐỀ COVER NGƯỜI DÙNG ÉP (giữ nguyên văn, chia 2 dòng hợp lý): {a.title}\n"
    user += f"NGÀY ĐĂNG/NGÀY LÀM: {date_full}\n\nNỘI DUNG BÀI (đã rút tag):\n{article}"
    proj = None
    last_err = ""
    for attempt in range(1, 4):
        print(f"=== [2/3] Gemini dựng deck (lượt {attempt}) ===", flush=True)
        prompt = user if attempt == 1 else user + f"\n\nLƯU Ý: lần trước deck bị các lỗi sau, hãy SỬA đúng:\n{last_err}"
        raw = gemini(SPEC, prompt, key, model)
        try:
            deck = json.loads(raw)
        except Exception as e:
            last_err = f"JSON không hợp lệ: {e}"
            print("  " + last_err, flush=True)
            continue
        if not proj:
            slug = a.slug or slugify(deck.get("source", {}).get("headline", "") or "tin")
            proj = f"giai-ma-tin-tuc-{slug}-{dd}-{mm}"
        out_dir = REPO / "slide" / proj
        assemble(deck, proj, date_full, out_dir)
        print("=== [3/3] Kiểm tra deck ===", flush=True)
        r = subprocess.run([sys.executable, str(REPO / "check_deck_cloud.py"), str(out_dir)],
                           capture_output=True, text=True)
        print(r.stdout, flush=True)
        if r.returncode == 0:
            print(f"PROJECT={proj}")
            return
        last_err = "\n".join([l for l in r.stdout.splitlines() if "LỖI:" in l])
    sys.exit(f"Không dựng được deck đạt sau 3 lượt. Lỗi cuối:\n{last_err}")


if __name__ == "__main__":
    main()
