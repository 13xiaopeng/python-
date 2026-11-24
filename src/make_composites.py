"""把手机(390px)和平板(768px)截图裁成合适高度后并排拼成一张图,供实验报告使用。
原因:单独放手机截图会过高(报告里 5cm 宽对应 30+cm 高),超出一页。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SHOTS = Path(__file__).resolve().parent.parent / "screenshots"
H = 1100          # 每张图保留的高度(像素)
GAP, HEAD = 50, 60

mobile = Image.open(SHOTS / "final_20_mobile.png").convert("RGB").crop((0, 0, 390, H))
tablet = Image.open(SHOTS / "final_21_tablet.png").convert("RGB").crop((0, 0, 768, H))
W = mobile.width + GAP + tablet.width
canvas = Image.new("RGB", (W + 40, H + HEAD + 20), "white")
d = ImageDraw.Draw(canvas)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 30)
x = 20
for im, label in [(mobile, "手机宽度 390px"), (tablet, "平板宽度 768px")]:
    d.text((x, 12), label, fill="#1E293B", font=font)
    canvas.paste(im, (x, HEAD))
    d.rectangle((x - 1, HEAD - 1, x + im.width, HEAD + im.height), outline="#94A3B8", width=2)   # 边框,区分截图与白底
    x += im.width + GAP
canvas.save(SHOTS / "final_22_responsive.png")
print("final_22_responsive.png", canvas.size)
