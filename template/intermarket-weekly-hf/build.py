#!/usr/bin/env python3
"""KenvinZone — Inter-market Weekly Bias (S&P 500 + Nasdaq + Vàng) -> HyperFrames.

Tổng kết liên thị trường tuần: hook (composite + 3 tài sản) -> lực vĩ mô chung ->
khối S&P 500 -> khối Nasdaq -> khối Vàng -> dòng tiền luân chuyển -> 3 kịch bản -> CTA.
8 dòng script = 8 slide. Mốc hiện hình tính theo mốc slide (tương đối) nên bền.
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
NLINES = 8
if len(SLIDES) != NLINES:
    raise SystemExit(f"Template intermarket-weekly can dung {NLINES} dong script (dang co {len(SLIDES)}).")


def slide_start(i):
    return round(SLIDES[i]["start"] + OFF, 3) if i > 0 else 0.0


def tline(line, frac, base=0.0):
    s = float(SLIDES[line]["start"]); d = float(SLIDES[line]["duration"])
    return round(s + max(0.0, min(1.0, frac)) * d + OFF - base, 3)


S = [slide_start(i) for i in range(NLINES)]
SCENES = [("hook", S[0], S[1]), ("macro", S[1], S[2]), ("spx", S[2], S[3]), ("nas", S[3], S[4]),
          ("gold", S[4], S[5]), ("rot", S[5], S[6]), ("scen", S[6], S[7]), ("cta", S[7], TOTAL)]
SC_LINE = {"hook": 0, "macro": 1, "spx": 2, "nas": 3, "gold": 4, "rot": 5, "scen": 6, "cta": 7}

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
.ttl{position:absolute;left:70px;right:70px;top:250px;font-weight:900;font-size:56px;line-height:1.12;letter-spacing:-0.5px;text-transform:uppercase;}
.sub{position:absolute;left:70px;right:70px;top:328px;font-weight:600;font-size:27px;color:#94a3b8;}
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
ASSETS = D["assets"]           # [spx, nas, gold]
AMAP = {a["key"]: a for a in ASSETS}


def regime_col(score):
    return "#4ade80" if score > 3 else ("#f87171" if score < -3 else "#fbbf24")


# ===================================================== SCENE 0 HOOK (composite + 3 gauges)
def scene_hook():
    st, en = SCENES[0][1], SCENES[0][2]
    dur = round(en - st, 3)
    comp = D["composite"]; cs = comp["score"]; cpos = (cs + 100) / 200 * 100
    def mini(a, cx):
        sc = a["score"]; pos = (sc + 100) / 200 * 100
        return (f'<div class="hk-m" style="left:{cx-165}px;width:330px;">'
                f'<div class="hk-mn" style="color:{a["accent"]};">{esc(a["name"])}</div>'
                f'<div class="hk-mv mono" id="hk-{a["key"]}" style="color:{regime_col(sc)};">{sc:+.1f}</div>'
                f'<div class="hk-mb"><div class="hk-mmk" style="left:{pos:.1f}%;"></div></div></div>')
    css = f"""
