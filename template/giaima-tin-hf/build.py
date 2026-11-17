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
DATA = json.loads(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8").read()
                  .replace("⑂", "↳"))   # ⑂ không font nào có → thay bằng mũi tên rẽ nhánh chuẩn
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
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-latin-ext-500-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/be-vietnam-pro-latin-500-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-vietnamese-700-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-latin-ext-700-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/be-vietnam-pro-latin-700-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-vietnamese-800-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-latin-ext-800-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/be-vietnam-pro-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-vietnamese-900-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-latin-ext-900-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/be-vietnam-pro-latin-900-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-vietnamese-800-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-latin-ext-800-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/jetbrains-mono-latin-800-normal.woff2') format('woff2');}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-vietnamese-700-normal.woff2') format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-latin-ext-700-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/jetbrains-mono-latin-700-normal.woff2') format('woff2');}
/*KZ-SYMBOLS*/
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'BVP';font-weight:500;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'BVP';font-weight:700;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'BVP';font-weight:800;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'BVP';font-weight:900;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'JBM';font-weight:700;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:U+200D,U+23F0,U+23F3,U+26A0-26A1,U+26FD,U+2705,U+274C,U+2B50,U+1F31F,U+1F389,U+1F3AF,U+1F3E6,U+1F3ED,U+1F402,U+1F43B,U+1F440,U+1F449,U+1F48E,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4B8-1F4B9,U+1F4C4,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F4E2-1F4E3,U+1F4F0,U+1F501,U+1F504,U+1F514,U+1F525,U+1F534-1F535,U+1F550,U+1F5D3,U+1F680,U+1F6E1-1F6E2,U+1F7E0-1F7E2,U+1F91D,U+1F947,U+1F9E0,U+1F9ED,U+1FA99;}
@font-face{font-family:'JBM';font-weight:800;src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:U+2190-2311,U+2318-2319,U+231C-2321,U+2324-2328,U+232B-232C,U+2373-2375,U+237A,U+237D,U+2387,U+2394,U+239B-23AE,U+23CE-23CF,U+23E3,U+23E5,U+23E8,U+2460-2469,U+2500-269C,U+269E-269F,U+26A2-26B8,U+26C0-26C3,U+26E2,U+2701-2704,U+2706-2709,U+270C-2727,U+2729-274B,U+274D,U+274F-2752,U+2756,U+2758-275E,U+2761-2794,U+2798-27AF,U+27B1-27BE;}
/*/KZ-SYMBOLS*/



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


_ACC_RE = re.compile(r"&lt;(b|mark)&gt;(.*?)&lt;/\1&gt;", re.S)


def rich(s, cls="acc"):
    """Escape nhưng giữ <b>/<mark> do Brain đánh dấu → từ khoá vàng/xanh neon (Kinetic Word Accent)."""
    return _ACC_RE.sub(lambda m: f'<span class="{cls}">{m.group(2)}</span>', esc(s))


def _norm(w):
    return re.sub(r"[^\w]", "", str(w).lower())


