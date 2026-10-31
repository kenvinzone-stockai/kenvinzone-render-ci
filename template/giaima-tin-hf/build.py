#!/usr/bin/env python3
"""KenvinZone - "Giai ma tin chung khoan" (news decode) -> HyperFrames composition generator.

Usage:  python build.py data.json subtitle-word-timing.json
Writes index.html + compositions/*.html in this folder.

9 scenes = the 9 fixed script lines of the giaima master (sentences per line 1,3,3,3,4,4,3,3,3).
Every reveal lands on the start of its own spoken sentence: sentence starts are read from the
word timestamps (a word ending in . ! ? closes a sentence), with a proportional fallback.
"""
import json, sys, math, html, re
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
if len(SLIDES) != 9:
    raise SystemExit(f"Template Giai ma tin can dung 9 dong script (dang co {len(SLIDES)}).")
VO_LEN = float(SUBS.get("duration") or SUBS["captions"][-1]["end"])
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
WORDS = [(w["text"], float(w["start"])) for c in SUBS["captions"] for w in c["words"]]


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", str(text).strip()) if s]


def _line_beats(i):
    st = float(SLIDES[i]["start"]); du = float(SLIDES[i]["duration"]); en = st + du
    sents = _sentences(SLIDES[i].get("text", ""))
    n = max(1, len(sents))
    ws = [(t, s) for t, s in WORDS if st - 0.05 <= s < en - 0.05]
    starts = []
    if ws:
        starts.append(ws[0][1])
        for k in range(len(ws) - 1):
            if re.search(r"[.!?]['\")\]]*$", ws[k][0]):
                starts.append(ws[k + 1][1])
    if len(starts) != n:
        # proportional fallback by characters
        tot = sum(len(s) for s in sents) or 1
        acc, starts = 0, []
        for s in sents:
            starts.append(st + du * acc / tot)
            acc += len(s)
    return [round(x + OFF, 3) for x in starts], n


BEATS = [_line_beats(i) for i in range(9)]


def LS(i):
    return (0.0 if i == 0 else round(float(SLIDES[i]["start"]) + OFF, 3)), float(SLIDES[i]["duration"])


def B(i, k, add=0.0):
    """Video time of sentence k of line i (clamped to the last sentence)."""
    starts, n = BEATS[i]
    k = max(0, min(k, len(starts) - 1))
    return round(starts[k] + add, 3)


SCENES = [(f"s{i}", LS(i)[0], (LS(i + 1)[0] if i < 8 else TOTAL)) for i in range(9)]
START = {c: s for c, s, e in SCENES}


def lt(scene, t_abs):
    return round(t_abs - START[scene], 3)


# news palette (master theme "news": blue + gold); every scene title gets its own gradient pair
BLUE, GOLD = "#3b82f6", "#f5c451"
TONE = {"up": "#4ade80", "down": "#f87171", "gold": "#f5c451", "blue": "#60a5fa", "green": "#4ade80",
        "yellow": "#fbbf24", "red": "#f87171", "flat": "#fbbf24"}
GRADS = [("#ffffff", "#f5c451"), ("#93c5fd", "#3b82f6"), ("#fde68a", "#f59e0b"), ("#fca5a5", "#ef4444"),
         ("#bbf7d0", "#22c55e"), ("#e9d5ff", "#a855f7"), ("#a5f3fc", "#06b6d4"), ("#fed7aa", "#f97316"), ("#fff", "#f5c451")]


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




VN_JS = """
function vn(v, dec){ const s = Math.abs(v).toFixed(dec).split('.'); const i = s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.'); return (v < 0 ? '-' : '') + i + (dec ? ',' + s[1] : ''); }
function vnCounter(sel, from, to, at, dur, dec, prefix, suffix){
  const el = Q(sel); const o = {v: from};
  el.textContent = (prefix||'') + vn(from, dec) + (suffix||'');
  tl.fromTo(o, {v: from}, {v: to, duration: dur, ease: 'power3.out', immediateRender:false, onUpdate(){ el.textContent = (prefix||'') + vn(o.v, dec) + (suffix||''); }}, at);
}
"""


def gcss(i):
    a, b = GRADS[i % len(GRADS)]
    return f"background:linear-gradient(180deg,{a} 0%,{b} 100%);-webkit-background-clip:text;background-clip:text;color:transparent;"


TITLE_CSS = """
.q{position:absolute;left:60px;right:60px;top:250px;text-align:center;font-weight:900;line-height:1.12;letter-spacing:-0.5px;}
.q .l1{font-size:56px;color:#f8fafc;display:block;}
.q .l2{font-size:62px;display:block;padding-top:.1em;line-height:1.15;}
"""


def qtitle(i, lines, ident):
    l1 = esc(lines[0]); l2 = esc(lines[1]) if len(lines) > 1 else ""
    return f'<div class="q" id="{ident}"><span class="l1">{l1}</span><span class="l2" style="{gcss(i)}">{l2}</span></div>'


