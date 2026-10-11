"""Draws the generic multifunction printer/scanner icon for the brands folder.

No brand name, logo or brand colour: a neutral grey device with an open lid,
a sheet on the glass, a paper slot and a green ready light. Writes
brands/brother_scanner/icon.png (256 x 256) and icon@2x.png (512 x 512); there
is no logo.png, so Home Assistant uses the icon in its place.

    python tools/make_icons.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "brands", "brother_scanner")

BODY = (72, 79, 92, 255)
BODY_DARK = (45, 51, 62, 255)
PANEL = (120, 128, 142, 255)
PAPER = (248, 249, 250, 255)
LINES = (173, 181, 189, 255)
SLOT = (28, 32, 40, 255)
LIGHT = (34, 197, 94, 255)


def draw(size):
    scale = size / 512
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def s(*values):
        return [round(v * scale) for v in values]

    # lid, open at an angle, seen from the front: a parallelogram
    d.polygon([tuple(s(118, 110)), tuple(s(394, 110)), tuple(s(430, 238)), tuple(s(82, 238))], fill=BODY_DARK)
    # sheet lying on the glass, with text lines
    d.polygon([tuple(s(156, 136)), tuple(s(356, 136)), tuple(s(380, 218)), tuple(s(132, 218))], fill=PAPER)
    for y, w in ((158, 150), (176, 120), (194, 136)):
        x0 = 170 + (y - 136) * 0.2
        d.line([tuple(s(x0, y)), tuple(s(x0 + w, y))], fill=LINES, width=max(1, round(8 * scale)))
    # body
    d.rounded_rectangle([tuple(s(40, 236)), tuple(s(472, 420))], radius=round(28 * scale), fill=BODY)
    # control panel strip
    d.rounded_rectangle([tuple(s(72, 262)), tuple(s(440, 296))], radius=round(10 * scale), fill=PANEL)
    # output slot with a sheet coming out
    d.rounded_rectangle([tuple(s(84, 328)), tuple(s(428, 352))], radius=round(8 * scale), fill=SLOT)
    d.rounded_rectangle([tuple(s(104, 334)), tuple(s(408, 346))], radius=round(5 * scale), fill=PAPER)
    # ready light
    d.ellipse([tuple(s(404, 374)), tuple(s(436, 406))], fill=LIGHT)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        draw(size).save(os.path.join(OUT, name), optimize=True)
        print("wrote", name, size)


if __name__ == "__main__":
    main()
