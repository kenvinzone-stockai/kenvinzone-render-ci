"""Chụp khung hình toàn cục: shoot.py <workdir> <outdir> t1 t2 ...  (t = giây; 'sN@0.85' = 85% cảnh N)"""
import sys, re, json, threading, http.server, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
work, outd = Path(sys.argv[1]).resolve(), Path(sys.argv[2]); outd.mkdir(parents=True, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(Q, directory=str(work))
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = r"""
async () => {
  window.__timelines = window.__timelines || {};
  const hosts = [...document.querySelectorAll('[data-composition-src]')];
  for (const h of hosts) {
    const txt = await (await fetch(h.dataset.compositionSrc)).text();
    const doc = new DOMParser().parseFromString(txt, 'text/html');
    const tpl = doc.querySelector('template');
    const frag = tpl.content.cloneNode(true);
    const scripts = [...frag.querySelectorAll('script')]; scripts.forEach(s => s.remove());
    h.style.position='absolute'; h.style.inset='0';
    h.appendChild(frag);
    for (const s of scripts) { const n = document.createElement('script'); n.textContent = s.textContent; document.body.appendChild(n); }
  }
  await document.fonts.ready;
  window.seekAll = (t) => {
    if (window.__timelines.main) window.__timelines.main.seek(t, false);
    for (const h of hosts) {
      const st = +h.dataset.start, du = +h.dataset.duration, id = h.dataset.compositionId;
      const on = t >= st && t < st + du; h.style.display = on ? 'block' : 'none';
      if (on && window.__timelines[id]) window.__timelines[id].seek(t - st, false);
    }
  };
  return hosts.map(h => [h.dataset.compositionId, +h.dataset.start, +h.dataset.duration]);
}
"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.add_init_script("window.__timelines={};"); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://127.0.0.1:{port}/index.html"); meta = pg.evaluate(JS)
    sc = {m[0]: (m[1], m[2]) for m in meta}
    for spec in sys.argv[3:]:
        m = re.fullmatch(r"([A-Za-z][\w-]*)@([\d.]+)", spec)
        t = sc[m.group(1)][0] + sc[m.group(1)][1] * float(m.group(2)) if m else float(spec)
        pg.evaluate(f"seekAll({t})"); pg.wait_for_timeout(60)
        pg.screenshot(path=str(outd / f"{spec.replace('@','_')}.png"))
    print("scenes", [(m[0], round(m[1], 2), round(m[2], 2)) for m in meta])
    if errs: print("PAGE ERRORS:", errs)
    b.close()
