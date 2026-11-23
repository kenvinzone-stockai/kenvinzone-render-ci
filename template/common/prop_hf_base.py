"""Shared HyperFrames helpers for KenvinZone Trade Quy Future templates."""
from __future__ import annotations

import html

W, H = 1080, 1920
SFX_LEN = {"whoosh.mp3": 0.62, "tick.mp3": 0.13, "impact.mp3": 0.73}

_VI = "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB"
_LE = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
_EM = "U+200D,U+23F0,U+23F3,U+26A0-26A1,U+2705,U+274C,U+2B50,U+1F3AF,U+1F4A1,U+1F4B0,U+1F4B5,U+1F4C8-1F4CA,U+1F4CC-1F4CD,U+1F525,U+1F680,U+1F6E1"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def font_css() -> str:
    r = []
    for w in (500, 700, 800, 900):
        r.append(f"@font-face{{font-family:'BVP';font-weight:{w};src:url('assets/fonts/be-vietnam-pro-vietnamese-{w}-normal.woff2') format('woff2');unicode-range:{_VI};}}")
        r.append(f"@font-face{{font-family:'BVP';font-weight:{w};src:url('assets/fonts/be-vietnam-pro-latin-ext-{w}-normal.woff2') format('woff2');unicode-range:{_LE};}}")
        r.append(f"@font-face{{font-family:'BVP';font-weight:{w};src:url('assets/fonts/be-vietnam-pro-latin-{w}-normal.woff2') format('woff2');}}")
        r.append(f"@font-face{{font-family:'BVP';font-weight:{w};src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:{_EM};}}")
    for w in (700, 800):
        r.append(f"@font-face{{font-family:'JBM';font-weight:{w};src:url('assets/fonts/jetbrains-mono-vietnamese-{w}-normal.woff2') format('woff2');unicode-range:{_VI};}}")
        r.append(f"@font-face{{font-family:'JBM';font-weight:{w};src:url('assets/fonts/jetbrains-mono-latin-{w}-normal.woff2') format('woff2');}}")
    return "\n".join(r)


def base_css(accent: str, accent2: str) -> str:
    return (
        "#root{position:absolute;inset:0;font-family:'BVP',sans-serif;color:#f8fafc;}"
        ".mono{font-family:'JBM',monospace;font-variant-numeric:tabular-nums;}"
        f".kicker{{font-size:28px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:{accent};}}"
        f".gttl{{padding-top:.14em;line-height:1.18;background:linear-gradient(180deg,#ffffff 10%,{accent} 95%);-webkit-background-clip:text;background-clip:text;color:transparent;}}"
        f".goldttl{{padding-top:.14em;line-height:1.18;background:linear-gradient(180deg,#fff7d6 10%,{accent2} 95%);-webkit-background-clip:text;background-clip:text;color:transparent;}}"
    )


def scene_file(cid: str, dur: float, css: str, body: str, js: str, accent: str, accent2: str) -> str:
    s_open, s_close = "<" + "script>", "</" + "script>"
    return (
        f"<template>\n<style>{font_css()}{base_css(accent, accent2)}{css}</style>\n"
        f'<div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-duration="{dur}">\n{body}\n</div>\n'
        f"{s_open}\n(function(){{\nconst tl = gsap.timeline({{ paused: true }});\n"
        f'const Q = (s) => document.querySelector(\'[data-composition-id="{cid}"] \' + s);\n'
        "function counter(sel, from, to, at, dur, dec, prefix, suffix){"
        "const el = Q(sel); if(!el) return; const o = {v: from};"
        "const f = (v) => (prefix||'') + Math.abs(v).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec}) + (suffix||'');"
        "el.textContent = f(from);"
        "tl.fromTo(o, {v: from}, {v: to, duration: dur, ease: 'power3.out', immediateRender:false, onUpdate(){ el.textContent = f(o.v); }}, at);}\n"
        f'{js}\nwindow.__timelines["{cid}"] = tl;\n}})();\n{s_close}\n</template>\n'
    )


def captions_scene(subs: dict, off: float, total: float, accent: str, accent2: str) -> tuple[str, float, str]:
    groups, js = [], []
    caps = subs.get("captions") or []
    for gi, c in enumerate(caps):
        s, e = round(c["start"] + off, 3), round(c["end"] + off, 3)
        nxt = caps[gi + 1]["start"] + off if gi + 1 < len(caps) else e + 0.6
        e2 = round(min(max(e + 0.25, e), nxt - 0.02), 3)
        ws = "".join(f'<span class="cw" id="cw{gi}_{wi}">{esc(w["text"])}</span> ' for wi, w in enumerate(c["words"]))
        groups.append(f'<div class="cg" id="cg{gi}"><div class="cpill">{ws}</div></div>')
        js.append(f"tl.set('#cg{gi}', {{opacity:1, visibility:'visible'}}, {s});tl.fromTo('#cg{gi} .cpill', {{y:18, opacity:0}}, {{y:0, opacity:1, duration:0.14, ease:'power3.out', immediateRender:false}}, {s});")
        for wi, w in enumerate(c["words"]):
            ws_ = round(w["start"] + off, 3)
            js.append(f"tl.fromTo('#cw{gi}_{wi}', {{color:'#cbd5e1', backgroundColor:'rgba(56,213,231,0)'}}, {{color:'#070f1d', backgroundColor:'{accent}', duration:0.06, immediateRender:false}}, {ws_});tl.to('#cw{gi}_{wi}', {{color:'#ffffff', backgroundColor:'rgba(56,213,231,0)'}}, {round(max(w['end'], w['start']+0.07)+off, 3)});")
        js.append(f"tl.to('#cg{gi} .cpill', {{opacity:0, duration:0.1, ease:'power2.in'}}, {e2-0.1});tl.set('#cg{gi}', {{opacity:0, visibility:'hidden'}}, {e2});")
    css = ".cg{position:absolute;left:40px;right:192px;top:1190px;text-align:center;opacity:0;visibility:hidden;}.cpill{display:inline-block;max-width:848px;padding:14px 26px;border-radius:22px;background:rgba(10,20,38,.94);border:1.5px solid rgba(255,255,255,.18);box-shadow:0 12px 35px rgba(0,0,0,.65);font-size:44px;font-weight:800;line-height:1.35;color:#cbd5e1;}.cw{display:inline-block;padding:0 6px;border-radius:10px;}"
    return "captions", total, scene_file("captions", total, css, "\n".join(groups), "\n".join(js), accent, accent2)


