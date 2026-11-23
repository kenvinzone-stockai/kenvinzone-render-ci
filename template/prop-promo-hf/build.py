#!/usr/bin/env python3
"""KenvinZone Trade Quy Future - Prop Promo / Flash Sale -> HyperFrames (5 scenes)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from hf_base import captions_scene, esc, root_html, scene_file

ROOT = Path(__file__).resolve().parent
DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data.json", encoding="utf-8"))
SUBS = json.load(open(sys.argv[2] if len(sys.argv) > 2 else ROOT / "subtitle-word-timing.json", encoding="utf-8"))

OFF = float(DATA.get("audio_offset", 0.8))
OUTRO = float(DATA.get("outro_hold", 3.2))
WORDS = [(w["text"], w["start"], w["end"]) for c in SUBS["captions"] for w in c["words"]]
VO_LEN = float(SUBS.get("duration", WORDS[-1][2] if WORDS else 30.0))
TOTAL = round(OFF + VO_LEN + OUTRO, 2)
SLIDES = SUBS["slides"]
if len(SLIDES) != 5:
    raise SystemExit(f"Template prop-promo-hf can dung 5 dong script (dang co {len(SLIDES)}).")

ACCENT = str(DATA.get("accent") or "#38D5E7")
ACCENT2 = str(DATA.get("accent2") or "#F3BE62")
FIRM = str(DATA.get("firm") or "PROP FUTURES")

S = [round(float(SLIDES[i]["start"]) + OFF, 3) if i > 0 else 0.0 for i in range(5)]
SCENES = [("s0", 0.0, S[1]), ("s1", S[1], S[2]), ("s2", S[2], S[3]), ("s3", S[3], S[4]), ("s4", S[4], TOTAL)]


def scene_s0():
    dur = round(SCENES[0][2] - SCENES[0][1], 3)
    lines = DATA.get("title_lines") or [FIRM, "FLASH SALE"]
    t_html = "".join(f'<span class="{"gttl" if i == 0 else "goldttl"}">{esc(l)}</span>' for i, l in enumerate(lines))
    css = f"""
