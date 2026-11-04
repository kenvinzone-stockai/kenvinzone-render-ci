#!/usr/bin/env python3
"""KHUNG MẪU — TEMPLATE HYPERFRAMES.

Mỗi template là một build.py sinh ra CÁC CẢNH (s0..s8 + captions) dưới dạng HTML tự chứa,
mỗi cảnh có timeline GSAP RIÊNG. Khung dọc 1080x1920, 30fps.

CÁCH DÙNG:
  - Cách nhanh nhất: COPY cả thư mục template gần giống nhất (vd template/giaima-tin-hf/)
    sang template/<loại-mới>-hf/ rồi sửa từng cảnh. File này là SKELETON minh họa các
    KHUÔN MẪU BẮT BUỘC để animation chạy đúng.

★ LUẬT VÀNG (sai là hình "đứng im", chỉ còn tiếng + phụ đề):
  Timeline mỗi cảnh chạy TƯƠNG ĐỐI theo mốc bắt đầu cảnh. Luôn trừ 'base' = start của cảnh.
  tline(line, frac, base=st) với base = thời điểm cảnh bắt đầu → ra thời gian NỘI BỘ cảnh.

★ Phụ đề trong VÙNG AN TOÀN (top ≤ ~1205px) — không để chìm khỏi khung người xem.
★ Hiệu ứng số: counter đếm, VU-meter (kim/thanh nhiệt chạy rồi dừng), scale-punch khi chốt.
★ SFX theo sự kiện: tick ở mỗi số, impact khi chốt điểm.
★ Cover s0: cỡ chữ có SÀN tối thiểu + white-space:nowrap; khung cách phụ đề đủ rộng (không chèn viền).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))
D = DATA
OFF = float(D.get("audio_offset", 1.0))   # giây lặng đầu video

W, H, FPS = 1080, 1920, 30
GOLD, BLUE = "#f5c451", "#3b82f6"

# ---- Mốc thời gian từng DÒNG lời đọc (dùng cho reveal theo câu) ----
# BEATS[i] = (start_giây, độ_dài_giây) của dòng i trong lời đọc. Lấy từ SUBS/timing.
# (Ở template thật, tính từ subtitle-word-timing.json; đây minh họa cấu trúc.)
def line_beats(i):
    seg = SUBS[i] if i < len(SUBS) else {"start": 0, "dur": 3}
    return (round(float(seg["start"]) + OFF, 3), float(seg.get("dur", 3)))
BEATS = [line_beats(i) for i in range(9)]

# Start/duration của từng CẢNH (thường = mốc dòng lời đọc tương ứng)
def scene_at(i):
    s, d = BEATS[i]
    return (0.0 if i == 0 else s), d


# ★ Helper thời gian NỘI BỘ cảnh — LUÔN truyền base = start của cảnh
def tline(line, frac, base=0.0):
    s, d = BEATS[line]
    return round(s + frac * d + OFF - base, 3)


def esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---- Khung HTML 1 cảnh (tự chứa: CSS + body + JS GSAP) ----
def scene_file(cid, dur, css, body, js):
    return f"""<template data-cid="{cid}" data-dur="{dur}">
<style>{css}</style>
{body}
<script>
(function(){{
  const QA=(s)=>Array.from(document.querySelectorAll(s));
  const tl = gsap.timeline();
  {js}
  window.__timelines = window.__timelines || {{}};
  window.__timelines["{cid}"] = tl;
}})();
</script>
</template>"""


# ================= CẢNH 0 — COVER (tiêu đề) =================
def s0():
    st, dur = scene_at(0)
    h = D["hook"]; lines = h["title_lines"]
    # Cỡ chữ: SÀN tối thiểu để tiêu đề dài không bị bé; trần để tiêu đề ngắn vẫn to.
    fa = int(max(58, min(120, 900 / (max(1, len(lines[0])) * 0.72))))
    fb = int(max(54, min(104, 900 / (max(1, len(lines[1]) if len(lines) > 1 else 1) * 0.72))))
    tb = 495 + int(fa * 1.34) + (int(fb * 1.30) if len(lines) > 1 else 0) + 44
    css = f"""
