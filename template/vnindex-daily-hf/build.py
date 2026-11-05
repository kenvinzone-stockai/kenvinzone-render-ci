#!/usr/bin/env python3
"""KenvinZone - VNINDEX daily bulletin -> HyperFrames composition generator.

Usage:  python build.py data.json subtitle-word-timing.json
Writes index.html + compositions/*.html in this folder.

Scenes follow the 10 fixed script lines of the VNINDEX master template:
  line 0 cover | 1 score | 2-4 journey (am snapshot, am condition, pm twist)
  5 subscores | 6 timeframes | 7 price levels | 8 scenarios | 9 action + outro
Every beat is timed from the start/length of its voiceover line, so the
picture follows the narration without any per-day timing work.
"""
import json, re, sys, math, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))
D = DATA

SFX_LEN = {'whoosh.mp3': 0.62, 'tick.mp3': 0.13, 'impact.mp3': 0.73}
OFF = float(D.get("audio_offset", 1.0))
OUTRO = float(D.get("outro_hold", 3.6))
W, H = 1080, 1920
SLIDES = SUBS["slides"]
if len(SLIDES) != 10:
    raise SystemExit(f"Template VNINDEX can dung 10 dong script (dang co {len(SLIDES)}).")
VO_LEN = float(SUBS.get("duration") or SUBS["captions"][-1]["end"])
TOTAL = round(OFF + VO_LEN + OUTRO, 2)


def L(i):
    """(video start, duration) of voiceover line i."""
    return (0.0 if i == 0 else round(float(SLIDES[i]["start"]) + OFF, 3)), float(SLIDES[i]["duration"])


def beat(i, frac):
    s, d = L(i)
    if i == 0:
        s, d = OFF, d
    return round(s + frac * d, 3)


SCENES = [
    ("cover", 0.0, L(1)[0]),
    ("score", L(1)[0], L(2)[0]),
    ("journey", L(2)[0], L(5)[0]),
    ("subs", L(5)[0], L(6)[0]),
    ("tf", L(6)[0], L(7)[0]),
    ("levels", L(7)[0], L(8)[0]),
    ("scen", L(8)[0], L(9)[0]),
    ("end", L(9)[0], TOTAL),
]
START = {c: s for c, s, e in SCENES}

SCORE = float(D["score"])
if SCORE < 45:
    TH = {"name": "bearish", "c": "#ef4444", "l": "#f87171", "d": "#7f1d1d", "rgb": "248,113,113", "glow": "239,68,68"}
elif SCORE <= 65:
    TH = {"name": "cautious", "c": "#f59e0b", "l": "#fbbf24", "d": "#92400e", "rgb": "251,191,36", "glow": "245,158,11"}
else:
    TH = {"name": "bullish", "c": "#10b981", "l": "#4ade80", "d": "#065f46", "rgb": "74,222,128", "glow": "16,185,129"}
TONE = {"up": "#4ade80", "down": "#f87171", "flat": "#fbbf24", "urgent": "#f87171", "positive": "#4ade80",
        "bullish": "#4ade80", "bearish": "#f87171", "neutral": "#fbbf24"}


def lt(scene, t_abs):
    return round(t_abs - START[scene], 3)


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




ACC_CSS = f"""
.acc{{padding-top:.1em;background:linear-gradient(180deg,#fff 0%,{TH['l']} 55%,{TH['c']} 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.ttl{{font-size:54px;}}
"""


def exit_js(stage, dur, kind="blur"):
    if kind == "up":
        return f"tl.to('{stage}', {{opacity:0, y:-110, filter:'blur(14px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});"
    if kind == "left":
        return f"tl.to('{stage}', {{opacity:0, x:-150, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});"
    return f"tl.to('{stage}', {{opacity:0, scale:0.96, filter:'blur(12px)', duration:0.28, ease:'power3.in'}}, {dur - 0.3});"


def title_in(sel, t=0.05, frm="y:-50"):
    return f"tl.fromTo('{sel}', {{opacity:0, {frm}, filter:'blur(10px)'}}, {{opacity:1, {frm.split(':')[0]}:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, {t});"


