#!/usr/bin/env python3
"""KenvinZone — US Equity Bias (S&P 500 + Nasdaq) -> HyperFrames composition.

Usage:  python3 build.py data.json subtitle-word-timing.json
Layout TUẦN TỰ (sequential blocks): hook (2 chỉ số) -> khối S&P 500 -> khối Nasdaq
-> so sánh & phân kỳ -> CTA. 7 dòng script = 7 slide.
Mọi SỐ lấy từ data.json; thời điểm hiện hình tính theo mốc slide (khung lời) nên bền,
không phụ thuộc nhận diện từng từ.
"""
import json, sys, math, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))

SFX_LEN = {'whoosh.mp3': 0.62, 'tick.mp3': 0.13, 'impact.mp3': 0.73}
OFF = float(DATA.get("audio_offset", 1.0))
OUTRO = float(DATA.get("outro_hold", 3.6))
W, H = 1080, 1920
WORDS = [(w["text"], w["start"], w["end"]) for c in SUBS["captions"] for w in c["words"]]
VO_LEN = float(SUBS.get("duration", WORDS[-1][2]))
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
SLIDES = SUBS["slides"]
NLINES = 7
if len(SLIDES) != NLINES:
    raise SystemExit(f"Template equity-bias can dung {NLINES} dong script (dang co {len(SLIDES)}).")


def slide_start(i):
    return round(SLIDES[i]["start"] + OFF, 3) if i > 0 else 0.0


def tline(line, frac):
    """Absolute video time at `frac` of its voiceover line."""
    s = float(SLIDES[line]["start"]); d = float(SLIDES[line]["duration"])
    return round(s + max(0.0, min(1.0, frac)) * d + OFF, 3)


