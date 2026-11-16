#!/usr/bin/env python3
"""Cổng QA zero-credit cho video HyperFrames — chạy TRƯỚC bước TTS.

    python tools/qa/gate.py <slide_dir> [--out <dir>] [--samples 3] [--strict]

Dựng composition từ hf-data.json + script (timing giọng đọc ước lượng ~4,1 từ/giây,
không gọi TTS), mở trong Chromium, tua qua nhiều thời điểm mỗi cảnh và kiểm:

  FONT     chữ thường được vẽ bằng font hệ thống thay vì webfont đã nạp
           (hỏi thẳng Chrome qua CDP CSS.getPlatformFontsForNode)          → LỖI
  SYMBOL   chỉ ký hiệu/emoji (▶ ⚡ ↗ ✓…) mượn font hệ thống — runner có thể
           vẽ ra ô vuông nếu thiếu font                                    → CẢNH BÁO
  OVERLAP  hai khối chữ đang hiện đè lên nhau (>18% diện tích khối nhỏ)     → LỖI
  CLIP     chữ tràn ra ngoài khung 1080×1920                                → LỖI
  SAFE     chữ nằm trong vùng giao diện Shorts/TikTok/Reels che             → CẢNH BÁO
           (đáy y>1450 · cột nút phải x>888 khi 840<y<1450 · đỉnh y<240)
  JS       lỗi JavaScript trên trang                                        → LỖI

Xuất report.json, report.md và contact.png (mỗi khung một ô, khoanh đỏ chỗ lỗi).
Mã thoát 1 khi có LỖI (hoặc có CẢNH BÁO với --strict).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
W, H = 1080, 1920
WPS = 4.1                                   # từ/giây đo thực của giọng clone
UNSAFE = [("đáy", 0, 1450, W, H), ("cột nút phải", 888, 840, W, 1450), ("đỉnh", 0, 0, W, 240)]
# Chữ được phép nằm ngoài vùng an toàn (trang trí / pháp lý / thương hiệu) — so khớp class hoặc id.
SAFE_ALLOW = re.compile(r"disc|brand|handle|wm|watermark|rootdisc|hdr|header|kz-top|prog", re.I)


# --------------------------------------------------------------------------- dựng
def build_work(slide_dir: Path, work: Path) -> dict:
    from render_hyperframes import ensure_word_timing
    data = json.loads((slide_dir / "hf-data.json").read_text(encoding="utf-8"))
    tpl = REPO / "template" / str(data.get("template") or "vnindex-daily-hf")
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(tpl, work)
    script = slide_dir / "script-90s.txt"
    lines = [l.strip() for l in script.read_text(encoding="utf-8").splitlines() if l.strip()] if script.exists() else []
    if not lines:
        lines = [str(s.get("text") or s) for s in data.get("script", [])] or ["(trống)"]
    out = work / "_qa_out"
    out.mkdir()
    timing = [{"line": i, "duration": round(len(t.split()) / WPS + 0.45, 2), "text": t} for i, t in enumerate(lines)]
    (out / "timing.json").write_text(json.dumps(timing, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(ensure_word_timing(out), work / "subtitle-word-timing.json")
    if (slide_dir / "index.html").exists():
        shutil.copy2(slide_dir / "index.html", work / "deck.html")
    (work / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, "build.py", "data.json", "subtitle-word-timing.json"], cwd=work, check=True,
                   capture_output=True)
    return data


# --------------------------------------------------------------------------- trình duyệt
LOAD_JS = r"""
async () => {
  const hosts = [...document.querySelectorAll('[data-composition-src]')];
  for (const h of hosts) {
    const txt = await (await fetch(h.dataset.compositionSrc)).text();
    const tpl = new DOMParser().parseFromString(txt, 'text/html').querySelector('template');
    if (!tpl) continue;
    const frag = tpl.content.cloneNode(true);
    const scripts = [...frag.querySelectorAll('script')]; scripts.forEach(s => s.remove());
    h.style.position = 'absolute'; h.style.inset = '0';
    h.appendChild(frag);
    for (const s of scripts) { const n = document.createElement('script'); n.textContent = s.textContent; document.body.appendChild(n); }
  }
  await document.fonts.ready;
  // Ép tải MỌI @font-face trước khi đo (trình duyệt chỉ tải lười khi chữ lần đầu xuất hiện).
  await Promise.all([...document.fonts].map(f => f.load().catch(() => null)));
  window.__qaSeek = (t) => {
    if (window.__timelines.main) window.__timelines.main.seek(t, false);
    for (const h of hosts) {
      const st = +h.dataset.start, du = +h.dataset.duration, id = h.dataset.compositionId;
      const on = t >= st && t < st + du; h.style.display = on ? 'block' : 'none';
      if (on && window.__timelines[id]) window.__timelines[id].seek(t - st, false);
    }
  };
  let n = 0;
  window.__qaTexts = () => {
    const out = [];
    const all = document.querySelectorAll('body *');
    for (const el of all) {
      if (['SCRIPT', 'STYLE', 'TEMPLATE'].includes(el.tagName)) continue;
      const own = [...el.childNodes].filter(c => c.nodeType === 3).map(c => c.textContent).join('').trim();
      if (!own) continue;
      let op = 1, hidden = false;
      for (let p = el; p && p.nodeType === 1; p = p.parentElement) {
        const cs = getComputedStyle(p);
        if (cs.display === 'none' || cs.visibility === 'hidden') { hidden = true; break; }
        op *= parseFloat(cs.opacity || '1');
      }
      if (hidden || op < 0.35) continue;
      // Khung của CHÍNH dòng chữ (Range trên text node), không phải cả thẻ chứa — thẻ rộng
      // hết bề ngang với chữ căn giữa sẽ báo nhầm đè chữ / lọt vùng an toàn.
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const c of el.childNodes) {
        if (c.nodeType !== 3 || !c.textContent.trim()) continue;
        const rg = document.createRange(); rg.selectNodeContents(c);
        for (const q of rg.getClientRects()) {
          if (q.width < 1) continue;
          x0 = Math.min(x0, q.left); y0 = Math.min(y0, q.top); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
        }
      }
      if (x1 < x0) continue;
      const r = {left: x0, top: y0, width: x1 - x0, height: y1 - y0};
      if (r.width < 2 || r.height < 2) continue;
      if (!el.dataset.qa) el.dataset.qa = 'q' + (n++);
      const host = el.closest('[data-composition-id]');
      const tag = (el.getAttribute('class') || '') + ' #' + (el.id || '');
      const anc = [], ancq = [];
      for (let p = el.parentElement; p && anc.length < 4; p = p.parentElement) anc.push((p.getAttribute('class') || '') + '#' + (p.id || ''));
      for (let p = el.parentElement; p; p = p.parentElement) if (p.dataset && p.dataset.qa) ancq.push(p.dataset.qa);
      const cs0 = getComputedStyle(el);
      out.push({qa: el.dataset.qa, text: own.slice(0, 60), x: r.left, y: r.top, w: r.width, h: r.height,
                op: +op.toFixed(2), comp: host ? host.dataset.compositionId : '', tag, anc: anc.join(' '), ancq,
                ff: cs0.fontFamily, fw: cs0.fontWeight, svg: el instanceof SVGElement, full: (el.textContent || '').trim().slice(0, 120), fs: parseFloat(cs0.fontSize) || 0});
    }
    return out;
  };
  return hosts.map(h => [h.dataset.compositionId, +h.dataset.start, +h.dataset.duration]);
}
"""


def _contains(a, b):
    return a["x"] <= b["x"] + 1 and a["y"] <= b["y"] + 1 and a["x"] + a["w"] >= b["x"] + b["w"] - 1 and a["y"] + a["h"] >= b["y"] + b["h"] - 1


def _inter(a, b):
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return ix * iy


def run_gate(slide_dir: Path, outdir: Path, samples: int) -> dict:
    from playwright.sync_api import sync_playwright
    try:
        from PIL import Image, ImageDraw
    except ImportError:                      # thiếu Pillow → bỏ ảnh tổng hợp, vẫn kiểm đủ
        Image = ImageDraw = None

    work = outdir / "work"
    data = build_work(slide_dir, work)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=str(work)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    issues, frames, font_seen = [], [], {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.add_init_script("window.__timelines={};")
        js_errors = []
        pg.on("pageerror", lambda e: js_errors.append(str(e)))
        pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/index.html")
        meta = pg.evaluate(LOAD_JS)
        cdp = pg.context.new_cdp_session(pg)
        cdp.send("DOM.enable"); cdp.send("CSS.enable")
        scenes = [m for m in meta if m[0] not in ("captions", "notes")]
        fracs = [round((k + 1) / (samples + 1), 2) for k in range(samples)]
        if samples >= 3:
            fracs[-1] = 0.92
        times = [(f"{c}@{f}", st + du * f) for c, st, du in scenes for f in fracs]
        for label, t in times:
            pg.evaluate(f"__qaSeek({t})")
            pg.wait_for_timeout(40)
            texts = pg.evaluate("__qaTexts()")
            shot = outdir / f"f_{label.replace('@', '_')}.png"
            pg.screenshot(path=str(shot))
            bad = []
            # FONT — hỏi Chrome font thực vẽ của từng node chữ (mỗi node một lần)
            root = cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})["root"]["nodeId"]
            for tx in texts:
                if tx["qa"] in font_seen:
                    continue
                try:
                    nid = cdp.send("DOM.querySelector", {"nodeId": root, "selector": f'[data-qa="{tx["qa"]}"]'})["nodeId"]
                    fonts = cdp.send("CSS.getPlatformFontsForNode", {"nodeId": nid})["fonts"]
                except Exception:  # noqa: BLE001
                    continue
                font_seen[tx["qa"]] = fonts
                sysf = [f for f in fonts if not f.get("isCustomFont")]
                if sysf:
                    # Ký hiệu/emoji không có trong Be Vietnam Pro → mượn font hệ thống cho riêng glyph đó (SYMBOL);
                    # chữ thường bị vẽ bằng font hệ thống → lỗi thật (FONT).
                    sym = [ch for ch in tx["full"] if not (ch.isalnum() or ch.isspace() or ch in ".,:;!?%/()+-–—'\"“”‘’&@#*=<>[]{}_|~^$")]
                    n_sys = sum(f.get("glyphCount", 0) for f in sysf)
                    names = ", ".join(sorted({f["familyName"] for f in sysf}))
                    if sym and n_sys <= len(sym):
                        issues.append({"level": "CẢNH BÁO", "kind": "SYMBOL", "at": label, "text": "".join(dict.fromkeys(sym)),
                                       "detail": f"ký hiệu mượn font hệ thống ({names}) — trong 「{tx['text'][:30]}」", "comp": tx["comp"]})
                    else:
                        issues.append({"level": "LỖI", "kind": "FONT", "at": label, "text": tx["text"],
                                       "detail": f"font hệ thống: {names} · CSS font-family={tx['ff'][:60]} w{tx['fw']}{' (SVG)' if tx['svg'] else ''}",
                                       "comp": tx["comp"]})
                        bad.append(tx)
            # CLIP + SAFE
            for tx in texts:
                if tx["x"] < -2 or tx["y"] < -2 or tx["x"] + tx["w"] > W + 2 or tx["y"] + tx["h"] > H + 2:
                    issues.append({"level": "LỖI", "kind": "CLIP", "at": label, "text": tx["text"],
                                   "detail": f"ra ngoài khung ({tx['x']:.0f},{tx['y']:.0f},{tx['w']:.0f}×{tx['h']:.0f})", "comp": tx["comp"]})
                    bad.append(tx)
                    continue
                if SAFE_ALLOW.search(tx["tag"] + " " + tx["anc"]):
                    continue
                for name, x0, y0, x1, y1 in UNSAFE:
                    a = _inter(tx, {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})
                    if a > 0.35 * tx["w"] * tx["h"]:
                        issues.append({"level": "CẢNH BÁO", "kind": "SAFE", "at": label, "text": tx["text"],
                                       "detail": f"vùng {name} (y={tx['y']:.0f}, x={tx['x']:.0f}–{tx['x'] + tx['w']:.0f})", "comp": tx["comp"]})
                        bad.append(tx)
                        break
            # OVERLAP — co khung dòng đơn về thân chữ (~0,72 × cỡ chữ) để bỏ phần đệm dòng cao
            def body(t):
                if t["fs"] and t["h"] < 1.6 * t["fs"]:
                    hh = 0.72 * t["fs"]
                    return {**t, "y": t["y"] + (t["h"] - hh) / 2, "h": hh}
                return t
            boxes = [body(t) for t in texts]
            for i, a in enumerate(boxes):
                for c in boxes[i + 1:]:
                    if _contains(a, c) or _contains(c, a) or a["qa"] in c["ancq"] or c["qa"] in a["ancq"]:
                        continue
                    ix = max(0.0, min(a["x"] + a["w"], c["x"] + c["w"]) - max(a["x"], c["x"]))
                    iy = max(0.0, min(a["y"] + a["h"], c["y"] + c["h"]) - max(a["y"], c["y"]))
                    # đè thật = chồng đáng kể theo CẢ hai chiều (hai đoạn cạnh nhau cùng dòng chỉ chạm mép)
                    if ix > 0.3 * min(a["w"], c["w"]) and iy > 0.4 * min(a["h"], c["h"]):
                        issues.append({"level": "LỖI", "kind": "OVERLAP", "at": label,
                                       "text": f"「{a['text']}」 ⟂ 「{c['text']}」", "detail": f"{a['comp']} / {c['comp']}", "comp": a["comp"]})
                        bad += [a, c]
            frames.append((label, shot, bad))
        for e in js_errors:
            issues.append({"level": "LỖI", "kind": "JS", "at": "-", "text": e[:160], "detail": "", "comp": ""})
        b.close()
    srv.shutdown()

    # gộp lỗi trùng (cùng loại + cùng chữ) để báo cáo gọn
    # gộp lỗi trùng để báo cáo gọn: SAFE gộp theo (composition, vùng, dải y); còn lại theo (loại, chữ)
    uniq, seen = [], {}
    for it in issues:
        if it["kind"] == "SAFE":
            m = re.search(r"vùng (.+?) \(y=(\d+)", it["detail"])
            key = ("SAFE", it["comp"], m.group(1), int(m.group(2)) // 60) if m else ("SAFE", it["text"])
        else:
            key = (it["kind"], it["text"], it["detail"].split(" (")[0])
        if key in seen:
            g = seen[key]
            if it["at"] not in g["at"]:
                g["at"] += f", {it['at']}"
            if it["kind"] == "SAFE" and it["text"] not in g["text"] and len(g["text"]) < 48:
                g["text"] += " · " + it["text"]
            continue
        seen[key] = dict(it); uniq.append(seen[key])

    # ảnh tổng hợp
    n_frames = len(frames)
    if Image is None:
        frames = []
    cols, tw, th = 6, 270, 480
    rows = max(1, (len(frames) + cols - 1) // cols)
    sheet = None if Image is None else Image.new("RGB", (cols * tw, rows * (th + 26)), (12, 14, 20))
    dr = ImageDraw.Draw(sheet) if sheet else None
    for k, (label, shot, bad) in enumerate(frames):
        im = Image.open(shot).convert("RGB")
        d = ImageDraw.Draw(im)
        for name, x0, y0, x1, y1 in UNSAFE:
            d.rectangle((x0, y0, x1, y1), outline=(255, 70, 90), width=3)
        for tx in bad:
            d.rectangle((tx["x"] - 4, tx["y"] - 4, tx["x"] + tx["w"] + 4, tx["y"] + tx["h"] + 4), outline=(255, 30, 30), width=8)
        x, y = (k % cols) * tw, (k // cols) * (th + 26)
        sheet.paste(im.resize((tw, th)), (x, y + 26))
        dr.text((x + 6, y + 6), label + ("  ✗" if bad else ""), fill=(255, 90, 90) if bad else (200, 200, 210))
    if sheet:
        sheet.save(outdir / "contact.png")

    n_err = sum(i["level"] == "LỖI" for i in uniq)
    n_warn = sum(i["level"] == "CẢNH BÁO" for i in uniq)
    report = {"slide": slide_dir.name, "template": data.get("template"), "frames": n_frames,
              "errors": n_err, "warnings": n_warn, "issues": uniq}
    (outdir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# QA · {slide_dir.name} · `{data.get('template')}`", "",
          f"{n_frames} khung · **{n_err} lỗi** · {n_warn} cảnh báo", "",
          "| Mức | Loại | Chữ | Chi tiết | Khung |", "|---|---|---|---|---|"]
    md += [f"| {i['level']} | {i['kind']} | {i['text']} | {i['detail']} | {i['at']} |" for i in uniq]
    (outdir / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slide_dir")
    ap.add_argument("--out", default=None)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    slide = Path(a.slide_dir).resolve()
    out = Path(a.out or slide / "output" / "qa").resolve()
    out.mkdir(parents=True, exist_ok=True)
    r = run_gate(slide, out, a.samples)
    print(f"QA {slide.name} [{r['template']}]: {r['frames']} khung · {r['errors']} lỗi · {r['warnings']} cảnh báo → {out}")
    for i in r["issues"][:40]:
        print(f"  {i['level']:8} {i['kind']:7} {i['text'][:70]} — {i['detail']} @ {i['at'][:60]}")
    return 1 if r["errors"] or (a.strict and r["warnings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