# ================================================================ COVER
def scene_cover():
    cid = "cover"; st, en = SCENES[0][1], SCENES[0][2]; dur = round(en - st, 3)
    c = D["cover"]
    chips = "".join(
        f'<div class="cv-chip{" hot" if ch.get("hot") else ""}" id="cv-chip{i}"><span class="i">{esc(ch["icon"])}</span>{esc(ch["label"])} <b>{esc(ch["value"])}</b></div>'
        for i, ch in enumerate(c["chips"]))
    title = "<br/>".join(esc(x) for x in c["title_lines"])
    # Tu co co chu cho VUA 1 hang (chong xuong hang lam de dong duoi).
    _maxlen = max((len(str(x)) for x in c["title_lines"]), default=1)
    _fa = int(max(60, min(92, 912 / (max(1, _maxlen) * 0.72))))
    _subtxt = re.sub(r"<[^>]+>", "", str(c.get("sub_html", "")))
    _subfs = int(max(30, min(40, 980 / (max(1, len(_subtxt)) * 0.52))))
    css = ACC_CSS + f"""
.cv-eb{{position:absolute;top:250px;left:0;right:0;text-align:center;}}
.cv-eb span{{display:inline-block;background:linear-gradient(135deg,{TH['l']},{TH['c']});color:#0b0f19;font-weight:900;font-size:30px;letter-spacing:4px;text-transform:uppercase;padding:14px 36px;border-radius:99px;box-shadow:0 10px 40px rgba({TH['glow']},.45);}}
.cv-logo{{position:absolute;top:340px;left:0;right:0;text-align:center;}}
.cv-logo img{{width:130px;height:130px;filter:drop-shadow(0 0 30px rgba({TH['glow']},.6));}}
.cv-plate{{position:absolute;top:500px;left:50px;right:50px;text-align:center;}}
.cv-plate div{{display:inline-block;padding:24px 34px;border-radius:26px;border:2px solid rgba({TH['glow']},.45);background:linear-gradient(160deg,rgba(255,255,255,.09),rgba({TH['glow']},.06));box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba({TH['glow']},.18);}}
.cv-plate h1{{font-size:{_fa}px;font-weight:900;line-height:1.16;letter-spacing:-1px;text-transform:uppercase;padding-top:.14em;white-space:nowrap;}}
.cv-sub{{position:absolute;top:790px;left:60px;right:60px;text-align:center;font-size:{_subfs}px;font-weight:700;color:#e2e8f0;white-space:nowrap;}}
.cv-sub b{{font-family:'JBM';color:{TH['l']};}}
.cv-chips{{position:absolute;top:870px;left:40px;right:40px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap;}}
.cv-chip{{font-family:'JBM';font-weight:800;font-size:32px;color:#e2e8f0;padding:12px 24px;border-radius:99px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.14);}}
.cv-chip b{{color:#fff;}} .cv-chip .i{{margin-right:8px;}}
.cv-chip.hot{{background:rgba({TH['glow']},.18);border-color:rgba({TH['glow']},.6);color:{TH['l']};}}
.cv-cta{{position:absolute;top:985px;left:60px;right:60px;text-align:center;font-size:40px;font-weight:900;color:{TH['l']};}}
.cv-date{{position:absolute;top:1070px;left:60px;right:60px;text-align:center;font-family:'JBM';font-weight:700;font-size:30px;color:#94a3b8;}}
.cv-date b{{color:#7dd3fc;}}
"""
    body = f"""<div id="cv-stage">
<div class="cv-eb"><span>{esc(c['eyebrow'])}</span></div>
<div class="cv-logo"><img src="assets/img/logo-kenvinzone.svg" alt=""/></div>
<div class="cv-plate"><div><h1 class="acc">{title}</h1></div></div>
<div class="cv-sub">{c['sub_html']}</div>
<div class="cv-chips">{chips}</div>
<div class="cv-cta">{esc(c['cta'])} <span id="cv-arrow" style="display:inline-block;">→</span></div>
<div class="cv-date"><b>{esc(D['handle'])}</b> · {esc(D['weekday'])} {esc(D['date'])}</div>
</div>"""
    hot = next((i for i, ch in enumerate(c["chips"]) if ch.get("hot")), len(c["chips"]) - 1)
    js = f"""
// everything is on screen at frame 0 (thumbnail = hook); motion lands on the narration
tl.fromTo('#cv-chip{hot}', {{scale:1}}, {{scale:1.12, duration:0.2, ease:'power3.out', immediateRender:false}}, {lt(cid, beat(0, 0.45))});
tl.to('#cv-chip{hot}', {{scale:1, duration:0.5, ease:'expo.out'}}, {lt(cid, beat(0, 0.45)) + 0.2});
tl.fromTo('#cv-arrow', {{x:0}}, {{x:18, duration:0.35, ease:'power2.inOut', yoyo:true, repeat:3, immediateRender:false}}, {lt(cid, beat(0, 0.8))});
{exit_js('#cv-stage', dur)}
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ================================================================ SCORE
def scene_score():
    cid = "score"; st, en = SCENES[1][1], SCENES[1][2]; dur = round(en - st, 3)
    am, pm = float(D["score_am"]), float(D["score"])
    R = 190; C = 2 * math.pi * R
    off = lambda v: C * (1 - v / 100)
    rows = "".join(
        f'<div class="sc-row" id="sc-r{i}" style="top:{860 + i*84}px;"><span class="k">{esc(r["label"])}</span>'
        f'<span class="v mono">{esc(r["am"])} <i>→</i> <b>{esc(r["pm"])}</b></span>'
        f'<span class="d mono" style="color:{TONE.get(r.get("tone","flat"))};">{esc(r["delta"])}</span></div>'
        for i, r in enumerate(D["compare"]))
    delta = int(round(pm - am))
    css = ACC_CSS + f"""
