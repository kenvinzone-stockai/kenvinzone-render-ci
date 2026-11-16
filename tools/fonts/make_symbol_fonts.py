#!/usr/bin/env python3
"""Sinh 2 font ký hiệu nhỏ, đóng gói vào mọi template HyperFrames → ký hiệu/emoji vẽ GIỐNG HỆT
nhau trên mọi máy (không phụ thuộc font hệ thống của runner).

    python tools/fonts/make_symbol_fonts.py [--src-symbols DejaVuSans-Bold.ttf] [--src-emoji NotoColorEmoji.ttf]

  kz-symbols.woff2  ← DejaVu Sans Bold (giấy phép Bitstream Vera/DejaVu, tự do): mũi tên, toán,
                      hình học, khối, dingbat, số khoanh tròn
  kz-emoji.woff2    ← Noto Color Emoji (SIL OFL 1.1): bộ emoji tài chính thường dùng

Hai font được khai dưới CHÍNH tên họ 'BVP' và 'JBM' kèm unicode-range (xem FONT_FACES), nên
không phải đổi font-family ở đâu cả. Muốn thêm ký hiệu/emoji: sửa SYMBOL_RANGES / EMOJI rồi chạy lại.
Sau đó: python tools/fonts/make_symbol_fonts.py --install  (copy vào template/*/assets/fonts).
"""
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "template" / "common" / "fonts"
SYMBOL_RANGES = [(0x2190, 0x21FF), (0x2200, 0x22FF), (0x2300, 0x23FF), (0x2460, 0x24FF), (0x2500, 0x257F),
                 (0x2580, 0x259F), (0x25A0, 0x25FF), (0x2600, 0x26FF), (0x2700, 0x27BF)]
# Emoji (vẽ màu). Ký tự nằm ở đây sẽ KHÔNG lấy từ font ký hiệu.
EMOJI = ("📈📉📊💹💰💵💸🏦🪙🥇🔥⚡✅❌⚠🛡🔄🔁📄📰📌📍🎯🚀💡🔔⭐🌟🟢🔴🟡🟠🔵⏰⏳🧭🧠👉👀🤝🎉📣📢🗓🕐"
         "🛢⛽🏭💎🐂🐻")


def cps(s):
    return sorted({ord(c) for c in s})


def ranges_css(points):
    out, start, prev = [], None, None
    for p in points:
        if start is None:
            start = prev = p
        elif p == prev + 1:
            prev = p
        else:
            out.append((start, prev)); start = prev = p
    if start is not None:
        out.append((start, prev))
    return ",".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in out)


def build(src_sym: Path, src_emoji: Path):
    OUT.mkdir(parents=True, exist_ok=True)
    emoji_cps = set(cps(EMOJI)) | {0xFE0F, 0x200D}
    cmap = TTFont(src_sym, lazy=True).getBestCmap()
    sym_cps = [c for a, b in SYMBOL_RANGES for c in range(a, b + 1) if c in cmap and c not in emoji_cps]
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.notdef_outline = False
    f = TTFont(src_sym); s = subset.Subsetter(opts); s.populate(unicodes=sym_cps); s.subset(f)
    f.save(OUT / "kz-symbols.woff2")
    ecm = TTFont(src_emoji, lazy=True).getBestCmap()
    have = [c for c in sorted(emoji_cps) if c in ecm]
    # Không đưa cờ quốc gia: giữ ký tự vùng kéo theo mọi tổ hợp cờ (~0,8 MB).
    eo = subset.Options(); eo.flavor = "woff2"; eo.layout_features = ["*"]
    f = TTFont(src_emoji); s = subset.Subsetter(eo); s.populate(unicodes=have); s.subset(f)
    f.save(OUT / "kz-emoji.woff2")
    css = font_faces(sym_cps, have)
    (OUT / "kz-symbols.css").write_text(css, encoding="utf-8")
    (OUT / "kz-symbols.ranges.json").write_text(json.dumps({"sym": ranges_css(sym_cps), "emoji": ranges_css(sorted(set(have)))}), encoding="utf-8")
    for n in ("kz-symbols.woff2", "kz-emoji.woff2"):
        print(f"{n}: {(OUT / n).stat().st_size / 1024:.0f} KB")
    print(f"{len(sym_cps)} ký hiệu · {len(have)} emoji → {OUT}")


