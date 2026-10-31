#!/usr/bin/env python3
"""KenvinZone AURORA Explainer -> HyperFrames composition generator.

Usage:  python build.py data.json subtitle-word-timing.json [deck.html]

Unlike the other HyperFrames templates, the content is NOT retyped into hf-data.json:
the episode's own slide deck (index.html, copied here as deck.html by render_hyperframes.py)
is parsed and every card (title, source card, stat row, quote, box, 3 highlight cards,
3 traffic lights, outro) is rebuilt as an animated 1080x1920 scene.
hf-data.json only needs {"template": "aurora-explainer-hf"} (+ optional hero_color, audio_offset, outro_hold).

Timing: one script line per slide. The title lands when the line starts, the first card ~0.9s later,
the remaining cards on the next sentence starts; the 3 highlight / traffic-light cards land on the
clauses after "...:" separated by ";" (the AURORA script formula "Ba ...: A; B; và C").
Only the standard library is used (no bs4) so it runs on any Python 3.8+.
"""
import json, sys, math, html, re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))
DECK = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "deck.html"
D = DATA

SFX_LEN = {'whoosh.mp3': 0.62, 'tick.mp3': 0.13, 'impact.mp3': 0.73}
OFF = float(D.get("audio_offset", 1.0))
OUTRO = float(D.get("outro_hold", 3.6))
W, H = 1080, 1920
HERO = str(D.get("hero_color") or "#fde68a")
SLIDES = SUBS["slides"]
VO_LEN = float(SUBS.get("duration") or SUBS["captions"][-1]["end"])
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
WORDS = [(w["text"], float(w["start"])) for c in SUBS["captions"] for w in c["words"]]

# ================================================================ tiny DOM (stdlib only)
VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr"}


