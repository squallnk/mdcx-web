"""生成 unraid/icon.png（Unraid 模板图标，256x256）。

一次性工具，改动视觉时重跑：
    python scripts/make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
OUT = Path(__file__).resolve().parent.parent / "unraid" / "icon.png"

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 深色渐变底：上深下浅，配合前端的玻璃态暗色主题
for y in range(SIZE):
    t = y / (SIZE - 1)
    r = int(18 + (46 - 18) * t)
    g = int(20 + (54 - 20) * t)
    b = int(28 + (78 - 28) * t)
    draw.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

# 圆角遮罩
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=48, fill=255)
img.putalpha(mask)

draw = ImageDraw.Draw(img)
# 主色描边
draw.rounded_rectangle([10, 10, SIZE - 11, SIZE - 11], radius=40, outline=(96, 165, 250, 255), width=3)

font = None
for candidate in (
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
):
    if Path(candidate).exists():
        font = ImageFont.truetype(candidate, 66)
        break
if font is None:
    font = ImageFont.load_default()

text = "MDCx"
left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
draw.text(
    ((SIZE - (right - left)) / 2 - left, (SIZE - (bottom - top)) / 2 - top - 8),
    text,
    font=font,
    fill=(226, 232, 240, 255),
)

bar_font = None
for candidate in (r"C:\Windows\Fonts\msyh.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    if Path(candidate).exists():
        bar_font = ImageFont.truetype(candidate, 26)
        break
if bar_font is None:
    bar_font = ImageFont.load_default()

sub = "WEB"
l2, t2, r2, b2 = draw.textbbox((0, 0), sub, font=bar_font)
draw.text(((SIZE - (r2 - l2)) / 2 - l2, 168), sub, font=bar_font, fill=(96, 165, 250, 255))

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")