def root_html(scene_meta, total: float, off: float, bgm_vol: float, date_str: str, accent: str, accent2: str, brand_text: str, impact_at: float | None = None) -> str:
    s_open, s_close = "<" + "script>", "</" + "script>"
    gsap_tag = "<" + 'script src="assets/js/gsap.min.js">' + "</" + "script>"
    hosts = [
        f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{st}" data-duration="{dur}" data-track-index="{i+2}" data-track-kind="{"captions" if cid=="captions" else "graphics"}" data-width="{W}" data-height="{H}" style="z-index:{50 if cid=="captions" else 10+i};"></div>'
        for i, (cid, st, dur) in enumerate(scene_meta)
    ]
    sfx = [
        f'<audio id="sfx{k}" class="clip" src="assets/audio/whoosh.mp3" data-start="{max(0, round(st-0.22, 3))}" data-duration="{SFX_LEN["whoosh.mp3"]}" data-volume="0.40" data-track-index="{40+k}"></audio>'
        for k, (cid, st, _d) in enumerate(scene_meta[1:]) if cid != "captions"
    ]
    if impact_at is not None:
        sfx.append(f'<audio id="sfx_imp" class="clip" src="assets/audio/impact.mp3" data-start="{round(impact_at, 3)}" data-duration="{SFX_LEN["impact.mp3"]}" data-volume="0.50" data-track-index="55"></audio>')
    return (
        f'<!doctype html>\n<html lang="vi"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />{gsap_tag}\n'
        f"<style>{font_css()}*{{margin:0;padding:0;box-sizing:border-box;}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#070F1D;}}"
        f"#root{{position:relative;width:100%;height:100%;font-family:'BVP',sans-serif;color:#f8fafc;}}"
        ".bg{position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 28%,#101D35 0%,#070F1D 62%,#040811 100%);}"
        ".gridbg{position:absolute;inset:0;background-image:radial-gradient(rgba(56,213,231,.14) 1px,transparent 1px);background-size:32px 32px;opacity:.55;}"
        f".glow{{position:absolute;left:-180px;right:-180px;top:220px;height:960px;filter:blur(130px);background:radial-gradient(circle at 50% 40%,{accent}33,{accent2}14 48%,transparent 72%);}}"
        ".brand{position:absolute;left:56px;right:56px;top:176px;height:44px;display:flex;align-items:center;gap:14px;z-index:60;}"
        f".brand img{{width:40px;height:40px;}}.brand .n{{font-size:26px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,.85);}}.brand .d{{margin-left:auto;font-family:'JBM';font-weight:800;font-size:24px;color:{accent};}}"
        f".prog{{position:absolute;left:56px;right:56px;top:228px;height:5px;border-radius:3px;background:rgba(255,255,255,.10);z-index:60;overflow:hidden;}}#progf{{height:100%;width:100%;background:linear-gradient(90deg,{accent},{accent2});transform-origin:left center;}}</style></head>\n"
        f'<body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">\n'
        f'  <div class="bg"></div><div class="gridbg"></div><div class="glow"></div>\n'
        f'  <div class="brand"><img src="assets/img/logo-kenvinzone.svg" alt=""/><span class="n">{esc(brand_text)}</span><span class="d">{esc(date_str)}</span></div>\n'
        '  <div class="prog"><div id="progf"></div></div>\n'
        f"{chr(10).join(hosts)}\n"
        f'  <audio id="vo" class="clip" src="assets/audio/voiceover.mp3" data-start="{off}" data-volume="1" data-track-index="30"></audio>\n'
        f'  <audio id="bgm" class="clip" src="assets/audio/bgm_loop.mp3" data-start="0" data-volume="{bgm_vol}" data-fade-out="2" data-track-index="31"></audio>\n'
        f"  {''.join(sfx)}\n</div>"
        f"{s_open}(function(){{const tl=gsap.timeline({{paused:true}});tl.fromTo('#progf',{{scaleX:0}},{{scaleX:1,duration:{total},ease:'none'}},0);window.__timelines['main']=tl;}})();{s_close}</body></html>"
    )
