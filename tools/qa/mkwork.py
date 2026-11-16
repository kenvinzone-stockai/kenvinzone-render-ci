"""Dựng thư mục work giống render_hyperframes (không TTS): mkwork.py <lesson.json> <workdir> [durations...]"""
import json, sys, shutil, subprocess
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R))
from render_hyperframes import ensure_word_timing
lesson, work = Path(sys.argv[1]), Path(sys.argv[2])
durs = [5.84, 9.0, 10.44, 10.36, 13.48, 11.6, 18.6, 11.84, 9.84]   # đo từ run 15:04
L = json.loads(lesson.read_text(encoding="utf-8"))
if work.exists(): shutil.rmtree(work)
shutil.copytree(R / "template" / L.get("template", "aurora-trading-explainer-hf"), work)
out = work / "_out"; out.mkdir()
(out / "timing.json").write_text(json.dumps([{"line": i, "duration": d, "text": t} for i, (d, t) in enumerate(zip(durs, L["script"]))], ensure_ascii=False))
shutil.copy2(ensure_word_timing(out), work / "subtitle-word-timing.json")
(work / "data.json").write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
subprocess.run([sys.executable, "build.py", "data.json", "subtitle-word-timing.json"], cwd=work, check=True)
