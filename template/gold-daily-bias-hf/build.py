#!/usr/bin/env python3
"""KenvinZone - Gold Daily Bias -> HyperFrames composition generator.

Usage:  python3 build.py data.json subtitle-word-timing.json
Writes index.html + compositions/*.html in this folder.
All visible numbers come from data.json; all timings come from the
voiceover word timestamps (subtitle-word-timing.json) so the picture
lands exactly on the spoken word.
"""
import json, sys, math, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))

SFX_LEN = {'whoosh.mp3': 0.62, 'tick.mp3': 0.13, 'impact.mp3': 0.73}
OFF = float(DATA.get("audio_offset", 1.0))      # hook pre-roll before voice starts
OUTRO = float(DATA.get("outro_hold", 3.6))
W, H = 1080, 1920
WORDS = [(w["text"], w["start"], w["end"]) for c in SUBS["captions"] for w in c["words"]]
VO_LEN = float(SUBS.get("duration", WORDS[-1][2]))
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
SLIDES = SUBS["slides"]
if len(SLIDES) != 6:
    raise SystemExit(f"Template Bias Vang can dung 6 dong script (dang co {len(SLIDES)}).")


def norm(s):
    return s.lower().strip(".,:;!?\"'()")


def anchor(phrase, after=0.0, fallback=None):
    """Absolute VIDEO time where `phrase` is spoken (first match after `after`, audio time)."""
    toks = [norm(t) for t in phrase.split()]
    for i in range(len(WORDS) - len(toks) + 1):
        if WORDS[i][1] < after:
            continue
        if all(norm(WORDS[i + j][0]).startswith(t) for j, t in enumerate(toks)):
            return round(WORDS[i][1] + OFF, 3)
    if fallback is None:
        raise SystemExit(f"anchor not found: {phrase!r}")
    return None if fallback < 0 else round(fallback + OFF, 3)


def slide_start(i):
    return round(SLIDES[i]["start"] + OFF, 3) if i > 0 else 0.0


# ---------------------------------------------------------------- scene slots
S = [slide_start(i) for i in range(6)]
# scene 0 = slide0, scene1 = slides 1+2 (tug of war), scene2 = slide3 (gamma),
# scene3 = slide4 (scenarios), scene4 = slide5 (action + CTA)
SCENES = [
    ("hook", 0.0, S[1]),
    ("forces", S[1], S[3]),
    ("gamma", S[3], S[4]),
    ("scen", S[4], S[5]),
    ("cta", S[5], TOTAL),
]

A = DATA.get("anchors", {})   # phrase per beat (from today's script)

# Where each beat sits inside its voiceover line when the phrase is not found
# (script reworded, or whisper misheard a number): (line index, fraction of that line)
DEFAULT_POS = {
    "score": (0, 0.45), "trend": (0, 0.65), "neutral": (0, 0.90),
    "usd": (1, 0.25), "flows": (1, 0.60), "gold_spec": (1, 0.88),
    "counterweight": (2, 0.0), "rates": (2, 0.12), "m2": (2, 0.30), "risk": (2, 0.48), "stress": (2, 0.69),
    "gex": (3, 0.09), "gex_value": (3, 0.11), "spot": (3, 0.16), "spot_xau": (3, 0.25), "flip": (3, 0.37),
    "put": (3, 0.58), "call": (3, 0.74), "vol": (3, 0.88),
    "s_base": (4, 0.06), "s_down": (4, 0.27), "s_up": (4, 0.60),
    "act_neutral": (5, 0.10), "act_buy": (5, 0.31), "aurora": (5, 0.77), "follow": (5, 0.82),
}
_LINE_START = {i: (0.0 if i == 0 else float(SLIDES[i]["start"])) for i in range(len(SLIDES))}
_CACHE = {}


def abs_at(key):
    """Absolute video time of a beat: spoken phrase if found, else its default position in the line."""
    if key in _CACHE:
        return _CACHE[key]
    line, frac = DEFAULT_POS[key]
    line_start = float(SLIDES[line]["start"])
    fallback_audio = line_start + frac * float(SLIDES[line]["duration"])
    phrase = A.get(key)
    t = None
    if phrase:
        t = anchor(phrase, after=max(0.0, line_start - 0.5), fallback=-1)
        # accept only a match inside its own line
        if t is not None and not (line_start - 0.5 <= t - OFF <= line_start + float(SLIDES[line]["duration"]) + 0.5):
            t = None
    if t is None or t < 0:
        print(f"  [anchor] '{key}' ({phrase!r}) not heard -> default position", file=sys.stderr)
        t = round(fallback_audio + OFF, 3)
    _CACHE[key] = t
    return t


def at(key, scene_start, *_, **__):
    return round(abs_at(key) - scene_start, 3)


FONT_CSS = """
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-vietnamese-500-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-latin-500-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-vietnamese-700-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-latin-700-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-vietnamese-800-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-vietnamese-900-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-latin-900-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-latin-700-normal.woff2') format('woff2');}
"""

BASE_CSS = """
#root{position:absolute;inset:0;font-family:'BVP',sans-serif;color:#f8fafc;}
.mono{font-family:'JBM',monospace;font-variant-numeric:tabular-nums;}
.ttl{position:absolute;left:70px;right:70px;top:250px;font-weight:900;font-size:58px;line-height:1.12;letter-spacing:-0.5px;text-transform:uppercase;}
.sub{position:absolute;left:70px;right:70px;top:330px;font-weight:600;font-size:28px;color:#94a3b8;}
.gold{background:linear-gradient(180deg,#fff 0%,#fde68a 45%,#f59e0b 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def scene_file(cid, dur, css, body, js):
    return f"""<template>
