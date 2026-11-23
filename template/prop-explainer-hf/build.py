#!/usr/bin/env python3
"""KenvinZone Trade Quy Future - Prop Explainer -> HyperFrames (7 scenes, 60-110s)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from hf_base import captions_scene, esc, root_html, scene_file

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))

OFF = float(DATA.get("audio_offset", 0.9))
OUTRO = float(DATA.get("outro_hold", 3.4))
WORDS = [(w["text"], w["start"], w["end"]) for c in SUBS["captions"] for w in c["words"]]
VO_LEN = float(SUBS.get("duration", WORDS[-1][2] if WORDS else 60.0))
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
SLIDES = SUBS["slides"]
if len(SLIDES) != 7:
    raise SystemExit(f"Template prop-explainer-hf can dung 7 dong script (dang co {len(SLIDES)}).")

ACCENT = str(DATA.get("accent") or "#38D5E7")
ACCENT2 = str(DATA.get("accent2") or "#F3BE62")
S = [round(float(SLIDES[i]["start"]) + OFF, 3) if i > 0 else 0.0 for i in range(7)]
SCENES = [(f"s{i}", S[i], S[i + 1] if i < 6 else TOTAL) for i in range(7)]


def scene_s0():
    dur = round(SCENES[0][2] - SCENES[0][1], 3)
    h = DATA.get("hook") or {}
    lines = h.get("title_lines") or ["GIẢI MÃ QUỸ FUTURES"]
    t_html = "".join(f'<span class="{"gttl" if i == 0 else "goldttl"}">{esc(l)}</span>' for i, l in enumerate(lines))
    chips = "".join(
        f'<span class="e0-chip e0-{esc(c.get("tone","cyan"))}">{esc(c.get("text",""))}</span>'
        for c in (h.get("chips") or [])[:3]
    )
    css = f"""
