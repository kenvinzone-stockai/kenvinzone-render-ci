"""safezone.py out.png in1.png in2.png ... — ghép ảnh, phủ đỏ vùng UI che (Shorts/TikTok/Reels, mức thận trọng)."""
import sys
from PIL import Image, ImageDraw
out, ins = sys.argv[1], sys.argv[2:]
tiles = []
for f in ins:
    im = Image.open(f).convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for box in [(0, 1450, 1080, 1920), (888, 840, 1080, 1450), (0, 0, 1080, 240)]:
        d.rectangle(box, fill=(255, 30, 60, 70), outline=(255, 60, 80, 255), width=4)
    tiles.append(Image.alpha_composite(im, ov).convert("RGB").resize((360, 640)))
c = Image.new("RGB", (360 * len(tiles), 640)); [c.paste(t, (i * 360, 0)) for i, t in enumerate(tiles)]; c.save(out)