.sc-ring{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}
.sc-num{{position:absolute;left:0;right:0;top:470px;text-align:center;font-family:'JBM';font-weight:800;font-size:150px;line-height:1;color:{TH['l']};}}
.sc-den{{position:absolute;left:0;right:0;top:625px;text-align:center;font-family:'JBM';font-weight:700;font-size:34px;color:#64748b;}}
.sc-when{{position:absolute;left:0;right:0;top:430px;text-align:center;font-weight:900;font-size:30px;letter-spacing:4px;color:#94a3b8;}}
.sc-delta{{position:absolute;left:770px;top:395px;font-family:'JBM';font-weight:800;font-size:52px;color:#fff;background:{TONE['down'] if delta < 0 else TONE['up']};padding:6px 20px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.4);}}
.sc-status{{position:absolute;left:0;right:0;top:785px;text-align:center;}}
.sc-status span{{display:inline-block;font-weight:900;font-size:32px;letter-spacing:2px;color:{TH['l']};border:2px solid {TH['c']};background:rgba({TH['glow']},.12);padding:8px 26px;border-radius:99px;}}
.sc-row{{position:absolute;left:70px;right:70px;height:70px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.08);}}
.sc-row .k{{width:250px;font-size:32px;font-weight:700;color:#cbd5e1;}}
.sc-row .v{{flex:1;font-size:36px;color:#94a3b8;}} .sc-row .v b{{color:#fff;}} .sc-row .v i{{font-style:normal;color:#64748b;}}
.sc-row .d{{font-size:32px;font-weight:800;text-align:right;}}
.sc-pill{{position:absolute;left:60px;right:60px;top:1125px;text-align:center;font-family:'JBM';font-weight:800;font-size:28px;color:#fde68a;}}
"""
    body = f"""<div id="sc-stage">
<div class="ttl" id="sc-ttl">Chốt ngày <span class="acc">Score {int(pm)}/100</span></div>
<svg class="sc-ring" viewBox="0 0 {W} {H}">
  <circle cx="540" cy="540" r="{R}" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="34"/>
  <circle id="sc-arc" cx="540" cy="540" r="{R}" fill="none" stroke="{TH['l']}" stroke-width="34" stroke-linecap="round"
    stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}" transform="rotate(-90 540 540)" style="filter:drop-shadow(0 0 16px rgba({TH['glow']},.7));"/>
</svg>
<div class="sc-when" id="sc-when-am">SÁNG 11:01</div><div class="sc-when" id="sc-when-pm" style="color:{TH['l']};">CHIỀU 15:01</div>
<div class="sc-num mono" id="sc-num">0</div>
<div class="sc-den">/ 100</div>
<div class="sc-delta" id="sc-delta">{delta:+d}</div>
<div class="sc-status" id="sc-status"><span>{esc(D['status'])}</span></div>
{rows}
<div class="sc-pill" id="sc-pill">{esc(D['range_pill'])}</div>
</div>"""
    t_am, t_pm, t_d = lt(cid, beat(1, 0.12)), lt(cid, beat(1, 0.42)), lt(cid, beat(1, 0.62))
    js = f"""
gsap.set('#sc-delta, #sc-status, .sc-row, #sc-pill, #sc-when-pm', {{opacity:0}});
{title_in('#sc-ttl')}
tl.fromTo('#sc-arc', {{strokeDashoffset:{C:.1f}}}, {{strokeDashoffset:{off(am):.1f}, duration:1.0, ease:'power3.out'}}, {t_am});
counter('#sc-num', 0, {am}, {t_am}, 1.0, 0, '', '');
tl.fromTo('#sc-arc', {{strokeDashoffset:{off(am):.1f}}}, {{strokeDashoffset:{off(pm):.1f}, duration:1.2, ease:'power3.inOut', immediateRender:false}}, {t_pm});
counter('#sc-num', {am}, {pm}, {t_pm}, 1.2, 0, '', '');
tl.fromTo('#sc-when-am', {{opacity:1}}, {{opacity:0, duration:0.2, immediateRender:false}}, {t_pm});
tl.fromTo('#sc-when-pm', {{opacity:0}}, {{opacity:1, duration:0.3, immediateRender:false}}, {t_pm + 0.1});
tl.fromTo('#sc-delta', {{opacity:0, scale:1.6, rotation:-8}}, {{opacity:1, scale:1, rotation:0, duration:0.35, ease:'back.out(2)', immediateRender:false}}, {t_d});
tl.fromTo('#sc-status', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_d + 0.3});
QA('.sc-row').forEach((r,i)=>tl.fromTo(r, {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_d + 0.6} + i*0.35));
tl.fromTo('#sc-pill', {{opacity:0}}, {{opacity:1, duration:0.4, immediateRender:false}}, {lt(cid, beat(1, 0.62)) + 1.4});
{exit_js('#sc-stage', dur, 'up')}
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ================================================================ JOURNEY (lines 2-4)
def scene_journey():
    cid = "journey"; st, en = SCENES[2][1], SCENES[2][2]; dur = round(en - st, 3)
    j = D["journey"]; lo, hi = j["axis"]
    yt, yb = 470, 890
    ym = lambda p: yb - (p - lo) / (hi - lo) * (yb - yt)
    xs = [190 + k * (720 / max(1, len(j["path"]) - 1)) for k in range(len(j["path"]))]
    pts = [(x, ym(p["price"])) for x, p in zip(xs, j["path"])]
    segs = []
    SEGLEN = [0]
    for k in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[k - 1], pts[k]
        ln = math.hypot(x1 - x0, y1 - y0) + 2
        col = TONE["up"] if y1 < y0 else TONE["down"]
        SEGLEN.append(round(ln))
        segs.append(f'<path id="jn-s{k}" d="M{x0:.0f},{y0:.0f} L{x1:.0f},{y1:.0f}" stroke="{col}" stroke-width="8" stroke-linecap="round" fill="none" stroke-dasharray="{ln:.0f}" stroke-dashoffset="{ln:.0f}"/>')
    dots = "".join(
        f'<g id="jn-p{k}"><circle cx="{x:.0f}" cy="{y:.0f}" r="{14 if k else 10}" fill="{"#fff" if k else "#94a3b8"}"/>'
        f'<text x="{x:.0f}" y="{y - 30:.0f}" text-anchor="middle" class="mono" font-size="32" font-weight="800" fill="#fff">{str(p["price"]).replace(".", ",")}</text>'
        f'<text x="{x:.0f}" y="{min(yb + 50, y + 56):.0f}" text-anchor="middle" font-size="28" font-weight="700" fill="#94a3b8">{esc(p["label"])}</text></g>'
        for k, ((x, y), p) in enumerate(zip(pts, j["path"])))
    r = j["resistance"]; z = j["zone"]
    yr = ym(r["price"]); zt, zb = ym(z["hi"]), ym(z["lo"])
    am, pm = j["am_card"], j["pm_card"]
    css = ACC_CSS + f"""
.jn-svg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}
.jn-banner{{position:absolute;left:60px;right:60px;top:335px;height:96px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:31px;font-weight:800;line-height:1.25;border-radius:18px;padding:0 22px;}}
.jn-warn{{color:#fde68a;background:rgba(245,158,11,.12);border:2px solid rgba(245,158,11,.5);}}
.jn-warn b,.jn-twist b{{font-family:'JBM';color:#fff;}}
.jn-twist{{color:#fff;background:linear-gradient(135deg,rgba({TH['glow']},.35),rgba(15,23,42,.6));border:2px solid {TH['l']};}}
.jn-card{{position:absolute;left:60px;right:60px;height:108px;border-radius:20px;background:rgba(15,23,42,.72);border:2px solid;padding:12px 24px;}}
.jn-card .t{{font-family:'JBM';font-weight:800;font-size:26px;}} .jn-card .m{{font-size:28px;color:#94a3b8;margin-left:14px;font-weight:700;}}
.jn-card .x{{font-size:29px;font-weight:700;color:#e2e8f0;margin-top:4px;white-space:nowrap;}} .jn-card .x b{{font-family:'JBM';color:#fff;}}
.jn-rlab{{position:absolute;right:70px;top:{yr - 46:.0f}px;font-size:26px;font-weight:800;color:#fca5a5;}}
.jn-zlab{{position:absolute;left:150px;top:{zb + 6:.0f}px;font-size:26px;font-weight:800;color:#fde68a;}}
"""
    body = f"""<div id="jn-stage">
<div class="ttl" id="jn-ttl">Hành trình <span class="acc">sáng → chiều</span></div>
<div class="jn-banner jn-warn" id="jn-warn"><span>⚠ {j['warn_card']}</span></div>
<div class="jn-banner jn-twist" id="jn-twist"><span>⚡ {esc(j['twist'])}</span></div>
<svg class="jn-svg" viewBox="0 0 {W} {H}">
  <rect id="jn-zone" x="110" y="{zt:.0f}" width="860" height="{zb - zt:.0f}" fill="rgba(245,158,11,.16)" stroke="rgba(245,158,11,.55)" stroke-dasharray="10 8" stroke-width="2"/>
  <line id="jn-res" x1="110" x2="970" y1="{yr:.0f}" y2="{yr:.0f}" stroke="#f87171" stroke-width="4" stroke-dasharray="16 10"/>
  <line x1="110" x2="970" y1="{yb + 10}" y2="{yb + 10}" stroke="rgba(255,255,255,.18)" stroke-width="2"/>
  {''.join(segs)}{dots}
</svg>
<div class="jn-rlab" id="jn-rlab">{esc(r['label'])}</div>
<div class="jn-zlab" id="jn-zlab">{esc(z['label'])}</div>
<div class="jn-card" id="jn-am" style="top:960px;border-color:{TONE['up']}88;"><div><span class="t" style="color:{TONE['up']};">{esc(am['time'])}</span><span class="m">{esc(am['meta'])}</span></div><div class="x">{am['text']}</div></div>
<div class="jn-card" id="jn-pm" style="top:1078px;border-color:{TH['l']}aa;"><div><span class="t" style="color:{TH['l']};">{esc(pm['time'])}</span><span class="m">{esc(pm['meta'])}</span></div><div class="x">{pm['text']}</div></div>
</div>"""
    t2, t3, t4 = lt(cid, L(2)[0]), lt(cid, L(3)[0]), lt(cid, L(4)[0])
    d4 = L(4)[1]
    n = len(pts)
    mid_js = "".join(
        f"tl.fromTo('#jn-s{k}', {{strokeDashoffset:{SEGLEN[k]}}}, {{strokeDashoffset:0, duration:1.2, ease:'power2.inOut', immediateRender:false}}, {t2 + 0.7});"
        f"tl.fromTo('#jn-p{k}', {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t2 + 1.7});"
        for k in range(1, n - 1))
    js = f"""
gsap.set('#jn-warn, #jn-twist, #jn-zone, #jn-res, #jn-rlab, #jn-zlab, #jn-am, #jn-pm, #jn-p1, #jn-p2, #jn-p3', {{opacity:0}});
{title_in('#jn-ttl')}
// line 2 - the morning: path climbs to the 11:01 print
tl.fromTo('#jn-p0', {{opacity:0, scale:0.5}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(2)', transformOrigin:'center'}}, {t2 + 0.2});
{mid_js}
tl.fromTo('#jn-am', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {t2 + 2.2});
// line 3 - the morning warning: resistance + the zone the report pointed at
tl.fromTo('#jn-res', {{opacity:0}}, {{opacity:1, duration:0.5, immediateRender:false}}, {t3 + 0.1});
tl.fromTo('#jn-rlab', {{opacity:0, x:30}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t3 + 0.3});
tl.fromTo('#jn-warn', {{opacity:0, y:-20, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out', immediateRender:false}}, {t3 + 0.6});
tl.fromTo('#jn-zone', {{opacity:0}}, {{opacity:1, duration:0.6, immediateRender:false}}, {t3 + 1.6});
tl.fromTo('#jn-zlab', {{opacity:0}}, {{opacity:1, duration:0.4, immediateRender:false}}, {t3 + 1.9});
// line 4 - the afternoon twist: path drops into the zone
tl.fromTo('#jn-s{n-1}', {{strokeDashoffset:{SEGLEN[n-1]}}}, {{strokeDashoffset:0, duration:1.3, ease:'power2.inOut', immediateRender:false}}, {t4 + 0.2});
tl.fromTo('#jn-p{n-1}', {{opacity:0, scale:0.4}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(2.2)', transformOrigin:'center', immediateRender:false}}, {t4 + 1.4});
tl.fromTo('#jn-pm', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {t4 + 1.6});
tl.to('#jn-warn', {{opacity:0, filter:'blur(8px)', duration:0.2, ease:'power2.in'}}, {t4 + min(3.0, d4 * 0.45)});
tl.fromTo('#jn-twist', {{opacity:0, scale:1.08, filter:'blur(8px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.35, ease:'expo.out', immediateRender:false}}, {t4 + min(3.0, d4 * 0.45) + 0.15});
{exit_js('#jn-stage', dur, 'left')}
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ================================================================ SUBSCORES
def scene_subs():
    cid = "subs"; st, en = SCENES[3][1], SCENES[3][2]; dur = round(en - st, 3)
    subs = D["subscores"]
    BW = 940
    tot = sum(s["pm"] - s["am"] for s in subs)
    worst = min(range(len(subs)), key=lambda i: subs[i]["pm"] - subs[i]["am"])
    def col(v, m):
        p = v / m
        return "#f87171" if p < 0.45 else ("#fbbf24" if p <= 0.65 else "#4ade80")
    rows, js_rows = [], []
    for i, s in enumerate(subs):
        y = 420 + i * 128
        wam = BW * s["am"] / s["max"]
        wpm = BW * s["pm"] / s["max"]
        dd = s["pm"] - s["am"]
        rows.append(
            f'<div class="sb-row" id="sb-r{i}" style="top:{y}px;"><div class="sb-h"><span class="k">{esc(s["label"])}</span>'
            f'<span class="v mono">{s["am"]} → <b id="sb-v{i}">{s["am"]}</b><i>/{s["max"]}</i></span>'
            f'<span class="d mono" style="color:{TONE["down"] if dd < 0 else (TONE["up"] if dd > 0 else "#94a3b8")};">{dd:+d}</span></div>'
            f'<div class="sb-track"><div class="sb-ghost" style="width:{wam:.0f}px;"></div><div class="sb-bar" id="sb-b{i}" style="width:{wam:.0f}px;background:{col(s["pm"], s["max"])};box-shadow:0 0 18px {col(s["pm"], s["max"])}88;"></div></div></div>')
        t = lt(cid, beat(5, 0.08 + i * 0.1))
        js_rows.append(
            f"tl.fromTo('#sb-r{i}', {{opacity:0, x:-50}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t});"
            f"tl.fromTo('#sb-b{i}', {{scaleX:1}}, {{scaleX:{(wpm / wam if wam else 1):.4f}, duration:0.9, ease:'power3.inOut', immediateRender:false}}, {t + 0.45});"
            f"counter('#sb-v{i}', {s['am']}, {s['pm']}, {t + 0.45}, 0.9, 0, '', '');")
    css = ACC_CSS + f"""
.sb-row{{position:absolute;left:70px;right:70px;height:110px;}}
.sb-h{{display:flex;align-items:baseline;justify-content:space-between;}}
.sb-h .k{{font-size:34px;font-weight:800;color:#e2e8f0;width:300px;}}
.sb-h .v{{flex:1;font-size:32px;color:#94a3b8;}} .sb-h .v b{{color:#fff;font-size:40px;}} .sb-h .v i{{font-style:normal;font-size:28px;color:#94a3b8;}}
.sb-h .d{{font-size:34px;font-weight:800;}}
.sb-track{{position:relative;margin-top:10px;height:26px;border-radius:13px;background:rgba(255,255,255,.06);}}
.sb-ghost{{position:absolute;left:0;top:0;bottom:0;border-radius:13px;background:rgba(255,255,255,.14);}}
.sb-bar{{position:absolute;left:0;top:0;bottom:0;border-radius:13px;transform-origin:left center;}}
.sb-tag{{position:absolute;right:170px;font-size:28px;font-weight:900;letter-spacing:2px;color:#fff;background:#ef4444;padding:4px 12px;border-radius:8px;}}
.sb-note{{position:absolute;left:60px;right:60px;top:1078px;text-align:center;font-size:30px;font-weight:700;color:#fde68a;padding:14px 20px;border:2px solid rgba(245,158,11,.45);border-radius:18px;background:rgba(245,158,11,.08);}}
"""
    body = f"""<div id="sb-stage">
<div class="ttl" id="sb-ttl">5 điểm thành phần <span class="acc">tổng {tot:+d}</span></div>
<div class="sub" id="sb-sub">Sáng 11:01 → chiều 15:01 · vạch mờ = điểm sáng</div>
{''.join(rows)}
<div class="sb-tag" id="sb-tag" style="top:{420 + worst*128 - 40}px;">GIẢM MẠNH NHẤT</div>
<div class="sb-note" id="sb-note">{esc(D.get('subscore_note', ''))}</div>
</div>"""
    js = f"""
gsap.set('#sb-stage .sb-row, #sb-tag, #sb-note', {{opacity:0}});
{title_in('#sb-ttl')}
tl.fromTo('#sb-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.3);
{''.join(js_rows)}
tl.fromTo('#sb-tag', {{opacity:0, scale:0.6}}, {{opacity:1, scale:1, duration:0.35, ease:'back.out(2)', immediateRender:false}}, {lt(cid, beat(5, 0.55))});
tl.fromTo('#sb-note', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(5, 0.6))});
{exit_js('#sb-stage', dur, 'up')}
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ================================================================ TIMEFRAMES
def scene_tf():
    cid = "tf"; st, en = SCENES[4][1], SCENES[4][2]; dur = round(en - st, 3)
    tfs = D["timeframes"]
    pos = [(60, 400), (555, 400), (60, 730), (555, 730)]
    cards, js = [], []
    order = sorted(range(len(tfs)), key=lambda i: {"D1": 0, "W1": 1, "3D": 2}.get(tfs[i]["tf"], 3))
    for rank, i in enumerate(order):
        t = tfs[i]; x, y = pos[i]; c = TONE.get(t["trend"], "#fbbf24")
        cards.append(
            f'<div class="tf-card" id="tf-c{i}" style="left:{x}px;top:{y}px;border-color:{c}99;">'
            f'<div class="tf-top"><span class="tf mono" style="color:{c};">{esc(t["tf"])}</span><span class="nm">{esc(t["name"])}</span></div>'
            f'<div class="tf-badge" style="background:{c}26;color:{c};border-color:{c}88;">{esc(t["badge"])}</div>'
            f'<div class="tf-d">{t["detail"]}</div></div>')
        js.append(f"tl.fromTo('#tf-c{i}', {{opacity:0, y:50, scale:0.95}}, {{opacity:1, y:0, scale:1, duration:0.5, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(6, 0.05 + rank * 0.2))});")
    css = ACC_CSS + """
.tf-card{position:absolute;width:465px;height:300px;border:2px solid;border-radius:26px;background:rgba(15,23,42,.66);padding:24px 26px;}
.tf-top{display:flex;align-items:baseline;gap:14px;} .tf-top .tf{font-size:62px;font-weight:800;} .tf-top .nm{font-size:30px;font-weight:700;color:#94a3b8;}
.tf-badge{display:inline-block;margin-top:10px;font-size:28px;font-weight:900;letter-spacing:1px;padding:6px 18px;border-radius:99px;border:2px solid;}
.tf-d{margin-top:16px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;} .tf-d b{font-family:'JBM';color:#fff;}
.tf-note{position:absolute;left:60px;right:60px;top:1070px;text-align:center;font-size:30px;font-weight:700;color:#fde68a;padding:14px 20px;border:2px solid rgba(245,158,11,.45);border-radius:18px;background:rgba(245,158,11,.08);}
"""
    body = f"""<div id="tf-stage">
<div class="ttl" id="tf-ttl">Đa khung <span class="acc">thời gian</span></div>
<div class="sub">D1 xác nhận · W1/3D xu hướng · M15 nhịp ngắn</div>
{''.join(cards)}
<div class="tf-note" id="tf-note">{esc(D.get('timeframe_note', ''))}</div>
</div>"""
    jss = f"""
gsap.set('#tf-stage .tf-card, #tf-note', {{opacity:0}});
{title_in('#tf-ttl')}
{''.join(js)}
tl.fromTo('#tf-note', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(6, 0.74))});
{exit_js('#tf-stage', dur)}
"""
    return cid, dur, scene_file(cid, dur, css, body, jss)


# ================================================================ LEVELS
def scene_levels():
    cid = "levels"; st, en = SCENES[5][1], SCENES[5][2]; dur = round(en - st, 3)
    lv = D["levels"]; lo, hi = lv["axis"]
    yt, yb = 430, 1030
    ym = lambda p: yb - (p - lo) / (hi - lo) * (yb - yt)
    items = sorted(lv["items"], key=lambda it: -it["price"])
    ys = [ym(it["price"]) for it in items]
    # label repulsion: keep labels >= 54 px apart, inside the chart
    lab = list(ys)
    for _ in range(60):
        for k in range(1, len(lab)):
            if lab[k] - lab[k - 1] < 54:
                mid = (lab[k] + lab[k - 1]) / 2
                lab[k - 1], lab[k] = mid - 27, mid + 27
        lab = [min(max(v, yt - 10), yb + 10) for v in lab]
    py = ym(lv["price"])
    x0, x1 = 120, 470
    rows, js = [], []
    for k, (it, y, ly) in enumerate(zip(items, ys, lab)):
        c = "#fbbf24" if it.get("key") else ("#f87171" if it["kind"] == "res" else "#4ade80")
        wdt = 6 if it.get("key") else 3
        rows.append(
            f'<line id="lv-l{k}" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{c}" stroke-width="{wdt}" style="filter:drop-shadow(0 0 6px {c});"/>'
            f'<path id="lv-k{k}" d="M{x1},{y:.1f} L{x1 + 40},{ly:.1f} L{x1 + 60},{ly:.1f}" stroke="{c}88" stroke-width="2" fill="none"/>'
            f'<text id="lv-t{k}" x="{x1 + 70}" y="{ly + 11:.1f}" font-size="30" font-weight="800" fill="{c}"><tspan class="mono" fill="#fff">{str(it["price"]).replace(".", ",")}</tspan>  {esc(it["label"])}{"  ★" if it.get("key") else ""}</text>')
        js.append(f"tl.fromTo('#lv-l{k}', {{opacity:0, scaleX:0}}, {{opacity:1, scaleX:1, transformOrigin:'left center', duration:0.5, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(7, 0.08 + k * 0.07))});"
                  f"tl.fromTo('#lv-k{k}, #lv-t{k}', {{opacity:0}}, {{opacity:1, duration:0.3, immediateRender:false}}, {lt(cid, beat(7, 0.08 + k * 0.07)) + 0.25});")
    keyk = next((k for k, it in enumerate(items) if it.get("key")), None)
    key_js = (f"tl.fromTo('#lv-l{keyk}', {{strokeWidth:6}}, {{strokeWidth:12, duration:0.25, yoyo:true, repeat:3, ease:'power2.inOut', immediateRender:false}}, {lt(cid, beat(7, 0.66))});" if keyk is not None else "")
    css = ACC_CSS + f"""
.lv-svg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;}}
.lv-chips{{position:absolute;left:60px;right:60px;top:1085px;display:flex;gap:16px;}}
.lv-chips div{{flex:1;text-align:center;font-family:'JBM';font-weight:800;font-size:27px;padding:14px 10px;border-radius:16px;border:2px solid;}}
"""
    body = f"""<div id="lv-stage">
<div class="ttl" id="lv-ttl">Vùng giá <span class="acc">cần canh</span></div>
<svg class="lv-svg" viewBox="0 0 {W} {H}">
  <line x1="{x0}" x2="{x0}" y1="{yt - 30}" y2="{yb + 30}" stroke="rgba(255,255,255,.3)" stroke-width="3"/>
  {''.join(rows)}
  <g id="lv-price"><circle cx="{x0 + 175}" cy="{py:.1f}" r="20" fill="#fff" style="filter:drop-shadow(0 0 14px #fff);"/>
  <text x="{x0 - 14}" y="{py + 10:.1f}" text-anchor="end" class="mono" font-size="0"> </text></g>
</svg>
<div style="position:absolute;left:30px;top:{py - 70:.0f}px;font-family:'JBM';font-weight:800;font-size:28px;color:#fff;" id="lv-plab">{esc(lv['price_label'])}</div>
<div class="lv-chips" id="lv-chips"><div style="color:{TONE['up']};border-color:{TONE['up']}88;background:rgba(74,222,128,.08);">▲ {esc(lv['up'])}</div><div style="color:{TONE['down']};border-color:{TONE['down']}88;background:rgba(248,113,113,.08);">✗ {esc(lv['down'])}</div></div>
</div>"""
    jss = f"""
gsap.set('#lv-price, #lv-plab, #lv-chips', {{opacity:0}});
{title_in('#lv-ttl')}
{''.join(js)}
tl.fromTo('#lv-price', {{opacity:0, x:-120}}, {{opacity:1, x:0, duration:0.8, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(7, 0.2))});
tl.fromTo('#lv-plab', {{opacity:0}}, {{opacity:1, duration:0.3, immediateRender:false}}, {lt(cid, beat(7, 0.3))});
{key_js}
tl.fromTo('#lv-chips', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {lt(cid, beat(7, 0.78))});
{exit_js('#lv-stage', dur, 'left')}
"""
    return cid, dur, scene_file(cid, dur, css, body, jss)


# ================================================================ SCENARIOS
def scene_scen():
    cid = "scen"; st, en = SCENES[6][1], SCENES[6][2]; dur = round(en - st, 3)
    cards, js = [], []
    for i, s in enumerate(D["scenarios"]):
        c = TONE.get(s["tone"], "#fbbf24"); y = 410 + i * 240
        t = lt(cid, beat(8, [0.04, 0.36, 0.68][i] if i < 3 else 0.9))
        cards.append(
            f'<div class="sn-card" id="sn-c{i}" style="top:{y}px;border-color:{c}88;background:linear-gradient(135deg,{c}22,rgba(15,23,42,.62));">'
            f'<div class="sn-pct mono" id="sn-p{i}" style="color:{c};">0%</div>'
            f'<div class="sn-txt"><div class="sn-name" style="color:{c};">{esc(s["name"])}</div><div class="sn-desc">{s["desc"]}</div></div>'
            f'<div class="sn-track"><div class="sn-fill" id="sn-f{i}" style="width:{s["pct"]}%;background:{c};"></div></div></div>')
        js.append(f"tl.fromTo('#sn-c{i}', {{opacity:0, x:{-120 if i % 2 == 0 else 120}}}, {{opacity:1, x:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {t});"
                  f"counter('#sn-p{i}', 0, {s['pct']}, {t + 0.2}, 1.2, 0, '', '%');"
                  f"tl.fromTo('#sn-f{i}', {{scaleX:0}}, {{scaleX:1, duration:1.2, ease:'power3.out', immediateRender:false}}, {t + 0.2});")
    css = ACC_CSS + """
.sn-card{position:absolute;left:60px;right:60px;height:212px;border:2px solid;border-radius:26px;}
.sn-pct{position:absolute;left:30px;top:44px;width:210px;font-size:88px;font-weight:800;}
.sn-txt{position:absolute;left:250px;right:28px;top:26px;}
.sn-name{font-size:33px;font-weight:900;text-transform:uppercase;line-height:1.15;}
.sn-desc{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;} .sn-desc b{color:#fde68a;font-family:'JBM';font-weight:800;}
.sn-track{position:absolute;left:30px;right:30px;bottom:18px;height:10px;border-radius:5px;background:rgba(255,255,255,.08);overflow:hidden;}
.sn-fill{height:100%;border-radius:5px;transform-origin:left center;}
"""
    body = f"""<div id="sn-stage">
<div class="ttl" id="sn-ttl">Kịch bản <span class="acc">phiên tới</span></div>
<div class="sub">Xác suất theo báo cáo chiều</div>
{''.join(cards)}
</div>"""
    jss = f"""
gsap.set('#sn-stage .sn-card', {{opacity:0}});
{title_in('#sn-ttl', frm='x:120')}
{''.join(js)}
{exit_js('#sn-stage', dur)}
"""
    return cid, dur, scene_file(cid, dur, css, body, jss)


# ================================================================ ACTION + OUTRO
def scene_end():
    cid = "end"; st, en = SCENES[7][1], SCENES[7][2]; dur = round(en - st, 3)
    acts = D["actions"]; o = D["outro"]
    cards = "".join(
        f'<div class="ed-card" id="ed-a{i}" style="top:{400 + i*200}px;border-color:{TONE.get(a["tone"])}99;"><div class="ed-ico" style="background:{TONE.get(a["tone"])}2e;color:{TONE.get(a["tone"])};">{"!" if a["tone"] == "urgent" else "✓"}</div>'
        f'<div class="ed-t"><div class="ed-h" style="color:{TONE.get(a["tone"])};">{esc(a["title"])}</div><div class="ed-d">{a["desc"]}</div></div></div>'
        for i, a in enumerate(acts))
    t_out = round(max(lt(cid, beat(9, 0.62)), 3.0), 3)
    css = ACC_CSS + f"""
.ed-card{{position:absolute;left:60px;right:60px;height:176px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.66);}}
.ed-ico{{position:absolute;left:26px;top:38px;width:96px;height:96px;border-radius:22px;display:flex;align-items:center;justify-content:center;font-size:56px;font-weight:900;}}
.ed-t{{position:absolute;left:148px;right:24px;top:26px;}}
.ed-h{{font-size:33px;font-weight:900;text-transform:uppercase;}}
.ed-d{{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;}} .ed-d b{{font-family:'JBM';color:#fde68a;}}
.ot-plate{{position:absolute;top:300px;left:60px;right:60px;text-align:center;}}
.ot-plate .k{{font-size:28px;font-weight:900;letter-spacing:5px;color:{TH['l']};}}
.ot-line{{margin:16px auto 0;max-width:900px;font-size:36px;font-weight:800;line-height:1.3;padding:18px 24px;border-radius:20px;}}
.ot-h{{position:absolute;top:740px;left:0;right:0;text-align:center;font-family:'JBM';font-weight:800;font-size:80px;background:linear-gradient(135deg,#fde047,{TH['c']} 50%,#38bdf8);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.ot-p{{position:absolute;top:855px;left:60px;right:60px;text-align:center;font-size:36px;font-weight:800;color:#e2e8f0;}}
.ot-pl{{position:absolute;top:925px;left:0;right:0;display:flex;gap:14px;justify-content:center;}}
.ot-pl span{{font-family:'JBM';font-weight:800;font-size:28px;color:{TH['l']};border:2px solid rgba({TH['glow']},.5);border-radius:12px;padding:8px 18px;}}
.ot-d{{position:absolute;left:70px;right:70px;top:1015px;text-align:center;font-size:28px;line-height:1.4;color:#fed7aa;padding:14px 18px;border:1px solid rgba(245,158,11,.3);border-radius:14px;background:rgba(255,255,255,.03);}}
"""
    body = f"""<div id="ed-stage">
<div class="ttl" id="ed-ttl">Anh em <span class="acc">làm gì?</span></div>
{cards}
</div>
<div id="ot-stage">
<div class="ot-plate"><div class="k">KENVINZONE ANALYTICS</div>
<div class="ot-line" style="color:{TONE['up']};border:2px solid {TONE['up']}77;background:rgba(74,222,128,.07);">▲ {esc(o['up'])}</div>
<div class="ot-line" style="color:{TONE['down']};border:2px solid {TONE['down']}77;background:rgba(248,113,113,.07);">✗ {esc(o['down'])}</div></div>
<div class="ot-h">{esc(o['follow_handle'])}</div>
<div class="ot-p">{esc(o['promise'])} →</div>
<div class="ot-pl"><span>TikTok</span><span>Reels</span><span>Shorts</span></div>
<div class="ot-d">⚠️ Nội dung chỉ mang tính tham khảo, <b>không phải lời khuyên đầu tư</b>. Nhà đầu tư tự chịu trách nhiệm với mọi quyết định.</div>
</div>"""
    js = f"""
gsap.set('#ed-stage .ed-card, #ot-stage', {{opacity:0}});
{title_in('#ed-ttl')}
QA('.ed-card').forEach((c,i)=>tl.fromTo(c, {{opacity:0, y:50, scale:0.96}}, {{opacity:1, y:0, scale:1, duration:0.45, ease:'expo.out', immediateRender:false}}, 0.25 + i*0.55));
tl.to('#ed-stage', {{opacity:0, scale:0.92, filter:'blur(12px)', duration:0.35, ease:'power3.in'}}, {t_out});
tl.fromTo('#ot-stage', {{opacity:0, scale:1.06, filter:'blur(12px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'expo.out', immediateRender:false}}, {t_out + 0.3});
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


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
        f'data-track-index="{i+2}" data-track-kind="{"captions" if cid == "captions" else "graphics"}" data-width="{W}" data-height="{H}" style="z-index:{50 if cid == "captions" else 10+i};"></div>'
        for i, (cid, st, dur) in enumerate(scene_meta))
    sfx = []
    k = 0

    def add(file, t, vol):
        nonlocal k
        sfx.append(f'<audio id="sfx{k}" class="clip" src="assets/audio/{file}" data-start="{max(0, round(t, 3))}" data-duration="{SFX_LEN[file]}" data-volume="{vol}" data-track-index="{40+k}"></audio>')
        k += 1
    for cid, st, en in SCENES[1:]:
        add("whoosh.mp3", st - 0.25, 0.45)
    add("impact.mp3", START["score"] + lt("score", beat(1, 0.62)) , 0.5)
    add("impact.mp3", beat(4, 0.0) + min(3.0, L(4)[1] * 0.45) + 0.15, 0.5)
    for f in (0.12, 0.42):
        add("tick.mp3", beat(1, f), 0.3)
    for i in range(len(D["subscores"])):
        add("tick.mp3", beat(5, 0.08 + i * 0.1) + 0.45, 0.25)
    for i in range(min(3, len(D["scenarios"]))):
        add("tick.mp3", beat(8, [0.04, 0.36, 0.68][i]) + 0.2, 0.3)
    bgm_vol = D.get("bgm_volume", 0.16)
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
.glow{{position:absolute;left:-200px;right:-200px;top:200px;height:1000px;filter:blur(120px);background:radial-gradient(circle at 50% 40%,rgba({TH['glow']},.28),rgba({TH['glow']},.10) 40%,transparent 70%);}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:176px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:40px;height:40px;}}
.brand .n{{font-size:28px;font-weight:800;letter-spacing:1px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:28px;color:#7dd3fc;}}
.prog{{position:absolute;left:60px;right:60px;top:226px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,{TH['c']},{TH['l']});transform-origin:left center;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="glow"></div>
  <canvas id="bgc" width="{W}" height="{H}"></canvas>
  <div class="vig"></div>
  <div class="brand" id="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">{esc(D['handle'])} · VNINDEX</span><span class="d">{esc(D['date'])}</span></div>
  <div class="prog" id="prog"><div id="progf"></div></div>
{hosts}
  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{OFF}" data-volume="1" data-track-index="30"></audio>
  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{bgm_vol}" data-fade-out="2" data-track-index="31"></audio>
  {''.join(sfx)}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
// "Candle Mono" background in the score theme colour, a pure function of time
const cv = document.getElementById('bgc'); const ctx = cv.getContext('2d');
let seed = 20261027; const rnd = () => {{ seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.16)}, CW = w / 9, SPEED = {D.get('bg_speed', 95)}, C = '{TH['rgb']}';
const N = Math.ceil(({TOTAL} * SPEED + w) / CW) + 3, CS = [];
let mid = h * 0.70;
for (let i = 0; i < N; i++) {{
  mid += (rnd() - 0.5) * h * 0.10; mid = Math.max(h * 0.50, Math.min(h * 0.88, mid));
  const up = rnd() > 0.5, bh = h * (0.035 + rnd() * 0.075);
  const o = up ? mid + bh / 2 : mid - bh / 2, c = up ? mid - bh / 2 : mid + bh / 2;
  CS.push({{ o, c, hi: Math.min(o, c) - h * (0.015 + rnd() * 0.03), lo: Math.max(o, c) + h * (0.015 + rnd() * 0.03), up }});
}}
function draw(t){{
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
    const k = CS[i], x0 = i * CW - off, bx = x0 + CW * 0.5, top = Math.min(k.o, k.c), bh = Math.abs(k.o - k.c) || 2, bw = CW * 0.56, bl = x0 + CW * 0.22, bot = top + bh;
    ctx.strokeStyle = line; ctx.lineWidth = 2.4;
    ctx.beginPath(); ctx.moveTo(bx, k.hi); ctx.lineTo(bx, top); ctx.moveTo(bx, bot); ctx.lineTo(bx, k.lo); ctx.stroke();
    if (k.up) {{ ctx.lineWidth = 2.6; ctx.strokeRect(bl, top, bw, bh); }}
    else {{ ctx.fillStyle = 'rgba(' + C + ',' + (A * 0.9) + ')'; ctx.fillRect(bl, top, bw, bh); }}
  }}
}}
const P = {{ t: 0 }}; draw(0);
tl.fromTo(P, {{ t: 0 }}, {{ t: {TOTAL}, duration: {TOTAL}, ease: 'none', onUpdate(){{ draw(P.t); }} }}, 0);
tl.fromTo('#progf', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {TOTAL}, ease: 'none' }}, 0);
// the cover carries its own handle + date: brand row arrives with the second scene
gsap.set('#brand, #prog', {{ opacity: 0 }});
tl.fromTo('#brand, #prog', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, immediateRender:false }}, {START['score']});
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
    for fn in (scene_cover, scene_score, scene_journey, scene_subs, scene_tf, scene_levels, scene_scen, scene_end):
        cid, dur, txt = fn()
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(START[cid], 3), dur))
    if D.get("captions", True):
        cid, dur, txt = captions()
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    (ROOT / "index.html").write_text(root(meta), encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