def acc_times(i, text, after_abs, fallback):
    """Mốc video (giây) khi giọng đọc tới từng cụm nhấn trong text — dò theo word timestamps của dòng i."""
    st = float(SLIDES[i]["start"]); en = st + float(SLIDES[i]["duration"])
    ws = [(_norm(t), s0 + OFF) for t, s0 in WORDS if st - 0.05 <= s0 < en]
    out = []
    for m in re.finditer(r"<(b|mark)>(.*?)</\1>", str(text), re.S):
        toks = [_norm(x) for x in re.sub(r"<[^>]+>", " ", m.group(2)).split() if _norm(x)]
        hit = None
        if toks:
            for k, (w, t) in enumerate(ws):
                if t >= after_abs - 0.3 and w == toks[0] and all(k + j < len(ws) and ws[k + j][0] == toks[j] for j in range(1, min(2, len(toks)))):
                    hit = t; break
        out.append(hit if hit is not None else fallback + 0.5 * len(out))
    return out


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
.q{position:absolute;left:60px;right:60px;top:250px;text-align:center;font-weight:900;line-height:1.18;letter-spacing:-0.5px;}
.q .l1{font-size:56px;color:#f8fafc;display:block;padding-top:.12em;}
.q .l2{font-size:62px;display:block;padding-top:.12em;line-height:1.18;}
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


# ================================================================ S0 THEMATIC VISUAL HOOK (V2)
HOOK_PAL = ["#3b82f6", "#10b981", "#f5c451", "#a855f7"]
_AUTO_HOOK = [
    ("shock_alert", r"bán tháo|bốc hơi|lao dốc|sập|giảm sâu|xả (?:ròng|hàng)|bán ròng kỷ lục|hoảng loạn|cảnh báo|rơi tự do"),
    ("liquidity_pump", r"bơm (?:tiền|ròng|thanh khoản)|\bomo\b|giải ngân|mua ròng|dòng tiền (?:đổ|vào|quay lại)|nới lỏng|hạ lãi suất"),
]


def hook_variant():
    """Brain khai hook.theme_variant; không khai thì tự đoán (chỉ 2 kiểu không cần dữ liệu riêng)."""
    h = D["hook"]; vis = h.get("visual") or {}
    items = vis.get("items") or []
    v = str(h.get("theme_variant") or "").strip()
    need = {"vs_clash": 2, "pie_allocation": 2, "sector_radar": 3}
    if v in need and len(items) < need[v]:
        v = ""
    if v not in ("liquidity_pump", "shock_alert", "vs_clash", "pie_allocation", "sector_radar"):
        blob = " ".join([str(D["source"].get("headline", "")), " ".join(map(str, h.get("title_lines", [])))]).lower()
        v = next((k for k, pat in _AUTO_HOOK if re.search(pat, blob)), "")
    return v, items


def hook_visual(v, items, t):
    """SVG 960×170 đặt ở dải logo (y 328). Khung 0 = trạng thái cuối (thumbnail); hoạt cảnh chạy lại từ t."""
    css, svg, js = "", "", []
    if v == "liquidity_pump":
        bars = []
        hs = [50, 72, 96, 120, 150, 120, 96, 72, 50]
        for i, hh in enumerate(hs):
            x = 300 + i * 42
            bars.append(f'<rect class="hp-bar" x="{x}" y="{165 - hh}" width="28" height="{hh}" rx="6" fill="url(#hpg)" style="transform-origin:{x + 14}px 165px;"/>')
        parts = "".join(f'<circle class="hp-pt" cx="{300 + (i * 53) % 370}" cy="150" r="{3 + i % 3}" fill="#67e8f9" opacity="0"/>' for i in range(14))
        svg = (f'<defs><linearGradient id="hpg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#10b981"/><stop offset="1" stop-color="#67e8f9"/></linearGradient></defs>'
               f'{"".join(bars)}{parts}<text x="700" y="70" class="hv-t" fill="#67e8f9">{esc(str((D["hook"].get("visual") or {}).get("label") or "DÒNG TIỀN")[:14])}</text>')
        js.append(f"QA('.hp-bar').forEach((b,i)=>tl.fromTo(b, {{scaleY:0}}, {{scaleY:1, duration:0.55, ease:'back.out(1.6)', immediateRender:false}}, {t} + Math.abs(i-4)*0.07));")
        js.append(f"QA('.hp-pt').forEach((p,i)=>tl.fromTo(p, {{attr:{{cy:150}}, opacity:0.95}}, {{attr:{{cy:-10}}, opacity:0, duration:1.4, ease:'power1.out', immediateRender:false}}, {t + 0.4} + (i%7)*0.18 + Math.floor(i/7)*0.9));")
    elif v == "shock_alert":
        pts = "60,40 170,60 240,50 330,95 400,80 480,128 560,112 650,150 900,165"
        svg = (f'<polyline id="hs-ln" points="{pts}" fill="none" stroke="#ef4444" stroke-width="8" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="1200" style="filter:drop-shadow(0 0 10px #ef4444);"/>'
               f'<polygon id="hs-bolt" points="500,6 452,92 490,92 466,166 540,64 500,64 528,6" fill="#fde047" stroke="#f59e0b" stroke-width="3" style="filter:drop-shadow(0 0 16px #f59e0b);transform-origin:496px 86px;"/>'
               f'<text x="60" y="150" class="hv-t" fill="#f87171">▼ RỦI RO</text>')
        js.append(f"tl.fromTo('#hs-ln', {{strokeDashoffset:1200}}, {{strokeDashoffset:0, duration:0.7, ease:'power2.in', immediateRender:false}}, {t});")
        js.append(f"tl.fromTo('#hs-bolt', {{opacity:0, scale:2.4}}, {{opacity:1, scale:1, duration:0.18, ease:'power4.out', immediateRender:false}}, {t + 0.6});")
        js.append(f"tl.fromTo('#h0-flash', {{opacity:0}}, {{opacity:1, duration:0.07, yoyo:true, repeat:3, ease:'none', immediateRender:false}}, {t + 0.62});")
    elif v == "vs_clash":
        a, b = items[0], items[1]
        def blk(it, x, c, ident):
            lab = esc(str(it.get("label", ""))[:18]); val = esc(str(it.get("value", ""))[:14])
            return (f'<g id="{ident}"><rect x="{x}" y="22" width="380" height="126" rx="22" fill="{c}22" stroke="{c}" stroke-width="3"/>'
                    f'<text x="{x + 190}" y="70" text-anchor="middle" class="hv-t" fill="#fff">{lab}</text>'
                    f'<text x="{x + 190}" y="126" text-anchor="middle" class="hv-n" fill="{c}">{val}</text></g>')
        svg = (blk(a, 30, "#4ade80" if a.get("tone") != "down" else "#f87171", "hvA") + blk(b, 550, "#f87171" if b.get("tone") != "up" else "#4ade80", "hvB")
               + '<polygon id="hv-sp" points="480,30 494,70 536,72 502,96 514,138 480,114 446,138 458,96 424,72 466,70" fill="#fde047" style="filter:drop-shadow(0 0 14px #f59e0b);transform-origin:480px 85px;"/>'
               + '<text x="480" y="96" text-anchor="middle" class="hv-vs">VS</text>')
        js.append(f"tl.fromTo('#hvA', {{x:-260, opacity:0}}, {{x:0, opacity:1, duration:0.45, ease:'power4.in', immediateRender:false}}, {t});")
        js.append(f"tl.fromTo('#hvB', {{x:260, opacity:0}}, {{x:0, opacity:1, duration:0.45, ease:'power4.in', immediateRender:false}}, {t});")
        js.append(f"tl.fromTo('#hv-sp', {{scale:0, rotation:-40}}, {{scale:1, rotation:0, duration:0.3, ease:'back.out(3)', immediateRender:false}}, {t + 0.45});")
        js.append(f"tl.fromTo('#hvA', {{x:0}}, {{x:-14, duration:0.08, yoyo:true, repeat:1, immediateRender:false}}, {t + 0.45}); tl.fromTo('#hvB', {{x:0}}, {{x:14, duration:0.08, yoyo:true, repeat:1, immediateRender:false}}, {t + 0.45});")
    elif v == "pie_allocation":
        its = items[:4]
        tot = sum(max(0.0, float(i.get("value", 0) or 0)) for i in its) or 1.0
        hi = max(range(len(its)), key=lambda k: float(its[k].get("value", 0) or 0)) if not any(i.get("hi") for i in its) else next(k for k, i in enumerate(its) if i.get("hi"))
        cx, cy, r = 480, 85, 78
        acc, slices, legs = -math.pi / 2, [], []
        for k, it in enumerate(its):
            frac = max(0.0, float(it.get("value", 0) or 0)) / tot
            a0, a1 = acc, acc + frac * 2 * math.pi; acc = a1
            if frac >= 0.999:
                d = f"M{cx},{cy - r} A{r},{r} 0 1,1 {cx - 0.01},{cy - r} Z"
            else:
                large = 1 if frac > 0.5 else 0
                d = f"M{cx},{cy} L{cx + r * math.cos(a0):.1f},{cy + r * math.sin(a0):.1f} A{r},{r} 0 {large},1 {cx + r * math.cos(a1):.1f},{cy + r * math.sin(a1):.1f} Z"
            mid = (a0 + a1) / 2
            c = it.get("color") or HOOK_PAL[k % 4]
            slices.append(f'<path id="pie{k}" d="{d}" fill="{c}" stroke="#0b1220" stroke-width="3" data-dx="{16 * math.cos(mid):.1f}" data-dy="{16 * math.sin(mid):.1f}"/>')
            lx = 40 if k % 2 == 0 else 600; ly = 60 + (k // 2) * 62
            legs.append(f'<g><rect x="{lx}" y="{ly - 22}" width="22" height="22" rx="5" fill="{c}"/><text x="{lx + 32}" y="{ly - 3}" class="hv-l" fill="#e2e8f0">{esc(str(it.get("label", ""))[:12])} '
                        f'<tspan fill="{c}">{esc(it.get("display") or (str(round(float(it.get("value", 0) or 0))) + "%"))}</tspan></text></g>')
        svg = f'<g id="pie" style="transform-origin:{cx}px {cy}px;">{"".join(slices)}</g>{"".join(legs)}'
        js.append(f"tl.fromTo('#pie', {{rotation:-360}}, {{rotation:0, duration:1.0, ease:'power3.out', immediateRender:false}}, {t});")
        js.append(f"(function(){{const s=Q('#pie{hi}'); tl.fromTo(s, {{x:0, y:0, filter:'drop-shadow(0 0 0px #fff)'}}, {{x:+s.dataset.dx, y:+s.dataset.dy, filter:'drop-shadow(0 0 14px #fde047)', duration:0.4, ease:'back.out(2.5)', immediateRender:false}}, {t + 1.0});}})();")
        # thumbnail: lát nổi bật đã tách sẵn (gsap.set) — hoạt cảnh xoay rồi bật lại từ t
        js.append(f"(function(){{const s=Q('#pie{hi}'); gsap.set(s, {{x:+s.dataset.dx, y:+s.dataset.dy, filter:'drop-shadow(0 0 14px #fde047)'}});}})();")
    elif v == "sector_radar":
        its = items[:4]
        chips = []
        for k, it in enumerate(its):
            lx = 20 if k % 2 == 0 else 640; ly = 22 + (k // 2) * 76
            chips.append(f'<g class="sr-c" id="sr{k}"><rect x="{lx}" y="{ly}" width="300" height="58" rx="14" fill="rgba(56,189,248,.12)" stroke="#38bdf8" stroke-width="2.5"/>'
                         f'<text x="{lx + 150}" y="{ly + 39}" text-anchor="middle" class="hv-l" fill="#e0f2fe">{esc(str(it.get("label", ""))[:16])}</text></g>')
        svg = ('<circle cx="480" cy="85" r="80" fill="none" stroke="rgba(56,189,248,.45)" stroke-width="2"/><circle cx="480" cy="85" r="52" fill="none" stroke="rgba(56,189,248,.25)" stroke-width="1.5" stroke-dasharray="4 6"/>'
               '<defs><linearGradient id="srg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8" stop-opacity="0"/><stop offset="1" stop-color="#38bdf8" stop-opacity=".6"/></linearGradient></defs>'
               '<g id="sr-sw" style="transform-origin:480px 85px;"><path d="M480,85 L560,85 A80,80 0 0,0 537,28 Z" fill="url(#srg)"/><line x1="480" y1="85" x2="560" y2="85" stroke="#38bdf8" stroke-width="3"/></g>'
               + "".join(chips))
        js.append(f"tl.fromTo('#sr-sw', {{rotation:0}}, {{rotation:720, duration:2.4, ease:'none', immediateRender:false}}, {t});")
        js.append(f"QA('.sr-c').forEach((c,i)=>tl.fromTo(c.querySelector('rect'), {{attr:{{fill:'rgba(56,189,248,.12)'}}}}, {{attr:{{fill:'rgba(56,189,248,.45)'}}, duration:0.18, yoyo:true, repeat:1, immediateRender:false}}, {t + 0.25} + i*0.3));")
    return css, svg, js


# ================================================================ S0 HOOK
def s0():
    cid, dur = mk("s0", 0)
    h = D["hook"]; src = D["source"]
    lines = h["title_lines"]
    # Giữ công thức gốc (tiêu đề ngắn vẫn to tới 120px) nhưng NÂNG SÀN tối thiểu để tiêu đề dài không bị bé xíu.
    fa = int(max(58, min(120, 900 / (max(1, len(lines[0])) * 0.72))))
    fb = int(max(54, min(104, 900 / (max(1, len(lines[1]) if len(lines) > 1 else 1) * 0.72))))
    v, vitems = hook_variant()
    t_h = lt(cid, B(0, 0))
    hv_css, hv_svg, hv_js = hook_visual(v, vitems, t_h + 0.15) if v else ("", "", [])
    py = 515 if v else 495                     # dải hình ẩn dụ (y 328–498) đẩy bảng tiêu đề xuống 20px
    stamp = str(h.get("stamp") or "").strip()[:28]
    s_col = {"red": "#ef4444", "down": "#ef4444", "green": "#22c55e", "up": "#22c55e"}.get(str(h.get("stamp_tone", "")), GOLD)
    tb = py + int(fa * 1.34) + (int(fb * 1.30) if len(lines) > 1 else 0) + 44
    chips = "".join(f'<div class="h0-chip" id="h0-c{i}" style="border-color:{TONE.get(c.get("tone","gold"))}99;color:{TONE.get(c.get("tone","gold"))};"><span>{esc(c["icon"])}</span> {esc(c["text"])}</div>' for i, c in enumerate(h["chips"]))
    css = f"""
.h0-eb{{position:absolute;top:250px;left:0;right:0;text-align:center;}}
.h0-eb span{{display:inline-block;background:linear-gradient(135deg,#fde68a,{GOLD});color:#0b0f19;font-weight:900;font-size:30px;letter-spacing:4px;text-transform:uppercase;padding:14px 36px;border-radius:99px;box-shadow:0 10px 40px rgba(245,196,81,.45);}}
.h0-logo{{position:absolute;top:345px;left:0;right:0;text-align:center;}} .h0-logo img{{width:120px;height:120px;filter:drop-shadow(0 0 30px rgba(59,130,246,.6));}}
.h0-plate{{position:absolute;top:{py}px;left:40px;right:40px;text-align:center;}}
.h0-vis{{position:absolute;left:60px;top:328px;width:960px;height:170px;}}
.h0-vis .hv-t{{font-family:'BVP';font-weight:900;font-size:30px;letter-spacing:1px;}}
.h0-vis .hv-l{{font-family:'BVP';font-weight:800;font-size:26px;}}
.h0-vis .hv-n{{font-family:'JBM';font-weight:800;font-size:44px;}}
.h0-vis .hv-vs{{font-family:'BVP';font-weight:900;font-size:30px;fill:#0b0f19;}}
.h0-stamp{{position:absolute;left:0;right:0;top:{tb - 16}px;text-align:center;}}
.h0-stamp span{{display:inline-block;transform:rotate(-3deg);padding:8px 26px;border:5px double {s_col};border-radius:12px;background:rgba(15,23,42,.9);box-shadow:0 10px 34px rgba(0,0,0,.6),0 0 28px {s_col}66;font-family:'JBM';font-weight:800;font-size:34px;letter-spacing:2px;color:#fff;white-space:nowrap;text-transform:uppercase;}}
.h0-flash{{position:absolute;inset:0;pointer-events:none;opacity:0;box-shadow:inset 0 0 120px 30px rgba(239,68,68,.75);}}
.h0-plate div{{display:inline-block;padding:22px 30px;border-radius:26px;border:2px solid rgba(96,165,250,.45);background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(59,130,246,.08));box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 40px rgba(59,130,246,.2);}}
.h0-plate h1{{font-weight:900;line-height:1.18;text-transform:uppercase;letter-spacing:-0.5px;}}
.h0-plate .a{{display:block;padding-top:.16em;font-size:{fa}px;white-space:nowrap;{gcss(1)}}}
.h0-plate .b{{display:block;padding-top:.12em;font-size:{fb}px;white-space:nowrap;{gcss(0)}}}
.h0-flow{{position:absolute;top:{tb + (84 if stamp else 72)}px;left:40px;right:40px;display:flex;flex-direction:column;align-items:center;gap:26px;}}
.h0-sub{{text-align:center;font-size:38px;font-weight:800;color:{GOLD};text-transform:uppercase;line-height:1.25;padding:0 20px;}}
.h0-chips{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}}
.h0-chip{{font-weight:800;font-size:30px;padding:12px 22px;border-radius:99px;border:2px solid;background:rgba(15,23,42,.6);}}
.h0-src{{text-align:center;}}
.h0-src span{{font-family:'JBM';font-weight:700;font-size:28px;color:#93c5fd;border:2px solid rgba(96,165,250,.45);padding:8px 22px;border-radius:99px;background:rgba(59,130,246,.1);}}
"""
    body = f"""<div id="h0">
<div class="h0-eb"><span>{esc(h['eyebrow'])}</span></div>
{'<svg class="h0-vis" id="h0-vis" viewBox="0 0 960 170">' + hv_svg + '</svg>' + ('<div class="h0-logo" style="top:356px;"><img src="assets/img/logo-kenvinzone.svg" alt="" style="width:110px;height:110px;"/></div>' if v in ('liquidity_pump', 'sector_radar') else '') if v else '<div class="h0-logo"><img src="assets/img/logo-kenvinzone.svg" alt=""/></div>'}
<div class="h0-plate"><div><h1><span class="a">{esc(lines[0])}</span><span class="b">{esc(lines[1]) if len(lines) > 1 else ''}</span></h1></div></div>
<div class="h0-flow">
<div class="h0-sub">{esc(h['sub'])}</div>
<div class="h0-chips">{chips}</div>
<div class="h0-src"><span>Nguồn: {esc(src['short'])} · {esc(src['date'])}</span></div>
</div>
{f'<div class="h0-stamp" id="h0-stamp"><span>{esc(stamp)}</span></div>' if stamp else ''}
<div class="h0-flash" id="h0-flash"></div>
</div>"""
    t = lt(cid, B(0, 0))
    js = f"""
// frame 0 already shows the full cover (thumbnail); chips light up one by one on the hook sentence
QA('.h0-chip').forEach((c,i)=>{{ tl.fromTo(c, {{scale:1}}, {{scale:1.1, duration:0.18, ease:'power3.out', immediateRender:false}}, {t + 1.2} + i*0.5); tl.to(c, {{scale:1, duration:0.4, ease:'expo.out'}}, {t + 1.38} + i*0.5); }});
{"".join(hv_js)}
{f"""tl.fromTo('#h0-stamp', {{opacity:0, scale:2.8, rotation:-10}}, {{opacity:1, scale:1, rotation:0, duration:0.2, ease:'power4.out', immediateRender:false}}, {t_h + 0.85});
tl.fromTo('#h0', {{x:-8, y:3}}, {{x:8, y:-3, duration:0.04, repeat:4, yoyo:true, ease:'none', immediateRender:false}}, {t_h + 1.02});
tl.set('#h0', {{x:0, y:0}}, {t_h + 1.22});""" if stamp else ""}
{ex('#h0', dur)}
"""
    return cid, dur, scene_file(cid, dur, TITLE_CSS + hv_css + css, body, VN_JS + js)


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
    s = D["s3"]; bars = s.get("bars") or []
    mode = str(s.get("mode") or "bars")
    if mode == "vs" and len(s.get("vs") or []) < 2: mode = "bars"
    if mode == "grid" and len(s.get("grid") or []) < 3: mode = "bars"
    cx, half = 540, 420
    mx = max([abs(b["value"]) for b in bars] or [1]) or 1
    rows, js = [], []
    if mode == "vs":            # So găng 1 đối 1: 2 thẻ lớn lao vào nhau, tia lửa ở giữa
        for i, it in enumerate(s["vs"][:2]):
            c = TONE.get(it.get("tone") or ("down" if float(it.get("value", 0) or 0) < 0 else "up"), GOLD)
            x = 60 if i == 0 else 580
            rows.append(f'<div class="s3-vs" id="s3-v{i}" style="left:{x}px;border-color:{c};box-shadow:0 0 40px {c}44;"><div class="lb">{esc(it.get("label", ""))}</div>'
                        f'<div class="nb mono" style="color:{c};font-size:{min(88, int(380 / (max(1, len(str(it.get("display", "")))) * 0.62)))}px;">{esc(it.get("display", ""))}</div>'
                        f'<div class="nt">{esc(it.get("note", ""))}</div></div>')
            t = lt(cid, B(3, it.get("beat", 1), 0.3))
            js.append(f"tl.fromTo('#s3-v{i}', {{opacity:0, x:{-300 if i == 0 else 300}}}, {{opacity:1, x:0, duration:0.45, ease:'power4.in', immediateRender:false}}, {t});"
                      f"tl.fromTo('#s3-v{i}', {{x:0}}, {{x:{-12 if i == 0 else 12}, duration:0.07, yoyo:true, repeat:1, immediateRender:false}}, {t + 0.45});")
        rows.append('<div class="s3-vsb" id="s3-vsb">VS</div>')
        js.append(f"tl.fromTo('#s3-vsb', {{opacity:0, scale:0, rotation:-90}}, {{opacity:1, scale:1, rotation:0, duration:0.35, ease:'back.out(3)', immediateRender:false}}, {lt(cid, B(3, s['vs'][1].get('beat', 1), 0.75))});")
    elif mode == "grid":        # Lưới 4 ô: ngành / mã tiêu biểu / mức thay đổi
        for i, it in enumerate(s["grid"][:4]):
            c = TONE.get(it.get("tone", "gold"), GOLD)
            x = 60 + (i % 2) * 420; y = 520 + (i // 2) * 200
            rows.append(f'<div class="s3-g" id="s3-g{i}" style="left:{x}px;top:{y}px;border-color:{c}aa;"><div class="nm">{esc(it.get("name", ""))}</div>'
                        f'<div class="tk mono">{esc(it.get("tickers", ""))}</div><div class="dv mono" style="color:{c};">{esc(it.get("display", ""))}</div></div>')
            t = lt(cid, B(3, it.get("beat", 1), 0.3 + 0.55 * (i % 2)))
            js.append(f"tl.fromTo('#s3-g{i}', {{opacity:0, scale:0.7, y:30}}, {{opacity:1, scale:1, y:0, duration:0.4, ease:'back.out(1.8)', immediateRender:false}}, {t});"
                      f"tl.fromTo('#s3-g{i}', {{boxShadow:'0 0 0px {c}'}}, {{boxShadow:'0 0 36px {c}', duration:0.25, yoyo:true, repeat:1, immediateRender:false}}, {t + 0.35});")
    for i, b in enumerate(bars if mode == "bars" else []):
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
.s3-vs{position:absolute;top:530px;width:440px;height:300px;border:3px solid;border-radius:28px;background:rgba(15,23,42,.8);text-align:center;padding:26px 18px;}
.s3-vs .lb{font-size:36px;font-weight:900;color:#fff;line-height:1.2;} .s3-vs .nb{margin-top:14px;font-weight:800;line-height:1.1;white-space:nowrap;}
.s3-vs .nt{margin-top:14px;font-size:27px;font-weight:600;color:#cbd5e1;line-height:1.3;}
.s3-vsb{position:absolute;left:490px;top:630px;width:100px;height:100px;border-radius:50%;background:radial-gradient(circle,#fde047,#f59e0b);color:#0b0f19;font-size:40px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 50px #f59e0b;}
.s3-g{position:absolute;width:400px;height:180px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.78);padding:20px 22px;}
.s3-g .nm{font-size:34px;font-weight:900;color:#fff;line-height:1.15;white-space:nowrap;} .s3-g .tk{margin-top:8px;font-size:24px;font-weight:700;color:#93c5fd;white-space:nowrap;}
.s3-g .dv{margin-top:6px;font-size:44px;font-weight:800;white-space:nowrap;}
.s3-co{position:absolute;left:60px;right:60px;top:960px;display:flex;align-items:center;gap:26px;padding:22px 30px;border-radius:24px;border:2px solid rgba(245,196,81,.6);background:rgba(245,196,81,.1);}
.s3-co .n{font-family:'JBM';font-weight:800;font-size:96px;color:#f5c451;line-height:1;} .s3-co .x{font-size:32px;font-weight:700;color:#fde68a;line-height:1.3;}
"""
    _lead = str(s.get('lead', '')).strip()
    _lead_html = (f'<span style="color:#4ade80;">▲ {esc(_lead.split("—")[0].strip())}</span>'
                  + (f' <span style="color:#64748b;">—</span> <span style="color:#f87171;">{esc(_lead.split("—")[1].strip())} ▼</span>' if '—' in _lead else '')) if _lead else ''
    body = f"""<div id="g3">{qtitle(3, s['title_lines'], 's3-q')}
<div class="s3-lead" id="s3-lead">{_lead_html}</div>
{'<div class="s3-axis" id="s3-axis"></div>' if mode == "bars" else ''}{''.join(rows)}
{f'<div class="s3-co" id="s3-co"><div class="n mono"><span id="s3-con">0</span>{esc(co.get("suffix", ""))}</div><div class="x">{esc(co["text"])}</div></div>' if co else ''}
</div>"""
    jss = f"""
gsap.set('#g3 .s3-row, #g3 .s3-vs, #g3 .s3-g, #s3-vsb, #s3-co, #s3-lead', {{opacity:0}});
{q_in('s3-q', max(0.1, lt(cid, B(3, 0))))}
tl.fromTo('#s3-lead', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {lt(cid, B(3, 0, 1.2))});
{f"tl.fromTo('#s3-axis', {{scaleY:0}}, {{scaleY:1, duration:0.7, ease:'power2.inOut', immediateRender:false}}, {lt(cid, B(3, 0, 1.4))});" if mode == "bars" else ""}
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
        html_cards.append(f'<div class="s4-c" id="s4-c{i}" style="top:{y}px;"><div class="s4-n mono">{i+1}</div><div class="s4-big mono" style="font-size:{min(44, int(300 / (max(1, len(str(c.get("big", "")))) * 0.6)))}px;">{esc(c.get("big", ""))}</div>'
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
.s5-c{position:absolute;left:236px;right:180px;height:205px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.72);padding:22px 26px;}
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
        nodes.append(f'<div class="s6-n" id="s6-n{i}" style="top:{y}px;"><div class="h">{rich(n["title"])}</div><div class="d" style="font-size:{30 if len(re.sub("<[^>]+>", "", str(n["text"]))) <= 62 else 26}px;">{rich(n["text"])}</div></div>')
        if i:
            nodes.append(f'<div class="s6-ar" id="s6-a{i}" style="top:{y - 62}px;">▼</div>')
        b = n.get("beat", 1); k = seen.get(b, 0); seen[b] = k + 1
        t = lt(cid, B(6, b, 0.2 + k * 1.6))
        if i:
            js.append(f"tl.fromTo('#s6-a{i}', {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.3, ease:'power2.out', immediateRender:false}}, {t - 0.2});")
        js.append(f"tl.fromTo('#s6-n{i}', {{opacity:0, scale:0.85, filter:'blur(8px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'expo.out', immediateRender:false}}, {t});")
        for k2, ta in enumerate(acc_times(6, f'{n["title"]} {n["text"]}', START[cid] + t, START[cid] + t + 0.7)):
            js.append(f"tl.fromTo(QA('#s6-n{i} .acc')[{k2}], {{scale:1, textShadow:'0 0 0px #f5c451'}}, {{scale:1.12, textShadow:'0 0 22px #f5c451', duration:0.22, yoyo:true, repeat:1, ease:'power2.out', immediateRender:false}}, {round(ta - START[cid], 3)});")
    css = """
.s6-n{position:absolute;left:110px;right:110px;height:170px;border-radius:26px;border:2px solid rgba(168,85,247,.6);background:linear-gradient(135deg,rgba(168,85,247,.18),rgba(15,23,42,.7));text-align:center;padding:26px 24px;}
.s6-n .h{font-size:40px;font-weight:900;color:#fff;line-height:1.15;} .s6-n .d{margin-top:10px;font-size:30px;font-weight:600;color:#e9d5ff;}
.s6-ar{position:absolute;left:0;right:0;text-align:center;font-size:44px;color:#c084fc;}
.s6-n .acc{display:inline-block;color:#fde047;font-weight:900;font-size:1.2em;line-height:1.05;}
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
                    + (f'</svg><div class="tx"><div class="h">{rich(it["title"])}</div><div class="d" style="font-size:{29 if len(re.sub("<[^>]+>", "", str(it["text"]))) <= 70 else 26}px;">{rich(it["text"])}</div></div></div>').replace('class="acc"', 'class="acc" style="color:#fbbf24;"' if warn else 'class="acc"'))
        b = it.get("beat", 1); k = seen.get(b, 0); seen[b] = k + 1
        t = lt(cid, B(7, b, 0.2 + k * 2.2))
        js.append(f"tl.fromTo('#s7-r{i}', {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.45, ease:'expo.out', immediateRender:false}}, {t});"
                  f"tl.fromTo('#s7-p{i}', {{strokeDashoffset:80}}, {{strokeDashoffset:0, duration:0.45, ease:'power2.out', immediateRender:false}}, {t + 0.35});")
        for k2, ta in enumerate(acc_times(7, f'{it["title"]} {it["text"]}', START[cid] + t, START[cid] + t + 0.8)):
            js.append(f"tl.fromTo(QA('#s7-r{i} .acc')[{k2}], {{scale:1, textShadow:'0 0 0px {c}'}}, {{scale:1.12, textShadow:'0 0 22px {c}', duration:0.22, yoyo:true, repeat:1, ease:'power2.out', immediateRender:false}}, {round(ta - START[cid], 3)});")
    css = """
.s7-r{position:absolute;left:60px;right:60px;height:190px;border:2px solid;border-radius:24px;background:rgba(15,23,42,.72);}
.s7-ic{position:absolute;left:26px;top:40px;width:110px;height:110px;}
.s7-r .acc{display:inline-block;color:#4ade80;font-weight:900;font-size:1.2em;line-height:1.05;}
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
// pha 1 — bài học chốt: bảng câu kết nằm giữa, to; pha 2 — bảng lùi lên, hiện handle/CTA/nền tảng/miễn trừ
tl.fromTo('#s8-plate', {{opacity:0, y:220, scale:1.12}}, {{opacity:1, y:200, scale:1.12, duration:0.5, ease:'expo.out', immediateRender:false}}, {max(0.4, lt(cid, B(8, 0, 0.4)))});
tl.to('#s8-plate', {{y:0, scale:1, duration:0.55, ease:'power3.inOut'}}, {lt(cid, B(8, 1)) - 0.45});
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
.cg{position:absolute;left:40px;right:192px;top:1190px;text-align:center;opacity:0;visibility:hidden;}
.cpill{display:inline-block;max-width:848px;padding:14px 26px;border-radius:22px;background:rgba(15,23,42,.94);border:1.5px solid rgba(255,255,255,.18);box-shadow:0 12px 35px rgba(0,0,0,.65),0 0 20px rgba(56,189,248,.15);font-size:44px;font-weight:800;line-height:1.35;color:#cbd5e1;}
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