<style>{FONT_CSS}{BASE_CSS}{css}</style>
<div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-duration="{dur}">
{body}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
const Q = (s) => document.querySelector('[data-composition-id="{cid}"] ' + s);
const QA = (s) => document.querySelectorAll('[data-composition-id="{cid}"] ' + s);
function counter(sel, from, to, at, dur, dec, prefix, suffix){{
  const el = Q(sel); const o = {{v: from}};
  const f = (v) => (prefix||'') + (v<0?'-':(prefix==='+'?'':'')) + Math.abs(v).toLocaleString('en-US',{{minimumFractionDigits:dec,maximumFractionDigits:dec}}) + (suffix||'');
  el.textContent = f(from);
  tl.fromTo(o, {{v: from}}, {{v: to, duration: dur, ease: 'power3.out', immediateRender:false, onUpdate(){{ el.textContent = f(o.v); }} }}, at);
}}
{js}
window.__timelines["{cid}"] = tl;
}})();
</script>
</template>
"""


D = DATA

# ================================================================ SCENE 0 HOOK
def scene_hook():
    st, en = SCENES[0][1], SCENES[0][2]
    dur = round(en - st, 3)
    t_score = at("score", st)
    t_trend = at("trend", st)
    t_neutral = at("neutral", st)
    sc = D["score"]
    pos = (sc + 100) / 200 * 100
    hist = D["history"]                     # [[label, value], ...] oldest -> today
    up = len(hist) < 2 or hist[-1][1] >= hist[-2][1]
    TCOL = "#4ade80" if up else "#f87171"       # today's colour: green when the score improved
    # mini trend geometry
    xs = [190, 540, 890]
    vals = [h[1] for h in hist]
    lo, hi = min(vals) - 1.0, max(vals) + 1.0
    ys = [1095 - (v - lo) / (hi - lo) * 0 for v in vals]  # placeholder
    ymap = lambda v: 1012 + (hi - v) / (hi - lo) * 70
    pts = [(x, ymap(v)) for x, v in zip(xs, vals)]
    path = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    dots = "".join(
        f'<g class="hk-pt" id="hk-pt{i}"><circle cx="{x:.0f}" cy="{y:.0f}" r="{12 if i==2 else 9}" fill="{TCOL if i==2 else "#fbbf24"}"/>'
        f'<text x="{x:.0f}" y="{y-26:.0f}" text-anchor="middle" class="mono" font-size="30" font-weight="800" fill="{TCOL if i==2 else "#fde68a"}">{v:+.2f}</text>'
        f'<text x="{x:.0f}" y="{y+52:.0f}" text-anchor="middle" font-size="28" font-weight="700" fill="#94a3b8">{esc(l)}</text></g>'
        for i, ((l, v), (x, y)) in enumerate(zip(hist, pts)))
    css = f"""
