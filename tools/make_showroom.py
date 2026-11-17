# Складає картинку першого екрана (img/hero/showroom*.webp) з фото товарів. Потрібен Pillow.
# Запуск: python3 tools/make_showroom.py img/products img/hero
import sys
from PIL import Image, ImageFilter, ImageDraw
SRC = sys.argv[1]; OUT = sys.argv[2]
W, H = 1900, 1000
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shadow = Image.new("L", (W, H), 0)
refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# (photo, left x, bottom y, height)  -- back to front
items = [
    ("dd-1",   1585, 740, 560),
    ("fwdd-1", 1335, 772, 610),
    ("hwdd-2", 1060, 808, 670),
    ("hw-2",   560,  895, 610),
    ("fw-2",   40,   965, 720),
]
def trim(name):
    im = Image.open(f"{SRC}/{name}.webp").convert("RGBA")
    a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    return im.crop(a.getbbox())
d = ImageDraw.Draw(shadow)
for name, x, by, h in items:
    im = trim(name)
    w = round(im.width * h / im.height)
    im = im.resize((w, h), Image.LANCZOS)
    y = by - h
    # floor contact shadow
    d.ellipse([x - 10, by - 18, x + w + 30, by + 22], fill=110)
    # reflection
    r = im.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, w, int(h * .35)))
    grad = Image.linear_gradient("L").resize((w, r.height)).point(lambda v: int((255 - v) * .22))
    ra = r.getchannel("A").point(lambda v: v)
    from PIL import ImageChops
    r.putalpha(ImageChops.multiply(ra, grad))
    refl.alpha_composite(r, (x, by + 2))
    canvas.alpha_composite(im, (x, y))
# compose: shadow -> reflection -> machines
sh = shadow.filter(ImageFilter.GaussianBlur(14))
base = Image.new("RGBA", (W, H), (20, 40, 70, 0))
base.putalpha(sh.point(lambda v: int(v * .55)))
out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
out.alpha_composite(base); out.alpha_composite(refl); out.alpha_composite(canvas)
out = out.crop(out.getchannel("A").getbbox())
print(out.size)
out.save(f"{OUT}/showroom.webp", quality=82, method=6)
s = out.resize((800, round(800 * out.height / out.width)), Image.LANCZOS)
s.save(f"{OUT}/showroom-sm.webp", quality=80, method=6)
print(s.size)
