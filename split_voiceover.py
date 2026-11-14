#!/usr/bin/env python3
"""Cắt một bản đọc liền mạch (full voiceover) thành line_0.mp3 … line_<n-1>.mp3.

Gọi bởi generate_tts.py (chế độ full của Edge / ElevenLabs / Gemini):

    python split_voiceover.py <slide_dir> <full_audio.mp3> --output-dir <output_dir>

Sinh ra đúng những thứ các bước sau cần (giống hệt nhánh per-slide trong tts/common.py):
  - line_<i>.mp3 (+ line_<i>.srt, line_<i>.txt)
  - timing.json  — LIST [{line, duration, original_audio_duration, video_duration, text}]
  - voiceover_concat.mp3 — encode thẳng từ bản gốc (khớp tuyệt đối với timing.json)

Thuật toán (không cần whisper, chạy vài giây trên runner):
  1. ffmpeg silencedetect → danh sách quãng lặng; bỏ lặng đầu/cuối để lấy vùng có tiếng.
  2. Ước lượng mốc từng ranh theo tỉ lệ số âm tiết tích lũy của các dòng script.
  3. Quy hoạch động TOÀN CỤC chọn n-1 quãng lặng làm ranh: thời lượng từng dòng phải
     sát tỉ lệ âm tiết, quãng lặng dài được ưu tiên (ngắt giữa dòng > ngắt dấu phẩy),
     ranh nằm trong cửa sổ quanh mốc ước lượng. Thiếu quãng lặng → giữ mốc ước lượng.
  4. Cắt tại GIỮA quãng lặng. timing.json ghi đúng hiệu các mốc cắt; voiceover_concat
     encode thẳng từ bản gốc → khớp tuyệt đối (không cộng dồn đệm encoder).

Thoát mã ≠ 0 khi không cắt được → generate_tts.py tự fallback về TTS từng dòng.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tts.common import read_script_lines, write_line_srt  # noqa: E402

WINDOW = 1.5          # cửa sổ snap ±s
NOISE_DB = -35        # ngưỡng lặng
MIN_SIL = 0.15        # quãng lặng tối thiểu để xét (s)
LONG_BONUS = 1.2      # mỗi giây độ dài quãng lặng được "trừ" bấy nhiêu giây khoảng cách
MIN_LINE = 0.6        # mỗi dòng tối thiểu (s)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def detect_silences(path: Path, total: float) -> list[tuple[float, float]]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={NOISE_DB}dB:d={MIN_SIL}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    sils, start = [], None
    for line in proc.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and start is not None:
            sils.append((start, float(m.group(1))))
            start = None
    if start is not None:                      # lặng kéo tới hết file
        sils.append((start, total))
    return sils


def weight(text: str) -> float:
    """Trọng số thời lượng đọc: tiếng Việt mỗi chữ cách là một âm tiết (~đều nhau),
    cộng phần nhỏ theo số ký tự (từ tiếng Anh dài) và phạt nhẹ cho dấu ngắt."""
    words = [w for w in text.split() if re.sub(r"[\W_]+", "", w)]
    chars = len(re.sub(r"[\W_]+", "", text, flags=re.UNICODE))
    pauses = len(re.findall(r"[,;:.!?…—–]", text))
    return max(1.0, len(words) + 0.08 * chars + 0.6 * pauses)


SIGMA = 0.25      # độ lệch tốc độ đọc giữa các dòng (log) chấp nhận được
SIL_GAIN = 10.0   # thưởng cho mỗi giây quãng lặng được chọn làm ranh
NO_SIL = 2.5      # phạt khi phải cắt giữa tiếng (không có quãng lặng)


def plan_cuts(lines: list[str], sils: list[tuple[float, float]], total: float) -> tuple[list[float], list[str]]:
    """Quy hoạch động toàn cục: chọn n-1 ranh giới trong các quãng lặng (hoặc mốc
    ước lượng nếu thiếu) sao cho thời lượng từng dòng sát tỉ lệ trọng số nhất và
    ưu tiên quãng lặng dài (ngắt giữa dòng thường dài hơn ngắt dấu phẩy)."""
    import math
    n = len(lines)
    speech_start, speech_end = 0.0, total
    if sils and sils[0][0] <= 0.05:
        speech_start = sils[0][1]
    if sils and sils[-1][1] >= total - 0.05:
        speech_end = sils[-1][0]
    inner = [s for s in sils if s[0] > speech_start + 0.01 and s[1] < speech_end - 0.01]

    w = [weight(t) for t in lines]
    W = sum(w)
    span = speech_end - speech_start
    cum = [0.0]
    for x in w:
        cum.append(cum[-1] + x)
    est = [speech_start + span * cum[k] / W for k in range(n + 1)]

    # ứng viên: (điểm cắt, điểm bắt đầu dòng sau, điểm kết thúc dòng trước, thưởng)
    cands = [((a + b) / 2, b, a, SIL_GAIN * (b - a)) for a, b in inner]
    # thêm mốc ước lượng thuần (cắt giữa tiếng) làm phương án dự phòng cho từng ranh
    for k in range(1, n):
        cands.append((est[k], est[k], est[k], -NO_SIL))
    cands.sort()
    start_node = (speech_start, speech_start, speech_start, 0.0)
    end_node = (speech_end, speech_end, speech_end, 0.0)
    nodes = [start_node] + cands + [end_node]
    N = len(nodes)

    def line_cost(i: int, a: int, b: int) -> float:
        dur = nodes[b][2] - nodes[a][1]          # từ hết lặng trước tới đầu lặng sau
        if dur < MIN_LINE:
            return math.inf
        expect = span * w[i] / W
        return (math.log(dur / expect) / SIGMA) ** 2

    INF = math.inf
    # dp[k][j]: chi phí tốt nhất khi ranh thứ k nằm ở node j
    dp = [[INF] * N for _ in range(n + 1)]
    back = [[-1] * N for _ in range(n + 1)]
    dp[0][0] = 0.0
    for k in range(1, n + 1):
        js = [N - 1] if k == n else range(1, N - 1)
        for j in js:
            # cửa sổ: ranh k phải nằm trong ±max(WINDOW, 25% quãng ước) quanh ước lượng
            if k < n and abs(nodes[j][0] - est[k]) > max(WINDOW, 0.25 * (est[k] - speech_start)):
                continue
            best, arg = INF, -1
            for i in range(0, j):
                if dp[k - 1][i] == INF:
                    continue
                c = dp[k - 1][i] + line_cost(k - 1, i, j) - nodes[j][3]
                if c < best:
                    best, arg = c, i
            dp[k][j], back[k][j] = best, arg

    if dp[n][N - 1] == INF:
        raise RuntimeError("không tìm được phương án cắt hợp lệ")
    path, j = [], N - 1
    for k in range(n, 0, -1):
        path.append(j)
        j = back[k][j]
    path.reverse()                              # node của ranh 1..n (ranh n = cuối)

    cuts, notes = [0.0], []
    for k, j in enumerate(path[:-1], start=1):
        cut, s1, s0, gain = nodes[j]
        cuts.append(cut)
        if gain > -NO_SIL + 1e-9:
            notes.append(f"ranh {k}: ước {est[k]:6.2f}s → lặng {s0:.2f}–{s1:.2f} ({s1 - s0:.2f}s) cắt {cut:.2f}s")
        else:
            notes.append(f"ranh {k}: ước {est[k]:6.2f}s → KHÔNG có lặng phù hợp, giữ {cut:.2f}s")
    cuts.append(total)
    return cuts, notes


def cut_segment(src: Path, dst: Path, start: float, end: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
         "-c:a", "libmp3lame", "-q:a", "2", str(dst)],
        check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slide_dir")
    ap.add_argument("full_audio")
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    slide_dir = Path(args.slide_dir).resolve()
    full_audio = Path(args.full_audio).resolve()
    out = Path(args.output_dir).resolve() if args.output_dir else slide_dir / "output"
    out.mkdir(parents=True, exist_ok=True)

    if not full_audio.exists() or full_audio.stat().st_size == 0:
        print(f"✗ Không thấy audio: {full_audio}")
        return 2
    lines = read_script_lines(slide_dir / "script-90s.txt")
    n = len(lines)
    total = probe_duration(full_audio)
    if total < MIN_LINE * n:
        print(f"✗ Audio quá ngắn ({total:.2f}s) cho {n} dòng")
        return 3

    sils = detect_silences(full_audio, total)
    cuts, notes = plan_cuts(lines, sils, total)
    print(f"Full voiceover {total:.2f}s · {len(sils)} quãng lặng · {n} dòng")
    for note in notes:
        print("  " + note)
    snapped = sum("KHÔNG" not in x for x in notes)
    print(f"  → snap được {snapped}/{n - 1} ranh giới vào quãng lặng")

    # Chốt an toàn: một dòng dài/ngắn bất thường so với tỉ lệ âm tiết (vd TTS đọc sót
    # hoặc lặp cả câu) → thoát lỗi để generate_tts.py quay về TTS từng dòng.
    w = [weight(t) for t in lines]
    span = cuts[-1] - cuts[0]
    for i in range(n):
        ratio = (cuts[i + 1] - cuts[i]) / (span * w[i] / sum(w))
        if not (0.45 <= ratio <= 2.2):
            print(f"✗ Dòng {i + 1} lệch tỉ lệ bất thường (x{ratio:.2f}) — nghi TTS đọc sót/lặp, huỷ cắt.")
            return 4

    timing = []
    for i, text in enumerate(lines):
        dst = out / f"line_{i}.mp3"
        cut_segment(full_audio, dst, cuts[i], cuts[i + 1])
        dur = round(cuts[i + 1] - cuts[i], 3)    # mốc cắt chính xác (mp3 có đệm encoder)
        write_line_srt(out / f"line_{i}.srt", text, dur)
        (out / f"line_{i}.txt").write_text(text, encoding="utf-8")
        (out / f"line_{i}.meta.json").unlink(missing_ok=True)   # tránh cache per-slide dùng nhầm
        timing.append({"line": i, "duration": dur, "original_audio_duration": dur,
                       "video_duration": 0.0, "text": text})
        print(f"Slide {i + 1}: {cuts[i]:7.2f}s → {cuts[i + 1]:7.2f}s  = {dur:.2f}s  -> {dst.name}")

    (out / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8")
    # Các đoạn liền nhau phủ kín bản gốc → ghép lại chính là bản gốc. Encode thẳng từ
    # bản gốc để voiceover_concat khớp tuyệt đối với timing.json (ghép n file mp3 sẽ
    # cộng dồn đệm encoder ~0,03–0,05s mỗi file → phụ đề trễ dần về cuối).
    concat = out / "voiceover_concat.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(full_audio),
                    "-c:a", "libmp3lame", "-q:a", "2", str(concat)], check=True)
    (out / "concat_list.txt").write_text("".join(f"file 'line_{i}.mp3'\n" for i in range(n)), encoding="utf-8")
    print(f"Concatenated voiceover: {probe_duration(concat):.2f}s -> {concat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