def q_in(ident, t=0.1):
    return (f"tl.fromTo('#{ident} .l1', {{opacity:0, y:-30, filter:'blur(8px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.35, ease:'expo.out'}}, {t});"
            f"tl.fromTo('#{ident} .l2', {{opacity:0, scale:1.15, filter:'blur(10px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.45, ease:'expo.out'}}, {t + 0.18});")


def ex(stage, dur, kind="blur"):
    if kind == "up":
        return f"tl.to('{stage}', {{opacity:0, y:-110, filter:'blur(14px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});"
    if kind == "left":
        return f"tl.to('{stage}', {{opacity:0, x:-150, filter:'blur(12px)', duration:0.3, ease:'power3.in'}}, {dur - 0.32});"
    return f"tl.to('{stage}', {{opacity:0, scale:0.96, filter:'blur(12px)', duration:0.28, ease:'power3.in'}}, {dur - 0.3});"


def mk(fn_id, idx):
    st, en = SCENES[idx][1], SCENES[idx][2]
    return fn_id, round(en - st, 3)


# ================================================================ S0 HOOK
def s0():
    cid, dur = mk("s0", 0)
    h = D["hook"]; src = D["source"]
    lines = h["title_lines"]
    fa = int(max(44, min(120, 900 / (max(1, len(lines[0])) * 0.72))))
    fb = int(max(44, min(104, 900 / (max(1, len(lines[1]) if len(lines) > 1 else 1) * 0.72))))
    tb = 495 + int(fa * 1.34) + (int(fb * 1.30) if len(lines) > 1 else 0) + 44
    chips = "".join(f'<div class="h0-chip" id="h0-c{i}" style="border-color:{TONE.get(c.get("tone","gold"))}99;color:{TONE.get(c.get("tone","gold"))};"><span>{esc(c["icon"])}</span> {esc(c["text"])}</div>' for i, c in enumerate(h["chips"]))
    css = f"""
.h0-eb{{position:absolute;top:250px;left:0;right:0;text-align:center;}}
.h0-eb span{{display:inline-block;background:linear-gradient(135deg,#fde68a,{GOLD});color:#0b0f19;font-weight:900;font-size:30px;letter-spacing:4px;text-transform:uppercase;padding:14px 36px;border-radius:99px;box-shadow:0 10px 40px rgba(245,196,81,.45);}}
.h0-logo{{position:absolute;top:345px;left:0;right:0;text-align:center;}} .h0-logo img{{width:120px;height:120px;filter:drop-shadow(0 0 30px rgba(59,130,246,.6));}}
.h0-plate{{position:absolute;top:495px;left:40px;right:40px;text-align:center;}}
.h0-plate div{{display:inline-block;padding:22px 30px;border-radius:26px;border:2px solid rgba(96,165,250,.45);background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(59,130,246,.08));box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(59,130,246,.2);}}
.h0-plate h1{{font-weight:900;line-height:1.18;text-transform:uppercase;letter-spacing:-0.5px;}}
.h0-plate .a{{display:block;padding-top:.16em;font-size:{fa}px;{gcss(1)}}}
.h0-plate .b{{display:block;padding-top:.12em;font-size:{fb}px;{gcss(0)}}}
.h0-flow{{position:absolute;top:{tb + 30}px;left:40px;right:40px;display:flex;flex-direction:column;align-items:center;gap:26px;}}
.h0-sub{{text-align:center;font-size:38px;font-weight:800;color:{GOLD};text-transform:uppercase;line-height:1.25;padding:0 20px;}}
.h0-chips{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}}
.h0-chip{{font-weight:800;font-size:30px;padding:12px 22px;border-radius:99px;border:2px solid;background:rgba(15,23,42,.6);}}
.h0-src{{text-align:center;}}
.h0-src span{{font-family:'JBM';font-weight:700;font-size:28px;color:#93c5fd;border:2px solid rgba(96,165,250,.45);padding:8px 22px;border-radius:99px;background:rgba(59,130,246,.1);}}
"""
    body = f"""<div id="h0">
<div class="h0-eb"><span>{esc(h['eyebrow'])}</span></div>
<div class="h0-logo"><img src="assets/img/logo-kenvinzone.svg" alt=""/></div>
<div class="h0-plate"><div><h1><span class="a">{esc(lines[0])}</span><span class="b">{esc(lines[1]) if len(lines) > 1 else ''}</span></h1></div></div>
<div class="h0-flow">
<div class="h0-sub">{esc(h['sub'])}</div>
<div class="h0-chips">{chips}</div>
<div class="h0-src"><span>Nguồn: {esc(src['short'])} · {esc(src['date'])}</span></div>
</div>
</div>"""
    t = lt(cid, B(0, 0))
    js = f"""
// frame 0 already shows the full cover (thumbnail); chips light up one by one on the hook sentence
QA('.h0-chip').forEach((c,i)=>{{ tl.fromTo(c, {{scale:1}}, {{scale:1.1, duration:0.18, ease:'power3.out', immediateRender:false}}, {t + 1.2} + i*0.5); tl.to(c, {{scale:1, duration:0.4, ease:'expo.out'}}, {t + 1.38} + i*0.5); }});
{ex('#h0', dur)}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + js)


# ================================================================ S1 SOURCE
def s1():
    cid, dur = mk("s1", 1)
    src = D["source"]; s = D["s1"]
    css = """
