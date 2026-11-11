#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KenvinZone — AURORA TRADING EXPLAINER → HyperFrames composition generator (Module 4, v2).

Usage:  python build.py data.json subtitle-word-timing.json   (render_hyperframes gọi với cwd=work)

v2 — contract MỚI theo bàn giao của ANTI (SAMPLE_HF_DATA_VOLUME_PROFILE_B.json):
  * DATA["coordinate_system"]  -> hệ tọa độ giá dùng chung (price_to_y) trên canvas 1080x1920.
  * DATA["scenes"]["s0".."s8"] -> mỗi cảnh tự khai báo phần tử đồ họa (nến, hộp, VP, level line,
    icon chibi...) + telemetry riêng; build.py chỉ RÁP bằng bộ 8 hàm chuẩn của trading_svg.py.
  * spawn_beat (0..1) trong phần tử = thời điểm xuất hiện tính theo %% thời lượng cảnh.
Nhịp câu 9 cảnh [1,3,3,3,4,4,3,3,3]; mốc câu B(i,k) lấy từ subtitle-word-timing.
"""
import json, sys, math, html, re
from pathlib import Path
from trading_svg import (price_to_y, render_candlesticks, render_volume_profile,
                         render_bottom_volume_bars, render_subpanel_rsi, render_price_box,
                         render_polyline, render_level_line, render_icon_avatar, grid,
                         DEFAULT_COORD, UP, DOWN, VP, POC, MIDLINE, LEVEL, INK)

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))
D = DATA
OFF = float(D.get("audio_offset", 1.0))
OUTRO = float(D.get("outro_hold", 3.6))
W, H = 1080, 1920
SLIDES = SUBS["slides"]
if len(SLIDES) != 9:
    raise SystemExit(f"Aurora Explainer can 9 dong script (dang co {len(SLIDES)}).")
VO_LEN = float(SUBS.get("duration") or SUBS["captions"][-1]["end"])
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
WORDS = [(w["text"], float(w["start"])) for c in SUBS["captions"] for w in c["words"]]

SC = D.get("scenes") or {}
if not SC:
    raise SystemExit("hf-data thieu khoi 'scenes' (contract v2 cua ANTI).")
COORD = dict(DEFAULT_COORD); COORD.update(D.get("coordinate_system") or {})
CX0 = COORD["chart_left_x"]; CX1 = COORD["chart_left_x"] + COORD["chart_width_px"]


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", str(text).strip()) if s]


def _line_beats(i):
    st = float(SLIDES[i]["start"]); du = float(SLIDES[i]["duration"]); en = st + du
    sents = _sentences(SLIDES[i].get("text", "")); n = max(1, len(sents))
    ws = [(t, s) for t, s in WORDS if st - 0.05 <= s < en - 0.05]
    starts = []
    if ws:
        starts.append(ws[0][1])
        for k in range(len(ws) - 1):
            if re.search(r"[.!?]['\")\]]*$", ws[k][0]):
                starts.append(ws[k + 1][1])
    if len(starts) != n:
        tot = sum(len(s) for s in sents) or 1; acc = 0; starts = []
        for s in sents:
            starts.append(st + du * acc / tot); acc += len(s)
    return [round(x + OFF, 3) for x in starts], n


BEATS = [_line_beats(i) for i in range(9)]
def LS(i): return (0.0 if i == 0 else round(float(SLIDES[i]["start"]) + OFF, 3)), float(SLIDES[i]["duration"])
def B(i, k, add=0.0):
    starts, n = BEATS[i]; k = max(0, min(k, len(starts) - 1)); return round(starts[k] + add, 3)
SCENES = [(f"s{i}", LS(i)[0], (LS(i + 1)[0] if i < 8 else TOTAL)) for i in range(9)]
START = {c: s for c, s, e in SCENES}
def lt(scene, t_abs): return round(t_abs - START[scene], 3)
def mk(idx): st, en = SCENES[idx][1], SCENES[idx][2]; return f"s{idx}", round(en - st, 3)
def esc(s): return html.escape(str(s), quote=True)
def sb(el, dur, default=0.3):
    """spawn_beat (0..1) -> giây cục bộ trong cảnh (chừa 0.8s cuối cho exit)."""
    frac = float(el.get("spawn_beat", default) if isinstance(el, dict) else default)
    return round(max(0.2, min(frac, 0.95) * max(dur - 0.8, 1.0)), 2)


# ============================ các mảnh SVG cục bộ (ngoài 8 hàm) ============================
def svg_layer(content, vid):
    return (f'<svg id="{vid}" class="layer" xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{content}</svg>')


def arrow(p1, p2, label="", color=DOWN, idn="arr"):
    x1, y1 = p1; x2, y2 = p2
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 22 * math.cos(ang - 0.42), y2 - 22 * math.sin(ang - 0.42))
    a2 = (x2 - 22 * math.cos(ang + 0.42), y2 - 22 * math.sin(ang + 0.42))
    svg = (f'<g class="arrow" id="{idn}">'
           f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
           f'<polygon points="{x2},{y2} {a1[0]:.0f},{a1[1]:.0f} {a2[0]:.0f},{a2[1]:.0f}" fill="{color}"/>')
    if label:
        svg += (f'<text x="{(x1+x2)/2+16:.0f}" y="{(y1+y2)/2-10:.0f}" fill="{color}" font-size="27"'
                f' font-weight="900" font-family="Consolas,monospace">{esc(label)}</text>')
    return svg + '</g>'


def pill(x, y, text, color, idn="pil", fs=20):
    w = 28 + len(str(text)) * fs * 0.62
    return (f'<g class="spill" id="{idn}"><rect x="{x-w/2:.0f}" y="{y-18:.0f}" width="{w:.0f}" height="36"'
            f' rx="18" fill="{color}"/><text x="{x:.0f}" y="{y+7:.0f}" fill="{INK}" font-size="{fs}"'
            f' font-weight="900" text-anchor="middle" font-family="Arial">{esc(text)}</text></g>')


def candle_tag(c, text, color, idn, below=False):
    """Nhãn chú thích neo trên đỉnh (hoặc dưới chân, below=True) một cây nến (dạng s7)."""
    x = float(c["x"]) + float(c.get("width", 16)) / 2
    y = (price_to_y(c["l"], COORD) + 42) if below else (price_to_y(c["h"], COORD) - 34)
    return pill(x, y, text, color, idn, fs=17)


def backdrop_candles(upto_break=True, dim=0.5):
    """Ngữ cảnh nền cho s3..s7: nến giảm (s0) + sideway (s1) (+ nến thủng đáy)."""
    cands = list(sc("s0").get("candles", [])) + list(sc("s1").get("sideway_candles", []))
    if upto_break and sc("s1").get("breakout_candle"):
        cands = cands + [sc("s1")["breakout_candle"]]
    return f'<g class="backdrop" opacity="{dim}">{render_candlesticks(cands, COORD)}</g>'


def sc(cid):
    return SC.get(cid, {})


def telemetry(cid):
    t = sc(cid).get("telemetry", {"left": "", "right": ""})
    return (f'<div class="tele" id="{cid}-tele"><div class="cell l"><span class="k">TÂM LÝ</span>'
            f'<span class="v" id="{cid}-tl">{esc(t.get("left",""))}</span></div>'
            f'<div class="cell r"><span class="k">PHE NẮM QUYỀN</span>'
            f'<span class="v" id="{cid}-tr">{esc(t.get("right",""))}</span></div></div>')


def crumb(cid):
    return f'<div class="crumb">{esc(sc(cid).get("stage",""))}</div>'


FONT_CSS = """
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-latin-700-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-latin-900-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-latin-700-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-latin-800-normal.woff2') format('woff2');}
"""
BASE_CSS = """
#root{position:absolute;inset:0;font-family:'BVP','Segoe UI',sans-serif;color:#e7e9f0;}
.mono{font-family:'JBM',monospace;}
.layer{position:absolute;inset:0;width:100%;height:100%;z-index:5;}
.panel{position:absolute;left:36px;right:36px;top:252px;height:842px;background:#131722;border:1px solid rgba(255,255,255,.08);border-radius:28px;box-shadow:0 30px 80px rgba(0,0,0,.5);z-index:1;}
.crumb{position:absolute;top:296px;left:0;right:0;text-align:center;font-size:31px;font-weight:900;letter-spacing:6px;color:#aab3c5;text-transform:uppercase;z-index:8;}
.eb{position:absolute;top:238px;left:0;right:0;text-align:center;z-index:8;}
.eb span{display:inline-block;background:linear-gradient(135deg,#8b5cf6,#22d3ee);color:#0a0616;font-weight:900;font-size:26px;letter-spacing:4px;padding:11px 26px;border-radius:12px;}
.tele{position:absolute;left:40px;right:40px;top:1380px;display:flex;gap:20px;z-index:8;}
.tele .cell{flex:1;background:#0b0f19;border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:22px;text-align:center;}
.tele .cell .k{display:block;font-size:22px;font-weight:800;letter-spacing:2px;color:#6b7280;}
.tele .cell .v{display:block;margin-top:8px;font-size:38px;font-weight:900;}
.tele .cell.l .v{color:#f43f5e;} .tele .cell.r .v{color:#f59e0b;}
.htitle{position:absolute;left:40px;right:40px;top:120px;text-align:center;font-size:62px;font-weight:900;line-height:1.08;letter-spacing:-1px;z-index:8;}
.htitle .b{color:#f59e0b;}
.bigq{position:absolute;left:60px;right:60px;top:1150px;text-align:center;font-size:46px;font-weight:900;line-height:1.16;z-index:8;}
.bigq .g{background:linear-gradient(100deg,#22d3ee,#8b5cf6);-webkit-background-clip:text;background-clip:text;color:transparent;}
.badge{position:absolute;left:0;right:0;top:1160px;text-align:center;z-index:8;}
.badge span{display:inline-block;padding:18px 34px;border-radius:18px;font-size:40px;font-weight:900;background:#0b0f19;border:2px solid currentColor;}
.checklist{position:absolute;left:70px;right:70px;top:1120px;display:flex;flex-direction:column;gap:18px;z-index:8;}
.chk{display:flex;align-items:center;gap:20px;background:#131722;border:1px solid rgba(255,255,255,.1);border-left:5px solid #10b981;border-radius:16px;padding:18px 24px;font-size:29px;font-weight:800;}
.chk .n{width:48px;height:48px;border-radius:50%;background:#10b981;color:#06240f;display:flex;align-items:center;justify-content:center;font-weight:900;flex-shrink:0;}
.chk.warn{border-left-color:#f59e0b;} .chk.warn .n{background:#f59e0b;color:#2a1a04;}
.pane2{position:absolute;left:40px;right:40px;height:420px;background:#131722;border:1px solid rgba(255,255,255,.08);border-radius:22px;z-index:1;}
.pane2 .lab{position:absolute;top:18px;left:28px;font-size:30px;font-weight:900;}
.pane2 .bst{position:absolute;top:18px;right:28px;font-size:26px;font-weight:900;padding:6px 16px;border-radius:12px;background:#0b0f19;}
"""


def scene_file(cid, dur, css, body, js):
    return f"""<template>
<style>{FONT_CSS}{BASE_CSS}{css}</style>
<div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-duration="{dur}">
{body}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
const Q=(s)=>document.querySelector('[data-composition-id="{cid}"] '+s);
const QA=(s)=>document.querySelectorAll('[data-composition-id="{cid}"] '+s);
{js}
window.__timelines["{cid}"]=tl;
}})();
</script>
</template>
"""


def ex(stage, dur): return f"tl.to('{stage}',{{opacity:0,filter:'blur(10px)',duration:0.3,ease:'power3.in'}},{dur-0.32});"


def draw_candles_js(sel, t0, step=0.12):
    return (f"QA('{sel} .candle-item').forEach((c,i)=>{{tl.fromTo(c,{{opacity:0,scaleY:0,transformOrigin:'center bottom'}},"
            f"{{opacity:1,scaleY:1,duration:0.28,ease:'power2.out',immediateRender:false}},{t0}+i*{step});}});")


def pop_js(sel, t, scale=0.6):
    return (f"tl.fromTo('{sel}',{{opacity:0,scale:{scale},transformOrigin:'center'}},"
            f"{{opacity:1,scale:1,duration:0.5,ease:'back.out(2)',immediateRender:false}},{t});")


def wipe_js(sel, t, dur=0.5):
    return (f"tl.fromTo('{sel}',{{opacity:0,scaleX:0,transformOrigin:'left center'}},"
            f"{{opacity:1,scaleX:1,duration:{dur},ease:'power2.out',immediateRender:false}},{t});")


def stamp_js(sel, t):
    """Kinetic stamp: lao từ ngoài vào như con dấu (chuẩn V2 cua ANTI)."""
    return (f"tl.fromTo('{sel}',{{opacity:0,scale:3.1,transformOrigin:'center'}},"
            f"{{opacity:1,scale:1,duration:0.24,ease:'back.out(2.6)',immediateRender:false}},{t});")


def sig_ring(c, color, idn):
    """Vòng tròn nét đứt khoanh cây nến tín hiệu (học video gốc)."""
    x = float(c["x"]) + float(c.get("width", 16)) / 2
    y = (price_to_y(c["h"], COORD) + price_to_y(c["l"], COORD)) / 2
    r = max(40.0, abs(price_to_y(c["h"], COORD) - price_to_y(c["l"], COORD)) / 2 + 20)
    return (f'<circle class="sigring" id="{idn}" cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="none"'
            f' stroke="{color}" stroke-width="3.4" stroke-dasharray="9 7" opacity="0.95"/>')


# ============================ SCENES ============================
def s_hook():
    cid, dur = mk(0); s = sc("s0"); h = D.get("header", {})
    cands = s.get("candles", [])
    cover = D.get("cover", {}) or s.get("cover", {})
    # tách tiêu đề 2 dòng theo dấu chấm giữa (• hoặc ·)
    tparts = [x.strip() for x in re.split(r"[•·]", str(h.get("title", ""))) if x.strip()] or [str(h.get("title", ""))]
    la = tparts[0]; lb = tparts[1] if len(tparts) > 1 else ""
    fa = int(max(56, min(104, 880 / (max(1, len(la)) * 0.70))))
    fb = int(max(50, min(92, 880 / (max(1, len(lb)) * 0.70)))) if lb else 0
    points = cover.get("points") or [sc(k).get("stage", "") for k in ("s2", "s3", "s7")]
    points = [pt for pt in points if pt][:3]
    chips = "".join(f'<div class="c0-chip" id="c0chip{i}"><span class="n">{i+1}</span>{esc(pt)}</div>'
                    for i, pt in enumerate(points))
    # chart hook thu gọn dưới chips: trải nến đều theo X, trục giá cục bộ
    chart_svg = ""
    if cands:
        lo = min(c["l"] for c in cands) - 4; hi = max(c["h"] for c in cands) + 4
        c0 = {"price_min": lo, "price_max": hi, "chart_top_y": 925, "chart_height_px": 240,
              "chart_left_x": 120, "chart_width_px": 840}
        laid = [dict(c, x=170 + k * (760 / max(1, len(cands) - 1)), width=16, id=f"cv{k}")
                for k, c in enumerate(cands)]
        a1 = (laid[0]["x"] + 40, price_to_y(laid[0]["h"], c0) + 10)
        a2 = (laid[-1]["x"] - 10, price_to_y(laid[-1]["l"], c0) - 6)
        chart_svg = svg_layer(grid(c0) + f'<g id="g0c">{render_candlesticks(laid, c0)}</g>'
                              + arrow(a1, a2, s.get("arrow_drop", {}).get("label", ""), DOWN, "arr0"), "g0")
    css0 = f"""
.c0-plate{{position:absolute;top:356px;left:40px;right:40px;text-align:center;z-index:8;}}
.c0-plate>div{{display:inline-block;padding:24px 34px;border-radius:26px;border:2px solid rgba(139,92,246,.5);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(139,92,246,.08));box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(34,211,238,.18);}}
.c0-plate h1{{font-weight:900;line-height:1.16;letter-spacing:-0.5px;margin:0;}}
.c0-plate .a{{display:block;padding-top:.16em;font-size:{fa}px;white-space:nowrap;background:linear-gradient(100deg,#22d3ee,#8b5cf6);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.c0-plate .b{{display:block;padding-top:.14em;font-size:{fb}px;white-space:nowrap;background:linear-gradient(100deg,#fde68a,{POC});-webkit-background-clip:text;background-clip:text;color:transparent;}}
.c0-sub{{position:absolute;top:634px;left:0;right:0;text-align:center;font-size:33px;font-weight:900;letter-spacing:3px;color:{POC};text-transform:uppercase;z-index:8;}}
.c0-chips{{position:absolute;top:694px;left:60px;right:60px;display:flex;flex-direction:column;align-items:center;gap:12px;z-index:8;}}
.c0-chip{{display:flex;align-items:center;gap:14px;font-weight:800;font-size:29px;color:#e2e8f0;padding:10px 24px;border-radius:99px;border:2px solid rgba(139,92,246,.45);background:rgba(15,23,42,.72);}}
.c0-chip .n{{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#8b5cf6,#22d3ee);color:#0a0616;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:22px;flex-shrink:0;}}
"""
    body = (f'<div class="eb"><span>AURORA EXPLAINER</span></div>'
            f'<div class="c0-plate" id="c0t"><div><h1><span class="a">{esc(la)}</span>'
            + (f'<span class="b">{esc(lb)}</span>' if lb else "") + '</h1></div></div>'
            f'<div class="c0-sub" id="c0s">{esc(cover.get("sub", "HÔM NAY BẠN SẼ HIỂU"))}</div>'
            f'<div class="c0-chips" id="c0c">{chips}</div>'
            f'<div class="panel" style="top:892px;height:300px;border-radius:24px;"></div>{chart_svg}{telemetry("s0")}')
    js = ["tl.fromTo('#c0t',{opacity:0,scale:1.12,filter:'blur(12px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:0.55,ease:'expo.out'},0.15);",
          "gsap.set('#c0s,.c0-chip,#g0 .candle-item,#g0 .arrow',{opacity:0});",
          "tl.fromTo('#c0s',{opacity:0,y:16},{opacity:1,y:0,duration:0.4,ease:'expo.out'},0.7);",
          "QA('.c0-chip').forEach((c,i)=>{tl.fromTo(c,{opacity:0,x:-50},{opacity:1,x:0,duration:0.4,ease:'expo.out',immediateRender:false},0.9+i*0.18);});"]
    for k, c in enumerate(cands):
        js.append(f"tl.fromTo('#g0 #cv{k}',{{opacity:0,scaleY:0,transformOrigin:'center bottom'}},"
                  f"{{opacity:1,scaleY:1,duration:0.3,ease:'power2.out',immediateRender:false}},{sb(c,dur)});")
    if cands:
        js.append(wipe_js("#g0 #arr0", sb({"spawn_beat": 0.86}, dur)))
    js.append(f"tl.fromTo('#s0-tele',{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4}},0.4);{ex('.panel,#g0,#c0t,#c0s,#c0c',dur)}")
    return cid, dur, scene_file(cid, dur, css0, body, "".join(js))

def s_trap():
    cid, dur = mk(1); s = sc("s1")
    box = s.get("sideway_box", {})
    side = s.get("sideway_candles", [])
    brk = s.get("breakout_candle")
    parts = [grid(COORD), backdrop_candles(upto_break=False, dim=0.45)]
    if box:
        parts.append(render_price_box(box["top_price"], box["bottom_price"], box["start_x"], box["end_x"],
                                      COORD, style="dashed", label=box.get("label", "SIDEWAY")))
    parts.append(f'<g id="g1side">{render_candlesticks(side, COORD)}</g>')

    def _labels(lst):
        """Nhiều avatar đứng sát nhau cùng nhãn -> chỉ avatar giữa mang pill (tránh chồng chữ)."""
        labs = [x.get("label") for x in lst]
        dense = len(lst) >= 3 and len(set(labs)) == 1
        mid = len(lst) // 2
        return [x.get("label") if (not dense or j == mid) else None for j, x in enumerate(lst)]

    buyers = s.get("buyers", []); traps = s.get("trapped_buyers", [])
    for j, (b, lab) in enumerate(zip(buyers, _labels(buyers))):
        parts.append(render_icon_avatar(b["type"], b["x"], b["y"], label=lab, scale=0.9).replace(
            'class="avatar-icon"', f'class="avatar-icon buyer-av" id="buy{j}"', 1))
    if brk:
        parts.append(f'<g id="g1brk">{render_candlesticks([brk], COORD, highlight_idx=0)}</g>')
    for j, (b, lab) in enumerate(zip(traps, _labels(traps))):
        parts.append(render_icon_avatar(b["type"], b["x"], b["y"], label=lab, scale=0.9).replace(
            'class="avatar-icon"', f'class="avatar-icon trap-av" id="trap{j}"', 1))
    body = f'{crumb(cid)}<div class="panel"></div>{svg_layer("".join(parts), "g1")}{telemetry("s1")}'
    js = ["gsap.set('#g1side .candle-item,#g1 .price-box,#g1 .buyer-av,#g1 #g1brk,#g1 .trap-av',{opacity:0});",
          draw_candles_js('#g1side', 0.3, step=0.1),
          pop_js('#g1 .price-box', lt(cid, B(1, 0, 0.5)))]
    for j, b in enumerate(s.get("buyers", [])):
        js.append(pop_js(f"#buy{j}", sb(b, dur, 0.3 + j * 0.1)))
    if brk:
        # mở wrapper #g1brk đúng lúc (wrapper bị ẩn ở gsap.set đầu cảnh) rồi mới mọc nến
        js.append(f"tl.set('#g1brk',{{opacity:1}},{sb(brk,dur,0.75)});"
                  f"tl.fromTo('#g1brk .candle-item',{{opacity:0,scaleY:0,transformOrigin:'center top'}},"
                  f"{{opacity:1,scaleY:1,duration:0.4,ease:'power3.in',immediateRender:false}},{sb(brk,dur,0.75)});")
    for j, b in enumerate(s.get("trapped_buyers", [])):
        js.append(f"tl.to('#buy{j}',{{opacity:0,duration:0.2}},{sb(b,dur,0.85)});")
        js.append(pop_js(f"#trap{j}", sb(b, dur, 0.85)))
    js.append(f"tl.fromTo('#s1-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g1',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, "".join(js))


def _pane_svg(spec, top_y, vid):
    """Mini chart trong 1 pane s2: tự co trục giá + trải đều X vào pane."""
    cands = spec.get("candles", [])
    lo = min(c["l"] for c in cands) - 6; hi = max(c["h"] for c in cands) + 6
    c2 = {"price_min": lo, "price_max": hi, "chart_top_y": top_y + 86,
          "chart_height_px": 290, "chart_left_x": 200, "chart_width_px": 680}
    xs = [c["x"] for c in cands]
    x_lo, x_hi = min(xs), max(xs)
    span = (x_hi - x_lo) or 1
    laid = [dict(c, x=240 + (c["x"] - x_lo) / span * 560, width=30, id=f"{vid}_{k}")
            for k, c in enumerate(cands)]
    return f'<g id="{vid}">{grid(c2)}{render_candlesticks(laid, c2)}</g>'


def s_two():
    cid, dur = mk(2); s = sc("s2")
    a, b = s.get("chart_top", {}), s.get("chart_bottom", {})
    parts = [_pane_svg(a, 380, "mA"), _pane_svg(b, 830, "mB")]
    body = (f'{crumb(cid)}'
            f'<div class="pane2" style="top:380px;"><div class="lab" style="color:{UP};">{esc(a.get("label",""))}</div>'
            f'<div class="bst" style="color:{UP};">{esc(a.get("badge_status",""))}</div></div>'
            f'<div class="pane2" style="top:830px;"><div class="lab" style="color:{DOWN};">{esc(b.get("label",""))}</div>'
            f'<div class="bst" style="color:{DOWN};">{esc(b.get("badge_status",""))}</div></div>'
            f'{svg_layer("".join(parts), "g2")}'
            f'<div class="bigq" style="top:1280px;font-size:42px;">Mắt thường nhìn <span class="g">giống hệt nhau</span> — phân biệt thế nào?</div>'
            f'{telemetry("s2")}')
    js = ("gsap.set('#mA .candle-item,#mB .candle-item',{opacity:0});"
          "tl.fromTo('.pane2',{opacity:0,y:30},{opacity:1,y:0,duration:0.5,stagger:0.25,ease:'expo.out'},0.2);"
          + draw_candles_js('#mA', 0.55, step=0.07)
          + draw_candles_js('#mB', 0.95, step=0.07)
          + f"tl.fromTo('.bigq',{{opacity:0}},{{opacity:1,duration:0.5}},{lt(cid,B(2,2))});"
          + f"tl.fromTo('#s2-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('#root>*',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, js)


def s_vpq():
    cid, dur = mk(3); s = sc("s3")
    vp = s.get("volume_profile", {})
    co = s.get("callout_b_shape", {})
    box = sc("s1").get("sideway_box", {})
    parts = [grid(COORD), backdrop_candles(dim=0.5)]
    if box:
        parts.append(f'<g opacity="0.65">{render_price_box(box["top_price"], box["bottom_price"], box["start_x"], box["end_x"], COORD, style="dashed")}</g>')
    parts.append(f'<g id="g3vp">{render_volume_profile(vp.get("bins", []), COORD, vp.get("poc_price", 0), x_start=CX0, max_w=215)}</g>')
    if co:
        parts.append(f'<g id="g3co">{pill(CX0 + 330, price_to_y(vp.get("poc_price", 100), COORD) - 72, co.get("label", "HÌNH CHỮ b"), POC, "copill", fs=24)}'
                     f'{pill(CX0 + 330, price_to_y(vp.get("poc_price", 100), COORD) - 20, co.get("warning", ""), DOWN, "warnpill", fs=20)}</g>')
    body = f'{crumb(cid)}<div class="panel"></div>{svg_layer("".join(parts), "g3")}{telemetry("s3")}'
    js = ("gsap.set('#g3vp .vp-bar',{scaleX:0});gsap.set('#g3co',{opacity:0});"
          f"tl.fromTo('#g3vp .vp-bar',{{scaleX:0}},{{scaleX:1,duration:0.6,stagger:0.07,ease:'power2.out',immediateRender:false}},{lt(cid,B(3,1))});"
          f"tl.to('#g3vp .vp-bar[data-poc=\"1\"]',{{filter:'drop-shadow(0 0 16px {POC})',duration:0.4}},{lt(cid,B(3,2))});"
          + pop_js('#g3co', lt(cid, B(3, 2, 0.2)))
          + f"tl.fromTo('#s3-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g3',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, js)


def s_anatomy():
    cid, dur = mk(4); s = sc("s4")
    vp = sc("s3").get("volume_profile", {})
    thin, fat = s.get("thin_area_bracket", {}), s.get("fat_area_bracket", {})
    parts = [grid(COORD), backdrop_candles(dim=0.4),
             f'<g opacity="0.95">{render_volume_profile(vp.get("bins", []), COORD, vp.get("poc_price", 0), x_start=CX0, max_w=215)}</g>']
    def _bracket(spec, style, col, gid):
        """Hộp vùng giá + nhãn pill ĐẶT BÊN TRONG hộp (không đè tiêu đề/crumb)."""
        y_in = price_to_y(spec["top_price"], COORD) + 42
        xm = (CX0 + 240 + CX1 - 20) / 2
        return (f'<g id="{gid}">'
                f'{render_price_box(spec["top_price"], spec["bottom_price"], CX0 + 240, CX1 - 20, COORD, style=style, fill_color=col)}'
                f'{pill(xm, y_in, spec.get("label", ""), col, gid + "p", fs=18)}</g>')

    if thin:
        parts.append(_bracket(thin, "fvg", VP, "g4thin"))
    if fat:
        parts.append(_bracket(fat, "dashed", POC, "g4fat"))
    body = f'{crumb(cid)}<div class="panel"></div>{svg_layer("".join(parts), "g4")}{telemetry("s4")}'
    js = ("gsap.set('#g4thin,#g4fat',{opacity:0});"
          + pop_js('#g4thin', lt(cid, B(4, 1)), 0.92)
          + pop_js('#g4fat', lt(cid, B(4, 2)), 0.92)
          + f"tl.fromTo('#s4-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g4',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, js)


def s_shark():
    cid, dur = mk(5); s = sc("s5")
    vp = sc("s3").get("volume_profile", {})
    bar = s.get("seller_barrier", {}); av = s.get("bank_seller_avatar", {}); bd = s.get("badge_conclusion", {})
    parts = [grid(COORD), backdrop_candles(dim=0.45),
             f'<g opacity="0.8">{render_volume_profile(vp.get("bins", []), COORD, vp.get("poc_price", 0), x_start=CX0, max_w=215)}</g>']
    if bar:
        parts.append(f'<g id="g5bar">{render_level_line(bar["price"], COORD, label=bar.get("label",""), line_style="solid", color=DOWN)}</g>')
    if av:
        parts.append(render_icon_avatar(av.get("type", "bank_vault"), av["x"], av["y"],
                                        label=av.get("label"), scale=1.25).replace(
            'class="avatar-icon"', 'class="avatar-icon" id="g5av"', 1))
    # badge "sửa nhận thức sai": tách "A ✘  B ✔" -> A pop, gạch ngang A, rồi B đóng dấu
    btxt = str(bd.get("text", ""))
    m = re.match(r"^(.*?)[✘xX]\s*(.*?)[✔vV]?\s*$", btxt) if ("✘" in btxt and "✔" in btxt) else None
    if m:
        bad_html = (f'<span class="bd-bad" id="g5bad">{esc(m.group(1).strip())}'
                    f'<i class="strike" id="g5strike"></i></span>'
                    f'<span class="bd-good" id="g5good">{esc(m.group(2).strip())} ✔</span>')
    else:
        bad_html = f'<span id="g5bad">{esc(btxt)}</span>'
    css5 = """
.badge .bd-bad{position:relative;display:inline-block;color:#8e99ab;margin-right:26px;}
.badge .bd-bad .strike{position:absolute;left:-4%;top:52%;width:108%;height:5px;background:#f43f5e;border-radius:3px;transform:scaleX(0);transform-origin:left center;}
.badge .bd-good{display:inline-block;color:#f59e0b;}
"""
    body = (f'{crumb(cid)}<div class="panel"></div>{svg_layer("".join(parts), "g5")}'
            f'<div class="badge" id="g5bd" style="color:{bd.get("color", POC)};"><span>{bad_html}</span></div>'
            f'{telemetry("s5")}')
    js = ("gsap.set('#g5bar,#g5av,#g5bd',{opacity:0});"
          + wipe_js('#g5bar', lt(cid, B(5, 1)))
          + pop_js('#g5av', lt(cid, B(5, 2)))
          + f"tl.set('#g5bd',{{opacity:1}},{lt(cid,B(5,3))});"
          + pop_js('#g5bad', lt(cid, B(5, 3)), 0.8))
    if m:
        js += (f"gsap.set('#g5good',{{opacity:0}});"
               f"tl.to('#g5strike',{{scaleX:1,duration:0.3,ease:'power3.in',immediateRender:false}},{lt(cid,B(5,3,0.7))});"
               + stamp_js('#g5good', lt(cid, B(5, 3, 1.05))))
    js += f"tl.fromTo('#s5-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g5,#g5bd',dur)}"
    return cid, dur, scene_file(cid, dur, css5, body, js)


def s_howto():
    cid, dur = mk(6); s = sc("s6")
    rb = s.get("rule_badge_1", {}); sl = s.get("support_line", {})
    box = sc("s1").get("sideway_box", {})
    vp6 = sc("s3").get("volume_profile", {})
    parts = [grid(COORD), backdrop_candles(dim=0.5),
             f'<g opacity="0.5">{render_volume_profile(vp6.get("bins", []), COORD, vp6.get("poc_price", 0), x_start=CX0, max_w=215)}</g>']
    if box:
        parts.append(render_price_box(box["top_price"], box["bottom_price"], box["start_x"], box["end_x"], COORD, style="dashed", label=box.get("label", "")))
    if sl:
        parts.append(f'<g id="g6sl">{render_level_line(sl["price"], COORD, label=sl.get("label",""), color=sl.get("color", MIDLINE))}</g>')
    body = (f'{crumb(cid)}<div class="panel"></div>{svg_layer("".join(parts), "g6")}'
            f'<div class="checklist" style="top:1160px;"><div class="chk warn" id="g6rb"><div class="n">!</div>'
            f'<div>{esc(rb.get("text",""))}</div></div></div>{telemetry("s6")}')
    js = ("gsap.set('#g6sl,#g6rb',{opacity:0});"
          + wipe_js('#g6sl', lt(cid, B(6, 1)))
          + f"tl.fromTo('#g6rb',{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.5,ease:'expo.out',immediateRender:false}},{lt(cid,B(6,2))});"
          + f"tl.fromTo('#s6-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g6,.checklist',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, js)


def s_entry():
    cid, dur = mk(7); s = sc("s7")
    box = sc("s1").get("sideway_box", {})
    bo, rt = s.get("breakout_down"), s.get("retest_candle")
    ep, slx = s.get("sell_entry_pill", {}), s.get("stop_loss_line", {})
    items = s.get("checklist_rules", [])
    vp7 = sc("s3").get("volume_profile", {})
    parts = [grid(COORD), backdrop_candles(dim=0.4),
             f'<g opacity="0.42">{render_volume_profile(vp7.get("bins", []), COORD, vp7.get("poc_price", 0), x_start=CX0, max_w=215)}</g>']
    if box:
        parts.append(f'<g opacity="0.7">{render_price_box(box["top_price"], box["bottom_price"], box["start_x"], box["end_x"], COORD, style="dashed")}</g>')
    evs = []
    if bo:
        evs.append((f'<g id="g7bo">{render_candlesticks([dict(bo, width=bo.get("width", 20), id="c7bo")], COORD)}'
                    f'{sig_ring(bo, DOWN, "r7bo")}'
                    f'{candle_tag(bo, bo.get("label", ""), DOWN, "t7bo", below=True)}</g>', 1))
    if rt:
        evs.append((f'<g id="g7rt">{render_candlesticks([dict(rt, width=rt.get("width", 20), id="c7rt")], COORD)}'
                    f'{sig_ring(rt, POC, "r7rt")}'
                    f'{candle_tag(rt, rt.get("label", ""), POC, "t7rt")}</g>', 2))
    if ep:
        ey = price_to_y(ep.get("price", 100), COORD)
        ex0 = float(ep.get("x", 720))
        evs.append((f'<g id="g7ep"><line x1="{ex0:.0f}" y1="{ey:.0f}" x2="{CX1-10}" y2="{ey:.0f}"'
                    f' stroke="{ep.get("color", DOWN)}" stroke-width="2.6" stroke-dasharray="8 5"/>'
                    f'{pill(CX1 - 120, ey, ep.get("label", "BÁN"), ep.get("color", DOWN), "p7ep", fs=22)}</g>', 2))
    if slx:
        evs.append((f'<g id="g7sl">{render_level_line(slx["price"], COORD, label=slx.get("label",""), color=slx.get("color", DOWN))}</g>', 2))
    alt = s.get("alt_branch")
    if alt:
        ax = float(alt.get("from_x", (box.get("start_x", CX0) + box.get("end_x", CX1)) / 2))
        ay = price_to_y(box.get("top_price", COORD["price_max"] - 20), COORD)
        tx = float(alt.get("to_x", min(ax + 300, CX1 - 60)))
        ty = ay - float(alt.get("rise_px", 300))
        labs = alt.get("labels", ["TẠO ĐÁY THẬT", "PHÁ LÊN ĐỈNH VÙNG", "ĐỨNG NGOÀI"])
        # stack nhãn NGAY DƯỚI đầu mũi tên, đi xuống — không tràn lên vùng tiêu đề
        lab_svg = "".join(pill(tx - 30, ty + 52 + 48 * k, t, UP if k == len(labs) - 1 else "#e2e8f0",
                               f"altlab{k}", fs=18) for k, t in enumerate(labs))
        cross = (f'<g id="altcross"><path d="M{CX1-158} {price_to_y(ep.get("price",100),COORD)-22} '
                 f'L{CX1-82} {price_to_y(ep.get("price",100),COORD)+22} '
                 f'M{CX1-82} {price_to_y(ep.get("price",100),COORD)-22} '
                 f'L{CX1-158} {price_to_y(ep.get("price",100),COORD)+22}" '
                 f'stroke="{UP}" stroke-width="7" stroke-linecap="round"/></g>') if ep else ""
        parts.append(
            f'<g id="g7alt">'
            f'<path id="altpath" d="M{ax:.0f} {ay+60:.0f} Q {ax+40:.0f} {ty+40:.0f} {tx:.0f} {ty:.0f}"'
            f' fill="none" stroke="{UP}" stroke-width="6" stroke-linecap="round"/>'
            f'<polygon points="{tx:.0f},{ty-14:.0f} {tx-26:.0f},{ty+16:.0f} {tx+8:.0f},{ty+18:.0f}" fill="{UP}"/>'
            f'<g id="altlabs">{lab_svg}</g>{cross}</g>')
    parts += [e for e, _ in evs]
    rows = "".join(f'<div class="chk{" warn" if i==0 else ""}" id="chk{i}"><div class="n">{i+1}</div><div>{esc(re.sub(chr(10), " ", it))}</div></div>'
                   for i, it in enumerate(items))
    body = (f'{crumb(cid)}<div class="panel" style="height:800px;"></div>{svg_layer("".join(parts), "g7")}'
            f'<div class="checklist" style="top:1090px;">{rows}</div>{telemetry("s7")}')
    js = ["gsap.set('#g7bo,#g7rt,#g7ep,#g7sl,.chk,#g7alt',{opacity:0});"]
    gids = [g for g, used in [("#g7bo", bo), ("#g7rt", rt), ("#g7ep", ep), ("#g7sl", slx)] if used]
    for (frag, beat), gid in zip(evs, gids):
        if gid == "#g7ep":
            js.append(f"tl.set('#g7ep',{{opacity:1}},{lt(cid,B(7,beat))});" + stamp_js("#p7ep", lt(cid, B(7, beat))) +
                      f"tl.fromTo('#g7ep line',{{opacity:0}},{{opacity:1,duration:0.3,immediateRender:false}},{lt(cid,B(7,beat))});")
        else:
            js.append(pop_js(gid, lt(cid, B(7, beat)), 0.85))
    js.append("QA('.sigring').forEach(r=>{tl.fromTo(r,{scale:1.7,opacity:0,transformOrigin:'center'},"
              "{scale:1,opacity:1,duration:0.4,ease:'back.out(2)',immediateRender:false},"
              + str(lt(cid, B(7, 1, 0.35))) + ");});")
    if alt:
        t_alt = lt(cid, B(7, 2, 1.1))
        js.append(f"tl.set('#g7alt',{{opacity:1}},{t_alt});"
                  f"gsap.set('#altlabs .spill,#altcross,#g7alt polygon',{{opacity:0}});"
                  f"const AP=Q('#altpath');const AL=AP.getTotalLength();AP.style.strokeDasharray=AL;"
                  f"tl.fromTo(AP,{{strokeDashoffset:AL}},{{strokeDashoffset:0,duration:0.6,ease:'power2.out',immediateRender:false}},{t_alt});"
                  f"tl.fromTo('#g7alt polygon',{{opacity:0}},{{opacity:1,duration:0.15,immediateRender:false}},{t_alt}+0.55);"
                  f"QA('#altlabs .spill').forEach((x,k)=>{{tl.fromTo(x,{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.3,ease:'expo.out',immediateRender:false}},{t_alt}+0.55+k*0.22);}});")
        if ep:
            js.append(f"tl.fromTo('#altcross',{{opacity:0,scale:2.4,transformOrigin:'center'}},"
                      f"{{opacity:1,scale:1,duration:0.22,ease:'back.out(2.4)',immediateRender:false}},{t_alt}+1.15);")
    for i in range(len(items)):
        js.append(f"tl.fromTo('#chk{i}',{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.45,ease:'expo.out',immediateRender:false}},{lt(cid,B(7,min(i,2),0.15*i))});")
    js.append(f"tl.fromTo('#s7-tele',{{opacity:0}},{{opacity:1,duration:0.4}},0.2);{ex('.panel,#g7,.checklist',dur)}")
    return cid, dur, scene_file(cid, dur, "", body, "".join(js))


def s_outro():
    cid, dur = mk(8); s = sc("s8")
    lad = s.get("ladder_model", {}); cta = s.get("cta", {})
    steps = lad.get("steps", [])
    # trục giá CỤC BỘ cho bậc thang nằm gọn trong panel 500..960
    parts = []
    if steps:
        plo = min(x["price"] for x in steps) - 14; phi = max(x["price"] for x in steps) + 14
        c8 = {"price_min": plo, "price_max": phi, "chart_top_y": 545, "chart_height_px": 330,
              "chart_left_x": CX0, "chart_width_px": COORD["chart_width_px"]}
        n = max(1, len(steps)); seg_w = int((CX1 - CX0 - 80) / n)
        for i, stp in enumerate(steps):
            y = price_to_y(stp["price"], c8); x_a = CX0 + 40 + i * seg_w
            parts.append(f'<g class="lad" id="lad{i}">'
                         f'<line x1="{x_a}" y1="{y:.0f}" x2="{x_a+seg_w-36}" y2="{y:.0f}" stroke="{DOWN}" stroke-width="7" stroke-linecap="round"/>'
                         f'{pill(x_a + (seg_w-36)/2, y + 40, stp.get("label", ""), DOWN, f"ladp{i}", fs=18)}</g>')
            if i < n - 1:
                y2 = price_to_y(steps[i + 1]["price"], c8)
                parts.append(f'<g class="ladarr" id="ladarr{i}">{arrow((x_a+seg_w-30, y+8), (x_a+seg_w+4, y2-8), "", "#8b93a7", f"laa{i}")}</g>')
    css8 = f"""
.o8-h{{position:absolute;top:1005px;left:0;right:0;text-align:center;font-family:'JBM';font-weight:800;font-size:62px;background:linear-gradient(135deg,#22d3ee,#8b5cf6 55%,{POC});-webkit-background-clip:text;background-clip:text;color:transparent;z-index:8;}}
.o8-cta{{position:absolute;top:1092px;left:50px;right:50px;text-align:center;font-size:30px;font-weight:800;color:#e2e8f0;line-height:1.35;z-index:8;}}
.o8-pl{{position:absolute;top:1186px;left:0;right:0;display:flex;gap:14px;justify-content:center;z-index:8;}}
.o8-pl span{{font-family:'JBM';font-weight:800;font-size:27px;color:#93c5fd;border:2px solid rgba(96,165,250,.5);border-radius:12px;padding:7px 18px;}}
.o8-d{{position:absolute;left:70px;right:70px;top:1268px;text-align:center;font-size:26px;line-height:1.4;color:#fed7aa;padding:12px 18px;border:1px solid rgba(245,158,11,.3);border-radius:14px;background:rgba(255,255,255,.03);z-index:8;}}
.o8-d b{{color:#fff;}}
"""
    tg = cta.get("telegram", "")
    body = (f'<div class="eb" style="top:260px;"><span>GHI NHỚ</span></div>'
            f'<div class="htitle" style="top:350px;">“{esc(lad.get("title","NGỪNG GIẢM ≠ HẾT GIẢM"))}”</div>'
            f'<div class="panel" style="top:500px;height:460px;"></div>{svg_layer("".join(parts), "g8")}'
            f'<div class="o8-h" id="o8h">{esc(D.get("handle","@kenvinzone"))}</div>'
            f'<div class="o8-cta" id="o8c">{esc(cta.get("text",""))}' + (f' → <span class="mono" style="color:#22d3ee;">{esc(tg)}</span>' if tg else "") + '</div>'
            f'<div class="o8-pl" id="o8p"><span>TikTok</span><span>Reels</span><span>Shorts</span></div>'
            f'<div class="o8-d" id="o8d">Nội dung mang tính <b>giáo dục</b>, chỉ để tham khảo — <b>KHÔNG phải khuyến nghị đầu tư</b>.</div>')
    js = ["tl.fromTo('.htitle',{opacity:0,scale:1.1,filter:'blur(10px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:0.5,ease:'expo.out'},0.2);",
          "gsap.set('#g8 .lad,#g8 .ladarr,#o8h,#o8c,#o8p,#o8d',{opacity:0});"]
    for i in range(len(steps)):
        js.append(wipe_js(f"#lad{i}", lt(cid, B(8, 0, 0.5 + i * 0.5))))
        if i < len(steps) - 1:
            js.append(pop_js(f"#ladarr{i}", lt(cid, B(8, 0, 0.85 + i * 0.5)), 0.7))
    js.append(f"tl.fromTo('#o8h',{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.45,ease:'expo.out',immediateRender:false}},{lt(cid,B(8,1))});")
    js.append(f"tl.fromTo('#o8c',{{opacity:0}},{{opacity:1,duration:0.4,immediateRender:false}},{lt(cid,B(8,1,0.3))});")
    js.append(f"QA('#o8p span').forEach((x,k)=>{{tl.fromTo(x,{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.3,ease:'back.out(2)',immediateRender:false}},{lt(cid,B(8,1,0.55))}+k*0.12);}});"
              f"tl.set('#o8p',{{opacity:1}},{lt(cid,B(8,1,0.5))});")
    js.append(f"tl.fromTo('#o8d',{{opacity:0}},{{opacity:1,duration:0.4,immediateRender:false}},{lt(cid,B(8,2))});")
    return cid, dur, scene_file(cid, dur, css8, body, "".join(js))

# ============================ CAPTIONS ============================
def _caption_chunks(words, max_w=8):
    """Cắt câu thành cụm NGẮN 1 dòng: ngắt ở dấu câu khi đã >=4 từ, trần max_w từ."""
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        brk = len(cur) >= 4 and w["text"].rstrip().endswith((",", ";", ":", "—", "–"))
        if brk or len(cur) >= max_w:
            chunks.append(cur); cur = []
    if cur:
        if chunks and len(cur) <= 2:
            chunks[-1].extend(cur)   # mẩu 1-2 từ cuối gộp vào cụm trước
        else:
            chunks.append(cur)
    return chunks


def captions():
    groups, js, gi = [], [], 0
    flat = [ch for c in SUBS["captions"] for ch in _caption_chunks(c["words"])]
    for gi, ch in enumerate(flat):
        s = round(ch[0]["start"] + OFF, 3)
        e = round(max(ch[-1].get("end", ch[-1]["start"] + 0.3), ch[-1]["start"] + 0.1) + OFF, 3)
        nxt = flat[gi + 1][0]["start"] + OFF if gi + 1 < len(flat) else e + 0.6
        e2 = round(min(e + 0.3, nxt - 0.02), 3)
        ws = "".join(f'<span class="cw" id="cw{gi}_{wi}">{esc(w["text"])}</span> ' for wi, w in enumerate(ch))
        groups.append(f'<div class="cg" id="cg{gi}"><div class="cpill">{ws}</div></div>')
        js.append(f"tl.set('#cg{gi}',{{opacity:1,visibility:'visible'}},{s});"
                  f"tl.fromTo('#cg{gi} .cpill',{{y:18,opacity:0}},{{y:0,opacity:1,duration:0.14,ease:'power3.out',immediateRender:false}},{s});")
        for wi, w in enumerate(ch):
            ws_ = round(w["start"] + OFF, 3)
            we_ = round(max(w.get("end", w["start"] + 0.2), w["start"] + 0.1) + OFF, 3)
            js.append(f"tl.fromTo('#cw{gi}_{wi}',{{color:'#8e99ab'}},{{color:'#fbbf24',duration:0.05,immediateRender:false}},{ws_});"
                      f"tl.to('#cw{gi}_{wi}',{{color:'#ffffff',duration:0.1}},{we_});")
        js.append(f"tl.to('#cg{gi} .cpill',{{opacity:0,duration:0.1}},{e2-0.1});tl.set('#cg{gi}',{{opacity:0,visibility:'hidden'}},{e2});")
    css = """
.cg{position:absolute;left:0;right:0;top:1500px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;white-space:nowrap;max-width:1000px;padding:12px 30px;border-radius:99px;background:rgba(15,23,42,.94);border:1.5px solid rgba(255,255,255,.18);box-shadow:0 12px 35px rgba(0,0,0,.65),0 0 20px rgba(56,213,231,.15);font-size:36px;font-weight:800;line-height:1.35;color:#8e99ab;}
.cw{display:inline-block;padding:0 4px;}
"""
    return "captions", TOTAL, scene_file("captions", TOTAL, css, "\n".join(groups), "\n".join(js))


# ============================ ROOT ============================
CHAPTER_COLORS = ["#f59e0b", "#f43f5e", "#22d3ee", "#8b5cf6", "#8b5cf6",
                  "#8b5cf6", "#eab308", "#10b981", "#38bdf8"]


def root(scene_meta):
    segs = "".join(f'<span class="seg"><i id="sg{i}" style="background:{CHAPTER_COLORS[i % 9]};"></i></span>'
                   for i in range(9))
    seg_js = "".join(
        f"tl.fromTo('#sg{i}',{{scaleX:0}},{{scaleX:1,duration:{max(round(e - st, 3), 0.1)},ease:'none',immediateRender:false}},{st});"
        for i, (cid, st, e) in enumerate((c, st_, st_ + d) for c, st_, d in scene_meta if c != "captions"))
    hosts = "\n".join(
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{st}" data-duration="{dur}" '
        f'data-track-index="{i+2}" data-track-kind="{"captions" if cid=="captions" else "graphics"}" data-width="{W}" data-height="{H}" style="z-index:{50 if cid=="captions" else 10+i};"></div>'
        for i, (cid, st, dur) in enumerate(scene_meta))
    bgm_vol = D.get("bgm_volume", 0.16)
    return f"""<!doctype html><html lang="vi"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width={W}, height={H}"/>
<script src="assets/js/gsap.min.js"></script>
<style>{FONT_CSS}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#0e111a;}}
#root{{position:relative;width:100%;height:100%;font-family:'BVP','Segoe UI',sans-serif;color:#e7e9f0;}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 25%,#141926 0%,#0e111a 60%,#090b12 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:170px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand .n{{font-size:28px;font-weight:800;letter-spacing:1px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:28px;color:#8b5cf6;}}
.prog{{position:absolute;left:60px;right:60px;top:226px;height:7px;display:flex;gap:6px;z-index:60;}}
.prog .seg{{flex:1;height:100%;border-radius:4px;background:rgba(255,255,255,.08);overflow:hidden;}}
.prog .seg i{{display:block;height:100%;width:100%;transform:scaleX(0);transform-origin:left center;}}
.rootdisc{{position:absolute;left:60px;right:60px;top:1760px;text-align:center;font-size:21px;color:#6e7891;z-index:60;}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="brand" id="brand"><span class="n">{esc(D.get('handle','@kenvinzone'))} · THƯ VIỆN TRADING</span></div>
  <div class="prog" id="prog">{segs}</div>
  <div class="rootdisc">Dữ liệu minh hoạ — không phải giá thực · Nội dung giáo dục, không phải khuyến nghị đầu tư</div>
{hosts}
  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{OFF}" data-volume="1" data-track-index="30"></audio>
  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{bgm_vol}" data-fade-out="2" data-track-index="31"></audio>
</div>
<script>(function(){{
const tl=gsap.timeline({{paused:true}});
{seg_js}
gsap.set('#brand,#prog',{{opacity:0}});
tl.fromTo('#brand,#prog',{{opacity:0}},{{opacity:1,duration:0.4,immediateRender:false}},0.5);
window.__timelines["main"]=tl;
}})();</script></body></html>"""


def main():
    comps = ROOT / "compositions"; comps.mkdir(exist_ok=True)
    meta = []
    for fn in (s_hook, s_trap, s_two, s_vpq, s_anatomy, s_shark, s_howto, s_entry, s_outro):
        cid, dur, txt = fn(); (comps / f"{cid}.html").write_text(txt, encoding="utf-8"); meta.append((cid, round(START[cid], 3), dur))
    if D.get("captions", True):
        cid, dur, txt = captions(); (comps / "captions.html").write_text(txt, encoding="utf-8"); meta.append(("captions", 0, dur))
    (ROOT / "index.html").write_text(root(meta), encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", [m[0] for m in meta])


if __name__ == "__main__":
    main()