def font_faces(sym_cps, emoji_cps, weights=None) -> str:
    """CSS khai 2 font dưới tên họ BVP và JBM, đúng theo các độ đậm template đang có."""
    r_sym, r_emo = ranges_css(sym_cps), ranges_css(sorted(set(emoji_cps)))
    # QUAN TRỌNG: lặp lại theo ĐÚNG các độ đậm họ font đang có. Trình duyệt chọn theo độ đậm
    # TRƯỚC rồi mới xét unicode-range — khai "100 900" sẽ khớp chính xác mọi độ đậm (vd 600, 900)
    # và loại mất file chữ thật → chữ thường rơi về font hệ thống.
    rows = []
    weights = weights or {"BVP": (500, 700, 800, 900), "JBM": (700, 800)}
    for fam, ws in weights.items():
        for w in ws:
            rows.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:{r_emo};}}")
            rows.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:{r_sym};}}")
    return "\n".join(rows) + "\n"


def _faces_for(build_src: str, rng: dict) -> str:
    """Khai font ký hiệu ĐÚNG theo các độ đậm mà template này đang có cho BVP / JBM
    (thêm độ đậm template không có sẽ "cướp" việc chọn font của chữ thường)."""
    rows = []
    for fam in ("BVP", "JBM"):
        ws = sorted({int(w) for w in re.findall(r"font-family:'%s';font-weight:(\d+);src:url\('assets/fonts/(?!kz-)" % fam, build_src)})
        for w in ws:
            rows.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('assets/fonts/kz-emoji.woff2') format('woff2');unicode-range:{rng['emoji']};}}")
            rows.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('assets/fonts/kz-symbols.woff2') format('woff2');unicode-range:{rng['sym']};}}")
    return "\n".join(rows)


def install():
    rng = json.loads((OUT / "kz-symbols.ranges.json").read_text(encoding="utf-8"))
    for t in sorted((REPO / "template").glob("*-hf")):
        fonts = t / "assets" / "fonts"
        if not fonts.exists():
            continue
        for n in ("kz-symbols.woff2", "kz-emoji.woff2"):
            shutil.copy2(OUT / n, fonts / n)
        bp = t / "build.py"; s = bp.read_text(encoding="utf-8")
        start, end = "/*KZ-SYMBOLS*/", "/*/KZ-SYMBOLS*/"
        if start in s:
            a, b = s.index(start), s.index(end) + len(end)
            s = s[:a] + s[b:]
        # chèn ngay sau dòng @font-face JBM cuối cùng (giữ nguyên kiểu ngoặc {{ }} nếu là f-string)
        css = _faces_for(s.replace("{{", "{").replace("}}", "}"), rng)
        idx = s.rfind("@font-face{font-family:'JBM'"); dbl = False
        if idx < 0:
            idx = s.rfind("@font-face{{font-family:'JBM'"); dbl = True
        line_end = s.index("\n", idx)
        block = start + "\n" + (css.replace("{", "{{").replace("}", "}}") if dbl else css) + "\n" + end
        s = s[:line_end + 1] + block + "\n" + s[line_end + 1:]
        bp.write_text(s, encoding="utf-8")
        got = sorted(set(re.findall(r"family:'(\w+)';font-weight:(\d+);src:url\('assets/fonts/kz-sym", css)))
        print(f"  cài vào {t.name}: {' '.join(f + str(w) for f, w in got)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-symbols", default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    ap.add_argument("--src-emoji", default="/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
    ap.add_argument("--install", action="store_true")
    a = ap.parse_args()
    build(Path(a.src_symbols), Path(a.src_emoji))
    if a.install:
        install()