.p0-wrap{{position:absolute;left:56px;right:56px;top:270px;text-align:center;}}
.p0-badge{{display:inline-block;padding:14px 34px;border-radius:999px;background:linear-gradient(135deg,#ef4444,#f59e0b);color:#fff;font-weight:900;font-size:30px;letter-spacing:2px;box-shadow:0 12px 36px rgba(239,68,68,.45);}}
.p0-firm{{margin-top:26px;font-family:'JBM';font-size:36px;font-weight:800;letter-spacing:5px;color:{ACCENT};}}
.p0-plate{{position:relative;overflow:hidden;margin-top:24px;padding:30px 28px;border-radius:28px;border:2px solid {ACCENT}88;background:linear-gradient(160deg,rgba(16,29,53,.92),rgba(7,15,29,.88));box-shadow:0 24px 60px rgba(0,0,0,.55),0 0 48px {ACCENT}33;}}
.p0-plate h1{{font-size:66px;font-weight:900;line-height:1.18;}}
.p0-plate h1 span{{display:block;}}
.p0-sheen{{position:absolute;top:-20%;bottom:-20%;left:0;width:24%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.36),transparent);transform:translateX(-160%) skewX(-18deg);pointer-events:none;}}
.p0-sub{{margin-top:28px;font-size:34px;font-weight:700;color:#cbd5e1;line-height:1.4;}}
.p0-dl{{display:inline-block;margin-top:34px;padding:14px 32px;border-radius:16px;border:2px solid {ACCENT2};background:rgba(243,190,98,.14);font-family:'JBM';font-weight:800;font-size:32px;color:{ACCENT2};}}
"""
    body = f"""<div class="p0-wrap" id="p0-stage">
  <div class="p0-badge" id="p0-badge"><span>{esc(DATA.get('badge','FLASH SALE'))}</span></div>
  <div class="p0-firm">{esc(FIRM.upper())}</div>
  <div class="p0-plate"><h1>{t_html}</h1><i class="p0-sheen" id="p0-sheen"></i></div>
  <div class="p0-sub">{esc(DATA.get('subtitle',''))}</div>
  <div class="p0-dl" id="p0-dl"><span>⏰ {esc(DATA.get('deadline','SẮP HẾT HẠN'))}</span></div>
</div>"""
    js = f"""
tl.fromTo('#p0-badge', {{scale:0.86}}, {{scale:1.06, duration:0.35, yoyo:true, repeat:1, ease:'power2.out'}}, 0.15);
tl.fromTo('#p0-sheen', {{xPercent:-160}}, {{xPercent:560, duration:0.9, ease:'power2.inOut', immediateRender:false}}, 0.45);
tl.fromTo('#p0-dl', {{scale:0.92}}, {{scale:1.06, duration:0.25, yoyo:true, repeat:1, ease:'back.out(2)'}}, {round(dur*0.55, 2)});
tl.to('#p0-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});
"""
    return "s0", dur, scene_file("s0", dur, css, body, js, ACCENT, ACCENT2)


def scene_s1():
    dur = round(SCENES[1][2] - SCENES[1][1], 3)
    orig, sale = float(DATA.get("orig_price", 175)), float(DATA.get("sale_price", 19.25))
    dec = 2 if (sale % 1 != 0) else 0
    unit, pct = str(DATA.get("unit", "/tháng")), str(DATA.get("discount_label", "-89%"))
    css = f"""
.p1-wrap{{position:absolute;left:56px;right:56px;top:270px;text-align:center;}}
.p1-ttl{{font-size:48px;font-weight:900;}}
.p1-card{{margin-top:34px;padding:42px 34px;border-radius:30px;border:2px solid {ACCENT}80;background:rgba(16,29,53,.92);box-shadow:0 24px 60px rgba(0,0,0,.55);}}
.p1-plan{{font-size:34px;font-weight:800;color:#e2e8f0;}}
.p1-orig-box{{position:relative;display:inline-block;margin-top:26px;font-family:'JBM';font-size:56px;font-weight:700;color:#94a3b8;}}
.p1-slash{{position:absolute;left:-14px;right:-14px;top:50%;height:7px;background:#fb7185;border-radius:4px;transform:rotate(-8deg);transform-origin:left center;}}
.p1-arrow{{margin:16px 0;font-size:42px;color:{ACCENT2};font-weight:900;}}
.p1-sale{{font-family:'JBM';font-size:112px;font-weight:800;line-height:1.05;color:{ACCENT};text-shadow:0 0 36px {ACCENT}66;}}
.p1-unit{{font-size:34px;color:#cbd5e1;font-weight:700;margin-left:8px;}}
.p1-pill{{display:inline-block;margin-top:22px;padding:12px 30px;border-radius:999px;background:{ACCENT2};color:#0b1120;font-family:'JBM';font-weight:900;font-size:36px;}}
.p1-note{{margin-top:26px;font-size:30px;font-weight:600;color:#cbd5e1;line-height:1.45;}}
"""
    body = f"""<div class="p1-wrap" id="p1-stage">
  <div class="kicker">SO SÁNH GIÁ THỰC TẾ</div>
  <div class="p1-ttl gttl">{esc(DATA.get('price_heading','MỨC GIÁ SIÊU HỜI'))}</div>
  <div class="p1-card" id="p1-card">
    <div class="p1-plan">{esc(DATA.get('plan_name','Gói $50,000'))}</div>
    <div class="p1-orig-box">${orig:,.0f}{esc(unit)}<div class="p1-slash" id="p1-slash"></div></div>
    <div class="p1-arrow">▼</div>
    <div class="p1-sale"><span id="p1-num">${orig:,.{dec}f}</span><span class="p1-unit">{esc(unit)}</span></div>
    <div class="p1-pill" id="p1-pill"><span>GIẢM {esc(pct)}</span></div>
    <div class="p1-note" id="p1-note">{esc(DATA.get('plan_note',''))}</div>
  </div>
</div>"""
    t_sl, t_dr, t_pl = round(dur * 0.22, 3), round(dur * 0.36, 3), round(dur * 0.62, 3)
    js = f"""
gsap.set('#p1-slash', {{scaleX:0}}); gsap.set('#p1-pill, #p1-note', {{opacity:0}});
tl.fromTo('#p1-card', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.35, ease:'expo.out'}}, 0.05);
tl.to('#p1-slash', {{scaleX:1, duration:0.32, ease:'power3.out'}}, {t_sl});
counter('#p1-num', {orig}, {sale}, {t_dr}, 0.85, {dec}, '$', '');
tl.fromTo('#p1-num', {{scale:1}}, {{scale:1.18, duration:0.16, yoyo:true, repeat:1, ease:'back.out(2)', immediateRender:false}}, {round(t_dr+0.72, 3)});
tl.fromTo('#p1-pill', {{opacity:0, scale:1.9, rotation:-6}}, {{opacity:1, scale:1, rotation:0, duration:0.28, ease:'back.out(2.2)', immediateRender:false}}, {t_pl});
tl.fromTo('#p1-note', {{opacity:0, y:16}}, {{opacity:1, y:0, duration:0.3, immediateRender:false}}, {round(t_pl+0.22, 3)});
tl.to('#p1-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});
"""
    return "s1", dur, scene_file("s1", dur, css, body, js, ACCENT, ACCENT2)


def scene_s2():
    dur = round(SCENES[2][2] - SCENES[2][1], 3)
    cards, js_cards = [], []
    for i, pk in enumerate((DATA.get("perks") or [])[:3]):
        cards.append(f'<div class="p2-card" id="p2-c{i}"><div class="p2-num mono">0{i+1}</div><div><div class="p2-ct">{esc(pk.get("title",""))}</div><div class="p2-cd">{esc(pk.get("detail",""))}</div></div></div>')
        js_cards.append(f"tl.fromTo('#p2-c{i}', {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.4, ease:'expo.out', immediateRender:false}}, {round(dur*(0.10+i*0.27), 3)});")
    css = f"""
.p2-wrap{{position:absolute;left:56px;right:56px;top:270px;}}
.p2-hd{{text-align:center;margin-bottom:34px;}}
.p2-ttl{{font-size:50px;font-weight:900;}}
.p2-card{{display:flex;align-items:flex-start;gap:24px;padding:28px 30px;margin-bottom:24px;border-radius:24px;border:1.5px solid {ACCENT}55;background:rgba(16,29,53,.90);box-shadow:0 16px 40px rgba(0,0,0,.45);}}
.p2-num{{flex:0 0 74px;height:74px;border-radius:18px;display:flex;align-items:center;justify-content:center;background:{ACCENT}22;border:2px solid {ACCENT};color:{ACCENT};font-size:34px;font-weight:800;}}
.p2-ct{{font-size:34px;font-weight:800;color:#fff;line-height:1.25;}}
.p2-cd{{margin-top:8px;font-size:28px;font-weight:500;color:#cbd5e1;line-height:1.38;}}
"""
    body = f"""<div class="p2-wrap" id="p2-stage"><div class="p2-hd"><div class="kicker">QUYỀN LỢI NỔI BẬT</div><div class="p2-ttl gttl">{esc(DATA.get('perks_heading','VÌ SAO DEAL NÀY CỰC HỜI?'))}</div></div>{''.join(cards)}</div>"""
    js = f"""gsap.set('#p2-stage .p2-card', {{opacity:0}});{''.join(js_cards)}
tl.to('#p2-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s2", dur, scene_file("s2", dur, css, body, js, ACCENT, ACCENT2)


def scene_s3():
    dur = round(SCENES[3][2] - SCENES[3][1], 3)
    code = str(DATA.get("code", "KENVINZONE"))
    css = f"""
.p3-wrap{{position:absolute;left:56px;right:56px;top:290px;text-align:center;}}
.p3-ttl{{font-size:50px;font-weight:900;}}
.p3-box{{position:relative;overflow:hidden;margin:38px auto 0;padding:46px 32px;border-radius:30px;border:3px dashed {ACCENT2};background:linear-gradient(160deg,rgba(243,190,98,.18),rgba(16,29,53,.95));box-shadow:0 0 60px {ACCENT2}44;}}
.p3-lbl{{font-size:28px;font-weight:800;letter-spacing:4px;color:{ACCENT2};}}
.p3-code{{margin-top:16px;font-family:'JBM';font-size:96px;font-weight:800;letter-spacing:8px;color:#ffffff;text-shadow:0 0 32px {ACCENT2}aa;}}
.p3-sheen{{position:absolute;top:-20%;bottom:-20%;left:0;width:26%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.42),transparent);transform:translateX(-160%) skewX(-18deg);pointer-events:none;}}
.p3-applies{{margin-top:34px;padding:20px 26px;border-radius:18px;background:rgba(16,29,53,.88);border:1.5px solid {ACCENT}55;font-size:30px;font-weight:700;color:#e2e8f0;line-height:1.4;}}
.p3-warn{{margin-top:26px;font-family:'JBM';font-size:30px;font-weight:800;color:#fb7185;}}
"""
    body = f"""<div class="p3-wrap" id="p3-stage">
  <div class="kicker">NHẬP MÃ TẠI BƯỚC CHECKOUT</div>
  <div class="p3-ttl goldttl">MÃ GIẢM GIÁ CHÍNH THỨC</div>
  <div class="p3-box" id="p3-box"><div class="p3-lbl">COUPON CODE · {esc(FIRM.upper())}</div><div class="p3-code" id="p3-code">{esc(code)}</div><i class="p3-sheen" id="p3-sheen"></i></div>
  <div class="p3-applies" id="p3-app">Áp dụng: <b>{esc(DATA.get('applies_to','Tất cả gói thi'))}</b></div>
  <div class="p3-warn" id="p3-warn">⏰ {esc(DATA.get('deadline',''))}</div>
</div>"""
    js = f"""gsap.set('#p3-app, #p3-warn', {{opacity:0}});
tl.fromTo('#p3-box', {{scale:0.82, opacity:0}}, {{scale:1, opacity:1, duration:0.42, ease:'back.out(2)'}}, 0.08);
tl.fromTo('#p3-sheen', {{xPercent:-160}}, {{xPercent:540, duration:0.85, ease:'power2.inOut', immediateRender:false}}, 0.55);
tl.fromTo('#p3-code', {{scale:1}}, {{scale:1.12, duration:0.14, yoyo:true, repeat:1, ease:'power2.out', immediateRender:false}}, {round(dur*0.35, 3)});
tl.fromTo('#p3-app', {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.35, immediateRender:false}}, {round(dur*0.42, 3)});
tl.fromTo('#p3-warn', {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.3, immediateRender:false}}, {round(dur*0.64, 3)});
tl.to('#p3-stage', {{opacity:0, y:-40, filter:'blur(8px)', duration:0.26, ease:'power2.in'}}, {max(0.2, round(dur-0.28, 3))});"""
    return "s3", dur, scene_file("s3", dur, css, body, js, ACCENT, ACCENT2)


def scene_s4():
    dur = round(SCENES[4][2] - SCENES[4][1], 3)
    css = f"""
.p4-wrap{{position:absolute;left:56px;right:56px;top:290px;text-align:center;}}
.p4-tag{{display:inline-block;padding:10px 26px;border-radius:999px;border:1.5px solid {ACCENT}88;background:{ACCENT}18;font-size:28px;font-weight:800;color:{ACCENT};letter-spacing:2px;}}
.p4-ttl{{margin-top:26px;font-size:54px;font-weight:900;}}
.p4-url{{margin:34px auto 0;padding:28px 34px;border-radius:24px;border:2px solid {ACCENT2};background:rgba(16,29,53,.94);box-shadow:0 0 46px {ACCENT2}33;}}
.p4-url .u{{font-family:'JBM';font-size:40px;font-weight:800;color:{ACCENT2};}}
.p4-url .s{{margin-top:10px;font-size:28px;font-weight:600;color:#cbd5e1;}}
.p4-cta{{margin-top:34px;font-size:34px;font-weight:800;color:#ffffff;line-height:1.4;}}
.p4-aur{{margin-top:30px;padding:16px 24px;border-radius:16px;background:rgba(56,213,231,.10);border:1px solid rgba(56,213,231,.35);font-size:26px;font-weight:700;color:#a5f3fc;}}
.p4-disc{{margin-top:26px;font-size:22px;color:#64748b;line-height:1.4;}}
"""
    body = f"""<div class="p4-wrap" id="p4-stage">
  <div class="p4-tag"><span>KENVINZONE · TRADE QUỸ FUTURE</span></div>
  <div class="p4-ttl gttl" id="p4-ttl">{esc(DATA.get('cta_heading','SO GIÁ & LẤY LINK ƯU ĐÃI'))}</div>
  <div class="p4-url" id="p4-url"><div class="u">prop.kenvinzone.com</div><div class="s">Bảng mô phỏng giá Coupon · Máy tính Size · Rule 3 quỹ</div></div>
  <div class="p4-cta" id="p4-cta">{esc(DATA.get('cta_line','👇 Link đăng ký & Mã giảm giá ở bình luận ghim!'))}</div>
  <div class="p4-aur" id="p4-aur">⚡ Kỷ luật pass quỹ cùng hệ thống TradingView: <b>aurora.kenvinzone.com</b></div>
  <div class="p4-disc">Nội dung chia sẻ thông tin quỹ & mã ưu đãi, không phải lời khuyên đầu tư tài chính.</div>
</div>"""
    js = f"""gsap.set('#p4-url, #p4-cta, #p4-aur', {{opacity:0}});
tl.fromTo('#p4-ttl', {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.35}}, 0.05);
tl.fromTo('#p4-url', {{opacity:0, scale:0.9}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(1.8)', immediateRender:false}}, 0.35);
tl.fromTo('#p4-cta', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.35, immediateRender:false}}, {round(dur*0.35, 3)});
tl.fromTo('#p4-aur', {{opacity:0, y:16}}, {{opacity:1, y:0, duration:0.35, immediateRender:false}}, {round(dur*0.55, 3)});"""
    return "s4", dur, scene_file("s4", dur, css, body, js, ACCENT, ACCENT2)


def main():
    comps = ROOT / "compositions"
    comps.mkdir(exist_ok=True)
    meta = []
    for fn in (scene_s0, scene_s1, scene_s2, scene_s3, scene_s4):
        cid, dur, txt = fn()
        st = next(s for c, s, _e in SCENES if c == cid)
        (comps / f"{cid}.html").write_text(txt, encoding="utf-8")
        meta.append((cid, round(st, 3), dur))
    if DATA.get("captions", True):
        cid, dur, txt = captions_scene(SUBS, OFF, TOTAL, ACCENT, ACCENT2)
        (comps / "captions.html").write_text(txt, encoding="utf-8")
        meta.append(("captions", 0, dur))
    html_out = root_html(meta, TOTAL, OFF, float(DATA.get("bgm_volume", 0.16)), str(DATA.get("date", "")), ACCENT, ACCENT2, "KENVINZONE · TRADE QUỸ FUTURE", impact_at=SCENES[3][1] + 0.1)
    (ROOT / "index.html").write_text(html_out, encoding="utf-8")
    print("TOTAL", TOTAL, "scenes", meta)


if __name__ == "__main__":
    main()