.s1-t{position:absolute;top:250px;left:60px;right:60px;text-align:center;font-size:58px;font-weight:900;line-height:1.15;}
.s1-paper{position:absolute;top:370px;left:60px;right:60px;border-radius:26px;background:linear-gradient(170deg,#f8fafc,#e2e8f0);color:#0f172a;padding:30px 34px;box-shadow:0 30px 70px rgba(0,0,0,.5);}
.s1-mast{display:flex;align-items:center;gap:16px;border-bottom:3px solid #0f172a;padding-bottom:16px;}
.s1-mast .ic{width:64px;height:64px;border-radius:14px;background:#1d4ed8;color:#fff;font-size:36px;font-weight:900;display:flex;align-items:center;justify-content:center;}
.s1-mast .nm{font-size:36px;font-weight:900;} .s1-mast .au{font-size:28px;font-weight:700;color:#475569;}
.s1-hl{margin-top:22px;font-size:46px;font-weight:900;line-height:1.2;font-style:italic;color:#0f172a;min-height:116px;}
.s1-meta{margin-top:16px;display:flex;justify-content:space-between;font-family:'JBM';font-weight:700;font-size:26px;color:#334155;}
.s1-sum{position:absolute;top:840px;left:60px;right:60px;padding:24px 28px;border-radius:22px;border:2px solid rgba(96,165,250,.5);background:rgba(15,23,42,.72);font-size:36px;font-weight:700;line-height:1.4;color:#e2e8f0;}
.s1-sum .k{color:#93c5fd;font-weight:900;margin-right:8px;}
.s1-sum mark{background:linear-gradient(90deg,rgba(245,196,81,.55),rgba(245,196,81,.55)) no-repeat 0 95%/0% 45%;color:#fff;font-weight:900;}
"""
    head = esc(src["headline"])
    author = str(src.get("author") or "").strip()
    dom = re.sub(r"^https?://", "", str(src.get("url") or "")).split("/")[0]
    if author and author.lower() not in {str(src.get("short") or "").lower(), str(src.get("site") or "").lower(), dom.lower()}:
        au_line = f"Tác giả: {esc(author)}"
    else:  # no named author -> just say where it comes from
        au_line = f"Nguồn: {esc(dom or src.get('site') or '')}"
    hl_fs = 46 if len(src["headline"]) <= 70 else (40 if len(src["headline"]) <= 110 else 34)
    body = f"""<div id="g1">
<div class="s1-t" id="s1-t"><span style="{gcss(1)}">{esc(s['title'])}</span></div>
<div class="s1-paper" id="s1-paper">
  <div class="s1-mast"><div class="ic">B</div><div><div class="nm">{esc(src['site'])}</div><div class="au">{au_line}</div></div></div>
  <div class="s1-hl" style="font-size:{hl_fs}px;">“<span id="s1-hl"></span>”</div>
  <div class="s1-meta"><span>Ngày {esc(src['date'])}</span><span>{esc(src['url'][:34])}…</span></div>
</div>
<div class="s1-sum" id="s1-sum"><span class="k">Tóm gọn:</span>{s['summary_html']}</div>
</div>"""
    t0, t1, t2 = lt(cid, B(1, 0)), lt(cid, B(1, 1)), lt(cid, B(1, 2))
    js = f"""
gsap.set('#s1-paper, #s1-sum', {{opacity:0}});
tl.fromTo('#s1-t', {{opacity:0, y:-40, filter:'blur(10px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.4, ease:'expo.out'}}, 0.05);
tl.fromTo('#s1-paper', {{opacity:0, y:220, rotation:-4}}, {{opacity:1, y:0, rotation:0, duration:0.8, ease:'expo.out', immediateRender:false}}, {max(0.3, t0 + 0.2)});
// headline types in like a printing press
const HL = {json.dumps(src['headline'], ensure_ascii=False)}; const hel = Q('#s1-hl'); const ho = {{n:0}}; hel.textContent = '';
tl.fromTo(ho, {{n:0}}, {{n:HL.length, duration:Math.min(2.2, HL.length*0.05), ease:'none', immediateRender:false, onUpdate(){{ hel.textContent = HL.slice(0, Math.round(ho.n)); }} }}, {max(0.3, t0 + 0.2) + 0.6});
tl.fromTo('#s1-sum', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {t1});
tl.fromTo('#s1-sum mark', {{backgroundSize:'0% 45%'}}, {{backgroundSize:'100% 45%', duration:0.9, ease:'power2.inOut', immediateRender:false}}, {t2 + 0.3});
{ex('#g1', dur, 'up')}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + js)


# ================================================================ S2 CONTEXT STATS
def s2():
    cid, dur = mk("s2", 2)
    s = D["s2"]; stats = s["stats"]
    tiles, js = [], []
    for i, st in enumerate(stats):
        c = TONE.get(st.get("tone", "gold"))
        big = i == 0
        y = 450 if big else 760
        x, w = (60, 960) if big else (60 + (i - 1) * 490, 470)
        tiles.append(
            f'<div class="s2-tile" id="s2-t{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{270 if big else 260}px;border-color:{c}88;">'
            f'<div class="v mono" style="color:{c};font-size:{120 if big else 88}px;"><span id="s2-v{i}">0</span><small>{esc(st.get("unit", ""))}</small></div>'
            f'<div class="l">{esc(st["label"])}</div>'
            + (f'<div class="bd" style="background:{TONE["down"]};">{esc(st["badge"])}</div>' if st.get("badge") else "") + '</div>')
        t = lt(cid, B(2, st.get("beat", 1), 0.15 + (0.6 if (i == 2) else 0)))
        js.append(f"tl.fromTo('#s2-t{i}', {{opacity:0, y:60, scale:0.92}}, {{opacity:1, y:0, scale:1, duration:0.5, ease:'expo.out', immediateRender:false}}, {t});"
                  f"vnCounter('#s2-v{i}', 0, {st['value']}, {t + 0.1}, 1.4, {st.get('decimals', 0)}, '', '');")
        if st.get("badge"):
            js.append(f"tl.fromTo('#s2-t{i} .bd', {{opacity:0, scale:1.6, rotation:-10}}, {{opacity:1, scale:1, rotation:0, duration:0.35, ease:'back.out(2)', immediateRender:false}}, {t + 1.4});")
    css = """
.s2-tile{position:absolute;border:2px solid;border-radius:28px;background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(15,23,42,.7));padding:30px 34px;}
.s2-tile .v{font-weight:800;line-height:1;font-variant-numeric:tabular-nums;} .s2-tile .v small{font-size:.42em;margin-left:10px;color:#cbd5e1;}
.s2-tile .l{margin-top:16px;font-size:32px;font-weight:700;color:#e2e8f0;line-height:1.25;}
.s2-tile .bd{position:absolute;right:30px;top:30px;font-family:'JBM';font-weight:800;font-size:32px;color:#fff;padding:8px 18px;border-radius:14px;}
.s2-note{position:absolute;left:60px;right:60px;top:1050px;text-align:center;font-size:30px;font-weight:700;color:#cbd5e1;line-height:1.35;}
"""
    body = f"""<div id="g2">{qtitle(2, s['title_lines'], 's2-q')}{''.join(tiles)}<div class="s2-note" id="s2-note">{esc(s.get('note', ''))}</div></div>"""
    jss = f"""
gsap.set('#g2 .s2-tile, #s2-note', {{opacity:0}});
{q_in('s2-q', max(0.1, lt(cid, B(2, 0))))}
{''.join(js)}
tl.fromTo('#s2-note', {{opacity:0}}, {{opacity:1, duration:0.5, immediateRender:false}}, {lt(cid, B(2, 2, 2.4))});
{ex('#g2', dur, 'left')}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S3 CORE: winners vs losers
def s3():
    cid, dur = mk("s3", 3)
    s = D["s3"]; bars = s["bars"]
    cx, half = 540, 420
    mx = max(abs(b["value"]) for b in bars) or 1
    rows, js = [], []
    for i, b in enumerate(bars):
        y = 560 + i * 120
        w = max(18, min(1.0, abs(b["value"]) / mx) * half)
        neg = b["value"] < 0
        c = TONE["down"] if neg else TONE["up"]
        x = cx - w if neg else cx
        lab = f"left:{cx + 24}px;text-align:left;" if neg else f"right:{W - cx + 24}px;text-align:right;"
        rows.append(f'<div class="s3-row" id="s3-r{i}" style="top:{y}px;"><div class="s3-bar" id="s3-b{i}" style="left:{x:.0f}px;width:{w:.0f}px;background:{c};box-shadow:0 0 26px {c}66;transform-origin:{"right" if neg else "left"} center;"></div>'
                    f'<div class="s3-lab" style="{lab}"><b>{esc(b["label"])}</b> <span class="mono" style="color:{c};">{esc(b["display"])}</span></div></div>')
        t = lt(cid, B(3, b.get("beat", 1), 0.3 + 0.7 * sum(1 for bb in bars[:i] if bb.get("beat", 1) == b.get("beat", 1))))
        js.append(f"tl.fromTo('#s3-r{i}', {{opacity:0}}, {{opacity:1, duration:0.2, immediateRender:false}}, {t});"
                  f"tl.fromTo('#s3-b{i}', {{scaleX:0}}, {{scaleX:1, duration:0.9, ease:'expo.out', immediateRender:false}}, {t});")
    co = s.get("callout")
    t_co = lt(cid, B(3, co.get("beat", 1), 2.2)) if co else 0
    css = """
.s3-lead{position:absolute;top:430px;left:60px;right:60px;text-align:center;font-size:40px;font-weight:900;letter-spacing:1px;}
.s3-axis{position:absolute;left:539px;top:530px;width:3px;height:380px;background:rgba(255,255,255,.4);transform-origin:center top;}
.s3-row{position:absolute;left:0;right:0;height:100px;}
.s3-bar{position:absolute;top:24px;height:52px;border-radius:12px;}
.s3-lab{position:absolute;top:30px;width:500px;font-size:30px;font-weight:700;color:#e2e8f0;white-space:nowrap;} .s3-lab b{color:#fff;font-weight:900;}
.s3-co{position:absolute;left:60px;right:60px;top:960px;display:flex;align-items:center;gap:26px;padding:22px 30px;border-radius:24px;border:2px solid rgba(245,196,81,.6);background:rgba(245,196,81,.1);}
.s3-co .n{font-family:'JBM';font-weight:800;font-size:96px;color:#f5c451;line-height:1;} .s3-co .x{font-size:32px;font-weight:700;color:#fde68a;line-height:1.3;}
"""
    body = f"""<div id="g3">{qtitle(3, s['title_lines'], 's3-q')}
<div class="s3-lead" id="s3-lead"><span style="color:#4ade80;">▲ {esc(s['lead'].split('—')[0].strip())}</span>{(' <span style="color:#64748b;">—</span> <span style="color:#f87171;">' + esc(s['lead'].split('—')[1].strip()) + ' ▼</span>') if '—' in s['lead'] else ''}</div>
<div class="s3-axis" id="s3-axis"></div>{''.join(rows)}
{f'<div class="s3-co" id="s3-co"><div class="n mono"><span id="s3-con">0</span>{esc(co.get("suffix", ""))}</div><div class="x">{esc(co["text"])}</div></div>' if co else ''}
</div>"""
    jss = f"""
gsap.set('#g3 .s3-row, #s3-co, #s3-lead', {{opacity:0}});
{q_in('s3-q', max(0.1, lt(cid, B(3, 0))))}
tl.fromTo('#s3-lead', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {lt(cid, B(3, 0, 1.2))});
tl.fromTo('#s3-axis', {{scaleY:0}}, {{scaleY:1, duration:0.7, ease:'power2.inOut', immediateRender:false}}, {lt(cid, B(3, 0, 1.4))});
{''.join(js)}
{f"tl.fromTo('#s3-co', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {t_co}); vnCounter('#s3-con', 0, {co['value']}, {t_co + 0.1}, 1.3, 0, '', '');" if co else ''}
{ex('#g3', dur)}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S4 IMPACT (spotlight cards)
def s4():
    cid, dur = mk("s4", 4)
    s = D["s4"]; cards = s["cards"]
    html_cards, js = [], []
    for i, c in enumerate(cards):
        y = 450 + i * 225
        html_cards.append(f'<div class="s4-c" id="s4-c{i}" style="top:{y}px;"><div class="s4-n mono">{i+1}</div><div class="s4-big mono">{esc(c.get("big", ""))}</div>'
                          f'<div class="s4-tx"><div class="h">{esc(c["title"])}</div><div class="d">{esc(c["text"])}</div></div></div>')
        t = lt(cid, B(4, i + 1, 0.1))
        js.append(f"tl.fromTo('#s4-c{i}', {{opacity:0, x:{-160 if i % 2 == 0 else 160}}}, {{opacity:1, x:0, duration:0.55, ease:'expo.out', immediateRender:false}}, {t});")
        # spotlight: the spoken card glows, the earlier ones dim
        js.append(f"tl.to('#s4-c{i}', {{borderColor:'rgba(245,196,81,.95)', boxShadow:'0 0 50px rgba(245,196,81,.35)', duration:0.3, immediateRender:false}}, {t + 0.2});")
        for j in range(i):
            js.append(f"tl.to('#s4-c{j}', {{opacity:0.45, borderColor:'rgba(255,255,255,.12)', boxShadow:'0 0 0 rgba(0,0,0,0)', duration:0.3}}, {t});")
    css = """
.s4-c{position:absolute;left:60px;right:60px;height:200px;border:2px solid rgba(255,255,255,.12);border-radius:26px;background:rgba(15,23,42,.72);}
.s4-n{position:absolute;left:26px;top:26px;width:70px;height:70px;border-radius:50%;background:#3b82f6;color:#fff;font-size:40px;font-weight:800;display:flex;align-items:center;justify-content:center;}
.s4-big{position:absolute;left:26px;top:112px;width:300px;font-size:44px;font-weight:800;color:#f5c451;white-space:nowrap;}
.s4-tx{position:absolute;left:340px;right:26px;top:28px;} .s4-tx .h{font-size:36px;font-weight:900;color:#fff;} .s4-tx .d{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#cbd5e1;}
"""
    body = f"""<div id="g4">{qtitle(4, s['title_lines'], 's4-q')}{''.join(html_cards)}</div>"""
    jss = f"""
gsap.set('#g4 .s4-c', {{opacity:0}});
{q_in('s4-q', max(0.1, lt(cid, B(4, 0))))}
{''.join(js)}
tl.to('#g4 .s4-c', {{opacity:1, duration:0.4}}, {lt(cid, B(4, 3, 5.0))});
{ex('#g4', dur, 'up')}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S5 TRAFFIC LIGHT
def s5():
    cid, dur = mk("s5", 5)
    s = D["s5"]; L = s["lights"]
    COL = {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"}
    lamps, cards, js = [], [], []
    for i, l in enumerate(L):
        c = COL.get(l["color"], "#facc15")
        y = 470 + i * 230
        lamps.append(f'<div class="s5-lamp" id="s5-l{i}" style="top:{y + 40}px;background:{c};box-shadow:0 0 60px {c},0 0 120px {c}88;"></div>')
        cards.append(f'<div class="s5-c" id="s5-c{i}" style="top:{y}px;border-color:{c}aa;"><div class="tg" style="background:{c};">{esc(l["tag"])}</div>'
                     f'<div class="h" style="color:{c};">{esc(l["title"])}</div><div class="d">{esc(l["text"])}</div></div>')
        t = lt(cid, B(5, i + 1, 0.1))
        js.append(f"tl.fromTo('#s5-l{i}', {{opacity:0.08, scale:0.8}}, {{opacity:1, scale:1, duration:0.35, ease:'back.out(2)', immediateRender:false}}, {t});"
                  f"tl.fromTo('#s5-c{i}', {{opacity:0, x:80}}, {{opacity:1, x:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {t + 0.15});")
    css = """
.s5-pole{position:absolute;left:60px;top:445px;width:170px;height:700px;border-radius:40px;background:linear-gradient(180deg,#1e293b,#0f172a);border:3px solid #334155;box-shadow:inset 0 0 30px rgba(0,0,0,.6);}
.s5-lamp{position:absolute;left:85px;width:120px;height:120px;border-radius:50%;}
.s5-c{position:absolute;left:260px;right:60px;height:205px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.72);padding:22px 26px;}
.s5-c .tg{position:absolute;right:20px;top:-18px;font-weight:900;font-size:24px;letter-spacing:2px;color:#0b0f19;padding:6px 14px;border-radius:10px;}
.s5-c .h{font-size:34px;font-weight:900;line-height:1.2;} .s5-c .d{margin-top:8px;font-size:29px;font-weight:600;line-height:1.35;color:#e2e8f0;}
"""
    body = f"""<div id="g5">{qtitle(5, s['title_lines'], 's5-q')}<div class="s5-pole" id="s5-pole"></div>{''.join(lamps)}{''.join(cards)}</div>"""
    jss = f"""
gsap.set('#g5 .s5-c', {{opacity:0}}); gsap.set('#g5 .s5-lamp', {{opacity:0.08}});
{q_in('s5-q', max(0.1, lt(cid, B(5, 0))))}
tl.fromTo('#s5-pole', {{opacity:0, y:60}}, {{opacity:1, y:0, duration:0.5, ease:'expo.out'}}, {max(0.3, lt(cid, B(5, 0, 0.8)))});
{''.join(js)}
{ex('#g5', dur, 'left')}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S6 WHY: cause -> effect chain
def s6():
    cid, dur = mk("s6", 6)
    s = D["s6"]; ch = s["chain"]
    nodes, js = [], []
    seen = {}
    for i, n in enumerate(ch):
        y = 450 + i * 245
        nodes.append(f'<div class="s6-n" id="s6-n{i}" style="top:{y}px;"><div class="h">{esc(n["title"])}</div><div class="d">{esc(n["text"])}</div></div>')
        if i:
            nodes.append(f'<div class="s6-ar" id="s6-a{i}" style="top:{y - 62}px;">▼</div>')
        b = n.get("beat", 1); k = seen.get(b, 0); seen[b] = k + 1
        t = lt(cid, B(6, b, 0.2 + k * 1.6))
        if i:
            js.append(f"tl.fromTo('#s6-a{i}', {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.3, ease:'power2.out', immediateRender:false}}, {t - 0.2});")
        js.append(f"tl.fromTo('#s6-n{i}', {{opacity:0, scale:0.85, filter:'blur(8px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'expo.out', immediateRender:false}}, {t});")
    css = """
.s6-n{position:absolute;left:110px;right:110px;height:170px;border-radius:26px;border:2px solid rgba(168,85,247,.6);background:linear-gradient(135deg,rgba(168,85,247,.18),rgba(15,23,42,.7));text-align:center;padding:26px 24px;}
.s6-n .h{font-size:40px;font-weight:900;color:#fff;line-height:1.15;} .s6-n .d{margin-top:10px;font-size:30px;font-weight:600;color:#e9d5ff;}
.s6-ar{position:absolute;left:0;right:0;text-align:center;font-size:44px;color:#c084fc;}
"""
    body = f"""<div id="g6">{qtitle(6, s['title_lines'], 's6-q')}{''.join(nodes)}</div>"""
    jss = f"""
gsap.set('#g6 .s6-n, #g6 .s6-ar', {{opacity:0}});
{q_in('s6-q', max(0.1, lt(cid, B(6, 0))))}
{''.join(js)}
{ex('#g6', dur)}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S7 F0 checklist
def s7():
    cid, dur = mk("s7", 7)
    s = D["s7"]; items = s["items"]
    rows, js = [], []
    seen = {}
    for i, it in enumerate(items):
        y = 460 + i * 215
        warn = it.get("icon") == "warn"
        c = "#fbbf24" if warn else "#4ade80"
        rows.append(f'<div class="s7-r" id="s7-r{i}" style="top:{y}px;border-color:{c}88;"><svg class="s7-ic" viewBox="0 0 100 100"><circle cx="50" cy="50" r="44" fill="{c}22" stroke="{c}" stroke-width="6"/>'
                    + (f'<path id="s7-p{i}" d="M28 52 L44 68 L74 34" fill="none" stroke="{c}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="80" stroke-dashoffset="80"/>' if not warn else
                       f'<path id="s7-p{i}" d="M50 24 L50 58 M50 74 L50 76" fill="none" stroke="{c}" stroke-width="11" stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="80"/>')
                    + f'</svg><div class="tx"><div class="h">{esc(it["title"])}</div><div class="d">{esc(it["text"])}</div></div></div>')
        b = it.get("beat", 1); k = seen.get(b, 0); seen[b] = k + 1
        t = lt(cid, B(7, b, 0.2 + k * 2.2))
        js.append(f"tl.fromTo('#s7-r{i}', {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {t});"
                  f"tl.fromTo('#s7-p{i}', {{strokeDashoffset:80}}, {{strokeDashoffset:0, duration:0.45, ease:'power2.out', immediateRender:false}}, {t + 0.35});")
    css = """
.s7-r{position:absolute;left:60px;right:60px;height:190px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.72);}
.s7-ic{position:absolute;left:26px;top:40px;width:110px;height:110px;}
.s7-r .tx{position:absolute;left:164px;right:24px;top:34px;} .s7-r .h{font-size:35px;font-weight:900;color:#fff;line-height:1.2;} .s7-r .d{margin-top:8px;font-size:29px;font-weight:600;color:#cbd5e1;}
.s7-shield{position:absolute;left:0;right:0;top:1110px;text-align:center;}
.s7-shield span{display:inline-block;font-weight:900;font-size:32px;letter-spacing:2px;color:#0b0f19;background:linear-gradient(135deg,#fde68a,#f5c451);padding:12px 30px;border-radius:99px;box-shadow:0 10px 30px rgba(245,196,81,.4);}
"""
    body = f"""<div id="g7">{qtitle(7, s['title_lines'], 's7-q')}{''.join(rows)}<div class="s7-shield" id="s7-sh"><span>🛡 QUẢN TRỊ RỦI RO LÊN HÀNG ĐẦU</span></div></div>"""
    jss = f"""
gsap.set('#g7 .s7-r, #s7-sh', {{opacity:0}});
{q_in('s7-q', max(0.1, lt(cid, B(7, 0))))}
{''.join(js)}
tl.fromTo('#s7-sh', {{opacity:0, scale:0.7}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(2)', immediateRender:false}}, {lt(cid, B(7, 2, 3.0))});
{ex('#g7', dur, 'up')}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + jss)


# ================================================================ S8 OUTRO
def s8():
    cid, dur = mk("s8", 8)
    o = D["outro"]; src = D["source"]
    css = f"""
.s8-k{{position:absolute;top:250px;left:0;right:0;text-align:center;font-size:28px;font-weight:900;letter-spacing:6px;color:#93c5fd;}}
.s8-tag{{position:absolute;top:290px;padding-top:.12em;line-height:1.2;left:0;right:0;text-align:center;font-size:62px;font-weight:900;text-transform:uppercase;{gcss(0)}}}
.s8-plate{{position:absolute;top:410px;left:60px;right:60px;text-align:center;}}
.s8-plate div{{display:inline-block;padding:26px 30px;border-radius:26px;border:2px solid rgba(245,196,81,.5);background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(245,196,81,.06));font-size:50px;font-weight:900;line-height:1.25;color:#fff;}}
.s8-h{{position:absolute;top:700px;left:0;right:0;text-align:center;font-family:'JBM';font-weight:800;font-size:66px;background:linear-gradient(135deg,#fde047,#f5c451 50%,#60a5fa);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.s8-cta{{position:absolute;top:800px;left:60px;right:60px;text-align:center;font-size:36px;font-weight:800;color:#e2e8f0;}}
.s8-pl{{position:absolute;top:870px;left:0;right:0;display:flex;gap:14px;justify-content:center;}}
.s8-pl span{{font-family:'JBM';font-weight:800;font-size:28px;color:#93c5fd;border:2px solid rgba(96,165,250,.5);border-radius:12px;padding:8px 18px;}}
.s8-d{{position:absolute;left:60px;right:60px;top:960px;text-align:center;font-size:28px;line-height:1.4;color:#fed7aa;padding:14px 18px;border:1px solid rgba(245,158,11,.3);border-radius:14px;background:rgba(255,255,255,.03);}}
.s8-d b{{color:#fff;}}
"""
    body = f"""<div id="g8">
<div class="s8-k">KENVINZONE ANALYTICS</div>
<div class="s8-tag" id="s8-tag">{esc(o['tag'])}</div>
<div class="s8-plate" id="s8-plate"><div>{esc(o['closing'])}</div></div>
<div class="s8-h" id="s8-h">{esc(D['handle'])}</div>
<div class="s8-cta" id="s8-cta">{esc(o['cta'])} →</div>
<div class="s8-pl" id="s8-pl"><span>TikTok</span><span>Reels</span><span>Shorts</span></div>
<div class="s8-d" id="s8-d">📄 Nguồn: {esc(src['site'])} — “{esc(src['headline'])}” ({esc(src['author'])}, {esc(src['date'])}). Nội dung được <b>tổng hợp &amp; bình luận lại</b>, không sao chép nguyên văn. ⚠️ Chỉ mang tính tham khảo, <b>KHÔNG phải khuyến nghị đầu tư</b>.</div>
</div>"""
    js = f"""
gsap.set('#s8-plate, #s8-h, #s8-cta, #s8-pl, #s8-d', {{opacity:0}});
tl.fromTo('#s8-tag', {{opacity:0, scale:1.2, filter:'blur(10px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.45, ease:'expo.out'}}, 0.1);
tl.fromTo('#s8-plate', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.5, ease:'expo.out', immediateRender:false}}, {max(0.4, lt(cid, B(8, 0, 0.4)))});
tl.fromTo('#s8-h', {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(1.8)', immediateRender:false}}, {lt(cid, B(8, 1))});
tl.fromTo('#s8-cta, #s8-pl', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {lt(cid, B(8, 1, 0.5))});
tl.fromTo('#s8-d', {{opacity:0}}, {{opacity:1, duration:0.5, immediateRender:false}}, {lt(cid, B(8, 2))});
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + css, body, VN_JS + js)


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
        add("whoosh.mp3", st - 0.25, 0.4)
    for i, stt in enumerate(D["s2"]["stats"]):
        add("tick.mp3", B(2, stt.get("beat", 1), 0.25 + (0.6 if i == 2 else 0)), 0.3)
    for i in range(3):
        add("tick.mp3", B(4, i + 1, 0.1), 0.3)
        add("tick.mp3", B(5, i + 1, 0.1), 0.35)
    add("impact.mp3", B(3, 2, 0.3), 0.45)
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
.glow{{position:absolute;left:-200px;right:-200px;top:200px;height:1000px;filter:blur(120px);background:radial-gradient(circle at 50% 40%,rgba(245,196,81,.28),rgba(245,196,81,.10) 40%,transparent 70%);}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:176px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:40px;height:40px;}}
.brand .n{{font-size:28px;font-weight:800;letter-spacing:1px;color:rgba(255,255,255,.75);}}
.brand .d{{margin-left:auto;font-family:'JBM';font-weight:700;font-size:28px;color:#7dd3fc;}}
.prog{{position:absolute;left:60px;right:60px;top:226px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,#3b82f6,#f5c451);transform-origin:left center;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="glow"></div>
  <canvas id="bgc" width="{W}" height="{H}"></canvas>
  <div class="vig"></div>
  <div class="brand" id="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">{esc(D['handle'])} · GIẢI MÃ TIN</span><span class="d">{esc(D['date'])}</span></div>
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
let seed = 20261029; const rnd = () => {{ seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.16)}, CW = w / 9, SPEED = {D.get('bg_speed', 95)}, C = '245,196,81';
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
tl.fromTo('#brand, #prog', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, immediateRender:false }}, {START['s1']});
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
    for fn in (s0, s1, s2, s3, s4, s5, s6, s7, s8):
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