class N:
    def __init__(self, tag, attrs, parent):
        self.tag, self.a, self.ch, self.p = tag, dict(attrs), [], parent

    @property
    def cls(self):
        return set((self.a.get("class") or "").split())

    def kids(self):
        return [c for c in self.ch if isinstance(c, N)]


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = N("root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = N(tag, attrs, self.cur)
        self.cur.ch.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.ch.append(N(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.p
        if n is not None and n.p is not None:
            self.cur = n.p

    def handle_data(self, d):
        self.cur.ch.append(d)


def walk(n):
    for c in n.ch:
        if isinstance(c, N):
            yield c
            yield from walk(c)


def find(n, cls=None, tag=None):
    for c in walk(n):
        if (cls is None or cls in c.cls) and (tag is None or c.tag == tag):
            return c
    return None


def findall(n, cls):
    return [c for c in walk(n) if cls in c.cls]


LATEX = {"rightarrow": "→", "leftarrow": "←", "Rightarrow": "⇒", "to": "→", "uparrow": "↑", "downarrow": "↓",
         "times": "×", "approx": "≈", "geq": "≥", "leq": "≤", "ge": "≥", "le": "≤", "pm": "±"}


def clean(s):
    s = re.sub(r"\$\s*\\([A-Za-z]+)\s*\$", lambda m: LATEX.get(m.group(1), ""), s)
    s = re.sub(r"\\(rightarrow|leftarrow|Rightarrow)", lambda m: LATEX[m.group(1)], s)
    return s


def text(n):
    if n is None:
        return ""
    out = []

    def rec(x):
        for c in x.ch:
            if isinstance(c, str):
                out.append(c)
            elif c.tag == "br":
                out.append("\n")
            elif c.tag not in ("script", "style"):
                rec(c)
    rec(n)
    s = clean("".join(out))
    return "\n".join(re.sub(r"\s+", " ", l).strip() for l in s.split("\n")).strip()


def icon(n):
    """<i class="fa-solid fa-xxx"> -> sanitized icon tag ('' if none)."""
    if n is None:
        return ""
    i = n if n.tag == "i" else find(n, tag="i")
    if i is None:
        return ""
    fa = [c for c in (i.a.get("class") or "").split() if c.startswith("fa")]
    return f'<i class="{" ".join(fa)}"></i>' if fa else ""


def inner(n, skip_icons=False):
    """Inline HTML with only safe formatting kept (strong/b/em/br/fa icons/gradient spans)."""
    out = []

    def rec(x):
        for c in x.ch:
            if isinstance(c, str):
                out.append(html.escape(clean(c), quote=False))
                continue
            t = c.tag
            if t in ("script", "style"):
                continue
            if t == "br":
                out.append("<br/>")
            elif t == "i":
                if not skip_icons:
                    col = re.search(r"color:\s*([^;\"]+)", c.a.get("style") or "")
                    ic = icon(c)
                    if ic and col:
                        ic = ic.replace("<i ", f'<i style="color:{html.escape(col.group(1).strip())}" ', 1)
                    out.append(ic)
            elif t in ("strong", "b", "em"):
                out.append(f"<{t}>"); rec(c); out.append(f"</{t}>")
            elif t == "span":
                g = [k for k in c.cls if k.startswith("gm-grad-")]
                out.append(f'<span class="{g[0]}">' if g else "<span>"); rec(c); out.append("</span>")
            else:
                rec(c)
    rec(n)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def esc(s):
    return html.escape(str(s), quote=True)


# ================================================================ parse the deck
_p = _P()
_p.feed(DECK.read_text(encoding="utf-8"))
_cont = next((n for n in walk(_p.root) if n.a.get("id") == "slideContainer"), _p.root)
DECK_SLIDES = sorted([n for n in walk(_cont) if "slide" in n.cls and n.a.get("data-slide") is not None],
                     key=lambda n: int(n.a["data-slide"]))
NS = len(DECK_SLIDES)
if NS < 2:
    raise SystemExit("Khong doc duoc slide nao trong deck (index.html).")
if len(SLIDES) != NS:
    raise SystemExit(f"So dong script ({len(SLIDES)}) khac so slide trong index.html ({NS}). "
                     "AURORA can dung 1 dong script cho 1 slide.")


def classify(c):
    if find(c, "kv-s1-content") or "kv-s1-content" in c.cls:
        return "hook"
    if find(c, "kv-outro-main-title") or "kv-outro-pill" in c.cls or find(c, "kv-outro-pill"):
        return "outro"
    for k, name in (("slide-title", "title"), ("gm-source-card", "src"), ("gm-stat-row", "stats"),
                    ("gm-quote", "quote"), ("gm-box", "box"), ("gm-impact", "impact"), ("gm-tl", "tl")):
        if k in c.cls:
            return name
    first = c.kids()[0] if c.kids() else None
    if first is not None and len(c.kids()) == 1:
        return classify(first)
    return "generic"


def unwrap(c, kind):
    """slide-element wrapper -> the component node itself."""
    key = {"title": "slide-title", "src": "gm-source-card", "stats": "gm-stat-row", "quote": "gm-quote",
           "box": "gm-box", "impact": "gm-impact", "tl": "gm-tl", "hook": "kv-s1-content"}.get(kind)
    if key and key not in c.cls:
        return find(c, key) or c
    return c


SCN = []  # per slide: {"mode":..., "items":[(kind,node)]}
for s in DECK_SLIDES:
    content = find(s, "slide-content") or s
    items = []
    for c in content.kids():
        k = classify(c)
        items.append((k, unwrap(c, k)))
    SCN.append({"mode": s.a.get("data-mode", ""), "items": items})

# ================================================================ timing
def LS(i):
    return (0.0 if i == 0 else round(float(SLIDES[i]["start"]) + OFF, 3)), float(SLIDES[i]["duration"])


SCENES = [(f"s{i}", LS(i)[0], (LS(i + 1)[0] if i < NS - 1 else TOTAL)) for i in range(NS)]
START = {c: s for c, s, e in SCENES}


def _bounds(i):
    st = float(SLIDES[i]["start"]); en = st + float(SLIDES[i]["duration"])
    ws = [(t, s) for t, s in WORDS if st - 0.05 <= s < en - 0.05]
    out, colon_seen = [], False
    for k in range(len(ws) - 1):
        w = re.sub(r"['\")\]”’»]+$", "", ws[k][0])
        if re.search(r"[.!?;:]$", w):
            strong = bool(re.search(r"[.!?]$", w))
            out.append({"t": ws[k + 1][1], "strong": strong, "after_colon": colon_seen or w.endswith(":")})
            if w.endswith(":"):
                colon_seen = True
    return st, en, out


def reveal_times(i, n_items, mode):
    """Absolute video times for the items of slide i (item 0 = title when present)."""
    st, en, bd = _bounds(i)
    if i == 0:
        return [0.0] * n_items
    s0, end = st + OFF, en + OFF - 0.6
    out = [round(s0 + 0.12, 3)]
    rest = n_items - 1
    if rest <= 0:
        return out[:n_items]
    picked = None
    if mode in ("highlight", "traffic-light"):
        cands = [b["t"] for b in bd if b["after_colon"]] or [b["t"] for b in bd]
        if len(cands) >= rest:
            picked = [c + OFF for c in cands[-rest:]]
    if picked is None:
        strong = [b["t"] for b in bd if b["strong"]]
        strong = [t for t in strong if t >= st + 2.0]
        pool = sorted({b["t"] for b in bd if b["t"] >= st + 2.0})
        later = []
        if rest > 1:
            later = strong[-(rest - 1):] if len(strong) >= rest - 1 else pool[-(rest - 1):]
        picked = [s0 + 0.9] + [x + OFF for x in later]
        while len(picked) < rest:  # not enough sentence starts -> spread the rest
            a = picked[-1]
            picked.append(a + (en + OFF - a) * 0.45)
    for t in picked:
        t = max(t, out[-1] + 0.6)
        out.append(round(min(t, max(out[-1] + 0.3, end)), 3))
    return out


def lt(cid, t):
    return round(t - START[cid], 3)


# ================================================================ shared CSS / scene file
FONT_CSS = """
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-vietnamese-500-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-latin-500-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-vietnamese-700-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-latin-700-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-vietnamese-800-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-vietnamese-900-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-latin-900-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-vietnamese-800-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-vietnamese-700-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-latin-700-normal.woff2') format('woff2');}
"""

GRAD = {"a": ("#3b82f6", "#93c5fd"), "gold": ("#f5c451", "#ffe08a"), "red": ("#ef4444", "#fca5a5"),
        "green": ("#10b981", "#6ee7b7"), "purple": ("#a855f7", "#f0abfc"), "cyan": ("#22d3ee", "#a5f3fc"),
        "orange": ("#f97316", "#fdba74"), "pink": ("#ec4899", "#f9a8d4"), "blue": ("#3b82f6", "#93c5fd")}
GRAD_CSS = "".join(
    f".gm-grad-{k}{{background:linear-gradient(120deg,{a},{b});-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;}}"
    for k, (a, b) in GRAD.items())

BASE_CSS = """
#root{position:absolute;inset:0;font-family:'BVP',sans-serif;color:#f8fafc;}
.mono{font-family:'JBM',monospace;font-variant-numeric:tabular-nums;}
.stage{position:absolute;left:60px;right:60px;top:262px;height:900px;display:flex;flex-direction:column;justify-content:center;align-items:stretch;}
.stage > *{flex-shrink:0;}
.t{text-align:center;position:relative;padding-bottom:.42em;}
.t .ln{display:block;font-size:1.72em;font-weight:900;line-height:1.2;letter-spacing:-.01em;}
.t .ln > span{display:inline-block;padding-top:.14em;}
.t .ln.w > span{color:#f8fafc;}
.t .ul{position:absolute;left:50%;bottom:.12em;width:3.4em;height:.16em;margin-left:-1.7em;border-radius:99px;background:linear-gradient(90deg,#3b82f6,#f5c451);transform-origin:center;}
.cd{position:relative;border-radius:.62em;padding:.62em .78em;background:rgba(255,255,255,.045);border:2px solid rgba(255,255,255,.1);box-shadow:0 18px 50px rgba(2,6,23,.5);overflow:hidden;}
.cd .sh{position:absolute;top:-20%;bottom:-20%;left:0;width:40%;background:linear-gradient(105deg,transparent 0%,rgba(255,255,255,.10) 45%,rgba(255,255,255,.22) 50%,rgba(255,255,255,.10) 55%,transparent 100%);transform:translateX(-160%) skewX(-12deg);pointer-events:none;}
.cd strong,.cd b{font-weight:800;}
.bx{font-size:1em;line-height:1.45;color:#cbd5e1;padding-left:1.05em;}
.bx .bar{position:absolute;left:0;top:0;bottom:0;width:.22em;background:#60a5fa;transform-origin:top center;}
.bx strong{color:#60a5fa;} .bx i{color:#f5c451;margin-right:.2em;}
.bx.gold{border-color:rgba(245,196,81,.38);background:rgba(245,196,81,.07);} .bx.gold strong{color:#f5c451;} .bx.gold .bar{background:#f5c451;}
.bx.red{border-color:rgba(239,68,68,.36);background:rgba(239,68,68,.07);} .bx.red strong{color:#f87171;} .bx.red .bar{background:#ef4444;}
.bx.green{border-color:rgba(16,185,129,.38);background:rgba(16,185,129,.07);} .bx.green strong{color:#34d399;} .bx.green .bar{background:#10b981;}
.bx.blue{border-color:rgba(96,165,250,.38);background:rgba(59,130,246,.08);}
.qt{display:flex;gap:.6em;align-items:flex-start;background:rgba(37,99,235,.09);border-color:rgba(96,165,250,.32);font-size:1em;line-height:1.45;color:#dbeafe;}
.qt .qi{font-size:1.35em;color:#f5c451;flex-shrink:0;width:1.2em;text-align:center;margin-top:.1em;}
.qt b,.qt strong{color:#fff;}
.qt .qw{display:inline;}
.sc{background:linear-gradient(160deg,rgba(37,99,235,.16),rgba(2,6,23,.5));border-color:rgba(96,165,250,.38);display:flex;flex-direction:column;gap:.5em;}
.sc .top{display:flex;align-items:center;gap:.55em;}
.sc .fav{width:2.2em;height:2.2em;border-radius:.55em;background:linear-gradient(135deg,#1e3a8a,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:1em;color:#fff;flex-shrink:0;box-shadow:0 10px 24px rgba(37,99,235,.45);}
.sc .fav.danger{background:linear-gradient(135deg,#991b1b,#ef4444);box-shadow:0 10px 24px rgba(239,68,68,.45);}
.sc .fav i{font-size:1.05em;}
.sc .out{font-size:1.12em;font-weight:900;color:#fff;line-height:1.15;}
.sc .out span{display:block;font-size:.66em;font-weight:700;color:#f5c451;letter-spacing:.02em;margin-top:.2em;}
.sc .tt{font-size:.98em;font-weight:700;color:#e2e8f0;line-height:1.42;border-left:.17em solid #f5c451;padding-left:.6em;}
.sc .ft{font-size:.74em;color:#94a3b8;line-height:1.45;font-family:'JBM',monospace;} .sc .ft b{color:#cbd5e1;}
.sr{display:flex;gap:.4em;}
.st{flex:1;text-align:center;padding:.62em .35em;border-radius:.55em;background:rgba(255,255,255,.045);border:2px solid rgba(255,255,255,.1);}
.st .nm{font-family:'JBM',monospace;font-weight:800;font-size:2.05em;line-height:1.05;color:#f5c451;white-space:nowrap;}
.st .nm span{font-size:.42em;margin-left:.1em;}
.st .lb{font-size:.74em;color:#94a3b8;line-height:1.3;margin-top:.35em;}
.st.tx .nm{font-family:'BVP',sans-serif;font-weight:900;font-size:1.02em;white-space:normal;line-height:1.2;padding-top:.12em;}
.st.blue .nm{color:#60a5fa;} .st.red .nm{color:#f87171;} .st.red{border-color:rgba(239,68,68,.3);background:rgba(239,68,68,.07);}
.st.green .nm{color:#34d399;} .st.green{border-color:rgba(16,185,129,.3);background:rgba(16,185,129,.07);}
.st.gold{border-color:rgba(245,196,81,.3);background:rgba(245,196,81,.06);}
.im{display:flex;align-items:flex-start;gap:.6em;}
.im .ic{width:2.25em;height:2.25em;border-radius:.6em;display:flex;align-items:center;justify-content:center;font-size:1em;flex-shrink:0;background:linear-gradient(135deg,#1e3a8a,#3b82f6);color:#fff;}
.im .ic i{font-size:1.05em;}
.im .ici{position:absolute;inset:0;border-radius:.6em;background:linear-gradient(135deg,#b45309,#f5c451);opacity:0;}
.im .icw{position:relative;width:2.25em;height:2.25em;flex-shrink:0;}
.im .icw .ic{position:absolute;inset:0;}
.im .icw .ic.on{background:transparent;color:#1a1205;}
.im strong{display:block;font-size:1.04em;font-weight:800;color:#fff;line-height:1.25;margin-bottom:.15em;}
.im .bd span{font-size:.86em;color:#a3b1c6;line-height:1.4;}
.im .glow{position:absolute;inset:-2px;border-radius:.62em;border:3px solid #f5c451;box-shadow:0 0 34px rgba(245,196,81,.35),inset 0 0 24px rgba(245,196,81,.08);opacity:0;}
.tl{display:flex;align-items:center;gap:.6em;}
.tl .dw{position:relative;width:1.15em;height:1.15em;flex-shrink:0;margin:0 .1em;}
.tl .dot{position:absolute;inset:0;border-radius:50%;}
.tl .halo{position:absolute;inset:-.55em;border-radius:50%;opacity:0;}
.tl .bd{flex:1;}
.tl strong{display:block;font-size:1.04em;font-weight:800;color:#fff;line-height:1.25;margin-bottom:.12em;}
.tl .bd span{font-size:.86em;color:#a3b1c6;line-height:1.4;}
.tl .tag{font-family:'JBM',monospace;font-size:.7em;font-weight:800;letter-spacing:.04em;padding:.4em .8em;border-radius:99px;flex-shrink:0;border:2px solid;white-space:nowrap;}
.tl .glow{position:absolute;inset:-2px;border-radius:.62em;border:3px solid;opacity:0;}
.gn{font-size:.96em;line-height:1.45;color:#cbd5e1;text-align:center;}
"""


def scene_file(cid, dur, css, body, js):
    return f"""<template>
<style>{FONT_CSS}{GRAD_CSS}{BASE_CSS}{css}</style>
<div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-duration="{dur}">
{body}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
const Q = (s) => document.querySelector('[data-composition-id="{cid}"] ' + s);
const QA = (s) => document.querySelectorAll('[data-composition-id="{cid}"] ' + s);
function counter(sel, from, to, at, dur, dec, sep){{
  const el = Q(sel); if (!el) return; const o = {{v: from}};
  const f = (v) => {{ let s = Math.abs(v).toFixed(dec); if (sep === ',') s = s.replace('.', ','); return (v < 0 ? '-' : '') + s; }};
  el.textContent = f(from);
  tl.fromTo(o, {{v: from}}, {{v: to, duration: dur, ease: 'power3.out', immediateRender:false, onUpdate(){{ el.textContent = f(o.v); }} }}, at);
}}
function sheen(sel, at){{ QA(sel).forEach((e)=>{{ tl.fromTo(e, {{xPercent:-160}}, {{xPercent:330, duration:1.1, ease:'power2.inOut', immediateRender:false}}, at); }}); }}
{js}
window.__timelines["{cid}"] = tl;
}})();
</script>
</template>
"""


# ================================================================ component -> html + height estimate (px at k=1, base 36px)
CW = 960


def _lines(s, fpx, width, wfac=0.54):
    cpl = max(6, width / (fpx * wfac))
    return sum(max(1, math.ceil(len(seg) / cpl)) for seg in (s or " ").split("\n"))


def c_title(n, idx):
    parts = []
    spans = [c for c in n.ch if isinstance(c, N) and c.tag == "span"]
    # split on <br>: each line keeps its gradient spans
    lines, cur = [], []
    for c in n.ch:
        if isinstance(c, N) and c.tag == "br":
            lines.append(cur); cur = []
        else:
            cur.append(c)
    lines.append(cur)
    lines = [l for l in lines if "".join(x if isinstance(x, str) else text(x) for x in l).strip()]
    if len(lines) == 1 and len(spans) >= 2:  # "<span A>..</span> <span B>..</span>" on one line -> one line each
        lines = [[s] for s in spans]
    html_lines, h, plain = [], 0, []
    for l in lines:
        frag, t = [], []
        for x in l:
            if isinstance(x, str):
                if x.strip():
                    frag.append(f"<span>{esc(clean(x.strip()))}</span>"); t.append(x.strip())
            else:
                g = [k for k in x.cls if k.startswith("gm-grad-")]
                tx = text(x)
                t.append(tx)
                frag.append(f'<span class="{g[0]}">{esc(tx)}</span>' if g else f"<span>{esc(tx)}</span>")
        white = all('class="gm-grad' not in f for f in frag)
        html_lines.append(f'<span class="ln{" w" if white else ""}">{" ".join(frag)}</span>')
        plain.append(" ".join(t))
        h += _lines(" ".join(t), 62, CW, 0.56) * 62 * 1.2 + 9
    return f'<div class="t it">{"".join(html_lines)}<div class="ul"></div></div>', h + 16


def c_box(n, idx):
    color = next((c for c in ("gold", "red", "green", "blue") if c in n.cls), "")
    body = inner(n)
    h = _lines(text(n), 36, CW - 80, 0.52) * 36 * 1.45 + 46
    return f'<div class="cd bx {color} it"><div class="bar"></div><div class="sh"></div>{body}</div>', h


def c_quote(n, idx):
    ic = icon(n.kids()[0]) if n.kids() and n.kids()[0].tag == "i" else icon(n)
    body_node = next((k for k in n.kids() if k.tag != "i"), None)
    body = inner(body_node) if body_node is not None else inner(n, skip_icons=True)
    h = _lines(text(body_node or n), 36, CW - 140, 0.52) * 36 * 1.45 + 46
    return f'<div class="cd qt it"><div class="sh"></div><div class="qi">{ic}</div><div class="qb">{body}</div></div>', h


def c_src(n, idx):
    fav = find(n, "gm-src-favicon")
    danger = "danger" if fav is not None and "danger" in fav.cls else ""
    out = find(n, "gm-src-outlet")
    out_sub = find(out, tag="span") if out is not None else None
    out_main = ""
    if out is not None:
        out_main = "".join(esc(clean(c)) for c in out.ch if isinstance(c, str)).strip()
    tt = find(n, "gm-src-title"); ft = find(n, "gm-src-foot")
    h = 2.2 * 36 + _lines(text(tt), 35, CW - 90, 0.53) * 35 * 1.42 + (_lines(text(ft), 27, CW - 60, 0.6) * 27 * 1.45 if ft else 0) + 2 * 18 + 46
    words = text(tt).split()
    tt_html = " ".join(f'<span class="tw">{esc(w)}</span>' for w in words)
    return (f'<div class="cd sc it"><div class="sh"></div><div class="top"><div class="fav {danger}">{icon(fav)}</div>'
            f'<div class="out">{out_main}{"<span>" + esc(text(out_sub)) + "</span>" if out_sub is not None else ""}</div></div>'
            f'<div class="tt">{tt_html}</div>{"<div class=ft>" + inner(ft) + "</div>" if ft is not None else ""}</div>'), h


def c_stats(n, idx):
    tiles, labs, cnt = [], [], []
    stats = findall(n, "gm-stat")
    for j, s in enumerate(stats):
        col = next((c for c in ("blue", "red", "green", "gold") if c in s.cls), "")
        num = find(s, "num"); lab = find(s, "lab")
        unit = find(num, tag="span") if num is not None else None
        raw = "".join(c for c in (num.ch if num is not None else []) if isinstance(c, str)).strip()
        m = re.fullmatch(r"([+-]?)(\d+)(?:([.,])(\d+))?", raw)
        if m:
            dec = len(m.group(4) or "")
            val = float((m.group(1) or "") + m.group(2) + ("." + m.group(4) if dec else ""))
            cnt.append((j, val, dec, m.group(3) or ""))
            shown = esc(raw)
        else:
            shown = esc(raw or text(num))
            if len(raw or text(num)) > 6:
                col += " tx"
        tiles.append(f'<div class="st {col} it2"><div class="nm"><b id="SN{j}">{shown}</b>{"<span>" + esc(text(unit)) + "</span>" if unit is not None else ""}</div>'
                     f'<div class="lb">{esc(text(lab))}</div></div>')
        labs.append(text(lab))
    nst = max(1, len(stats))
    tw = (CW - (nst - 1) * 14) / nst - 20
    h = (2.6 * 36 if any(' tx' in t_ for t_ in tiles) else 2.05 * 36 * 1.05) + max(_lines(l, 26.6, tw, 0.53) for l in labs or [""]) * 26.6 * 1.3 + 12 + 46
    return f'<div class="sr it">{"".join(tiles)}</div>', h, cnt


def c_impact(n, idx):
    ic = icon(find(n, "ic"))
    st = find(n, tag="strong"); sp = find(find(n, "bd") or n, tag="span")
    h = _lines(text(st), 37.4, CW - 160, 0.55) * 37.4 * 1.25 + _lines(text(sp), 31, CW - 160, 0.52) * 31 * 1.4 + 6 + 46
    return (f'<div class="cd im it"><div class="glow"></div><div class="sh"></div><div class="icw"><div class="ic">{ic}</div>'
            f'<div class="ici"></div><div class="ic on">{ic}</div></div>'
            f'<div class="bd"><strong>{esc(text(st))}</strong><span>{esc(text(sp))}</span></div></div>'), max(h, 2.25 * 36 + 46)


TL_COL = {"green": ("#22c55e", "34,197,94"), "yellow": ("#f59e0b", "245,158,11"), "red": ("#ef4444", "239,68,68")}


def c_tl(n, idx):
    col = n.a.get("data-light-color") or ("green", "yellow", "red")[idx % 3]
    hexc, rgb = TL_COL.get(col, TL_COL["green"])
    st = find(n, tag="strong"); sp = find(find(n, "bd") or n, tag="span"); tag = find(n, "tag")
    tw = len(text(tag)) * 25 * 0.62 + 46 if tag is not None else 0
    wid = CW - 60 - 50 - tw - 40
    h = _lines(text(st), 37.4, wid, 0.55) * 37.4 * 1.25 + _lines(text(sp), 31, wid, 0.52) * 31 * 1.4 + 6 + 46
    return (f'<div class="cd tl it" style="--c:{hexc};--r:{rgb};"><div class="glow" style="border-color:{hexc};box-shadow:0 0 36px rgba({rgb},.35);"></div>'
            f'<div class="dw"><div class="halo" style="background:radial-gradient(circle,rgba({rgb},.75),rgba({rgb},0) 70%);"></div>'
            f'<div class="dot" style="background:{hexc};box-shadow:0 0 18px {hexc};"></div></div>'
            f'<div class="bd"><strong>{esc(text(st))}</strong><span>{esc(text(sp))}</span></div>'
            f'{"<div class=tag style=color:" + hexc + ";border-color:rgba(" + rgb + ",.55);background:rgba(" + rgb + ",.1);>" + esc(text(tag)) + "</div>" if tag is not None else ""}</div>'), h


def c_generic(n, idx):
    tx = text(n)
    if not tx:
        return "", 0
    return f'<div class="cd gn it"><div class="sh"></div>{inner(n)}</div>', _lines(tx, 34.5, CW - 60, 0.52) * 34.5 * 1.45 + 46


# ================================================================ scenes
def ex(sel, dur):
    return f"tl.to('{sel}', {{opacity:0, scale:0.96, filter:'blur(12px)', duration:0.28, ease:'power3.in'}}, {round(dur - 0.3, 3)});"


def scene_generic(i):
    cid, st, en = SCENES[i]
    dur = round(en - st, 3)
    mode = SCN[i]["mode"]
    blocks, hs, kinds, counters = [], [], [], []
    li = ti = 0
    for kind, node in SCN[i]["items"]:
        if kind == "title":
            b, h = c_title(node, i)
        elif kind == "box":
            b, h = c_box(node, i)
        elif kind == "quote":
            b, h = c_quote(node, i)
        elif kind == "src":
            b, h = c_src(node, i)
        elif kind == "stats":
            b, h, cnt = c_stats(node, i)
            counters.append((len(blocks), cnt))
        elif kind == "impact":
            b, h = c_impact(node, li); li += 1
        elif kind == "tl":
            b, h = c_tl(node, ti); ti += 1
        else:
            b, h = c_generic(node, i)
        if not b:
            continue
        blocks.append(b); hs.append(h); kinds.append(kind)
    gap = 30
    est = sum(hs) + gap * max(0, len(hs) - 1)
    k = max(0.62, min(1.0, (800 if mode else 830) / max(1, est)))
    body = f'<div class="stage" id="st{i}" style="font-size:{36 * k:.1f}px;gap:{gap * k:.0f}px;">' + "".join(
        f'<div class="blk" id="b{i}_{j}">{b}</div>' for j, b in enumerate(blocks)) + "</div>"
    times = reveal_times(i, len(blocks), mode)
    js = []
    for j, kind in enumerate(kinds):
        t = lt(cid, times[j])
        sel = f"#b{i}_{j}"
        if kind == "title":
            js.append(f"tl.fromTo('{sel} .ln', {{opacity:0, y:-34, filter:'blur(10px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.5, stagger:0.16, ease:'expo.out'}}, {t});")
            js.append(f"tl.fromTo('{sel} .ul', {{scaleX:0}}, {{scaleX:1, duration:0.6, ease:'expo.out'}}, {t + 0.3});")
            continue
        if mode in ("highlight", "traffic-light") and kind in ("impact", "tl"):
            continue  # handled below: all cards dim-in with the title, then light up one by one
        js.append(f"tl.fromTo('{sel}', {{opacity:0, y:70, scale:0.95, filter:'blur(10px)'}}, {{opacity:1, y:0, scale:1, filter:'blur(0px)', duration:0.55, ease:'expo.out'}}, {t});")
        js.append(f"sheen('{sel} .sh', {t + 0.35});")
        if kind == "box":
            js.append(f"tl.fromTo('{sel} .bar', {{scaleY:0}}, {{scaleY:1, duration:0.5, ease:'expo.out'}}, {t + 0.15});")
        if kind == "quote":
            js.append(f"tl.fromTo('{sel} .qi', {{scale:0, rotate:-90}}, {{scale:1, rotate:0, duration:0.55, ease:'back.out(2)'}}, {t + 0.1});")
        if kind == "src":
            js.append(f"tl.fromTo('{sel} .fav', {{scale:0}}, {{scale:1, duration:0.5, ease:'back.out(2.2)'}}, {t + 0.12});")
            js.append(f"tl.fromTo('{sel} .tw', {{opacity:0.08}}, {{opacity:1, duration:0.12, stagger:0.045, ease:'none'}}, {t + 0.4});")
            js.append(f"tl.fromTo('{sel} .ft', {{opacity:0, y:12}}, {{opacity:1, y:0, duration:0.4, ease:'power2.out'}}, {t + 1.1});")
        if kind == "stats":
            js.append(f"tl.fromTo('{sel} .st', {{opacity:0, y:50, rotateX:-60}}, {{opacity:1, y:0, rotateX:0, duration:0.55, stagger:0.14, ease:'back.out(1.6)'}}, {t});")
            for bj, cnt in counters:
                if bj == j:
                    for (sj, val, dec, sep) in cnt:
                        js.append(f"counter('{sel} #SN{sj}', 0, {val}, {t + 0.15 + sj * 0.14}, 1.2, {dec}, '{sep}');")
    # light-up modes
    lit = [j for j, kd in enumerate(kinds) if kd in ("impact", "tl")]
    if mode in ("highlight", "traffic-light") and lit:
        t0 = lt(cid, times[0]) + 0.35
        for j in lit:
            js.append(f"tl.fromTo('#b{i}_{j}', {{opacity:0, y:40}}, {{opacity:0.3, y:0, duration:0.45, ease:'power3.out'}}, {t0 + 0.08 * lit.index(j)});")
        prev = None
        for n_, j in enumerate(lit):
            t = max(lt(cid, times[j]), t0 + 0.6)
            sel = f"#b{i}_{j}"
            js.append(f"tl.to('{sel}', {{opacity:1, duration:0.35, ease:'power2.out'}}, {t});")
            js.append(f"tl.fromTo('{sel} .cd', {{scale:1}}, {{scale:1.035, duration:0.2, ease:'power2.out', yoyo:true, repeat:1}}, {t});")
            js.append(f"tl.to('{sel} .glow', {{opacity:1, duration:0.3}}, {t});")
            js.append(f"sheen('{sel} .sh', {t + 0.1});")
            if kinds[j] == "impact":
                js.append(f"tl.to('{sel} .ici, {sel} .ic.on', {{opacity:1, duration:0.3}}, {t});")
                js.append(f"tl.fromTo('{sel} .icw', {{rotate:0}}, {{rotate:360, duration:0.6, ease:'power3.out'}}, {t});")
            else:
                js.append(f"tl.fromTo('{sel} .halo', {{opacity:0, scale:0.6}}, {{opacity:1, scale:1.25, duration:0.7, ease:'sine.inOut', yoyo:true, repeat:{max(1, int((dur - t) / 0.7) - 1)}}}, {t});")
                js.append(f"tl.fromTo('{sel} .tag', {{scale:1.6, rotate:-8, opacity:0}}, {{scale:1, rotate:0, opacity:1, duration:0.45, ease:'back.out(2.5)', immediateRender:false}}, {t + 0.15});")
            if prev is not None:
                js.append(f"tl.to('{prev} .glow', {{opacity:0.25, duration:0.4}}, {t});")
            prev = sel
    if i < NS - 1:
        js.append(ex(f"#st{i}", dur))
    return cid, dur, scene_file(cid, dur, "", body, "\n".join(js)), [lt(cid, x) + START[cid] for x in times[1:]]


def scene_hook(i):
    cid, st, en = SCENES[i]
    dur = round(en - st, 3)
    n = next(node for kind, node in SCN[i]["items"] if kind == "hook")
    eb = find(n, "gm-eyebrow"); bt = find(n, "kv-hero-bigtitle"); sub = find(n, "kv-hero-sub")
    chips = findall(n, "kv-chip"); badge = find(n, "gm-source-badge")
    lines = [l for l in text(bt).split("\n") if l.strip()] or ["AURORA"]
    mx = max(len(l) for l in lines)
    fs = int(max(50, min(112, 880 / (mx * 0.66))))
    t_lines = sum(max(1, math.ceil(len(l) * fs * 0.66 / 880)) for l in lines)
    sub_t = text(sub) if sub is not None else ""
    rows, roww = 1, 0
    for ch in chips:
        cw_ = len(text(ch)) * 30 * 0.64 + 100
        if roww + cw_ > 980:
            rows += 1; roww = 0
        roww += cw_ + 16
    est = 70 + 244 + 50 + t_lines * fs * 1.16 * 1.14 + _lines(sub_t, 40, 940, 0.6) * 52 + rows * 76 + (56 if badge is not None else 0) + 5 * 28
    zk = round(max(0.7, min(1.0, 880 / est)), 3)
    chip_col = {"c1": "#f5c451", "c2": "#60a5fa", "c3": "#f87171"}
    chip_html = "".join(
        f'<div class="hc" style="--cc:{chip_col.get(next((c for c in ch.cls if c in chip_col), "c1"))}">{icon(ch)}<span>{esc(text(ch))}</span></div>'
        for ch in chips)
    tlines = "".join(f'<span class="hl">{esc(l)}</span>' for l in lines)
    css = f"""
.hk{{position:absolute;left:50px;right:50px;top:250px;height:910px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;text-align:center;}}
.heb{{display:inline-flex;align-items:center;gap:14px;background:linear-gradient(135deg,#f5c451,#ffe08a);color:#1a1205;font-weight:900;letter-spacing:5px;text-transform:uppercase;font-size:32px;padding:14px 36px;border-radius:99px;box-shadow:0 12px 40px rgba(245,196,81,.4);}}
.hlogo{{position:relative;width:200px;height:200px;}}
.hlogo img{{position:absolute;inset:0;width:200px;height:200px;border-radius:50%;filter:drop-shadow(0 0 34px rgba(59,130,246,.65));}}
.hlogo .ring{{position:absolute;inset:-22px;border-radius:50%;border:3px solid rgba(96,165,250,.45);border-top-color:#f5c451;}}
.hplate{{display:inline-block;padding:20px 34px 26px;border-radius:28px;border:2px solid rgba(96,165,250,.45);background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(59,130,246,.08));box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(59,130,246,.2);max-width:980px;}}
.htw{{position:relative;}}
.ht{{font-weight:900;font-size:{fs}px;line-height:1.16;letter-spacing:-1px;text-transform:uppercase;}}
.ht .hl{{display:block;padding-top:.14em;background:linear-gradient(180deg,#ffffff 0%,{HERO} 38%,{HERO} 100%);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;filter:drop-shadow(0 6px 26px {HERO}66);}}
.ht.gl{{position:absolute;inset:0;pointer-events:none;}}
.ht.gl .hl{{background:linear-gradient(105deg,transparent 0%,transparent 42%,rgba(255,255,255,.95) 50%,transparent 58%,transparent 100%);background-size:300% 100%;background-position:100% 0;-webkit-background-clip:text;background-clip:text;filter:none;}}
.hsub{{font-size:40px;font-weight:800;line-height:1.3;color:#f5c451;text-transform:uppercase;letter-spacing:1px;text-shadow:0 2px 20px rgba(245,196,81,.35);padding-top:.1em;}}
.hcs{{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;max-width:980px;}}
.hc{{display:inline-flex;align-items:center;gap:12px;font-weight:800;font-size:30px;text-transform:uppercase;color:#e2e8f0;padding:14px 26px;border-radius:99px;background:rgba(15,23,42,.65);border:2px solid rgba(255,255,255,.16);box-shadow:0 10px 30px rgba(2,6,23,.5);}}
.hc i{{color:var(--cc);}}
.hbd{{display:inline-flex;align-items:center;gap:12px;font-weight:800;font-size:28px;color:#60a5fa;padding:10px 26px;border-radius:99px;background:rgba(37,99,235,.12);border:2px solid rgba(59,130,246,.45);}}
.hbd i{{color:#f5c451;}}
"""
    body = f"""<div class="hk" id="hk"><div class="hz" style="zoom:{zk};display:flex;flex-direction:column;align-items:center;gap:28px;">
<div class="heb">{icon(eb)}<span>{esc(text(eb))}</span></div>
<div class="hlogo"><div class="ring"></div><img src="assets/img/logo-kenvinzone.svg" alt=""/></div>
<div class="hplate"><div class="htw"><div class="ht">{tlines}</div><div class="ht gl">{tlines}</div></div></div>
{'<div class="hsub">' + inner(sub) + '</div>' if sub is not None else ''}
<div class="hcs">{chip_html}</div>
{'<div class="hbd">' + icon(badge) + '<span>' + esc(text(badge)) + '</span></div>' if badge is not None else ''}
</div></div>"""
    js = f"""
// frame 0 already shows the full cover (thumbnail). Life comes from glints, a spinning ring and chip pulses.
tl.fromTo('#hk .hlogo .ring', {{rotate:0}}, {{rotate:360, duration:{dur}, ease:'none'}}, 0);
tl.fromTo('#hk .ht.gl .hl', {{backgroundPosition:'100% 0'}}, {{backgroundPosition:'0% 0', duration:1.3, stagger:0.12, ease:'power2.inOut', immediateRender:false}}, 0.5);
tl.fromTo('#hk .ht.gl .hl', {{backgroundPosition:'100% 0'}}, {{backgroundPosition:'0% 0', duration:1.3, stagger:0.12, ease:'power2.inOut', immediateRender:false}}, {round(min(dur - 2.0, 4.6), 2)});
QA('.hc').forEach((c,i)=>{{ tl.fromTo(c, {{scale:1}}, {{scale:1.1, duration:0.18, ease:'power3.out', immediateRender:false}}, 1.6 + i*0.55); tl.to(c, {{scale:1, duration:0.4, ease:'expo.out'}}, 1.78 + i*0.55); }});
tl.fromTo('#hk .hplate', {{boxShadow:'0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(59,130,246,.2)'}}, {{boxShadow:'0 18px 50px rgba(0,0,0,.45),0 0 70px rgba(59,130,246,.5)', duration:1.2, ease:'sine.inOut', yoyo:true, repeat:{max(1, int(dur / 1.2) - 1)}}}, 0);
tl.fromTo('#hk .hlogo img', {{scale:1}}, {{scale:1.06, duration:0.9, ease:'sine.inOut', yoyo:true, repeat:{max(1, int(dur / 0.9) - 1)}}}, 0);
{ex('#hk', dur)}
"""
    return cid, dur, scene_file(cid, dur, css, body, js), []


def scene_outro(i):
    cid, st, en = SCENES[i]
    dur = round(en - st, 3)
    n = SCN[i]["items"][0][1] if SCN[i]["items"] else DECK_SLIDES[i]
    root_n = DECK_SLIDES[i]
    pill = find(root_n, "kv-outro-pill"); mt = find(root_n, "kv-outro-main-title"); url = find(root_n, "kv-at-url")
    pls = findall(root_n, "kv-platform-pill"); btn = find(root_n, "kv-outro-btn"); dis = find(root_n, "kv-disclaimer")
    l1 = "".join(clean(c) if isinstance(c, str) else ("\n" if c.tag == "br" else (text(c) if c.tag != "em" else "")) for c in (mt.ch if mt is not None else []))
    l1 = " ".join(x.strip() for x in l1.split("\n") if x.strip())
    em = find(mt, tag="em") if mt is not None else None
    l2 = text(em).replace("\n", " ") if em is not None else ""
    mx = max(len(l1), len(l2), 1)
    fs = int(max(48, min(80, 960 * 1.5 / (mx * 0.62))))
    nl = sum(max(1, math.ceil(len(x) * fs * 0.64 / 960)) for x in (l1, l2) if x)
    est = 74 + nl * fs * 1.2 * 1.14 + 76 + 64 + 112 + (_lines(text(dis), 25, 900, 0.5) * 36 if dis is not None else 0) + 5 * 30
    zk = round(max(0.7, min(1.0, 860 / est)), 3)
    u = text(url) or "aurora.kenvinzone.com"
    css = f"""
.ou{{position:absolute;left:50px;right:50px;top:250px;height:910px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px;text-align:center;}}
.opill{{font-weight:900;font-size:30px;letter-spacing:5px;text-transform:uppercase;color:#38d5e7;background:rgba(56,213,231,.12);border:2px solid rgba(56,213,231,.45);padding:14px 40px;border-radius:99px;box-shadow:0 6px 30px rgba(56,213,231,.25);}}
.omt{{position:relative;font-weight:900;font-size:{fs}px;line-height:1.2;letter-spacing:-.5px;text-transform:uppercase;}}
.omt .a{{display:block;color:#fff;text-shadow:0 2px 26px rgba(56,213,231,.35);padding-top:.12em;}}
.omt .b{{display:block;padding-top:.16em;background:linear-gradient(135deg,#ffffff 0%,#fde047 30%,#f59e0b 65%,#38d5e7 100%);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;filter:drop-shadow(0 3px 18px rgba(243,190,98,.55));}}
.omt.gl{{position:absolute;inset:0;pointer-events:none;}}
.omt.gl .a,.omt.gl .b{{color:transparent;text-shadow:none;filter:none;background:linear-gradient(105deg,transparent 42%,rgba(255,255,255,.95) 50%,transparent 58%);background-size:300% 100%;background-position:100% 0;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
.ourl{{font-family:'JBM',monospace;font-weight:800;font-size:58px;color:#38d5e7;letter-spacing:1px;text-shadow:0 0 26px rgba(56,213,231,.7),0 0 50px rgba(56,213,231,.35);}}
.ourl .cur{{display:inline-block;width:.08em;height:.9em;background:#38d5e7;margin-left:.08em;vertical-align:-.1em;}}
.opls{{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;}}
.opl{{font-family:'JBM',monospace;font-weight:800;font-size:28px;letter-spacing:1px;color:#cbd5e1;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.18);padding:12px 24px;border-radius:99px;}}
.obtn{{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;padding:30px 60px;font-weight:900;font-size:38px;letter-spacing:1px;text-transform:uppercase;background:linear-gradient(135deg,#f59e0b 0%,#fde047 50%,#f59e0b 100%);color:#050811;border-radius:99px;border:3px solid rgba(255,255,255,.85);box-shadow:0 12px 50px rgba(245,158,11,.6),0 0 40px rgba(253,224,71,.4);}}
.obtn .gl{{position:absolute;top:-50%;left:0;width:30%;height:200%;background:linear-gradient(115deg,transparent 0%,rgba(255,255,255,.75) 50%,transparent 100%);transform:translateX(-200%) rotate(12deg);}}
.odis{{font-size:25px;line-height:1.45;color:rgba(255,255,255,.55);max-width:900px;}}
"""
    chars = "".join(f'<span class="uc">{esc(ch)}</span>' for ch in u)
    lines = f'<span class="a">{esc(l1)}</span>' + (f'<span class="b">{esc(l2)}</span>' if l2 else "")
    body = f"""<div class="ou" id="ou"><div class="oz" style="zoom:{zk};display:flex;flex-direction:column;align-items:center;gap:30px;">
<div class="opill">{esc(text(pill) or 'KENVINZONE AURORA')}</div>
<div class="omt"><div>{lines}</div><div class="omt gl">{lines}</div></div>
<div class="ourl">{chars}<span class="cur"></span></div>
<div class="opls">{''.join(f'<span class="opl">{esc(text(p))}</span>' for p in pls)}</div>
<div class="obtn"><span>{esc(text(btn) or 'TRẢI NGHIỆM DÙNG THỬ MIỄN PHÍ')}</span><div class="gl"></div></div>
{'<div class="odis">' + esc(text(dis)) + '</div>' if dis is not None else ''}
</div></div>"""
    t = 0.15
    nglint = max(1, int((dur - 3.2) / 2.4))
    js = f"""
tl.fromTo('#ou .opill', {{opacity:0, y:-40, scale:0.8}}, {{opacity:1, y:0, scale:1, duration:0.5, ease:'back.out(2)'}}, {t});
tl.fromTo('#ou .omt .a', {{opacity:0, scale:1.25, filter:'blur(14px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.6, ease:'expo.out'}}, {t + 0.25});
tl.fromTo('#ou .omt .b', {{opacity:0, scale:1.25, filter:'blur(14px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.6, ease:'expo.out'}}, {t + 0.55});
tl.fromTo('#ou .omt.gl .a, #ou .omt.gl .b', {{backgroundPosition:'100% 0'}}, {{backgroundPosition:'0% 0', duration:1.2, stagger:0.15, ease:'power2.inOut', immediateRender:false}}, {t + 1.3});
tl.fromTo('#ou .uc', {{opacity:0}}, {{opacity:1, duration:0.01, stagger:0.045, ease:'none'}}, {t + 0.95});
tl.fromTo('#ou .cur', {{opacity:1}}, {{opacity:0, duration:0.3, ease:'steps(1)', yoyo:true, repeat:{max(1, int(dur / 0.3))}}}, {t + 0.95});
tl.fromTo('#ou .opl', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, stagger:0.12, ease:'back.out(2)'}}, {t + 1.8});
tl.fromTo('#ou .obtn', {{opacity:0, scale:0.6}}, {{opacity:1, scale:1, duration:0.6, ease:'back.out(2.4)'}}, {t + 2.3});
tl.fromTo('#ou .obtn', {{scale:1}}, {{scale:1.05, duration:0.6, ease:'sine.inOut', yoyo:true, repeat:{max(1, int((dur - 3.2) / 0.6))}, immediateRender:false}}, {t + 3.0});
tl.fromTo('#ou .obtn .gl', {{xPercent:-200}}, {{xPercent:520, duration:1.2, ease:'power2.inOut', repeat:{nglint}, repeatDelay:1.2, immediateRender:false}}, {t + 2.8});
tl.fromTo('#ou .odis', {{opacity:0}}, {{opacity:1, duration:0.6}}, {t + 2.8});
"""
    return cid, dur, scene_file(cid, dur, css, body, js), [START[cid] + t + 2.3]


def captions():
    groups, js = [], []
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
            js.append(f"tl.fromTo('#cw{gi}_{wi}', {{color:'#cbd5e1', backgroundColor:'rgba(56,213,231,0)'}}, {{color:'#04121a', backgroundColor:'rgba(56,213,231,1)', duration:0.06, immediateRender:false}}, {ws_});"
                      f"tl.to('#cw{gi}_{wi}', {{color:'#ffffff', backgroundColor:'rgba(56,213,231,0)', duration:0.06}}, {round(max(w['end'], w['start'] + 0.07) + OFF, 3)});")
        js.append(f"tl.to('#cg{gi} .cpill', {{opacity:0, duration:0.1, ease:'power2.in'}}, {e2 - 0.1});"
                  f"tl.set('#cg{gi}', {{opacity:0, visibility:'hidden'}}, {e2});")
    css = """
.cg{position:absolute;left:0;right:0;top:1190px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;max-width:960px;padding:14px 26px;border-radius:22px;background:rgba(2,6,23,.74);border:1px solid rgba(255,255,255,.08);font-size:44px;font-weight:800;line-height:1.35;color:#cbd5e1;}
.cw{display:inline-block;padding:0 6px;border-radius:10px;}
"""
    return "captions", TOTAL, scene_file("captions", TOTAL, css, "\n".join(groups), "\n".join(js))


# ================================================================ ROOT
def root(scene_meta, reveal_abs):
    hosts = "\n".join(
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{st}" data-duration="{dur}" '
        f'data-track-index="{i+2}" data-track-kind="{"captions" if cid == "captions" else "graphics"}" data-width="{W}" data-height="{H}" style="z-index:{50 if cid == "captions" else 10+i};"></div>'
        for i, (cid, st, dur) in enumerate(scene_meta))
    sfx, k = [], 0

    def add(file, t, vol):
        nonlocal k
        sfx.append(f'<audio id="sfx{k}" class="clip" src="assets/audio/{file}" data-start="{max(0, round(t, 3))}" data-duration="{SFX_LEN[file]}" data-volume="{vol}" data-track-index="{40+k}"></audio>')
        k += 1
    for cid, st, en in SCENES[1:]:
        add("whoosh.mp3", st - 0.25, 0.4)
    for t in reveal_abs[:-1]:
        add("tick.mp3", t + 0.05, 0.3)
    if reveal_abs:
        add("impact.mp3", reveal_abs[-1], 0.4)
    bgm_vol = D.get("bgm_volume", 0.14)
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<link rel="stylesheet" href="assets/fa/css/all.min.css" />
<script src="assets/js/gsap.min.js"></script>
<style>
{FONT_CSS}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#020617;}}
#root{{position:relative;width:100%;height:100%;font-family:'BVP',sans-serif;color:#f8fafc;}}
.bg{{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 30%,#0b1730 0%,#020617 62%,#01030b 100%);}}
#bgc{{position:absolute;inset:0;width:{W}px;height:{H}px;}}
.orb{{position:absolute;width:900px;height:900px;border-radius:50%;filter:blur(130px);}}
#orbA{{left:-380px;top:120px;background:radial-gradient(circle,rgba(59,130,246,.42),rgba(59,130,246,0) 70%);}}
#orbB{{right:-420px;top:820px;background:radial-gradient(circle,{HERO}55,rgba(0,0,0,0) 70%);}}
#orbC{{left:90px;top:1300px;width:700px;height:700px;background:radial-gradient(circle,rgba(56,213,231,.22),rgba(0,0,0,0) 70%);}}
.vig{{position:absolute;inset:0;background:radial-gradient(130% 90% at 50% 45%,transparent 55%,rgba(0,0,0,.7) 100%);}}
.brand{{position:absolute;left:60px;right:60px;top:176px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}}
.brand img{{width:42px;height:42px;}}
.brand .n{{font-size:28px;font-weight:800;letter-spacing:1px;color:rgba(255,255,255,.8);}}
.brand .d{{margin-left:auto;font-weight:900;font-size:28px;letter-spacing:4px;background:linear-gradient(90deg,#60a5fa,#38d5e7,#f5c451);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.prog{{position:absolute;left:60px;right:60px;top:228px;height:5px;border-radius:3px;background:rgba(255,255,255,.08);z-index:60;overflow:hidden;}}
#progf{{height:100%;width:100%;background:linear-gradient(90deg,#3b82f6,#a855f7,#f5c451,#10b981);transform-origin:left center;}}
.wm{{position:absolute;right:60px;bottom:96px;display:flex;align-items:center;gap:12px;opacity:.75;z-index:60;}}
.wm img{{width:44px;height:44px;}} .wm span{{font-weight:800;font-size:28px;letter-spacing:2px;color:#e2e8f0;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
  <div class="bg"></div>
  <div class="orb" id="orbA"></div><div class="orb" id="orbB"></div><div class="orb" id="orbC"></div>
  <canvas id="bgc" width="{W}" height="{H}"></canvas>
  <div class="vig"></div>
  <div class="brand" id="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">KenvinZone</span><span class="d">AURORA</span></div>
  <div class="prog" id="prog"><div id="progf"></div></div>
  <div class="wm"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span>AURORA</span></div>
{hosts}
  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{OFF}" data-volume="1" data-track-index="30"></audio>
  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{bgm_vol}" data-fade-out="2" data-track-index="31"></audio>
  {''.join(sfx)}
</div>
<script>
(function(){{
const tl = gsap.timeline({{ paused: true }});
// "Candle Mono" background (monochrome, large candle blocks), a pure function of time
const cv = document.getElementById('bgc'); const ctx = cv.getContext('2d');
let seed = 20261029; const rnd = () => {{ seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; }};
const w = {W}, h = {H}, A = {D.get('bg_alpha', 0.13)}, CW = w / 9, SPEED = {D.get('bg_speed', 90)}, C = '226,232,240';
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
  ctx.strokeStyle = 'rgba(' + C + ',' + (A * 1.4) + ')'; ctx.lineWidth = 3; ctx.stroke();
  const line = 'rgba(' + C + ',' + (A * 1.1) + ')';
  for (let i = i0; i <= i1; i++) {{
    const k = CS[i], x0 = i * CW - off, bx = x0 + CW * 0.5, top = Math.min(k.o, k.c), bh = Math.abs(k.o - k.c) || 2, bw = CW * 0.56, bl = x0 + CW * 0.22, bot = top + bh;
    ctx.strokeStyle = line; ctx.lineWidth = 2.4;
    ctx.beginPath(); ctx.moveTo(bx, k.hi); ctx.lineTo(bx, top); ctx.moveTo(bx, bot); ctx.lineTo(bx, k.lo); ctx.stroke();
    if (k.up) {{ ctx.lineWidth = 2.6; ctx.strokeRect(bl, top, bw, bh); }}
    else {{ ctx.fillStyle = 'rgba(' + C + ',' + (A * 0.85) + ')'; ctx.fillRect(bl, top, bw, bh); }}
  }}
}}
const P = {{ t: 0 }}; draw(0);
tl.fromTo(P, {{ t: 0 }}, {{ t: {TOTAL}, duration: {TOTAL}, ease: 'none', onUpdate(){{ draw(P.t); }} }}, 0);
tl.fromTo('#progf', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {TOTAL}, ease: 'none' }}, 0);
// slow aurora light drift
const R = {max(1, int(TOTAL / 7))};
tl.fromTo('#orbA', {{ x: 0, y: 0 }}, {{ x: 260, y: 180, duration: 7, ease: 'sine.inOut', yoyo: true, repeat: R }}, 0);
tl.fromTo('#orbB', {{ x: 0, y: 0 }}, {{ x: -240, y: -220, duration: 8, ease: 'sine.inOut', yoyo: true, repeat: R }}, 0);
tl.fromTo('#orbC', {{ x: 0, opacity: 0.6 }}, {{ x: 300, opacity: 1, duration: 6, ease: 'sine.inOut', yoyo: true, repeat: R }}, 0);
// the cover has its own big logo: the brand row arrives with the second scene
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
    for old in comps.glob("s*.html"):
        old.unlink()
    meta, reveals = [], []
    for i in range(NS):
        kinds = [k for k, _ in SCN[i]["items"]]
        if "hook" in kinds:
            cid, dur, txt, rv = scene_hook(i)
        elif "outro" in kinds:
            cid, dur, txt, rv = scene_outro(i)
        else:
            cid, dur, txt, rv = scene_generic(i)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(START[cid], 3), dur))
        reveals += rv
    if D.get("captions", True):
        cid, dur, txt = captions()
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    (ROOT / "index.html").write_text(root(meta, reveals), encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", [(c, s, d) for c, s, d in meta])


if __name__ == "__main__":
    main()
