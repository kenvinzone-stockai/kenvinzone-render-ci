#!/usr/bin/env python3
"""Render a slide project with HyperFrames (frame-by-frame, no screen capture).

Used automatically by auto_render.py when the slide folder contains `hf-data.json`
(e.g. the Gold Daily Bias template). Can also be run by hand after TTS exists:

    python render_hyperframes.py slide/gold-daily-bias-28-10

Inputs (in the slide folder):
    hf-data.json                     numbers + labels for the video (written per bulletin)
    output/voiceover_concat.mp3      from generate_tts.py
    output/timing.json               from generate_tts.py
    output/subtitle-word-timing.json word timings (auto_render.py makes it; rebuilt here if missing)
Output:
    output/final_video.mp4
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TEMPLATE_ROOT = REPO_ROOT / "template"
DEFAULT_TEMPLATE = "gold-daily-bias-hf"
TEMPLATE_DIR = TEMPLATE_ROOT / DEFAULT_TEMPLATE
HF_VERSION = "0.8.210"


class HyperFramesUnavailable(RuntimeError):
    """Node/npx missing: caller may fall back to the legacy screen recording."""


def log(msg: str) -> None:
    print(msg, flush=True)


def find_npx() -> str:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise HyperFramesUnavailable(
            "Chua tim thay Node.js (npx). Cai Node.js 22 tro len tai https://nodejs.org (ban LTS) "
            "roi khoi dong lai Web UI de dung HyperFrames."
        )
    try:
        out = subprocess.run([npx, "--version"], capture_output=True, text=True, timeout=60)
        node = shutil.which("node") or shutil.which("node.exe")
        ver = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=30).stdout.strip() if node else ""
        m = re.match(r"v(\d+)", ver)
        if m and int(m.group(1)) < 22:
            raise HyperFramesUnavailable(f"Node.js {ver} qua cu, HyperFrames can Node 22 tro len.")
    except (OSError, subprocess.SubprocessError) as exc:
        raise HyperFramesUnavailable(f"Khong chay duoc npx: {exc}") from exc
    return npx


def _copy_writable(src, dst, *, follow_symlinks=True):
    """Copy content only (no read-only attribute), so the next render can overwrite it."""
    shutil.copyfile(src, dst)
    try:
        os.chmod(dst, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass
    return dst


def _force_rmtree(path: Path) -> None:
    def _fix(func, p, *_):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass
    try:
        shutil.rmtree(path, onexc=_fix)  # Python 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=_fix)
    except OSError:
        pass


def find_browser() -> str | None:
    """A Chrome/Chromium already on this machine, so HyperFrames does not have to download one
    (the download fails behind company networks that re-sign HTTPS: 'self-signed certificate')."""
    import glob
    env = os.environ.get("HYPERFRAMES_BROWSER_PATH")
    if env and Path(env).exists():
        return env
    cands: list[str] = []
    pw_dirs = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or ""]
    if os.name == "nt":
        pw_dirs.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"))
    else:
        pw_dirs += [os.path.expanduser("~/.cache/ms-playwright"), os.path.expanduser("~/Library/Caches/ms-playwright"), "/opt/pw-browsers"]
    for d in [x for x in pw_dirs if x]:
        # headless shell first: it supports the fast BeginFrame capture path
        cands += sorted(glob.glob(os.path.join(d, "chromium_headless_shell-*", "*", "chrome-headless-shell.exe" if os.name == "nt" else "chrome-headless-shell")), reverse=True)
        cands += sorted(glob.glob(os.path.join(d, "chromium-*", "*", "chrome.exe" if os.name == "nt" else "chrome")), reverse=True)
    try:  # the Playwright the Web UI already uses
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            cands.append(pw.chromium.executable_path)
    except Exception:
        pass
    if os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), os.environ.get("LOCALAPPDATA", "")):
            cands.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
            cands.append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
    else:
        cands += ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in cands:
        if c and Path(c).is_file() and not c.endswith((".zip", ".json")):
            return c
    return None


def ensure_word_timing(output_dir: Path) -> Path:
    """Return a subtitle-word-timing.json that has per-word times (synthesised if needed)."""
    path = output_dir / "subtitle-word-timing.json"
    data = None
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = None
    if data and data.get("captions") and all(c.get("words") for c in data["captions"]):
        return path

    timing = json.loads((output_dir / "timing.json").read_text(encoding="utf-8"))
    slides, captions, t = [], [], 0.0
    for item in timing:
        dur = float(item["duration"])
        words = str(item["text"]).split()
        slides.append({"line": item["line"], "start": round(t, 3), "duration": dur, "text": item["text"]})
        per = dur / max(1, len(words))
        for g in range(0, len(words), 6):
            chunk = words[g:g + 6]
            ws = [{"text": w, "start": round(t + (g + i) * per, 3), "end": round(t + (g + i + 1) * per, 3)} for i, w in enumerate(chunk)]
            captions.append({"slide": item["line"], "start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(chunk), "words": ws})
        t += dur
    synth = output_dir / "hf-word-timing.json"
    synth.write_text(json.dumps({"version": 2, "source": "synthetic", "duration": round(t, 3), "slides": slides, "captions": captions}, ensure_ascii=False), encoding="utf-8")
    log("  [captions] Khong co word timing tu whisper -> chia deu theo so tu.")
    return synth


def check_data_date(folder: str, date: str) -> None:
    """Stop when hf-data.json was copied from another day (folder date != data date)."""
    if "template" in folder or "master" in folder:
        return
    m = re.match(r"(\d{1,2})/(\d{1,2})", date.strip())
    if not m:
        return
    dd, mm = int(m.group(1)), int(m.group(2))
    f = re.search(r"(?<!\d)(\d{2})-(\d{2})(?!\d)", folder) or re.search(r"(?<!\d)(\d{2})(\d{2})\d{4}(?!\d)", folder)
    if f and (int(f.group(1)), int(f.group(2))) != (dd, mm):
        raise ValueError(
            f"hf-data.json ghi ngay {date} nhung thu muc la '{folder}'. "
            "Co the ban dang dung so lieu cua ngay khac - cap nhat hf-data.json roi render lai."
        )


def make_bgm(slide_dir: Path, settings: dict, total: float, dst: Path, default_bgm: Path) -> None:
    bgm = (settings or {}).get("bgm") or {}
    src = default_bgm
    if bgm.get("mode") == "none":
        src = None
    elif bgm.get("mode") == "custom":
        rel = ((bgm.get("custom") or {}).get("path") or "").strip()
        if rel and (slide_dir / rel).exists():
            src = slide_dir / rel
    if src is None:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{total:.2f}", str(dst)], check=True)
        return
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(src), "-t", f"{total:.2f}",
        "-af", f"afade=t=in:d=1.5,afade=t=out:st={max(0.0, total - 4):.2f}:d=4", "-ar", "44100", str(dst),
    ], check=True)


def render_hyperframes(slide_dir: Path, output_dir: Path | None = None, voiceover: Path | None = None,
                       settings: dict | None = None, quality: str = "delivery") -> Path:
    slide_dir = Path(slide_dir).resolve()
    output_dir = Path(output_dir or slide_dir / "output").resolve()
    data_file = slide_dir / "hf-data.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Khong co {data_file.name} trong {slide_dir}")
    data_peek = json.loads(data_file.read_text(encoding="utf-8"))
    check_data_date(slide_dir.name, str(data_peek.get("date") or ""))
    tpl_name = str(data_peek.get("template") or DEFAULT_TEMPLATE).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", tpl_name):
        raise ValueError(f"Ten template khong hop le: {tpl_name}")
    tpl_dir = TEMPLATE_ROOT / tpl_name
    if not tpl_dir.exists():
        raise FileNotFoundError(f"Thieu template HyperFrames: {tpl_dir}")
    voiceover = Path(voiceover or output_dir / "voiceover_concat.mp3")
    if not voiceover.exists():
        raise FileNotFoundError("Chua co voiceover_concat.mp3 - chay buoc TTS truoc.")
    if settings is None:
        ps = slide_dir / "preview-settings.json"
        settings = json.loads(ps.read_text(encoding="utf-8")) if ps.exists() else {}

    npx = find_npx()
    work = output_dir / "hf"
    log(f"=== HyperFrames ({tpl_name}): dung project tai {work} ===")
    if work.exists():
        _force_rmtree(work)
    if work.exists():  # a file is still locked (Windows: open in another program) -> use a fresh folder
        work = output_dir / f"hf_{int(time.time())}"
        log(f"  Thu muc hf cu dang bi khoa, dung thu muc moi: {work.name}")
    shutil.copytree(tpl_dir, work, copy_function=_copy_writable)

    data = json.loads(data_file.read_text(encoding="utf-8"))
    bgm_cfg = (settings or {}).get("bgm") or {}
    if "bgm_volume" not in data and bgm_cfg.get("volume") is not None:
        data["bgm_volume"] = round(float(bgm_cfg["volume"]) * 0.8, 3)
    if (settings or {}).get("subtitles", {}).get("enabled") is False:
        data["captions"] = False
    if "hero_color" not in data:
        ht = (settings or {}).get("heroTitle") or {}
        if ht.get("mode") == "custom" and ht.get("color"):
            data["hero_color"] = ht["color"]
    deck = slide_dir / "index.html"
    if deck.exists():  # templates that rebuild the episode's own deck (AURORA Explainer) read it as deck.html
        shutil.copy2(deck, work / "deck.html")
    (work / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    timing_src = ensure_word_timing(output_dir)
    shutil.copy2(timing_src, work / "subtitle-word-timing.json")
    shutil.copy2(voiceover, work / "assets" / "audio" / "voiceover.mp3")
    subs = json.loads((work / "subtitle-word-timing.json").read_text(encoding="utf-8"))
    vo_len = float(subs.get("duration") or subs["captions"][-1]["end"])
    total = float(data.get("audio_offset", 1.0)) + vo_len + float(data.get("outro_hold", 3.6))
    make_bgm(slide_dir, settings, total, work / "assets" / "audio" / "bgm_loop.mp3", tpl_dir / "assets" / "audio" / "bgm_default.mp3")

    log("=== HyperFrames: dung composition tu hf-data.json ===")
    subprocess.run([sys.executable, str(work / "build.py"), str(work / "data.json"), str(work / "subtitle-word-timing.json")],
                   cwd=str(work), check=True)
    choice = os.environ.get("KZ_HF_PALETTE", "template")
    if choice not in ("", "template"):
        try:
            sys.path.insert(0, str(REPO_ROOT))
            from hf_palette import recolor_project, resolve_palette
            pal = resolve_palette(choice, settings)
            if pal:
                n = recolor_project(work, pal, work / "palette-map.json")
                log(f"  Bang mau video: {choice} -> {pal.get('primary')} / {pal.get('accent')} ({n} file)")
            else:
                log(f"  Bang mau video: khong tim thay '{choice}' -> giu mau mau.")
        except Exception as exc:  # colours are cosmetic: never block the render
            log(f"  [bang mau] bo qua: {exc}")

    out_tmp = output_dir / "final_video.hf.mp4"
    cmd = [npx, "--yes", f"hyperframes@{HF_VERSION}", "render", "--quality", quality, "--output", str(out_tmp)]
    log(f"=== HyperFrames: render tung khung hinh ({total:.1f}s video) ===")
    env = os.environ.copy()
    env.setdefault("HYPERFRAMES_NO_TELEMETRY", "1")
    browser = find_browser()
    if browser:
        env["HYPERFRAMES_BROWSER_PATH"] = browser
        log(f"  Trinh duyet render: {browser}")
    proc = subprocess.Popen(cmd, cwd=str(work), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", env=env)
    last_pct = -10
    full_log, tail = [], []
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        full_log.append(line)
        if not line.startswith("@hf-progress") and "Streaming frame" not in line:
            tail = (tail + [line])[-25:]
        if line.startswith("@hf-progress"):
            try:
                pct = int(json.loads(line.split(" ", 1)[1]).get("pct", 0))
            except Exception:
                continue
            if pct >= last_pct + 10:
                last_pct = pct
                log(f"  HyperFrames render {pct}%")
            continue
        if "Streaming frame" in line or "█" in line or "░" in line or "Framey" in line or line.lstrip().startswith(("[INFO]", "[initSession", "[BrowserManager]", "[HyperFrames] render runtime", "[hyperframes] browserGpuMode")):
            continue
        log("  " + line)
    code = proc.wait()
    log_file = output_dir / "hf_render.log"
    try:
        log_file.write_text("\n".join([" ".join(cmd), f"exit code: {code}", ""] + full_log), encoding="utf-8")
    except OSError:
        pass
    if code != 0 or not out_tmp.exists() or out_tmp.stat().st_size == 0:
        log("  ---- HyperFrames bao loi (25 dong cuoi) ----")
        for l in tail:
            log("  | " + l)
        reason = next((l for l in reversed(tail) if re.search(r"error|fail|not found|cannot|ENOENT|EACCES|denied", l, re.I)), tail[-1] if tail else "")
        raise RuntimeError(f"HyperFrames render that bai (exit {code}): {reason.strip()[:300]} | Log day du: {log_file}")

    final = output_dir / "final_video.mp4"
    os.replace(out_tmp, final)
    log(f"Final video (HyperFrames): {final}")
    return final


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slide_dir")
    ap.add_argument("--quality", default="delivery", choices=["draft", "looks", "delivery"])
    args = ap.parse_args()
    try:
        render_hyperframes(Path(args.slide_dir), quality=args.quality)
    except HyperFramesUnavailable as exc:
        print(f"[HyperFrames] {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