# scene slots (start,end in absolute video time)
S = [slide_start(i) for i in range(NLINES)]
SCENES = [
    ("hook",  0.0,  S[1]),
    ("spx",   S[1], S[3]),   # slides 1-2
    ("nas",   S[3], S[5]),   # slides 3-4
    ("cmp",   S[5], S[6]),   # slide 5
    ("cta",   S[6], TOTAL),  # slide 6
]

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
.sky{background:linear-gradient(180deg,#fff 0%,#bae6fd 45%,#38bdf8 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}
.amber{background:linear-gradient(180deg,#fff 0%,#fde68a 45%,#f59e0b 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}
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
  const el = Q(sel); if(!el) return; const o = {{v: from}};
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
IDX = {i["key"]: i for i in D["indices"]}
COLOR = {"spx": "#38bdf8", "nas": "#a78bfa"}        # S&P xanh dương, Nasdaq tím
WARM = ["#ef4444", "#f87171", "#fb923c"]
COOL = ["#4ade80", "#38bdf8", "#22d3ee"]


def regime_col(score):
    return "#4ade80" if score > 3 else ("#f87171" if score < -3 else "#fbbf24")


# ============================================================= SCENE 0 HOOK
def scene_hook():
    st, en = SCENES[0][1], SCENES[0][2]
    dur = round(en - st, 3)
    spx, nas = IDX["spx"], IDX["nas"]
    def gauge(ix, cx):
        sc = ix["score"]; pos = (sc + 100) / 200 * 100
        col = regime_col(sc)
        return (f'<div class="hk-g" style="left:{cx-250}px;width:500px;">'
                f'<div class="hk-gn" style="color:{COLOR[ix["key"]]};">{esc(ix["name"])}</div>'
                f'<div class="hk-gr">{esc(ix["regime"])}</div>'
                f'<div class="hk-gv mono" id="hk-{ix["key"]}" style="color:{col};">{sc:+.1f}</div>'
                f'<div class="hk-gb"><div class="hk-gmk" style="left:{pos:.1f}%;"></div></div>'
                f'<div class="hk-gs mono">/ 100</div></div>')
    dv = D.get("divergence_tag") or ""
    css = f"""
.hk-eyebrow{{position:absolute;top:250px;left:0;right:0;display:flex;justify-content:center;}}
.hk-eyebrow span{{background:linear-gradient(135deg,#38bdf8,#6366f1);color:#fff;font-weight:900;font-size:27px;letter-spacing:3px;padding:14px 32px;border-radius:99px;box-shadow:0 10px 40px rgba(99,102,241,.45);}}
.hk-title{{position:absolute;top:360px;left:60px;right:60px;text-align:center;}}
.hk-title h1{{font-size:62px;font-weight:900;line-height:1.14;letter-spacing:-1px;}}
.hk-date{{position:absolute;top:560px;left:0;right:0;text-align:center;}}
.hk-date span{{font-family:'JBM';font-weight:800;font-size:27px;color:#7dd3fc;border:2px solid rgba(56,189,248,.45);padding:8px 24px;border-radius:99px;background:rgba(56,189,248,.08);letter-spacing:2px;}}
.hk-g{{position:absolute;top:660px;text-align:center;}}
.hk-gn{{font-size:40px;font-weight:900;letter-spacing:1px;}}
.hk-gr{{margin-top:4px;font-size:25px;font-weight:800;letter-spacing:3px;color:#94a3b8;}}
.hk-gv{{font-family:'JBM';font-weight:800;font-size:104px;line-height:1.1;}}
.hk-gb{{position:relative;margin:6px auto 0;width:420px;height:14px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.hk-gmk{{position:absolute;top:-12px;width:9px;height:38px;margin-left:-4px;border-radius:5px;background:#fff;box-shadow:0 0 16px #fff;}}
.hk-gs{{margin-top:12px;font-size:24px;color:#64748b;}}
.hk-dv{{position:absolute;top:1120px;left:70px;right:70px;text-align:center;font-size:30px;font-weight:800;line-height:1.35;padding:20px 26px;border-radius:20px;border:2px solid rgba(251,191,36,.5);background:rgba(251,191,36,.10);color:#fde68a;}}
.hk-dv b{{color:#fff;}}
"""
    body = f"""
<div class="hk-stage" id="hk-stage">
  <div class="hk-eyebrow"><span>{esc(D.get('eyebrow') or '⚡ BIAS ĐỊNH LƯỢNG · CHỨNG KHOÁN MỸ')}</span></div>
  <div class="hk-title"><h1>{D.get('title_html','BIAS CHỨNG KHOÁN MỸ')}</h1></div>
  <div class="hk-date"><span>{esc(D.get('date_prefix') or 'PHIÊN')} {esc(D['date'])}</span></div>
  {gauge(spx, 290)}
  {gauge(nas, 790)}
  <div class="hk-dv" id="hk-dv">{dv}</div>
</div>"""
    t_spx = tline(0, 0.35); t_nas = tline(0, 0.6); t_dv = tline(0, 0.86)
    js = f"""
gsap.set('#hk-dv', {{opacity:0}});
tl.fromTo('#hk-spx', {{scale:1.2, opacity:0}}, {{scale:1, opacity:1, duration:0.4, ease:'back.out(1.6)', immediateRender:false}}, {t_spx});
tl.fromTo('#hk-nas', {{scale:1.2, opacity:0}}, {{scale:1, opacity:1, duration:0.4, ease:'back.out(1.6)', immediateRender:false}}, {t_nas});
tl.fromTo('#hk-dv', {{opacity:0, y:30, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.45, ease:'expo.out', immediateRender:false}}, {t_dv});
tl.to('#hk-stage', {{opacity:0, filter:'blur(10px)', scale:0.96, duration:0.28, ease:'power3.in'}}, {dur - 0.3});
"""
    return "hook", dur, scene_file("hook", dur, css, body, js)


# ============================================================= INDEX BLOCK (reused)
def scene_index(key, line_hdr, line_gamma):
    ix = IDX[key]
    cid = key
    stsc = next(s for c, s, e in SCENES if c == cid)
    ensc = next(e for c, s, e in SCENES if c == cid)
    dur = round(ensc - stsc, 3)
    acc = COLOR[key]
    sc = ix["score"]
    # --- forces (6, tug of war) ---
    rows = ix["forces"]
    maxabs = max(abs(r["value"]) for r in rows) or 1.0
    half = 360; cx = 540; top0 = 470; rh = 74
    frows = []; fjs = []
    for i, r in enumerate(rows):
        y = top0 + i * rh
        w = abs(r["value"]) / maxabs * half
        neg = r["value"] < 0
        x = cx - w if neg else cx
        lbl = f"left:{cx+22}px;text-align:left;" if neg else f"right:{W-cx+22}px;text-align:right;"
        frows.append(
            f'<div class="ix-row" id="{cid}-row{i}" style="top:{y}px;">'
            f'<div class="ix-bar" id="{cid}-bar{i}" style="left:{x:.0f}px;width:{w:.0f}px;background:{r["color"]};box-shadow:0 0 20px {r["color"]}55;transform-origin:{"right" if neg else "left"} center;"></div>'
            f'<div class="ix-lbl" style="{lbl}"><span class="ix-nm">{esc(r["label"])}</span> '
            f'<span class="ix-vl mono" id="{cid}-vl{i}" style="color:{r["color"]};">{r["value"]:+.2f}</span></div></div>')
        t = tline(line_hdr, 0.28 + 0.52 * (i / max(1, len(rows) - 1)))
        fjs.append(
            f"tl.fromTo('#{cid}-bar{i}', {{scaleX:0}}, {{scaleX:1, duration:0.6, ease:'expo.out', immediateRender:false}}, {t});"
            f"counter('#{cid}-vl{i}', 0, {r['value']}, {t}, 0.6, 2, '{'+' if r['value']>0 else ''}', '');")
    # --- gamma panel ---
    g = ix["gamma"]; neg = g["net_gex_m"] < 0
    gcol = "#ef4444" if neg else "#22c55e"
    gword = "ÂM · khuếch đại" if neg else "DƯƠNG · kìm nén"
    spot_above = g["spot"] >= g["flip"]
    t_hdr = tline(line_hdr, 0.04)
    t_gpanel = tline(line_gamma, 0.05)
    t_gex = tline(line_gamma, 0.2)
    t_lv = tline(line_gamma, 0.5)
    t_em = tline(line_gamma, 0.8)
    pos = (sc + 100) / 200 * 100
    css = f"""
.ix-hd{{position:absolute;left:60px;right:60px;top:250px;}}
.ix-tk{{display:inline-block;font-size:30px;font-weight:900;letter-spacing:2px;color:#fff;background:{acc};padding:8px 20px;border-radius:12px;}}
.ix-nm2{{display:inline-block;margin-left:14px;font-size:40px;font-weight:900;color:{acc};vertical-align:middle;}}
.ix-sc{{position:absolute;right:60px;top:250px;text-align:right;}}
.ix-sc .v{{font-family:'JBM';font-weight:800;font-size:72px;line-height:1;color:{regime_col(sc)};}}
.ix-sc .r{{font-size:24px;font-weight:800;letter-spacing:2px;color:#94a3b8;}}
.ix-scbar{{position:absolute;left:60px;right:60px;top:410px;height:12px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.ix-scmk{{position:absolute;top:-10px;left:{pos:.1f}%;width:8px;height:32px;margin-left:-4px;border-radius:5px;background:#fff;box-shadow:0 0 14px #fff;}}
.ix-axis{{position:absolute;left:539px;top:452px;width:3px;height:{6*rh-10}px;background:linear-gradient(180deg,transparent,rgba(255,255,255,.4) 10%,rgba(255,255,255,.4) 90%,transparent);}}
.ix-row{{position:absolute;left:0;right:0;height:62px;}}
.ix-bar{{position:absolute;top:16px;height:30px;border-radius:8px;}}
.ix-lbl{{position:absolute;top:6px;width:430px;}}
.ix-nm{{font-size:24px;font-weight:700;color:#cbd5e1;}}
.ix-vl{{font-size:30px;font-weight:800;margin-left:8px;}}
.ix-side{{position:absolute;top:430px;font-size:22px;font-weight:800;letter-spacing:2px;}}
.ix-gp{{position:absolute;left:60px;right:60px;top:{top0+6*rh+20}px;border-radius:22px;border:2px solid {gcol}88;background:linear-gradient(135deg,{gcol}18,rgba(15,23,42,.6));padding:22px 26px;}}
.ix-gp .row1{{display:flex;justify-content:space-between;align-items:center;}}
.ix-gp .gk{{font-size:30px;font-weight:900;color:{gcol};letter-spacing:1px;}}
.ix-gp .gex{{font-family:'JBM';font-weight:800;font-size:34px;color:{gcol};}}
.ix-lvls{{display:flex;justify-content:space-between;margin-top:18px;gap:10px;}}
.ix-lv{{flex:1;text-align:center;border-radius:12px;padding:12px 6px;background:rgba(255,255,255,.05);}}
.ix-lv .k{{font-size:20px;font-weight:800;letter-spacing:1px;}}
.ix-lv .v{{font-family:'JBM';font-weight:800;font-size:30px;margin-top:4px;color:#fff;}}
.ix-em{{margin-top:16px;font-size:26px;font-weight:700;color:#e2e8f0;}}
.ix-em b{{font-family:'JBM';color:#fde68a;}}
"""
    lv = lambda k, label, col: f'<div class="ix-lv"><div class="k" style="color:{col};">{label}</div><div class="v">{g[k]:g}</div></div>'
    body = f"""
<div id="{cid}-stage">
  <div class="ix-hd"><span class="ix-tk">{esc(ix['ticker'])}</span><span class="ix-nm2">{esc(ix['name'])}</span></div>
  <div class="ix-sc"><div class="v" id="{cid}-score">{sc:+.1f}</div><div class="r">{esc(ix['regime'])}</div></div>
  <div class="ix-scbar"><div class="ix-scmk"></div></div>
  <div class="ix-side" style="left:70px;color:#f87171;">◀ KÉO XUỐNG</div>
  <div class="ix-side" style="right:70px;color:#4ade80;">NÂNG ĐỠ ▶</div>
  <div class="ix-axis" id="{cid}-axis"></div>
  {''.join(frows)}
  <div class="ix-gp" id="{cid}-gp">
    <div class="row1"><div class="gk">GAMMA {gword}</div><div class="gex"><span style="font-size:22px;color:#94a3b8;">Net GEX </span><span id="{cid}-gex">$0M</span></div></div>
    <div class="ix-lvls">
      {lv('put','PUT WALL','#f87171')}
      {lv('flip','GAMMA FLIP','#fbbf24')}
      {lv('spot','SPOT '+esc(g.get('underlying','')),'#fff')}
      {lv('call','CALL WALL','#4ade80')}
    </div>
    <div class="ix-em" id="{cid}-em">Spot <b>{g['spot']:g}</b> {'TRÊN' if spot_above else 'DƯỚI'} Gamma Flip · biến động kỳ vọng ± <b>{g['expected_move']:g}</b></div>
  </div>
</div>"""
    js = f"""
gsap.set('#{cid}-gp, #{cid}-em', {{opacity:0}});
tl.fromTo('#{cid}-hd, #{cid}-stage .ix-hd', {{opacity:0, y:-40}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out'}}, {t_hdr});
tl.fromTo('#{cid}-stage .ix-sc', {{opacity:0, x:40}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out'}}, {t_hdr});
counter('#{cid}-score', 0, {sc}, {t_hdr+0.1}, 0.7, 1, '{'+' if sc>0 else ''}', '');
tl.fromTo('#{cid}-stage .ix-scbar', {{scaleX:0}}, {{scaleX:1, duration:0.6, ease:'power2.out', transformOrigin:'left center'}}, {t_hdr});
tl.fromTo('#{cid}-axis', {{scaleY:0}}, {{scaleY:1, duration:0.6, ease:'power2.inOut', transformOrigin:'center top'}}, {t_hdr+0.2});
{''.join(fjs)}
tl.fromTo('#{cid}-gp', {{opacity:0, y:40, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.45, ease:'expo.out', immediateRender:false}}, {t_gpanel});
counter('#{cid}-gex', 0, {g['net_gex_m']}, {t_gex}, 1.0, 0, '$', 'M');
tl.fromTo('#{cid}-em', {{opacity:0}}, {{opacity:1, duration:0.4, immediateRender:false}}, {t_em});
tl.to('#{cid}-stage', {{opacity:0, y:-100, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ============================================================= SCENE 3 COMPARE + SCENARIOS
def scene_cmp():
    st, en = SCENES[3][1], SCENES[3][2]
    dur = round(en - st, 3)
    spx, nas = IDX["spx"], IDX["nas"]
    dv = D.get("divergence_tag") or ""
    cards = []; js = []
    for i, s in enumerate(D.get("scenarios", [])[:3]):
        y = 980 + i * 0  # scenarios laid horizontally
        t = tline(5, 0.45 + i * 0.16)
        cards.append(
            f'<div class="cs-card" id="cs-{i}" style="left:{60 + i*((W-120)//3)}px;width:{(W-120)//3 - 16}px;border-color:{s["color"]}99;">'
            f'<div class="cs-p mono" id="cs-p{i}" style="color:{s["color"]};">0%</div>'
            f'<div class="cs-n" style="color:{s["color"]};">{esc(s["name"])}</div></div>')
        js.append(f"tl.fromTo('#cs-{i}', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t-0.1});"
                  f"counter('#cs-p{i}', 0, {int(s['pct'])}, {t}, 0.9, 0, '', '%');")
    def col(ix):
        return (f'<div class="cmp-col" style="border-color:{COLOR[ix["key"]]}66;">'
                f'<div class="cmp-h" style="color:{COLOR[ix["key"]]};">{esc(ix["name"])}</div>'
                f'<div class="cmp-r"><span>Ngày</span><b style="color:{regime_col(ix.get("day_score",ix["score"]))};">{ix.get("day_score",ix["score"]):+.1f}</b></div>'
                f'<div class="cmp-r"><span>Tuần</span><b style="color:{regime_col(ix.get("week_score",ix["score"]))};">{ix.get("week_score",ix["score"]):+.1f}</b></div>'
                f'<div class="cmp-r"><span>Gamma</span><b style="color:{"#f87171" if ix["gamma"]["net_gex_m"]<0 else "#4ade80"};">{"ÂM" if ix["gamma"]["net_gex_m"]<0 else "DƯƠNG"}</b></div></div>')
    css = f"""
.cmp-wrap{{position:absolute;left:60px;right:60px;top:420px;display:flex;gap:24px;}}
.cmp-col{{flex:1;border:2px solid;border-radius:22px;background:rgba(15,23,42,.55);padding:22px 24px;}}
.cmp-h{{font-size:34px;font-weight:900;text-align:center;margin-bottom:14px;}}
.cmp-r{{display:flex;justify-content:space-between;align-items:center;font-size:27px;font-weight:700;color:#cbd5e1;padding:10px 0;border-top:1px solid rgba(255,255,255,.08);}}
.cmp-r b{{font-family:'JBM';font-size:34px;}}
.cs-dv{{position:absolute;left:60px;right:60px;top:800px;text-align:center;font-size:29px;font-weight:800;line-height:1.35;padding:18px 24px;border-radius:18px;border:2px solid rgba(167,139,250,.5);background:rgba(167,139,250,.12);color:#ddd6fe;}}
.cs-dv b{{color:#fff;}}
.cs-ttl{{position:absolute;left:60px;right:60px;top:1010px;text-align:center;font-size:28px;font-weight:800;color:#94a3b8;letter-spacing:2px;}}
.cs-card{{position:absolute;top:1070px;height:150px;border:2px solid;border-radius:20px;background:rgba(15,23,42,.6);text-align:center;}}
.cs-p{{font-size:60px;font-weight:800;margin-top:18px;}}
.cs-n{{font-size:22px;font-weight:800;text-transform:uppercase;line-height:1.1;padding:0 8px;}}
"""
    body = f"""
<div id="cmp-stage">
  <div class="ttl" id="cmp-ttl"><span class="sky">So sánh</span> & phân kỳ</div>
  <div class="cmp-wrap" id="cmp-wrap">{col(spx)}{col(nas)}</div>
  <div class="cs-dv" id="cs-dv">{dv}</div>
  <div class="cs-ttl">KỊCH BẢN PHIÊN TỚI</div>
  {''.join(cards)}
</div>"""
    jj = f"""
tl.fromTo('#cmp-ttl', {{opacity:0, y:-40, filter:'blur(10px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#cmp-wrap', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:'expo.out'}}, {tline(5,0.08)-st if tline(5,0.08)>st else 0.2});
tl.fromTo('#cs-dv', {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(1.5)', immediateRender:false}}, {tline(5,0.3)});
{''.join(js)}
tl.to('#cmp-stage', {{opacity:0, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "cmp", dur, scene_file("cmp", dur, css, body, jj)


# ============================================================= SCENE 4 CTA
def scene_cta():
    st, en = SCENES[4][1], SCENES[4][2]
    dur = round(en - st, 3)
    t_f = tline(6, 0.25)
    css = """
.ct{position:absolute;left:0;right:0;top:470px;text-align:center;}
.ct img{width:170px;height:170px;filter:drop-shadow(0 0 30px rgba(56,189,248,.6));}
.ct-h{font-family:'JBM';font-weight:800;font-size:78px;margin-top:18px;background:linear-gradient(135deg,#fde047,#f59e0b 50%,#38bdf8);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ct-s{font-size:31px;font-weight:700;color:#cbd5e1;margin-top:10px;}
.ct-p{display:flex;gap:14px;justify-content:center;margin-top:26px;}
.ct-p span{font-family:'JBM';font-weight:800;font-size:27px;color:#7dd3fc;border:2px solid rgba(56,189,248,.5);border-radius:12px;padding:8px 18px;background:rgba(56,189,248,.08);}
.ct-aur{position:absolute;left:0;right:0;top:1040px;display:flex;align-items:center;justify-content:center;gap:16px;font-size:29px;font-weight:800;color:#c4b5fd;}
.ct-aur img{width:60px;height:60px;}
.ct-d{position:absolute;left:70px;right:70px;top:1140px;text-align:center;font-size:26px;line-height:1.4;color:#bfdbfe;padding:14px 18px;border:1px solid rgba(56,189,248,.3);border-radius:14px;background:rgba(255,255,255,.03);}
.ct-d b{color:#fff;}
"""
    body = f"""
<div id="ct-stage">
  <div class="ct"><img src="assets/img/logo-kenvinzone.svg" alt=""/>
    <div class="ct-h">@kenvinzone</div>
    <div class="ct-s">Follow để nhận Bias Chứng khoán Mỹ mỗi {esc(D.get('cadence_word','phiên'))}</div>
    <div class="ct-p"><span>TikTok</span><span>Shorts</span><span>Reels</span><span>YouTube</span></div>
  </div>
  <div class="ct-aur" id="ct-aur"><img src="assets/img/logo-aurora.svg" alt=""/>Xác nhận tín hiệu cùng AURORA</div>
  <div class="ct-d" id="ct-d">⚠️ Phân tích định lượng mang tính giáo dục, <b>không phải lời khuyên đầu tư</b>. Nguồn: Market Bias Platform · KenvinZone Analytics</div>
</div>"""
    js = f"""
gsap.set('#ct-aur, #ct-d', {{opacity:0}});
tl.fromTo('#ct-stage .ct', {{opacity:0, scale:1.08, filter:'blur(12px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'expo.out'}}, {max(0.1, t_f-0.2)});
tl.fromTo('#ct-aur', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_f+0.3});
tl.fromTo('#ct-d', {{opacity:0}}, {{opacity:1, duration:0.4, immediateRender:false}}, {t_f+0.6});
"""
    return "cta", dur, scene_file("cta", dur, css, body, js)


# ============================================================= CAPTIONS
def captions():
    groups = []; js = []
    for gi, c in enumerate(SUBS["captions"]):
        s = round(c["start"] + OFF, 3); e = round(c["end"] + OFF, 3)
        nxt = SUBS["captions"][gi + 1]["start"] + OFF if gi + 1 < len(SUBS["captions"]) else e + 0.6
        e2 = round(min(max(e + 0.25, e), nxt - 0.02), 3)
        ws = "".join(f'<span class="cw" id="cw{gi}_{wi}">{esc(w["text"])}</span> ' for wi, w in enumerate(c["words"]))
        groups.append(f'<div class="cg" id="cg{gi}"><div class="cpill">{ws}</div></div>')
        js.append(f"tl.set('#cg{gi}', {{opacity:1, visibility:'visible'}}, {s});"
                  f"tl.fromTo('#cg{gi} .cpill', {{y:18, opacity:0}}, {{y:0, opacity:1, duration:0.14, ease:'power3.out', immediateRender:false}}, {s});")
        for wi, w in enumerate(c["words"]):
            ws_ = round(w["start"] + OFF, 3)
            js.append(f"tl.fromTo('#cw{gi}_{wi}', {{color:'#cbd5e1', backgroundColor:'rgba(56,189,248,0)'}}, {{color:'#0b0f19', backgroundColor:'rgba(125,211,252,1)', duration:0.06, immediateRender:false}}, {ws_});"
                      f"tl.to('#cw{gi}_{wi}', {{color:'#ffffff', backgroundColor:'rgba(56,189,248,0)', duration:0.06}}, {round(max(w['end'], w['start'] + 0.07) + OFF, 3)});")
        js.append(f"tl.to('#cg{gi} .cpill', {{opacity:0, duration:0.1, ease:'power2.in'}}, {e2 - 0.1});"
                  f"tl.set('#cg{gi}', {{opacity:0, visibility:'hidden'}}, {e2});")
    css = """
.cg{position:absolute;left:0;right:0;top:1660px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;max-width:960px;padding:14px 26px;border-radius:22px;background:rgba(2,6,23,.72);border:1px solid rgba(255,255,255,.08);font-size:42px;font-weight:800;line-height:1.35;color:#cbd5e1;}
.cw{display:inline-block;padding:0 6px;border-radius:10px;}
"""
    return "captions", TOTAL, scene_file("captions", TOTAL, css, "\n".join(groups), "\n".join(js))


# ============================================================= ROOT
def root(scene_meta):
    hosts = "\n".join(
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{stt}" data-duration="{dd}" '
        f'data-track-index="{i+2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{10+i};"></div>'
        for i, (cid, stt, dd) in enumerate(scene_meta))
    sfx = []; k = 0
    def add(file, t, vol):
        nonlocal k
        sfx.append(f'<audio id="sfx{k}" class="clip" src="assets/audio/{file}" data-start="{max(0, round(t,3))}" data-duration="{SFX_LEN[file]}" data-volume="{vol}" data-track-index="{40+k}"></audio>')
        k += 1
    for cid, stt, dd in scene_meta[1:]:
        if cid != "captions":
            add("whoosh.mp3", stt - 0.25, 0.45)
    # ticks on each force reveal + impact on each index score
    for key in ("spx", "nas"):
        add("impact.mp3", tline(1 if key == "spx" else 3, 0.1), 0.5)
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
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 28%,#0f1626 0%,#060a13 60%,#03050a 100%);}}
#bgc{{position:absolute;inset:0;width:{W}px;height:{H}px;}}
.glow{{position:absolute;left:-200px;right:-200px;top:160px;height:1000px;filter:blur(120px);background:radial-gradient(circle at 50% 40%,rgba(56,189,248,.22),rgba(99,102,241,.10) 40%,transparent 70%);}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:150px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:40px;height:40px;}}
.brand .n{{font-size:27px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:27px;color:#7dd3fc;letter-spacing:1px;}}
.prog{{position:absolute;left:60px;right:60px;top:200px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,#38bdf8,#818cf8);transform-origin:left center;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="glow"></div>
  <canvas id="bgc" width="{W}" height="{H}"></canvas>
  <div class="vig"></div>
  <div class="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">KENVINZONE · MARKET BIAS</span><span class="d">{esc(D['date'])}</span></div>
  <div class="prog"><div id="progf"></div></div>
{hosts}
  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{OFF}" data-volume="1" data-track-index="30"></audio>
  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{D.get('bgm_volume', 0.16)}" data-fade-out="2" data-track-index="31"></audio>
  {''.join(sfx)}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
const cv = document.getElementById('bgc'); const ctx = cv.getContext('2d');
let seed = 20261103; const rnd = () => {{ seed = (seed*1664525+1013904223)%4294967296; return seed/4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.15)}, CW = w/9, SPEED = {D.get('bg_speed', 95)};
const N = Math.ceil(({TOTAL}*SPEED + w)/CW)+3, CS=[]; let mid = h*0.70;
for(let i=0;i<N;i++){{ mid += (rnd()-0.5)*h*0.10; mid=Math.max(h*0.5,Math.min(h*0.88,mid));
  const up=rnd()>0.5, bh=h*(0.035+rnd()*0.075); const o=up?mid+bh/2:mid-bh/2, c=up?mid-bh/2:mid+bh/2;
  CS.push({{o,c,hi:Math.min(o,c)-h*(0.015+rnd()*0.03),lo:Math.max(o,c)+h*(0.015+rnd()*0.03),up}}); }}
function draw(t){{
  const C='56,189,248';
  ctx.clearRect(0,0,w,h);
  ctx.strokeStyle='rgba('+C+','+(A*0.22)+')'; ctx.lineWidth=1;
  for(let i=1;i<6;i++){{ const gx=w*i/6; ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,h); ctx.stroke(); }}
  for(let i=1;i<11;i++){{ const gy=h*i/11; ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(w,gy); ctx.stroke(); }}
  const off=t*SPEED, i0=Math.max(0,Math.floor(off/CW)-1), i1=Math.min(N-1,i0+Math.ceil(w/CW)+2);
  ctx.beginPath();
  for(let i=i0;i<=i1;i++){{ const kk=CS[i], x=i*CW-off+CW/2, y=(kk.o+kk.c)/2; i===i0?ctx.moveTo(x,y):ctx.lineTo(x,y); }}
  ctx.strokeStyle='rgba('+C+','+(A*1.5)+')'; ctx.lineWidth=3; ctx.stroke();
  const line='rgba('+C+','+(A*1.15)+')';
  for(let i=i0;i<=i1;i++){{ const kk=CS[i], x0=i*CW-off, bx=x0+CW*0.5, top=Math.min(kk.o,kk.c), bh=Math.abs(kk.o-kk.c)||2, bw=CW*0.56, blft=x0+CW*0.22, bot=top+bh;
    ctx.strokeStyle=line; ctx.lineWidth=2.4; ctx.beginPath(); ctx.moveTo(bx,kk.hi); ctx.lineTo(bx,top); ctx.moveTo(bx,bot); ctx.lineTo(bx,kk.lo); ctx.stroke();
    if(kk.up){{ ctx.lineWidth=2.6; ctx.strokeRect(blft,top,bw,bh); }} else {{ ctx.fillStyle='rgba('+C+','+(A*0.9)+')'; ctx.fillRect(blft,top,bw,bh); }} }}
}}
const P={{t:0}}; draw(0);
tl.fromTo(P,{{t:0}},{{t:{TOTAL},duration:{TOTAL},ease:'none',onUpdate(){{draw(P.t);}}}},0);
tl.fromTo('#progf',{{scaleX:0}},{{scaleX:1,duration:{TOTAL},ease:'none'}},0);
window.__timelines["main"]=tl;
}})();
</script>
</body>
</html>
"""


def main():
    comps = ROOT / "compositions"
    comps.mkdir(exist_ok=True)
    meta = []
    builders = [scene_hook,
                lambda: scene_index("spx", 1, 2),
                lambda: scene_index("nas", 3, 4),
                scene_cmp, scene_cta]
    for fn in builders:
        cid, dur, txt = fn()
        stt = next(s for c, s, e in SCENES if c == cid)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(stt, 3), dur))
    if D.get("captions", True):
        cid, dur, txt = captions()
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    html_root = root(meta)
    html_root = html_root.replace('data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:15;"',
                                  'data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:50;"')
    (ROOT / "index.html").write_text(html_root, encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
