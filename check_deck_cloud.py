#!/usr/bin/env python3
"""Validator GỌN cho deck Giải Mã trên pipeline cloud (chỉ hf-data + script + metadata).
Khác verify_deck.py gốc (kiểm cả deck Web UI index.html/app.js) — ở cloud render HyperFrames
chỉ cần hf-data.json + script-90s.txt + upload-metadata.json.

   python check_deck_cloud.py slide/giai-ma-tin-tuc-<chude>-<ddmm>
Mã thoát 0 = ĐẠT, 1 = CHƯA ĐẠT.
"""
import json, os, re, sys

REVEAL = [1, 3, 3, 3, 4, 4, 3, 3, 3]
FORBID = ["chắc chắn tăng", "chắc chắn giảm", "cam kết lãi", "x2 tài khoản", "x3 tài khoản", "làm giàu nhanh",
          "mua ngay", "bán ngay", "bí mật nội bộ", "thao túng", "lãi đảm bảo", "không thể thua", "all-in", "all in"]
HF_KEYS = ["template", "date", "source", "hook", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "outro"]


def main(d):
    d = os.path.abspath(d); name = os.path.basename(d); errs = []; warns = []
    def bad(m): errs.append(m)
    def warn(m): warns.append(m)
    def rd(f):
        p = os.path.join(d, f)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None

    # ---- script-90s.txt ----
    sc = rd("script-90s.txt")
    if sc is None:
        bad("thiếu script-90s.txt")
        lines = []
    else:
        lines = [l.strip() for l in sc.split("\n") if l.strip()]
        if len(lines) != 9:
            bad(f"script cần 9 dòng, có {len(lines)}")
        else:
            counts = [len([s for s in re.split(r"(?<=[.!?])\s+", l) if s.strip()]) for l in lines]
            if counts != REVEAL:
                bad(f"số câu/dòng {counts} ≠ {REVEAL}")
        words = len(re.findall(r"\w+", " ".join(lines)))
        if words > 720:
            bad(f"script {words} từ — QUÁ DÀI, video sẽ vượt 3 phút Shorts; cắt gọn còn ≤ 620 từ (câu ngắn, bỏ ý lan man)")
        elif words > 680:
            warn(f"script {words} từ — hơi dài (sát mốc 3 phút), nên gọn thêm nếu được")
        elif words < 420:
            warn(f"script {words} từ — hơi ngắn")
        low = (sc or "").lower()
        for w in FORBID:
            if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", low):
                bad(f"từ cấm/nhạy cảm: '{w}'")
        if len(lines) > 1 and not re.search(r"nguồn|đăng|tác giả|báo cáo|bài viết", lines[1], re.I):
            warn("dòng 2 nên nêu nguồn (trang, tác giả, ngày)")
        if lines and not re.search(r"không phải|chứ không phải|không là", lines[-1]):
            warn("dòng cuối thiếu disclaimer 'không phải lời khuyên đầu tư'")

    # ---- hf-data.json ----
    hf = None
    try:
        hf = json.loads(rd("hf-data.json") or "")
    except Exception as e:
        bad(f"hf-data.json hỏng hoặc thiếu: {e}")
    if hf:
        for k in HF_KEYS:
            if k not in hf:
                bad(f"hf-data thiếu khóa '{k}'")
        if hf.get("template") != "giaima-tin-hf":
            bad(f"hf-data.template phải 'giaima-tin-hf' (đang {hf.get('template')!r})")
        dt = str(hf.get("date") or "")
        md = re.match(r"(\d{1,2})/(\d{1,2})", dt)
        mf = re.search(r"(?<!\d)(\d{2})-(\d{2})(?!\d)", name)
        if not md:
            bad(f"hf-data.date {dt!r} sai dạng DD/MM/YYYY")
        elif mf and (int(mf.group(1)), int(mf.group(2))) != (int(md.group(1)), int(md.group(2))):
            bad(f"hf-data.date '{dt}' lệch ngày với thư mục '{name}'")
        hook = hf.get("hook") or {}
        tl = hook.get("title_lines") or []
        if len(tl) != 2:
            bad(f"hook.title_lines cần 2 dòng, có {len(tl)}")
        for l in tl:
            if len(str(l)) > 22:
                warn(f"tiêu đề cover '{l}' dài {len(str(l))} ký tự (>22)")
        if len(hook.get("chips") or []) != 3:
            bad(f"hook.chips cần 3, có {len(hook.get('chips') or [])}")
        lights = [str((x or {}).get("color")) for x in (hf.get("s5") or {}).get("lights") or []]
        if sorted(lights) != ["green", "red", "yellow"]:
            bad(f"s5.lights cần đúng green/yellow/red, thấy {lights}")
        if len((hf.get("s4") or {}).get("cards") or []) != 3:
            warn("s4.cards nên có 3")
        if len((hf.get("s7") or {}).get("items") or []) != 3:
            warn("s7.items nên có 3")
        src = hf.get("source") or {}
        if not src.get("site") or not src.get("headline"):
            bad("hf-data.source thiếu site/headline (dẫn nguồn)")

    # ---- upload-metadata.json ----
    try:
        md = json.loads(rd("upload-metadata.json") or "")
        blob = json.dumps(md, ensure_ascii=False).lower()
        if "#escbase" in blob:
            bad("metadata chứa #Escbase")
        y = md.get("youtube", {})
        t = y.get("title", "")
        if not t or len(t) > 100:
            bad(f"YouTube title rỗng hoặc >100 ({len(t)})")
        if not t.lstrip().startswith("[Giải mã]"):
            warn("YouTube title nên bắt đầu '[Giải mã] '")
        if "khuyến nghị" not in y.get("description", "").lower():
            bad("YouTube description thiếu câu 'không phải khuyến nghị đầu tư'")
        if "http" not in y.get("description", ""):
            warn("YouTube description chưa có link nguồn")
        if "#kechuyenchungkhoan" not in blob:
            warn("thiếu hashtag kênh #kechuyenchungkhoan")
    except Exception as e:
        bad(f"upload-metadata.json hỏng/thiếu: {e}")

    print(f"=== check_deck_cloud: {name} ===")
    for w in warns: print("  CẢNH BÁO:", w)
    for e in errs: print("  LỖI:", e)
    print("KẾT QUẢ:", "ĐẠT" if not errs else f"CHƯA ĐẠT ({len(errs)} lỗi)")
    return 1 if errs else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1]))