.hk-eyebrow{{position:absolute;top:250px;left:0;right:0;display:flex;justify-content:center;}}
.hk-eyebrow span{{background:linear-gradient(135deg,#38bdf8,#0284c7);color:#fff;font-weight:900;font-size:28px;letter-spacing:4px;padding:14px 34px;border-radius:99px;box-shadow:0 10px 40px rgba(56,189,248,.45);}}
.hk-bars{{position:absolute;top:322px;left:0;right:0;display:flex;justify-content:center;}}
.hk-bars img{{width:220px;filter:drop-shadow(0 18px 40px rgba(245,158,11,.55));}}
.hk-title{{position:absolute;top:515px;left:60px;right:60px;text-align:center;}}
.hk-plate{{display:inline-block;padding:22px 30px;border-radius:24px;border:2px solid rgba(251,191,36,.35);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(251,191,36,.05));}}
.hk-plate h1{{font-size:66px;font-weight:900;line-height:1.18;letter-spacing:-1px;padding-top:.12em;}}
.hk-date{{position:absolute;top:728px;left:0;right:0;text-align:center;}}
.hk-date span{{font-family:'JBM';font-weight:800;font-size:28px;color:#7dd3fc;border:2px solid rgba(56,189,248,.45);padding:9px 26px;border-radius:99px;background:rgba(56,189,248,.08);letter-spacing:2px;}}
.hk-score{{position:absolute;top:788px;left:0;right:0;text-align:center;}}
.hk-lbl{{font-size:28px;font-weight:800;letter-spacing:4px;color:#94a3b8;}}
.hk-val{{font-family:'JBM';font-weight:800;font-size:112px;line-height:1.05;color:#fbbf24;font-variant-numeric:tabular-nums;}}
.hk-val small{{font-size:34px;color:#64748b;}}
.hk-bar{{position:relative;margin:4px auto 0;width:760px;height:16px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.hk-band{{position:absolute;top:-10px;bottom:-10px;left:42.5%;width:15%;border:2px solid rgba(255,255,255,.0);border-radius:10px;}}
.hk-mk{{position:absolute;top:-14px;width:10px;height:44px;margin-left:-5px;border-radius:5px;background:#fff;box-shadow:0 0 18px #fff;left:{pos:.2f}%;}}
.hk-trend{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}
.hk-tag{{position:absolute;top:1138px;left:0;right:0;text-align:center;font-size:30px;font-weight:800;color:{"#86efac" if up else "#fca5a5"};}}
"""
    body = f"""
<div class="hk-stage" id="hk-stage">
  <div class="hk-eyebrow"><span>⚡ DAILY FLASH BIAS · VÀNG</span></div>
  <div class="hk-bars"><img src="assets/img/gold-bars-3d-3bars.png" alt=""/></div>
  <div class="hk-title"><div class="hk-plate"><h1 class="gold">{D['title_html']}</h1></div></div>
  <div class="hk-date"><span>PHIÊN NGÀY {esc(D['date'])}</span></div>
  <div class="hk-score" id="hk-score">
    <div class="hk-lbl">COMPOSITE BIAS · <span id="hk-regime">{esc(D['regime'])}</span></div>
    <div class="hk-val"><span id="hk-num">{sc:+.2f}</span><small> / 100</small></div>
    <div class="hk-bar"><div class="hk-band" id="hk-band"></div><div class="hk-mk" id="hk-mk"></div></div>
  </div>
  <svg class="hk-trend" id="hk-trend" viewBox="0 0 {W} {H}">
    <path id="hk-line" d="{path}" fill="none" stroke="url(#hkg)" stroke-width="6" stroke-linecap="round" stroke-dasharray="1000" stroke-dashoffset="1000"/>
    <defs><linearGradient id="hkg" x1="0" x2="1"><stop offset="0" stop-color="#fbbf24"/><stop offset="1" stop-color="{TCOL}"/></linearGradient></defs>
    {dots}
  </svg>
  <div class="hk-tag" id="hk-tag">{esc(D['trend_tag'])}</div>
</div>"""
    js = f"""
gsap.set('#hk-stage .hk-pt, #hk-tag', {{opacity:0}});
// score is on screen from frame 0 (thumbnail = hook). Punch on the spoken number.
tl.fromTo('#hk-num', {{scale:1}}, {{scale:1.14, duration:0.18, ease:'power3.out', immediateRender:false}}, {t_score});
tl.to('#hk-num', {{scale:1, color:'{TCOL}', duration:0.5, ease:'expo.out'}}, {t_score + 0.18});
tl.fromTo('#hk-mk', {{x:0}}, {{x:{14 if up else -14}, duration:0.25, ease:'power2.out', yoyo:true, repeat:3, immediateRender:false}}, {t_score});
// 3 sessions in a row: the line draws through the points
tl.fromTo('#hk-line', {{strokeDashoffset:1000}}, {{strokeDashoffset:0, duration:1.4, ease:'power2.inOut', immediateRender:false}}, {t_trend});
QA('.hk-pt').forEach((p,i)=>tl.fromTo(p, {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.35, ease:'back.out(1.6)', immediateRender:false}}, {t_trend} + i*0.45));
tl.fromTo('#hk-tag', {{opacity:0, filter:'blur(8px)'}}, {{opacity:1, filter:'blur(0px)', duration:0.25, ease:'power3.out', immediateRender:false}}, {t_trend} + 1.4);
tl.fromTo('#hk-band', {{borderColor:'rgba(255,255,255,0)', backgroundColor:'rgba(255,255,255,0)'}}, {{borderColor:'rgba(253,224,71,.95)', backgroundColor:'rgba(253,224,71,.18)', duration:0.4, ease:'power2.out', immediateRender:false}}, {t_neutral});
tl.fromTo('#hk-regime', {{color:'#94a3b8'}}, {{color:'#fde047', duration:0.3, immediateRender:false}}, {t_neutral});
// exit: blur swap
tl.to('#hk-stage', {{opacity:0, filter:'blur(10px)', scale:0.96, duration:0.28, ease:'power3.in'}}, {dur - 0.3});
"""
    return "hook", dur, scene_file("hook", dur, css, body, js)


# ================================================================ SCENE 1 FORCES
def scene_forces():
    st, en = SCENES[1][1], SCENES[1][2]
    dur = round(en - st, 3)
    rows = D["forces"]          # [{label, value, color, key}]
    maxabs = max(abs(r["value"]) for r in rows)
    half = 400
    cx = 540
    top0 = 420
    rh = 98
    body_rows = []
    js_rows = []
    for i, r in enumerate(rows):
        y = top0 + i * rh + (40 if r["value"] > 0 else 0)
        w = abs(r["value"]) / maxabs * half
        neg = r["value"] < 0
        x = cx - w if neg else cx
        lbl_side = f"left:{cx + 28}px;text-align:left;" if neg else f"right:{W - cx + 28}px;text-align:right;"
        body_rows.append(
            f'<div class="fr-row" id="fr-row{i}" style="top:{y}px;">'
            f'<div class="fr-bar" id="fr-bar{i}" style="left:{x:.0f}px;width:{w:.0f}px;background:{r["color"]};box-shadow:0 0 28px {r["color"]}66;transform-origin:{"right" if neg else "left"} center;"></div>'
            f'<div class="fr-lbl" style="{lbl_side}"><div class="fr-name">{esc(r["label"])}</div>'
            f'<div class="fr-val mono" id="fr-val{i}" style="color:{r["color"]};">{r["value"]:+.2f}</div></div></div>')
        t = at(r["key"], st, fallback_abs=None)
        js_rows.append(
            f"tl.fromTo('#fr-row{i}', {{opacity:0}}, {{opacity:1, duration:0.2, immediateRender:false}}, {t - 0.15});"
            f"tl.fromTo('#fr-bar{i}', {{scaleX:0}}, {{scaleX:1, duration:0.9, ease:'expo.out', immediateRender:false}}, {t});"
            f"counter('#fr-val{i}', 0, {r['value']}, {t}, 0.9, 2, '{'+' if r['value']>0 else ''}', '');")
    t_counter = at("counterweight", st)
    t_stress = at("stress", st)
    big = max(range(len(rows)), key=lambda i: abs(rows[i]["value"]))
    css = """
.fr-axis{position:absolute;left:539px;top:400px;width:3px;height:660px;background:linear-gradient(180deg,transparent,rgba(255,255,255,.45) 10%,rgba(255,255,255,.45) 90%,transparent);transform-origin:center top;}
.fr-side{position:absolute;top:378px;font-size:28px;font-weight:800;letter-spacing:3px;}
.fr-row{position:absolute;left:0;right:0;height:96px;}
.fr-bar{position:absolute;top:30px;height:44px;border-radius:10px;}
.fr-lbl{position:absolute;top:0;width:470px;}
.fr-name{font-size:28px;font-weight:700;color:#cbd5e1;}
.fr-val{font-size:44px;font-weight:800;line-height:1.1;}
.fr-big{position:absolute;font-size:28px;font-weight:900;letter-spacing:2px;color:#fff;background:#ef4444;padding:6px 14px;border-radius:8px;}
.fr-card{position:absolute;left:70px;right:70px;top:1062px;padding:22px 28px;border-radius:20px;border:2px solid rgba(245,158,11,.55);background:rgba(245,158,11,.10);font-size:29px;font-weight:700;line-height:1.35;color:#fde68a;}
.fr-card b{color:#fff;}
.fr-mid{position:absolute;left:0;right:0;top:770px;text-align:center;font-size:26px;font-weight:800;letter-spacing:4px;color:#86efac;}
"""
    stress = D["stress"]
    body = f"""
<div id="fr-stage">
  <div class="ttl" id="fr-ttl"><span class="gold">Cuộc kéo co</span> định lượng</div>
  <div class="sub" id="fr-sub">Đóng góp vào điểm Bias tổng · đơn vị: điểm</div>
  <div class="fr-side" style="left:70px;color:#f87171;" id="fr-sl">◀ KÉO GIÁ XUỐNG</div>
  <div class="fr-side" style="right:70px;color:#4ade80;" id="fr-sr">ĐỠ GIÁ ▶</div>
  <div class="fr-axis" id="fr-axis"></div>
  {''.join(body_rows)}
  <div class="fr-big" id="fr-big" style="{f"left:{cx - half}px" if rows[big]["value"] < 0 else f"right:{W - cx - half}px;background:#16a34a"};top:{top0 + big*rh + (80 if rows[big]["value"] < 0 else 120)}px;">{"LỰC KÉO LỚN NHẤT" if rows[big]["value"] < 0 else "LỰC ĐỠ LỚN NHẤT"}</div>
  <div class="fr-card" id="fr-card">{D.get("stress_note_html") or f"⚠ Tín dụng căng thẳng ({esc(stress)}) nhưng vàng <b>chưa hút được</b> dòng tiền trú ẩn"}</div>
</div>"""
    js = f"""
gsap.set('#fr-stage .fr-row, #fr-card, #fr-big, #fr-sr', {{opacity:0}});
tl.fromTo('#fr-ttl', {{opacity:0, filter:'blur(10px)'}}, {{opacity:1, filter:'blur(0px)', duration:0.3, ease:'power3.out'}}, 0.05);
tl.fromTo('#fr-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.25);
tl.fromTo('#fr-axis', {{scaleY:0}}, {{scaleY:1, duration:0.8, ease:'power2.inOut'}}, 0.3);
tl.fromTo('#fr-sl', {{opacity:0, x:30}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out'}}, 0.6);
{''.join(js_rows)}
tl.fromTo('#fr-big', {{opacity:0, scale:0.6}}, {{opacity:1, scale:1, duration:0.35, ease:'back.out(2)', immediateRender:false}}, {at(rows[big]['key'], st) + 0.7});
tl.fromTo('#fr-sr', {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_counter});
tl.fromTo('#fr-card', {{opacity:0, y:40, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.45, ease:'expo.out', immediateRender:false}}, {t_stress});
tl.to('#fr-stage', {{opacity:0, y:-120, filter:'blur(14px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "forces", dur, scene_file("forces", dur, css, body, js)


# ================================================================ SCENE 2 GAMMA
def scene_gamma():
    st, en = SCENES[2][1], SCENES[2][2]
    dur = round(en - st, 3)
    g = D["gamma"]
    lo, hi = g["axis"]
    ytop, ybot = 520, 1110
    ymap = lambda p: ybot - (p - lo) / (hi - lo) * (ybot - ytop)
    x0, x1 = 150, 1000
    if g["spot"].get("gld") in (None, "") and g["spot"].get("xau"):
        lvls = sorted(((g[k]["xau"], g[k]["gld"]) for k in ("put", "flip", "call")))
        sx = g["spot"]["xau"]
        a, b = (lvls[0], lvls[1]) if sx <= lvls[1][0] else (lvls[1], lvls[2])
        g["spot"]["_pos"] = a[1] + (sx - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    else:
        g["spot"]["_pos"] = g["spot"]["gld"]
    lv = {k: ymap(g[k]["gld"]) for k in ("call", "flip", "put")}
    lv["spot"] = ymap(g["spot"]["_pos"])
    neg_gamma = g["net_gex_m"] < 0
    t_gex = at("gex", st)
    t_gexv = at("gex_value", st)
    t_spot = at("spot", st)
    t_spotx = at("spot_xau", st)
    t_flip = at("flip", st)
    t_put = at("put", st)
    t_call = at("call", st)
    t_vol = at("vol", st)
    # amplified volatility path (deterministic): oscillation around spot, growing amplitude
    pts = []
    n = 90
    for i in range(n + 1):
        f = i / n
        x = 330 + f * 640
        amp = 10 + 95 * f ** 1.4
        y = lv["spot"] + math.sin(f * 21.0) * amp * (0.75 + 0.25 * math.sin(f * 47.0))
        pts.append(f"{x:.1f},{y:.1f}")
    vpath = "M" + " L".join(pts)
    ticks = "".join(
        f'<line x1="{x0-14}" x2="{x0}" y1="{ymap(p):.0f}" y2="{ymap(p):.0f}" stroke="rgba(255,255,255,.35)" stroke-width="2"/>'
        f'<text x="{x0-22}" y="{ymap(p)+9:.0f}" text-anchor="end" class="mono" font-size="28" font-weight="700" fill="#64748b">{p}</text>'
        for p in range(int(lo) + (5 - int(lo) % 5) % 5, int(hi) + 1, 5))

    bands = [(lv["call"] - 62, lv["call"] - 10), (lv["flip"] - 62, lv["flip"] - 10), (lv["put"] + 10, lv["put"] + 62)]
    lab_h = 92 if g["spot"].get("gld") not in (None, "") else 84
    def _free(y):
        return all(y + lab_h < a or y > b for a, b in bands) and y > ytop - 40 and y + lab_h < ybot + 30
    spot_lab_y = next((y for y in (lv["spot"] + 28, lv["spot"] - lab_h - 26, lv["flip"] + 16, lv["call"] + 16, lv["put"] - lab_h - 16) if _free(y)), lv["spot"] + 28)

    def level(key, color, name, above):
        y = lv[key]
        lab_y = y - 58 if above else y + 14
        gld = g[key]["gld"]
        xau = g[key]["xau"]
        return (f'<div class="gm-lvl" id="gm-{key}" style="top:{y-2:.0f}px;"><div class="gm-line" id="gm-{key}-ln" style="background:{color};box-shadow:0 0 18px {color};"></div></div>'
                f'<div class="gm-lab" id="gm-{key}-lab" style="top:{lab_y:.0f}px;color:{color};"><b>{esc(name)}</b> '
                f'<span class="mono">GLD {gld:g}</span> <span class="gm-x mono">≈ {xau:,.0f} XAUUSD</span></div>')

    css = f"""
.gm-badge{{position:absolute;top:340px;left:70px;right:70px;height:140px;border-radius:24px;border:3px solid #ef4444;background:linear-gradient(135deg,rgba(239,68,68,.25),rgba(127,29,29,.35));display:flex;align-items:center;justify-content:space-between;padding:0 34px;box-shadow:0 0 60px rgba(239,68,68,.35);}}
.gm-badge .k{{font-size:58px;font-weight:900;letter-spacing:1px;color:#fff;}}
.gm-badge .v{{font-family:'JBM';font-weight:800;font-size:52px;color:#fca5a5;text-align:right;}}
.gm-badge .v small{{display:block;font-family:'BVP';font-size:28px;font-weight:700;color:#fecaca;letter-spacing:2px;}}
.gm-axis{{position:absolute;left:{x0}px;top:{ytop-20}px;width:3px;height:{ybot-ytop+40}px;background:rgba(255,255,255,.35);transform-origin:center bottom;}}
.gm-svg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}
.gm-lvl{{position:absolute;left:{x0}px;width:{x1-x0}px;height:4px;}}
.gm-line{{position:absolute;inset:0;border-radius:2px;transform-origin:left center;}}
.gm-lab{{position:absolute;left:{x0+24}px;right:60px;font-size:28px;line-height:1.5;white-space:nowrap;}}
.gm-lab b{{font-weight:900;letter-spacing:1px;margin-right:10px;}}
.gm-lab .mono{{font-weight:800;color:#fff;}}
.gm-x{{color:#fde68a !important;margin-left:8px;}}
.gm-zone{{position:absolute;left:{x0}px;width:{x1-x0}px;}}
.gm-spot{{position:absolute;left:{x0+770}px;top:{lv['spot']-22:.0f}px;width:44px;height:44px;margin-left:-22px;border-radius:50%;background:#fff;box-shadow:0 0 0 8px rgba(255,255,255,.18),0 0 40px #fff;}}
.gm-spot-lab{{position:absolute;right:60px;top:{spot_lab_y:.0f}px;text-align:right;font-size:28px;font-weight:800;line-height:1.3;}}
.gm-spot-lab .p{{font-family:'JBM';font-size:40px;color:#fff;}}
.gm-spot-lab .x{{font-family:'JBM';font-size:34px;color:#fde68a;}}
.gm-vtag{{position:absolute;left:70px;right:70px;top:1150px;text-align:center;font-size:32px;font-weight:900;color:#fca5a5;letter-spacing:1px;}}
"""
    zone_neg = f'<div class="gm-zone" id="gm-zneg" style="top:{lv["flip"]:.0f}px;height:{lv["put"]-lv["flip"]:.0f}px;background:linear-gradient(180deg,rgba(239,68,68,.22),rgba(239,68,68,.05));"><span style="position:absolute;left:24px;bottom:14px;font-size:28px;font-weight:900;letter-spacing:3px;color:#f87171;">VÙNG GAMMA ÂM</span></div>'
    zone_pos = f'<div class="gm-zone" id="gm-zpos" style="top:{lv["call"]:.0f}px;height:{lv["flip"]-lv["call"]:.0f}px;background:linear-gradient(0deg,rgba(34,197,94,.16),rgba(34,197,94,.03));"></div>'
    body = f"""
<div id="gm-stage">
  <div class="ttl" id="gm-ttl">Cấu trúc <span class="gold">Gamma</span></div>
  <div class="gm-badge" id="gm-badge"><div class="k">{"GAMMA ÂM" if neg_gamma else "GAMMA DƯƠNG"}</div><div class="v"><small>NET GEX</small><span id="gm-gex">$0.0M</span></div></div>
  <div class="gm-axis" id="gm-axis"></div>
  <svg class="gm-svg" viewBox="0 0 {W} {H}"><g id="gm-ticks">{ticks}</g>
    <path id="gm-vpath" d="{vpath}" fill="none" stroke="#fca5a5" stroke-width="5" stroke-linejoin="round" stroke-dasharray="4000" stroke-dashoffset="4000" opacity="0.95"/></svg>
  {zone_pos}{zone_neg}
  {level('call', '#4ade80', 'CALL WALL', True)}
  {level('flip', '#fbbf24', 'GAMMA FLIP', True)}
  {level('put', '#f87171', 'PUT WALL', False)}
  <div class="gm-spot" id="gm-spot"></div>
  <div class="gm-spot-lab" id="gm-spot-lab">GIÁ HIỆN TẠI<br/>{('<span class="p">GLD ' + format(g['spot']['gld'], 'g') + '</span><br/>') if g['spot'].get('gld') not in (None, '') else ''}<span class="x" id="gm-spotx">{'≈ ' if g['spot'].get('gld') not in (None, '') else ''}{g['spot']['xau']:,.1f} XAUUSD</span></div>
  <div class="gm-vtag" id="gm-vtag">Gamma âm → biến động bị <span style="color:#fff;">khuếch đại</span></div>
</div>"""
    gex = g["net_gex_m"]
    js = f"""
gsap.set('#gm-badge, .gm-lvl, .gm-lab, .gm-zone, #gm-spot, #gm-spot-lab, #gm-spotx, #gm-vtag', {{opacity:0}});
tl.fromTo('#gm-ttl', {{opacity:0, y:-60, filter:'blur(12px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.45, ease:'expo.out'}}, 0.05);
tl.fromTo('#gm-axis', {{scaleY:0}}, {{scaleY:1, duration:0.9, ease:'power2.inOut'}}, 0.35);
tl.fromTo('#gm-ticks', {{opacity:0}}, {{opacity:1, duration:0.6}}, 0.8);
tl.fromTo('#gm-badge', {{opacity:0, scale:1.35, filter:'blur(14px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.32, ease:'power4.out', immediateRender:false}}, {t_gex});
counter('#gm-gex', 0, {gex}, {t_gexv}, 1.2, 1, '$', 'M');
// spot arrives from above and settles on its price
tl.fromTo('#gm-spot', {{opacity:0, y:-380}}, {{opacity:1, y:0, duration:0.9, ease:'expo.out', immediateRender:false}}, {t_spot});
tl.fromTo('#gm-spot-lab', {{opacity:0, x:40}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_spot + 0.5});
tl.fromTo('#gm-spotx', {{opacity:0, filter:'blur(8px)'}}, {{opacity:1, filter:'blur(0px)', duration:0.3, ease:'power3.out', immediateRender:false}}, {t_spotx});
function lvl(k, t){{
  tl.set('#gm-'+k, {{opacity:1}}, t);
  tl.fromTo('#gm-'+k+'-ln', {{scaleX:0}}, {{scaleX:1, duration:0.7, ease:'expo.out', immediateRender:false}}, t);
  tl.fromTo('#gm-'+k+'-lab', {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, t + 0.25);
}}
lvl('flip', {t_flip});
tl.fromTo('#gm-zneg', {{opacity:0}}, {{opacity:1, duration:0.6, immediateRender:false}}, {t_flip + 0.7});
tl.fromTo('#gm-zpos', {{opacity:0}}, {{opacity:1, duration:0.6, immediateRender:false}}, {t_flip + 0.9});
lvl('put', {t_put});
lvl('call', {t_call});
tl.fromTo('#gm-vpath', {{strokeDashoffset:4000}}, {{strokeDashoffset:0, duration:3.2, ease:'power1.inOut', immediateRender:false}}, {t_vol});
tl.fromTo('#gm-vtag', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_vol + 0.4});
tl.to('#gm-stage', {{opacity:0, filter:'blur(12px)', duration:0.28, ease:'power3.in'}}, {dur - 0.3});
"""
    return "gamma", dur, scene_file("gamma", dur, css, body, js)


# ================================================================ SCENE 3 SCENARIOS
def scene_scen():
    st, en = SCENES[3][1], SCENES[3][2]
    dur = round(en - st, 3)
    cards = []
    js = []
    for i, s in enumerate(D["scenarios"]):
        y = 430 + i * 245
        t = at(s["key"], st)
        cards.append(
            f'<div class="sc-card" id="sc-c{i}" style="top:{y}px;border-color:{s["color"]}88;background:linear-gradient(135deg,{s["color"]}22,rgba(15,23,42,.6));">'
            f'<div class="sc-pct mono" id="sc-p{i}" style="color:{s["color"]};">0%</div>'
            f'<div class="sc-txt"><div class="sc-name" style="color:{s["color"]};">{esc(s["name"])}</div><div class="sc-desc">{s["desc"]}</div></div>'
            f'<div class="sc-track"><div class="sc-fill" id="sc-f{i}" style="width:{s["pct"]}%;background:{s["color"]};"></div></div></div>')
        js.append(
            f"tl.fromTo('#sc-c{i}', {{opacity:0, x:{-120 if i%2==0 else 120}}}, {{opacity:1, x:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {t - 0.25});"
            f"counter('#sc-p{i}', 0, {s['pct']}, {t}, 1.2, 0, '', '%');"
            f"tl.fromTo('#sc-f{i}', {{scaleX:0}}, {{scaleX:1, duration:1.2, ease:'power3.out', immediateRender:false}}, {t});")
    css = """
.sc-card{position:absolute;left:60px;right:60px;height:215px;border:2px solid;border-radius:26px;}
.sc-pct{position:absolute;left:30px;top:44px;width:210px;font-size:88px;font-weight:800;}
.sc-txt{position:absolute;left:250px;right:28px;top:26px;}
.sc-name{font-size:33px;font-weight:900;text-transform:uppercase;line-height:1.15;}
.sc-desc{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;}
.sc-desc b{color:#fde68a;font-family:'JBM';font-weight:800;}
.sc-track{position:absolute;left:30px;right:30px;bottom:18px;height:10px;border-radius:5px;background:rgba(255,255,255,.08);overflow:hidden;}
.sc-fill{height:100%;border-radius:5px;transform-origin:left center;}
"""
    body = f"""
<div id="sc-stage">
  <div class="ttl" id="sc-ttl"><span class="gold">3 kịch bản</span> trong ngày</div>
  <div class="sub" id="sc-sub">Xác suất từ mô hình Market Bias</div>
  {''.join(cards)}
</div>"""
    jss = f"""
tl.fromTo('#sc-ttl', {{opacity:0, x:120, filter:'blur(10px)'}}, {{opacity:1, x:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#sc-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.3);
{''.join(js)}
tl.to('#sc-stage', {{opacity:0, x:-160, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "scen", dur, scene_file("scen", dur, css, body, jss)


# ================================================================ SCENE 4 ACTION + CTA
def scene_cta():
    st, en = SCENES[4][1], SCENES[4][2]
    dur = round(en - st, 3)
    t_a = at("act_neutral", st)
    t_b = at("act_buy", st)
    t_aur = at("aurora", st)
    t_f = at("follow", st)
    acts = D["actions"]
    cards = "".join(
        f'<div class="ac-card" id="ac-{i}" style="top:{420 + i*205}px;border-color:{a["color"]}99;"><div class="ac-ico" style="background:{a["color"]}33;color:{a["color"]};">{a["icon"]}</div>'
        f'<div class="ac-t"><div class="ac-h" style="color:{a["color"]};">{esc(a["title"])}</div><div class="ac-d">{a["desc"]}</div></div></div>'
        for i, a in enumerate(acts))
    css = """
.ac-card{position:absolute;left:60px;right:60px;height:180px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.65);}
.ac-ico{position:absolute;left:26px;top:40px;width:96px;height:96px;border-radius:22px;display:flex;align-items:center;justify-content:center;font-size:52px;font-weight:900;}
.ac-t{position:absolute;left:148px;right:24px;top:28px;}
.ac-h{font-size:31px;font-weight:900;letter-spacing:.5px;text-transform:uppercase;}
.ac-d{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;}
.ac-d b{font-family:'JBM';font-weight:800;color:#fde68a;}
.ac-aur{position:absolute;left:0;right:0;top:1050px;display:flex;align-items:center;justify-content:center;gap:18px;font-size:30px;font-weight:800;color:#c4b5fd;}
.ac-aur img{width:64px;height:64px;}
.ct{position:absolute;left:0;right:0;top:470px;text-align:center;}
.ct img{width:180px;height:180px;filter:drop-shadow(0 0 30px rgba(56,189,248,.6));}
.ct-h{font-family:'JBM';font-weight:800;font-size:82px;margin-top:20px;background:linear-gradient(135deg,#fde047,#f59e0b 50%,#38bdf8);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ct-s{font-size:32px;font-weight:700;color:#cbd5e1;margin-top:10px;}
.ct-p{display:flex;gap:14px;justify-content:center;margin-top:28px;}
.ct-p span{font-family:'JBM';font-weight:800;font-size:28px;color:#fbbf24;border:2px solid rgba(245,158,11,.5);border-radius:12px;padding:8px 18px;background:rgba(245,158,11,.08);}
.ct-d{position:absolute;left:70px;right:70px;top:990px;text-align:center;font-size:28px;line-height:1.4;color:#fed7aa;padding:16px 20px;border:1px solid rgba(245,158,11,.3);border-radius:14px;background:rgba(255,255,255,.03);}
"""
    body = f"""
<div id="ac-stage">
  <div class="ttl" id="ac-ttl">Hành động <span class="gold">tác chiến</span></div>
  <div class="sub" id="ac-sub">Theo cấu trúc Gamma & Bias hôm nay</div>
  {cards}
  <div class="ac-aur" id="ac-aur"><img src="assets/img/logo-aurora.svg" alt=""/>Xác nhận tín hiệu cùng AURORA</div>
</div>
<div id="ct-stage">
  <div class="ct"><img src="assets/img/logo-kenvinzone.svg" alt=""/>
    <div class="ct-h">@kenvinzone</div>
    <div class="ct-s">Follow để nhận Flash Bias mỗi ngày</div>
    <div class="ct-p"><span>TikTok</span><span>Shorts</span><span>Reels</span><span>YouTube</span></div>
  </div>
  <div class="ct-d" id="ct-d">⚠️ Nội dung phân tích định lượng mang tính giáo dục, <b>không phải lời khuyên đầu tư</b>. Nguồn: Market Bias Platform · KenvinZone Analytics</div>
</div>"""
    t_c = round(t_b + 1.7, 3)
    js = f"""
gsap.set('#ac-stage .ac-card, #ac-aur, #ct-stage', {{opacity:0}});
tl.fromTo('#ac-ttl', {{opacity:0, y:-60, filter:'blur(10px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#ac-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.3);
[{t_a}, {t_b}, {t_c}].forEach((t,i)=>tl.fromTo('#ac-'+i, {{opacity:0, y:50, scale:0.96}}, {{opacity:1, y:0, scale:1, duration:0.5, ease:'expo.out', immediateRender:false}}, t));
tl.fromTo('#ac-aur', {{opacity:0, scale:0.85}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(1.8)', immediateRender:false}}, {min(t_aur - 0.6, t_c + 1.9)});
tl.to('#ac-stage', {{opacity:0, scale:0.9, filter:'blur(12px)', duration:0.35, ease:'power3.in'}}, {t_f - 0.1});
tl.fromTo('#ct-stage', {{opacity:0, scale:1.08, filter:'blur(12px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'expo.out', immediateRender:false}}, {t_f + 0.2});
"""
    return "cta", dur, scene_file("cta", dur, css, body, js)


# ================================================================ CAPTIONS
def captions():
    groups = []
    js = []
    for gi, c in enumerate(SUBS["captions"]):
        s = round(c["start"] + OFF, 3)
        e = round(c["end"] + OFF, 3)
        nxt = SUBS["captions"][gi + 1]["start"] + OFF if gi + 1 < len(SUBS["captions"]) else e + 0.6
        e2 = round(min(max(e + 0.25, e), nxt - 0.02), 3)
        ws = "".join(f'<span class="cw" id="cw{gi}_{wi}">{esc(w["text"])}</span> ' for wi, w in enumerate(c["words"]))
        groups.append(f'<div class="cg" id="cg{gi}"><div class="cpill">{ws}</div></div>')
        js.append(f"tl.set('#cg{gi}', {{opacity:1, visibility:'visible'}}, {s});"
                  f"tl.fromTo('#cg{gi} .cpill', {{y:18, opacity:0}}, {{y:0, opacity:1, duration:0.14, ease:'power3.out', immediateRender:false}}, {s});")
        for wi, w in enumerate(c["words"]):
            ws_ = round(w["start"] + OFF, 3)
            js.append(f"tl.fromTo('#cw{gi}_{wi}', {{color:'#cbd5e1', backgroundColor:'rgba(245,158,11,0)'}}, {{color:'#0b0f19', backgroundColor:'rgba(251,191,36,1)', duration:0.06, immediateRender:false}}, {ws_});"
                      f"tl.to('#cw{gi}_{wi}', {{color:'#ffffff', backgroundColor:'rgba(245,158,11,0)', duration:0.06}}, {round(max(w['end'], w['start'] + 0.07) + OFF, 3)});")
        js.append(f"tl.to('#cg{gi} .cpill', {{opacity:0, duration:0.1, ease:'power2.in'}}, {e2 - 0.1});"
                  f"tl.set('#cg{gi}', {{opacity:0, visibility:'hidden'}}, {e2});")
    css = """
.cg{position:absolute;left:0;right:0;top:1190px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;max-width:960px;padding:14px 26px;border-radius:22px;background:rgba(2,6,23,.72);border:1px solid rgba(255,255,255,.08);font-size:44px;font-weight:800;line-height:1.35;color:#cbd5e1;}
.cw{display:inline-block;padding:0 6px;border-radius:10px;}
"""
    dur = TOTAL
    return "captions", dur, scene_file("captions", dur, css, "\n".join(groups), "\n".join(js))


# ================================================================ ROOT
def root(scene_meta):
    hosts = "\n".join(
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{st}" data-duration="{dur}" '
        f'data-track-index="{i+2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{10+i};"></div>'
        for i, (cid, st, dur) in enumerate(scene_meta))
    # SFX
    sfx = []
    k = 0
    def add(file, t, vol):
        nonlocal k
        sfx.append(f'<audio id="sfx{k}" class="clip" src="assets/audio/{file}" data-start="{max(0, round(t, 3))}" data-duration="{SFX_LEN[file]}" data-volume="{vol}" data-track-index="{40+k}"></audio>')
        k += 1
    for cid, st, dur in scene_meta[1:]:
        if cid != "captions":
            add("whoosh.mp3", st - 0.25, 0.45)
    for key in D["sfx_ticks"]:
        add("tick.mp3", abs_at(key), 0.3)
    for key in D["sfx_impacts"]:
        add("impact.mp3", abs_at(key), 0.55)
    # red glow window = gamma scene
    g0, g1 = SCENES[2][1], SCENES[2][2]
    t_gex = abs_at("gex")
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="assets/js/gsap.min.js"></script>
<style>
{FONT_CSS}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#060a13;}}
#root{{position:relative;width:100%;height:100%;font-family:'BVP',sans-serif;color:#f8fafc;}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 30%,#0f1626 0%,#060a13 60%,#03050a 100%);}}
#bgc{{position:absolute;inset:0;width:{W}px;height:{H}px;}}
.glow{{position:absolute;left:-200px;right:-200px;top:200px;height:1000px;filter:blur(120px);}}
#glow-a{{background:radial-gradient(circle at 50% 40%,rgba(245,158,11,.30),rgba(217,119,6,.12) 40%,transparent 70%);}}
#glow-r{{background:radial-gradient(circle at 50% 40%,rgba(239,68,68,.34),rgba(127,29,29,.16) 40%,transparent 70%);opacity:0;}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:176px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:40px;height:40px;}}
.brand .n{{font-size:28px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:28px;color:#7dd3fc;letter-spacing:1px;}}
.prog{{position:absolute;left:60px;right:60px;top:226px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,#f59e0b,#fde047);transform-origin:left center;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="glow" id="glow-a"></div>
  <div class="glow" id="glow-r"></div>
  <canvas id="bgc" width="{W}" height="{H}"></canvas>
  <div class="vig"></div>
  <div class="brand" id="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">KENVINZONE · MARKET BIAS</span><span class="d">{esc(D['date'])}</span></div>
  <div class="prog"><div id="progf"></div></div>
{hosts}
  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{OFF}" data-volume="1" data-track-index="30"></audio>
  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{D.get('bgm_volume', 0.16)}" data-fade-out="2" data-track-index="31"></audio>
  {''.join(sfx)}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
// deterministic background = "Candle Mono Gold" of the old template (big monochrome candle blocks,
// hollow up / filled down, a mid-price line through them), ported to a pure function of time.
const cv = document.getElementById('bgc'); const ctx = cv.getContext('2d');
let seed = 20261028; const rnd = () => {{ seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.16)}, CW = w / 9, SPEED = {D.get('bg_speed', 95)};
const N = Math.ceil(({TOTAL} * SPEED + w) / CW) + 3, CS = [];
let mid = h * 0.70;
for (let i = 0; i < N; i++) {{
  mid += (rnd() - 0.5) * h * 0.10; mid = Math.max(h * 0.50, Math.min(h * 0.88, mid));
  const up = rnd() > 0.5, bh = h * (0.035 + rnd() * 0.075);
  const o = up ? mid + bh / 2 : mid - bh / 2, c = up ? mid - bh / 2 : mid + bh / 2;
  CS.push({{ o, c, hi: Math.min(o, c) - h * (0.015 + rnd() * 0.03), lo: Math.max(o, c) + h * (0.015 + rnd() * 0.03), up }});
}}
// gold -> red while the gamma scene is negative, then back (same window as the glow flood)
const R0 = {t_gex}, R1 = {g1 - 0.3};
function redMix(t){{ const a = Math.min(1, Math.max(0, (t - R0) / 0.4)); const b = Math.min(1, Math.max(0, (t - R1) / 0.6)); return a * (1 - b); }}
function draw(t){{
  const m = redMix(t), r = Math.round(251 - 3 * m), g = Math.round(191 - 78 * m), bl = Math.round(36 + 77 * m), C = r + ',' + g + ',' + bl;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = 'rgba(' + C + ',' + (A * 0.22) + ')'; ctx.lineWidth = 1;
  for (let i = 1; i < 6; i++) {{ const gx = w * i / 6; ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke(); }}
  for (let i = 1; i < 11; i++) {{ const gy = h * i / 11; ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke(); }}
  const off = t * SPEED, i0 = Math.max(0, Math.floor(off / CW) - 1), i1 = Math.min(N - 1, i0 + Math.ceil(w / CW) + 2);
  ctx.beginPath();
  for (let i = i0; i <= i1; i++) {{ const k = CS[i], x = i * CW - off + CW / 2, y = (k.o + k.c) / 2; i === i0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); }}
  ctx.strokeStyle = 'rgba(' + C + ',' + (A * 1.5) + ')'; ctx.lineWidth = 3; ctx.stroke();
  const line = 'rgba(' + C + ',' + (A * 1.15) + ')';
  for (let i = i0; i <= i1; i++) {{
    const k = CS[i], x0 = i * CW - off, bx = x0 + CW * 0.5, top = Math.min(k.o, k.c), bh = Math.abs(k.o - k.c) || 2, bw = CW * 0.56, blft = x0 + CW * 0.22, bot = top + bh;
    ctx.strokeStyle = line; ctx.lineWidth = 2.4;
    ctx.beginPath(); ctx.moveTo(bx, k.hi); ctx.lineTo(bx, top); ctx.moveTo(bx, bot); ctx.lineTo(bx, k.lo); ctx.stroke();
    if (k.up) {{ ctx.lineWidth = 2.6; ctx.strokeRect(blft, top, bw, bh); }}
    else {{ ctx.fillStyle = 'rgba(' + C + ',' + (A * 0.9) + ')'; ctx.fillRect(blft, top, bw, bh); }}
  }}
}}
const P = {{ t: 0 }}; draw(0);
tl.fromTo(P, {{ t: 0 }}, {{ t: {TOTAL}, duration: {TOTAL}, ease: 'none', onUpdate(){{ draw(P.t); }} }}, 0);
tl.fromTo('#progf', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {TOTAL}, ease: 'none' }}, 0);
// colour flood: amber world -> red when gamma turns negative -> amber again
tl.fromTo('#glow-r', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: 'power2.inOut', immediateRender:false }}, {t_gex});
tl.to('#glow-a', {{ opacity: 0.25, duration: 0.4, ease: 'power2.inOut' }}, {t_gex});
tl.to('#glow-r', {{ opacity: 0, duration: 0.6, ease: 'power2.inOut' }}, {g1 - 0.3});
tl.to('#glow-a', {{ opacity: 1, duration: 0.6, ease: 'power2.inOut' }}, {g1 - 0.3});
window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
"""


def main():
    comps = ROOT / "compositions"
    comps.mkdir(exist_ok=True)
    meta = []
    for fn in (scene_hook, scene_forces, scene_gamma, scene_scen, scene_cta):
        cid, dur, txt = fn()
        st = next(s for c, s, e in SCENES if c == cid)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(st, 3), dur))
    if D.get("captions", True):
        cid, dur, txt = captions()
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    html_root = root(meta).replace('id="captions" data-composition-id="captions"', 'id="captions" data-composition-id="captions"')
    html_root = html_root.replace('data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:15;"', 'data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:50;"')
    (ROOT / "index.html").write_text(html_root, encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