.e0-wrap{{position:absolute;left:56px;right:56px;top:270px;text-align:center;}}
.e0-badge{{display:inline-block;padding:12px 30px;border-radius:999px;border:2px solid {ACCENT};background:{ACCENT}20;color:{ACCENT};font-weight:900;font-size:28px;letter-spacing:2px;}}
.e0-plate{{position:relative;overflow:hidden;margin-top:28px;padding:34px 28px;border-radius:28px;border:2px solid {ACCENT}88;background:linear-gradient(160deg,rgba(16,29,53,.94),rgba(7,15,29,.90));box-shadow:0 24px 60px rgba(0,0,0,.55),0 0 46px {ACCENT}28;}}
.e0-plate h1{{font-size:60px;font-weight:900;line-height:1.18;}}
.e0-plate h1 span{{display:block;}}
.e0-sheen{{position:absolute;top:-20%;bottom:-20%;left:0;width:24%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.34),transparent);transform:translateX(-160%) skewX(-18deg);pointer-events:none;}}
.e0-sub{{margin-top:28px;font-size:34px;font-weight:700;color:#cbd5e1;line-height:1.42;}}
.e0-chips{{margin-top:34px;display:flex;flex-wrap:wrap;justify-content:center;gap:14px;}}
.e0-chip{{padding:12px 24px;border-radius:999px;font-family:'JBM';font-size:26px;font-weight:800;border:1.5px solid rgba(255,255,255,.22);background:rgba(16,29,53,.88);color:#e2e8f0;}}
.e0-rose{{border-color:#fb7185;color:#fda4af;background:rgba(251,113,133,.14);}}
.e0-gold{{border-color:#f3be62;color:#fde68a;background:rgba(243,190,98,.14);}}
.e0-green{{border-color:#34d399;color:#6ee7b7;background:rgba(52,211,153,.14);}}
.e0-cyan{{border-color:#38d5e7;color:#a5f3fc;background:rgba(56,213,231,.14);}}
"""
    body = f"""<div class="e0-wrap" id="e0-stage">
  <div class="e0-badge" id="e0-badge"><span>{esc(h.get('badge','GIẢI MÃ QUỸ FUTURES'))}</span></div>
  <div class="e0-plate"><h1>{t_html}</h1><i class="e0-sheen" id="e0-sheen"></i></div>
  <div class="e0-sub">{esc(h.get('sub',''))}</div>
  <div class="e0-chips" id="e0-chips">{chips}</div>
</div>"""
    js = f"""
tl.fromTo('#e0-sheen', {{xPercent:-160}}, {{xPercent:560, duration:0.9, ease:'power2.inOut', immediateRender:false}}, 0.35);
tl.fromTo('#e0-chips', {{y:18, opacity:0}}, {{y:0, opacity:1, duration:0.4, ease:'power3.out'}}, 0.55);
tl.to('#e0-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});
"""
    return "s0", dur, scene_file("s0", dur, css, body, js, ACCENT, ACCENT2)


def scene_s1():
    dur = round(SCENES[1][2] - SCENES[1][1], 3)
    s1 = DATA.get("s1") or {}
    css = f"""
.e1-wrap{{position:absolute;left:56px;right:56px;top:270px;text-align:center;}}
.e1-ttl{{font-size:48px;font-weight:900;}}
.e1-stat{{margin-top:34px;padding:38px 32px;border-radius:28px;border:2px solid #fb718588;background:linear-gradient(160deg,rgba(251,113,133,.14),rgba(16,29,53,.94));box-shadow:0 20px 54px rgba(0,0,0,.5);}}
.e1-big{{font-family:'JBM';font-size:96px;font-weight:800;color:#fb7185;line-height:1.05;}}
.e1-lbl{{margin-top:12px;font-size:32px;font-weight:800;color:#fff;}}
.e1-box{{margin-top:30px;padding:30px 32px;border-radius:24px;border:1.5px solid {ACCENT}55;background:rgba(16,29,53,.92);font-size:32px;font-weight:600;color:#e2e8f0;line-height:1.48;text-align:left;}}
.e1-box b{{color:{ACCENT2};}}
"""
    body = f"""<div class="e1-wrap" id="e1-stage">
  <div class="kicker">{esc(s1.get('kicker','VẤN ĐỀ THỰC TẾ'))}</div>
  <div class="e1-ttl gttl">{esc(s1.get('title','VÌ SAO TRADER HAY MẤT TIỀN OAN?'))}</div>
  <div class="e1-stat" id="e1-stat"><div class="e1-big">{esc(s1.get('stat_value','$140+'))}</div><div class="e1-lbl">{esc(s1.get('stat_label',''))}</div></div>
  <div class="e1-box" id="e1-box">{esc(s1.get('summary',''))}</div>
</div>"""
    js = f"""gsap.set('#e1-stat, #e1-box', {{opacity:0}});
tl.fromTo('#e1-stat', {{opacity:0, scale:0.88}}, {{opacity:1, scale:1, duration:0.42, ease:'back.out(1.7)', immediateRender:false}}, 0.12);
tl.fromTo('#e1-box', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {round(dur*0.38, 3)});
tl.to('#e1-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s1", dur, scene_file("s1", dur, css, body, js, ACCENT, ACCENT2)


def scene_s2():
    dur = round(SCENES[2][2] - SCENES[2][1], 3)
    s2 = DATA.get("s2") or {}
    vtype = str(s2.get("type") or "compare_table")
    if vtype == "drawdown_meter":
        steps = s2.get("bars") or []
        bars_html, js_b = [], []
        for i, b in enumerate(steps[:3]):
            pct = max(8, min(100, int(b.get("pct", 50))))
            col = str(b.get("color") or ACCENT)
            bars_html.append(
                f'<div class="dm-row" id="dm-r{i}"><div class="dm-top"><span>{esc(b.get("label",""))}</span><b class="mono" style="color:{col}">{esc(b.get("val",""))}</b></div>'
                f'<div class="dm-trk"><div class="dm-fill" id="dm-f{i}" style="width:{pct}%;background:{col};"></div></div>'
                f'<div class="dm-sub">{esc(b.get("note",""))}</div></div>'
            )
            t_i = round(dur * (0.12 + i * 0.28), 3)
            js_b.append(f"tl.fromTo('#dm-r{i}', {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.35, immediateRender:false}}, {t_i});tl.fromTo('#dm-f{i}', {{scaleX:0}}, {{scaleX:1, duration:0.7, ease:'expo.out', immediateRender:false}}, {t_i+0.12});")
        css = f"""
.e2-wrap{{position:absolute;left:56px;right:56px;top:270px;}}
.e2-hd{{text-align:center;margin-bottom:32px;}}.e2-ttl{{font-size:48px;font-weight:900;}}
.dm-row{{padding:24px 28px;margin-bottom:22px;border-radius:22px;background:rgba(16,29,53,.92);border:1.5px solid rgba(255,255,255,.14);}}
.dm-top{{display:flex;justify-content:space-between;align-items:center;font-size:30px;font-weight:800;margin-bottom:14px;}}
.dm-trk{{height:26px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;}}
.dm-fill{{height:100%;border-radius:99px;transform-origin:left center;}}
.dm-sub{{margin-top:12px;font-size:26px;color:#cbd5e1;font-weight:600;}}
"""
        body = f"""<div class="e2-wrap" id="e2-stage"><div class="e2-hd"><div class="kicker">{esc(s2.get('kicker','MÔ PHỎNG CƠ CHẾ'))}</div><div class="e2-ttl gttl">{esc(s2.get('title',''))}</div></div>{''.join(bars_html)}</div>"""
        js = f"""gsap.set('#e2-stage .dm-row', {{opacity:0}});gsap.set('#e2-stage .dm-fill', {{scaleX:0}});{''.join(js_b)}
tl.to('#e2-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
        return "s2", dur, scene_file("s2", dur, css, body, js, ACCENT, ACCENT2)

    # Default: compare_table
    rows = s2.get("rows") or []
    r_html, js_r = [], []
    for i, r in enumerate(rows[:4]):
        win = str(r.get("winner") or "")
        c1 = "ct-win" if win == "left" else ("ct-lose" if win == "right" else "")
        c2 = "ct-win" if win == "right" else ("ct-lose" if win == "left" else "")
        r_html.append(
            f'<div class="ct-row" id="ct-r{i}"><div class="ct-k">{esc(r.get("metric",""))}</div>'
            f'<div class="ct-cols"><div class="ct-c {c1}">{esc(r.get("left",""))}</div><div class="ct-c {c2}">{esc(r.get("right",""))}</div></div></div>'
        )
        js_r.append(f"tl.fromTo('#ct-r{i}', {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.35, ease:'expo.out', immediateRender:false}}, {round(dur*(0.10+i*0.21), 3)});")
    css = f"""
.e2-wrap{{position:absolute;left:50px;right:50px;top:266px;}}
.e2-hd{{text-align:center;margin-bottom:24px;}}.e2-ttl{{font-size:46px;font-weight:900;}}
.ct-head{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;text-align:center;font-family:'JBM';font-size:28px;font-weight:800;}}
.ct-h1{{padding:12px;border-radius:14px;background:{ACCENT2}22;border:1.5px solid {ACCENT2};color:{ACCENT2};}}
.ct-h2{{padding:12px;border-radius:14px;background:{ACCENT}22;border:1.5px solid {ACCENT};color:{ACCENT};}}
.ct-row{{padding:18px 20px;margin-bottom:14px;border-radius:18px;background:rgba(16,29,53,.92);border:1px solid rgba(255,255,255,.12);}}
.ct-k{{font-size:24px;font-weight:800;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;}}
.ct-cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
.ct-c{{padding:12px 14px;border-radius:12px;background:rgba(7,15,29,.7);font-size:26px;font-weight:700;color:#e2e8f0;line-height:1.3;}}
.ct-win{{border:1.5px solid #34d399;background:rgba(52,211,153,.14);color:#6ee7b7;}}
.ct-lose{{border:1.5px solid #fb718566;color:#fda4af;}}
"""
    body = f"""<div class="e2-wrap" id="e2-stage"><div class="e2-hd"><div class="kicker">{esc(s2.get('kicker','SO SÁNH TRỰC DIỆN'))}</div><div class="e2-ttl gttl">{esc(s2.get('title',''))}</div></div>
  <div class="ct-head"><div class="ct-h1">{esc(s2.get('left_label','PHƯƠNG ÁN A'))}</div><div class="ct-h2">{esc(s2.get('right_label','PHƯƠNG ÁN B'))}</div></div>
  {''.join(r_html)}</div>"""
    js = f"""gsap.set('#e2-stage .ct-row', {{opacity:0}});{''.join(js_r)}
tl.to('#e2-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s2", dur, scene_file("s2", dur, css, body, js, ACCENT, ACCENT2)


def scene_s3():
    dur = round(SCENES[3][2] - SCENES[3][1], 3)
    s3 = DATA.get("s3") or {}
    cards, js_c = [], []
    for i, it in enumerate((s3.get("items") or [])[:3]):
        cards.append(f'<div class="e3-card" id="e3-c{i}"><div class="e3-n mono">0{i+1}</div><div><div class="e3-t">{esc(it.get("title",""))}</div><div class="e3-d">{esc(it.get("detail",""))}</div></div></div>')
        js_c.append(f"tl.fromTo('#e3-c{i}', {{opacity:0, x:-36}}, {{opacity:1, x:0, duration:0.38, ease:'expo.out', immediateRender:false}}, {round(dur*(0.10+i*0.27), 3)});")
    css = f"""
.e3-wrap{{position:absolute;left:56px;right:56px;top:270px;}}
.e3-hd{{text-align:center;margin-bottom:30px;}}.e3-ttl{{font-size:48px;font-weight:900;}}
.e3-card{{display:flex;gap:22px;align-items:flex-start;padding:26px 28px;margin-bottom:22px;border-radius:22px;border:1.5px solid {ACCENT}55;background:rgba(16,29,53,.92);}}
.e3-n{{flex:0 0 68px;height:68px;border-radius:16px;display:flex;align-items:center;justify-content:center;background:{ACCENT2}22;border:2px solid {ACCENT2};color:{ACCENT2};font-size:32px;font-weight:800;}}
.e3-t{{font-size:32px;font-weight:800;color:#fff;line-height:1.25;}}.e3-d{{margin-top:8px;font-size:27px;color:#cbd5e1;line-height:1.38;}}
"""
    body = f"""<div class="e3-wrap" id="e3-stage"><div class="e3-hd"><div class="kicker">{esc(s3.get('kicker','CHI TIẾT CẦN NẮM'))}</div><div class="e3-ttl gttl">{esc(s3.get('title',''))}</div></div>{''.join(cards)}</div>"""
    js = f"""gsap.set('#e3-stage .e3-card', {{opacity:0}});{''.join(js_c)}
tl.to('#e3-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s3", dur, scene_file("s3", dur, css, body, js, ACCENT, ACCENT2)


def scene_s4():
    dur = round(SCENES[4][2] - SCENES[4][1], 3)
    s4 = DATA.get("s4") or {}
    bullets = "".join(f'<li id="e4-b{i}">✅ {esc(b)}</li>' for i, b in enumerate((s4.get("bullets") or [])[:3]))
    css = f"""
.e4-wrap{{position:absolute;left:56px;right:56px;top:276px;}}
.e4-hd{{text-align:center;margin-bottom:28px;}}.e4-ttl{{font-size:48px;font-weight:900;}}
.e4-verdict{{padding:32px 30px;border-radius:26px;border:2px solid #34d39988;background:linear-gradient(160deg,rgba(52,211,153,.14),rgba(16,29,53,.95));font-size:32px;font-weight:800;color:#fff;line-height:1.42;}}
.e4-ul{{list-style:none;margin-top:28px;}}.e4-ul li{{padding:20px 24px;margin-bottom:16px;border-radius:18px;background:rgba(16,29,53,.90);border:1px solid {ACCENT}44;font-size:29px;font-weight:700;color:#e2e8f0;line-height:1.38;}}
"""
    body = f"""<div class="e4-wrap" id="e4-stage"><div class="e4-hd"><div class="kicker">💡 CHỐT NHANH THỰC CHIẾN</div><div class="e4-ttl goldttl">{esc(s4.get('title','CÁCH XỬ LÝ CHUẨN NHẤT'))}</div></div>
  <div class="e4-verdict" id="e4-v">{esc(s4.get('verdict',''))}</div><ul class="e4-ul">{bullets}</ul></div>"""
    js = f"""gsap.set('#e4-v, #e4-stage li', {{opacity:0}});
tl.fromTo('#e4-v', {{opacity:0, scale:0.92}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(1.6)', immediateRender:false}}, 0.08);
tl.to('#e4-stage li', {{opacity:1, y:0, duration:0.35, stagger:{round(dur*0.2, 2)}}}, {round(dur*0.32, 3)});
tl.to('#e4-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s4", dur, scene_file("s4", dur, css, body, js, ACCENT, ACCENT2)


def scene_s5():
    dur = round(SCENES[5][2] - SCENES[5][1], 3)
    s5 = DATA.get("s5") or {}
    css = f"""
.e5-wrap{{position:absolute;left:56px;right:56px;top:280px;text-align:center;}}
.e5-ttl{{font-size:48px;font-weight:900;}}
.e5-box{{margin-top:32px;padding:34px 30px;border-radius:26px;border:2px solid {ACCENT}80;background:rgba(16,29,53,.94);text-align:left;}}
.e5-h{{font-family:'JBM';font-size:32px;font-weight:800;color:{ACCENT};margin-bottom:14px;}}
.e5-p{{font-size:30px;font-weight:600;color:#e2e8f0;line-height:1.45;}}
.e5-aur{{margin-top:28px;padding:28px 30px;border-radius:24px;border:2px solid {ACCENT2}88;background:linear-gradient(145deg,rgba(243,190,98,.14),rgba(16,29,53,.92));text-align:left;}}
.e5-at{{font-size:30px;font-weight:900;color:{ACCENT2};}}.e5-ad{{margin-top:10px;font-size:27px;color:#cbd5e1;line-height:1.4;}}
"""
    body = f"""<div class="e5-wrap" id="e5-stage"><div class="kicker">QUẢN TRỊ RỦI RO & KỶ LUẬT</div><div class="e5-ttl gttl">{esc(s5.get('title','GIỮ VỮNG TÀI KHOẢN QUỸ'))}</div>
  <div class="e5-box" id="e5-b1"><div class="e5-h">{esc(s5.get('rule_head','NGUYÊN TẮC VÀNG'))}</div><div class="e5-p">{esc(s5.get('rule_body',''))}</div></div>
  <div class="e5-aur" id="e5-b2"><div class="e5-at">⚡ KENVINZONE AURORA · TRADINGVIEW</div><div class="e5-ad">{esc(s5.get('aurora_note','Hệ thống setup Entry – F-SL – TP sẵn 1R/2R giúp đánh đều tay trên MNQ/MGC, tránh overtrade & vi phạm Consistency Rule.'))}</div></div></div>"""
    js = f"""gsap.set('#e5-b1, #e5-b2', {{opacity:0}});
tl.fromTo('#e5-b1', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, immediateRender:false}}, 0.1);
tl.fromTo('#e5-b2', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, immediateRender:false}}, {round(dur*0.48, 3)});
tl.to('#e5-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s5", dur, scene_file("s5", dur, css, body, js, ACCENT, ACCENT2)


def scene_s6():
    dur = round(SCENES[6][2] - SCENES[6][1], 3)
    out = DATA.get("outro") or {}
    css = f"""
.e6-wrap{{position:absolute;left:56px;right:56px;top:290px;text-align:center;}}
.e6-tag{{display:inline-block;padding:10px 26px;border-radius:999px;border:1.5px solid {ACCENT};background:{ACCENT}18;font-size:28px;font-weight:800;color:{ACCENT};letter-spacing:2px;}}
.e6-ttl{{margin-top:26px;font-size:52px;font-weight:900;}}
.e6-url{{margin:32px auto 0;padding:28px 32px;border-radius:24px;border:2px solid {ACCENT2};background:rgba(16,29,53,.94);}}
.e6-url .u{{font-family:'JBM';font-size:40px;font-weight:800;color:{ACCENT2};}}.e6-url .s{{margin-top:10px;font-size:27px;color:#cbd5e1;font-weight:600;}}
.e6-cta{{margin-top:32px;font-size:34px;font-weight:800;color:#fff;line-height:1.4;}}
.e6-disc{{margin-top:34px;font-size:22px;color:#64748b;line-height:1.4;}}
"""
    body = f"""<div class="e6-wrap" id="e6-stage"><div class="e6-tag"><span>KENVINZONE.TRADEQUY</span></div>
  <div class="e6-ttl gttl">{esc(out.get('heading','TRA CỨU RULE & SĂN MÃ GIẢM GIÁ'))}</div>
  <div class="e6-url" id="e6-u"><div class="u">prop.kenvinzone.com</div><div class="s">So sánh Bulenox · Earn2Trade · Topstep & Máy tính Size miễn phí</div></div>
  <div class="e6-cta" id="e6-c">{esc(out.get('cta','Follow kênh & xem toàn bộ link ưu đãi ở bình luận ghim!'))}</div>
  <div class="e6-disc">Nội dung chia sẻ kiến thức & luật quỹ Futures, không phải lời khuyên đầu tư tài chính.</div></div>"""
    js = f"""gsap.set('#e6-u, #e6-c', {{opacity:0}});
tl.fromTo('#e6-u', {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(1.7)', immediateRender:false}}, 0.25);
tl.fromTo('#e6-c', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.35, immediateRender:false}}, {round(dur*0.42, 3)});"""
    return "s6", dur, scene_file("s6", dur, css, body, js, ACCENT, ACCENT2)


def main():
    comps = ROOT / "compositions"
    comps.mkdir(exist_ok=True)
    meta = []
    for fn in (scene_s0, scene_s1, scene_s2, scene_s3, scene_s4, scene_s5, scene_s6):
        cid, dur, txt = fn()
        st = next(s for c, s, _e in SCENES if c == cid)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(st, 3), dur))
    if DATA.get("captions", True):
        cid, dur, txt = captions_scene(SUBS, OFF, TOTAL, ACCENT, ACCENT2)
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    html_out = root_html(meta, TOTAL, OFF, float(DATA.get("bgm_volume", 0.16)), str(DATA.get("date", "")), ACCENT, ACCENT2, "KENVINZONE · TRADE QUỸ FUTURE", impact_at=SCENES[1][1] + 0.12)
    (ROOT / "index.html").write_text(html_out, encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