.plate{{position:absolute;top:495px;left:40px;right:40px;text-align:center;}}
.plate div{{display:inline-block;padding:22px 30px;border-radius:26px;
  border:2px solid rgba(96,165,250,.45);box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(59,130,246,.2);}}
.plate .a{{display:block;font-size:{fa}px;font-weight:900;white-space:nowrap;color:#bfe0ff;}}
.plate .b{{display:block;font-size:{fb}px;font-weight:900;white-space:nowrap;color:{GOLD};}}
/* tb + 72 : chừa đủ chỗ để dòng phụ đề KHÔNG chèn lên viền khung tiêu đề */
.flow{{position:absolute;top:{tb + 72}px;left:40px;right:40px;text-align:center;}}
.sub{{font-size:38px;font-weight:800;color:{GOLD};}}
"""
    body = (f'<div class="plate"><div><h1><span class="a">{esc(lines[0])}</span>'
            f'<span class="b">{esc(lines[1]) if len(lines) > 1 else ""}</span></h1></div></div>'
            f'<div class="flow"><div class="sub">{esc(h.get("sub",""))}</div></div>')
    js = ""  # cover hiện đủ ở frame 0 (dùng làm thumbnail)
    return cid_dur("s0", dur, css, body, js)


# ================= CẢNH CÓ SỐ (ví dụ counter + VU-meter) =================
def s_number(idx, cid):
    st, dur = scene_at(idx)
    val = D.get(cid, {}).get("value", 0)
    css = """
.cap{position:absolute;top:1205px;left:40px;right:40px;text-align:center;font-size:40px;color:#fff;} /* VÙNG AN TOÀN */
.num{position:absolute;top:620px;left:0;right:0;text-align:center;font-size:150px;font-weight:900;color:#f5c451;}
.marker{position:absolute;top:900px;left:50%;width:18px;height:60px;background:#f5c451;}
"""
    body = f'<div class="num" id="N">0</div><div class="marker" id="MK"></div><div class="cap" id="CAP"></div>'
    # ★ Mọi thời gian trừ base = st (start cảnh). counter đếm + kim chạy rồi dừng.
    js = f"""
    // counter đếm số
    var o={{v:0}}; tl.to(o, {{v:{val}, duration:1.1, ease:'power2.out',
      onUpdate:function(){{document.getElementById('N').textContent=Math.round(o.v);}}}}, {tline(idx,0.1,st)});
    // VU-meter: kim quét trái->phải rồi elastic dừng
    tl.set('#MK',{{left:'50%'}}, 0);
    tl.to('#MK',{{left:'12%',duration:0.25}}, {tline(idx,0.1,st)});
    tl.to('#MK',{{left:'86%',duration:0.5}}, {tline(idx,0.3,st)});
    tl.to('#MK',{{left:'60%',duration:0.8,ease:'elastic.out(1,0.4)'}}, {tline(idx,0.55,st)});
    // scale-punch khi chốt
    tl.fromTo('#N',{{scale:1}},{{scale:1.12,duration:0.18,yoyo:true,repeat:1}}, {tline(idx,0.75,st)});
    """
    return cid_dur(cid, dur, css, body, js)


def cid_dur(cid, dur, css, body, js):
    return cid, dur, scene_file(cid, dur, css, body, js)


# ================= PHỤ ĐỀ =================
def captions():
    # sinh track phụ đề từ SUBS (đặt trong vùng an toàn). Trả (cid, dur, html).
    return cid_dur("captions", sum(b[1] for b in BEATS), ".sub{bottom:...}", "<div id=caps></div>", "")


def main():
    comps = ROOT / "compositions"; comps.mkdir(exist_ok=True)
    meta = []
    scenes = [s0, lambda: s_number(2, "s2")]   # >>> SỬA: liệt kê đủ các cảnh của bạn
    for fn in scenes:
        cid, dur, txt = fn()
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, dur))
    cid, dur, txt = captions()
    (comps / "captions.html").write_text(txt, encoding="utf-8")
    print("scenes", meta)


if __name__ == "__main__":
    main()