.hk-eyebrow{{position:absolute;top:248px;left:0;right:0;display:flex;justify-content:center;}}
.hk-eyebrow span{{background:linear-gradient(135deg,#38bdf8,#6366f1);color:#fff;font-weight:900;font-size:26px;letter-spacing:3px;padding:14px 32px;border-radius:99px;box-shadow:0 10px 40px rgba(99,102,241,.45);}}
.hk-title{{position:absolute;top:356px;left:60px;right:60px;text-align:center;}}
.hk-title h1{{font-size:58px;font-weight:900;line-height:1.14;letter-spacing:-1px;}}
.hk-date{{position:absolute;top:548px;left:0;right:0;text-align:center;}}
.hk-date span{{font-family:'JBM';font-weight:800;font-size:26px;color:#7dd3fc;border:2px solid rgba(56,189,248,.45);padding:8px 22px;border-radius:99px;background:rgba(56,189,248,.08);letter-spacing:1px;}}
.hk-comp{{position:absolute;top:620px;left:0;right:0;text-align:center;}}
.hk-cl{{font-size:26px;font-weight:800;letter-spacing:3px;color:#94a3b8;}}
.hk-cv{{font-family:'JBM';font-weight:800;font-size:120px;line-height:1.02;color:{regime_col(cs)};}}
.hk-cr{{font-size:30px;font-weight:900;letter-spacing:2px;color:#cbd5e1;margin-top:-6px;}}
.hk-cbar{{position:relative;margin:10px auto 0;width:720px;height:14px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.hk-cmk{{position:absolute;top:-12px;left:{cpos:.1f}%;width:9px;height:38px;margin-left:-4px;border-radius:5px;background:#fff;box-shadow:0 0 16px #fff;}}
.hk-m{{position:absolute;top:1010px;text-align:center;}}
.hk-mn{{font-size:30px;font-weight:900;}}
.hk-mv{{font-family:'JBM';font-weight:800;font-size:60px;line-height:1.1;}}
.hk-mb{{position:relative;margin:4px auto 0;width:260px;height:10px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.hk-mmk{{position:absolute;top:-9px;width:7px;height:28px;margin-left:-3px;border-radius:4px;background:#fff;box-shadow:0 0 12px #fff;}}
"""
    body = f"""
<div class="hk-stage" id="hk-stage">
  <div class="hk-eyebrow"><span>{esc(D.get('eyebrow') or '⚡ WEEKLY · LIÊN THỊ TRƯỜNG')}</span></div>
  <div class="hk-title"><h1>{D.get('title_html','TỔNG KẾT LIÊN THỊ TRƯỜNG')}</h1></div>
  <div class="hk-date"><span>{esc(D.get('date_prefix') or 'TUẦN · đến')} {esc(D['date'])}</span></div>
  <div class="hk-comp" id="hk-comp">
    <div class="hk-cl">ĐIỂM COMPOSITE LIÊN THỊ TRƯỜNG</div>
    <div class="hk-cv"><span id="hk-compv">{cs:+.1f}</span></div>
    <div class="hk-cr">{esc(comp['regime'])}</div>
    <div class="hk-cbar"><div class="hk-cmk"></div></div>
  </div>
  {mini(AMAP['spx'], 230)}
  {mini(AMAP['nas'], 540)}
  {mini(AMAP['gold'], 850)}
</div>"""
    t_c = tline(0, 0.35, st)
    t_m = tline(0, 0.72, st)
    js = f"""
counter('#hk-compv', 0, {cs}, {t_c}, 0.8, 1, '{'+' if cs>0 else ''}', '');
tl.fromTo('#hk-comp .hk-cv', {{scale:1.3}}, {{scale:1, duration:0.5, ease:'back.out(2)', immediateRender:false}}, {t_c});
tl.fromTo('#hk-comp .hk-cmk', {{left:'50%'}}, {{left:'{cpos:.1f}%', duration:0.6, ease:'power3.out', immediateRender:false}}, {t_c});
["spx","nas","gold"].forEach((k,i)=>{{
  tl.fromTo('#hk-'+k, {{scale:1.2, opacity:0}}, {{scale:1, opacity:1, duration:0.4, ease:'back.out(1.6)', immediateRender:false}}, {t_m} + i*0.18);
}});
counter('#hk-spx', 0, {AMAP['spx']['score']}, {t_m}, 0.5, 1, '{'+' if AMAP['spx']['score']>0 else ''}', '');
counter('#hk-nas', 0, {AMAP['nas']['score']}, {t_m}+0.18, 0.5, 1, '{'+' if AMAP['nas']['score']>0 else ''}', '');
counter('#hk-gold', 0, {AMAP['gold']['score']}, {t_m}+0.36, 0.5, 1, '{'+' if AMAP['gold']['score']>0 else ''}', '');
tl.to('#hk-stage', {{opacity:0, filter:'blur(10px)', scale:0.96, duration:0.28, ease:'power3.in'}}, {dur - 0.3});
"""
    return "hook", dur, scene_file("hook", dur, css, body, js)


# ===================================================== SCENE 1 MACRO (shared forces)
def scene_macro():
    st, en = SCENES[1][1], SCENES[1][2]
    dur = round(en - st, 3)
    rows = D["macro"]
    maxabs = max(abs(r["value"]) for r in rows) or 1.0
    half = 360; cx = 540; top0 = 470; rh = 86
    body_rows = []; js_rows = []
    for i, r in enumerate(rows):
        y = top0 + i * rh
        w = abs(r["value"]) / maxabs * half
        neg = r["value"] < 0
        x = cx - w if neg else cx
        lbl = f"left:{cx+22}px;text-align:left;" if neg else f"right:{W-cx+22}px;text-align:right;"
        body_rows.append(
            f'<div class="mc-row" id="mc-row{i}" style="top:{y}px;">'
            f'<div class="mc-bar" id="mc-bar{i}" style="left:{x:.0f}px;width:{w:.0f}px;background:{r["color"]};box-shadow:0 0 22px {r["color"]}55;transform-origin:{"right" if neg else "left"} center;"></div>'
            f'<div class="mc-lbl" style="{lbl}"><span class="mc-nm">{esc(r["label"])}</span> '
            f'<span class="mc-vl mono" id="mc-vl{i}" style="color:{r["color"]};">{r["value"]:+.2f}</span></div></div>')
        t = tline(1, 0.3 + 0.52 * (i / max(1, len(rows) - 1)), st)
        js_rows.append(
            f"tl.fromTo('#mc-bar{i}', {{scaleX:0}}, {{scaleX:1, duration:0.6, ease:'expo.out', immediateRender:false}}, {t});"
            f"counter('#mc-vl{i}', 0, {r['value']}, {t}, 0.6, 2, '{'+' if r['value']>0 else ''}', '');")
    css = f"""
.mc-axis{{position:absolute;left:539px;top:452px;width:3px;height:{len(rows)*rh-10}px;background:linear-gradient(180deg,transparent,rgba(255,255,255,.45) 10%,rgba(255,255,255,.45) 90%,transparent);}}
.mc-side{{position:absolute;top:430px;font-size:24px;font-weight:800;letter-spacing:2px;}}
.mc-row{{position:absolute;left:0;right:0;height:72px;}}
.mc-bar{{position:absolute;top:18px;height:36px;border-radius:9px;}}
.mc-lbl{{position:absolute;top:6px;width:430px;}}
.mc-nm{{font-size:27px;font-weight:700;color:#cbd5e1;}}
.mc-vl{{font-size:34px;font-weight:800;margin-left:8px;}}
"""
    body = f"""
<div id="mc-stage">
  <div class="ttl" id="mc-ttl"><span class="sky">Lực vĩ mô</span> chung</div>
  <div class="sub" id="mc-sub">Trung bình đóng góp trên S&amp;P 500 · Nasdaq · Vàng</div>
  <div class="mc-side" style="left:70px;color:#f87171;">◀ KÉO TOÀN TT</div>
  <div class="mc-side" style="right:70px;color:#4ade80;">NÂNG TOÀN TT ▶</div>
  <div class="mc-axis" id="mc-axis"></div>
  {''.join(body_rows)}
</div>"""
    js = f"""
tl.fromTo('#mc-ttl', {{opacity:0, filter:'blur(10px)'}}, {{opacity:1, filter:'blur(0px)', duration:0.3, ease:'power3.out'}}, 0.05);
tl.fromTo('#mc-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.25);
tl.fromTo('#mc-axis', {{scaleY:0}}, {{scaleY:1, duration:0.7, ease:'power2.inOut', transformOrigin:'center top'}}, 0.3);
{''.join(js_rows)}
tl.to('#mc-stage', {{opacity:0, y:-100, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "macro", dur, scene_file("macro", dur, css, body, js)


# ===================================================== ASSET MINI (spx / nas / gold)
def scene_asset(key):
    a = AMAP[key]; cid = key
    st = next(s for c, s, e in SCENES if c == cid)
    en = next(e for c, s, e in SCENES if c == cid)
    dur = round(en - st, 3)
    acc = a["accent"]; sc = a["score"]; pos = (sc + 100) / 200 * 100
    line = SC_LINE[cid]
    gneg = a["gamma_neg"]; gcol = "#f87171" if gneg else "#4ade80"
    gtxt = "GAMMA ÂM" if gneg else "GAMMA DƯƠNG"
    em = a.get("expected_move")
    t_hd = tline(line, 0.06, st)
    t_sup = tline(line, 0.4, st)
    t_drag = tline(line, 0.58, st)
    t_g = tline(line, 0.8, st)
    css = f"""
.as-hd{{position:absolute;left:60px;right:60px;top:300px;}}
.as-tk{{display:inline-block;font-size:30px;font-weight:900;letter-spacing:2px;color:#fff;background:{acc};padding:8px 20px;border-radius:12px;}}
.as-nm{{display:inline-block;margin-left:14px;font-size:44px;font-weight:900;color:{acc};vertical-align:middle;}}
.as-sc{{position:absolute;right:60px;top:300px;text-align:right;}}
.as-sc .v{{font-family:'JBM';font-weight:800;font-size:80px;line-height:1;color:{regime_col(sc)};}}
.as-sc .r{{font-size:25px;font-weight:800;letter-spacing:2px;color:#94a3b8;}}
.as-bar{{position:absolute;left:60px;right:60px;top:470px;height:14px;border-radius:99px;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#22c55e);}}
.as-mk{{position:absolute;top:-11px;left:{pos:.1f}%;width:9px;height:36px;margin-left:-4px;border-radius:5px;background:#fff;box-shadow:0 0 14px #fff;}}
.as-chip{{position:absolute;left:60px;right:60px;border-radius:20px;padding:26px 30px;font-size:34px;font-weight:800;display:flex;justify-content:space-between;align-items:center;}}
.as-chip .mono{{font-size:42px;}}
.as-sup{{top:580px;border:2px solid rgba(74,222,128,.5);background:rgba(74,222,128,.10);color:#bbf7d0;}}
.as-drag{{top:700px;border:2px solid rgba(248,113,113,.5);background:rgba(248,113,113,.10);color:#fecaca;}}
.as-g{{position:absolute;left:60px;right:60px;top:840px;border-radius:20px;border:2px solid {gcol}88;background:linear-gradient(135deg,{gcol}18,rgba(15,23,42,.6));padding:26px 30px;display:flex;justify-content:space-between;align-items:center;}}
.as-g .k{{font-size:34px;font-weight:900;color:{gcol};letter-spacing:1px;}}
.as-g .e{{font-family:'JBM';font-weight:800;font-size:30px;color:#fde68a;}}
"""
    em_html = f'<span class="e">biến động ± {em}</span>' if em else '<span class="e" style="color:#94a3b8;">XAUUSD</span>'
    body = f"""
<div id="{cid}-stage">
  <div class="as-hd"><span class="as-tk">{esc(a['ticker'])}</span><span class="as-nm">{esc(a['name'])}</span></div>
  <div class="as-sc"><div class="v" id="{cid}-score">{sc:+.1f}</div><div class="r">{esc(a['regime'])}</div></div>
  <div class="as-bar"><div class="as-mk" id="{cid}-mk"></div></div>
  <div class="as-chip as-sup" id="{cid}-sup"><span>▲ Đỡ nhiều nhất · {esc(a['support']['label'])}</span><span class="mono">{a['support']['value']:+.2f}</span></div>
  <div class="as-chip as-drag" id="{cid}-drag"><span>▼ Cản nhiều nhất · {esc(a['drag']['label'])}</span><span class="mono">{a['drag']['value']:+.2f}</span></div>
  <div class="as-g" id="{cid}-g"><span class="k">{gtxt}</span>{em_html}</div>
</div>"""
    js = f"""
gsap.set('#{cid}-sup, #{cid}-drag, #{cid}-g', {{opacity:0}});
tl.fromTo('#{cid}-stage .as-hd', {{opacity:0, y:-40}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out'}}, {t_hd});
tl.fromTo('#{cid}-stage .as-sc', {{opacity:0, x:40}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out'}}, {t_hd});
counter('#{cid}-score', 0, {sc}, {t_hd+0.1}, 0.7, 1, '{'+' if sc>0 else ''}', '');
tl.fromTo('#{cid}-score', {{scale:1.3}}, {{scale:1, duration:0.5, ease:'back.out(2)', immediateRender:false}}, {t_hd+0.1});
tl.fromTo('#{cid}-stage .as-bar', {{scaleX:0}}, {{scaleX:1, duration:0.6, ease:'power2.out', transformOrigin:'left center'}}, {t_hd});
tl.fromTo('#{cid}-mk', {{left:'50%'}}, {{left:'{pos:.1f}%', duration:0.6, ease:'power3.out', immediateRender:false}}, {t_hd+0.1});
tl.fromTo('#{cid}-sup', {{opacity:0, x:-50}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_sup});
tl.fromTo('#{cid}-drag', {{opacity:0, x:50}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_drag});
tl.fromTo('#{cid}-g', {{opacity:0, y:30, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out', immediateRender:false}}, {t_g});
tl.to('#{cid}-stage', {{opacity:0, y:-90, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return cid, dur, scene_file(cid, dur, css, body, js)


# ===================================================== SCENE 5 ROTATION
def scene_rot():
    st, en = SCENES[5][1], SCENES[5][2]
    dur = round(en - st, 3)
    tag = D.get("rotation_tag") or "Dòng tiền luân chuyển giữa các nhóm tài sản."
    css = """
.rt-ic{position:absolute;left:0;right:0;top:430px;text-align:center;font-size:150px;line-height:1;}
.rt-card{position:absolute;left:70px;right:70px;top:700px;border-radius:24px;border:2px solid rgba(56,189,248,.5);background:rgba(56,189,248,.10);padding:40px 36px;text-align:center;font-size:40px;font-weight:800;line-height:1.4;color:#e0f2fe;}
.rt-card b{color:#fff;}
.rt-flow{position:absolute;left:70px;right:70px;top:1010px;display:flex;justify-content:center;gap:20px;}
.rt-flow span{font-size:27px;font-weight:800;color:#cbd5e1;border:2px solid rgba(255,255,255,.14);border-radius:14px;padding:12px 20px;background:rgba(255,255,255,.04);}
"""
    body = f"""
<div id="rt-stage">
  <div class="ttl" id="rt-ttl"><span class="sky">Dòng tiền</span> luân chuyển</div>
  <div class="rt-ic" id="rt-ic">🔄</div>
  <div class="rt-card" id="rt-card">{tag}</div>
  <div class="rt-flow" id="rt-flow"><span>Tấn công ➜ Phòng thủ</span><span>Chờ tín hiệu USD</span></div>
</div>"""
    t_c = tline(5, 0.3, st)
    js = f"""
gsap.set('#rt-card, #rt-flow', {{opacity:0}});
tl.fromTo('#rt-ttl', {{opacity:0, y:-40, filter:'blur(10px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#rt-ic', {{scale:0.4, opacity:0, rotation:-120}}, {{scale:1, opacity:1, rotation:0, duration:0.7, ease:'back.out(1.6)'}}, 0.2);
tl.to('#rt-ic', {{rotation:360, duration:{max(2.0, dur-1.5)}, ease:'none'}}, 0.9);
tl.fromTo('#rt-card', {{opacity:0, y:40, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.5, ease:'expo.out', immediateRender:false}}, {t_c});
tl.fromTo('#rt-flow', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {t_c+0.4});
tl.to('#rt-stage', {{opacity:0, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "rot", dur, scene_file("rot", dur, css, body, js)


# ===================================================== SCENE 6 SCENARIOS
def scene_scen():
    st, en = SCENES[6][1], SCENES[6][2]
    dur = round(en - st, 3)
    cards = []; js = []
    for i, s in enumerate(D.get("scenarios", [])[:3]):
        t = tline(6, 0.3 + i * 0.2, st)
        y = 520 + i * 240
        cards.append(
            f'<div class="sc-card" id="sc-c{i}" style="top:{y}px;border-color:{s["color"]}99;background:linear-gradient(135deg,{s["color"]}1e,rgba(15,23,42,.6));">'
            f'<div class="sc-p mono" id="sc-p{i}" style="color:{s["color"]};">0%</div>'
            f'<div class="sc-n" style="color:{s["color"]};">{esc(s["name"])}</div></div>')
        js.append(f"tl.fromTo('#sc-c{i}', {{opacity:0, x:{-120 if i%2==0 else 120}}}, {{opacity:1, x:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {t-0.15});"
                  f"counter('#sc-p{i}', 0, {int(s['pct'])}, {t}, 1.0, 0, '', '%');")
    css = """
.sc-card{position:absolute;left:60px;right:60px;height:210px;border:2px solid;border-radius:26px;display:flex;align-items:center;padding:0 40px;gap:36px;}
.sc-p{font-size:96px;font-weight:800;min-width:230px;}
.sc-n{font-size:40px;font-weight:900;text-transform:uppercase;line-height:1.15;}
"""
    body = f"""
<div id="sc-stage">
  <div class="ttl" id="sc-ttl"><span class="amber">3 kịch bản</span> tuần tới</div>
  <div class="sub" id="sc-sub">Xác suất từ mô hình Market Bias liên thị trường</div>
  {''.join(cards)}
</div>"""
    jj = f"""
tl.fromTo('#sc-ttl', {{opacity:0, x:120, filter:'blur(10px)'}}, {{opacity:1, x:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#sc-sub', {{opacity:0}}, {{opacity:1, duration:0.3}}, 0.3);
{''.join(js)}
tl.to('#sc-stage', {{opacity:0, x:-150, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});
"""
    return "scen", dur, scene_file("scen", dur, css, body, jj)


# ===================================================== SCENE 7 CTA
def scene_cta():
    st, en = SCENES[7][1], SCENES[7][2]
    dur = round(en - st, 3)
    t_f = tline(7, 0.25, st)
    css = """
.ct{position:absolute;left:0;right:0;top:470px;text-align:center;}
.ct img{width:170px;height:170px;filter:drop-shadow(0 0 30px rgba(56,189,248,.6));}
.ct-h{font-family:'JBM';font-weight:800;font-size:78px;margin-top:18px;background:linear-gradient(135deg,#fde047,#f59e0b 50%,#38bdf8);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ct-s{font-size:31px;font-weight:700;color:#cbd5e1;margin-top:10px;}
.ct-p{display:flex;gap:14px;justify-content:center;margin-top:26px;}
.ct-p span{font-family:'JBM';font-weight:800;font-size:27px;color:#7dd3fc;border:2px solid rgba(56,189,248,.5);border-radius:12px;padding:8px 18px;background:rgba(56,189,248,.08);}
.ct-aur{position:absolute;left:0;right:0;top:975px;display:flex;align-items:center;justify-content:center;gap:16px;font-size:29px;font-weight:800;color:#c4b5fd;}
.ct-aur img{width:60px;height:60px;}
.ct-d{position:absolute;left:70px;right:70px;top:1070px;text-align:center;font-size:26px;line-height:1.4;color:#bfdbfe;padding:14px 18px;border:1px solid rgba(56,189,248,.3);border-radius:14px;background:rgba(255,255,255,.03);}
.ct-d b{color:#fff;}
"""
    body = f"""
<div id="ct-stage">
  <div class="ct"><img src="assets/img/logo-kenvinzone.svg" alt=""/>
    <div class="ct-h">@kenvinzone</div>
    <div class="ct-s">Follow để nhận Bias liên thị trường mỗi tuần</div>
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


# ===================================================== CAPTIONS
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
.cg{position:absolute;left:0;right:0;top:1205px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;max-width:960px;padding:14px 26px;border-radius:22px;background:rgba(2,6,23,.78);border:1px solid rgba(255,255,255,.08);font-size:44px;font-weight:800;line-height:1.35;color:#cbd5e1;}
.cw{display:inline-block;padding:0 6px;border-radius:10px;}
"""
    return "captions", TOTAL, scene_file("captions", TOTAL, css, "\n".join(groups), "\n".join(js))


# ===================================================== ROOT
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
    # SFX dày: impact ở composite + 3 điểm tài sản; tick ở từng lực vĩ mô + từng kịch bản.
    add("impact.mp3", tline(0, 0.35), 0.55)                    # composite
    for i in range(3):
        add("impact.mp3", tline(0, 0.72) + i * 0.18, 0.4)      # 3 điểm tài sản
    nmac = len(D["macro"])
    for i in range(nmac):
        add("tick.mp3", tline(1, 0.3 + 0.52 * (i / max(1, nmac - 1))), 0.3)
    for key, ln in (("spx", 2), ("nas", 3), ("gold", 4)):
        add("impact.mp3", tline(ln, 0.16), 0.45)               # điểm từng tài sản
    for i in range(3):
        add("tick.mp3", tline(6, 0.3 + i * 0.2), 0.34)         # 3 kịch bản
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
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 28%,#111a2e 0%,#060a13 60%,#03050a 100%);}}
#bgc{{position:absolute;inset:0;width:{W}px;height:{H}px;}}
.glow{{position:absolute;left:-200px;right:-200px;top:160px;height:1000px;filter:blur(120px);background:radial-gradient(circle at 50% 40%,rgba(99,102,241,.22),rgba(56,189,248,.10) 40%,transparent 70%);}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:150px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:40px;height:40px;}}
.brand .n{{font-size:27px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:27px;color:#7dd3fc;letter-spacing:1px;}}
.prog{{position:absolute;left:60px;right:60px;top:200px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,#6366f1,#38bdf8);transform-origin:left center;}}
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
let seed = 20261108; const rnd = () => {{ seed = (seed*1664525+1013904223)%4294967296; return seed/4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.15)}, CW = w/9, SPEED = {D.get('bg_speed', 95)};
const N = Math.ceil(({TOTAL}*SPEED + w)/CW)+3, CS=[]; let mid = h*0.70;
for(let i=0;i<N;i++){{ mid += (rnd()-0.5)*h*0.10; mid=Math.max(h*0.5,Math.min(h*0.88,mid));
  const up=rnd()>0.5, bh=h*(0.035+rnd()*0.075); const o=up?mid+bh/2:mid-bh/2, c=up?mid-bh/2:mid+bh/2;
  CS.push({{o,c,hi:Math.min(o,c)-h*(0.015+rnd()*0.03),lo:Math.max(o,c)+h*(0.015+rnd()*0.03),up}}); }}
function draw(t){{
  const C='99,102,241';
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
    builders = [scene_hook, scene_macro,
                lambda: scene_asset("spx"), lambda: scene_asset("nas"), lambda: scene_asset("gold"),
                scene_rot, scene_scen, scene_cta]
    for fn in builders:
        cid, dur, txt = fn()
        stt = next(s for c, s, e in SCENES if c == cid)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(stt, 3), dur))
    if D.get("captions", True):
        cid, dur, txt = captions()
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    html_root = root(meta).replace('data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:17;"',
                                   'data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:50;"')
    (ROOT / "index.html").write_text(html_root, encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
