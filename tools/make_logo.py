"""Laver skolens logo om til vektorgrafik (SVG) til siden.

Læser "Filer/Emmerske Efterskole logo.png" og skriver:
  assets/img/logo.svg     hele logoet. Kan vises som billede og bruges med <use href="assets/img/logo.svg#ee-logo">
                          (og #ee-mark for kun symbolet). Ordet EMMERSKE følger tekstfarven (currentColor),
                          det grønne kan styres med CSS-variablen --ee-green.
  assets/img/favicon.svg  symbolet på en lys flade.
Kør fra repoets rod:  python tools/make_logo.py
Kræver: pillow, numpy, potracer (pip install pillow numpy potracer)
"""
from pathlib import Path

import numpy as np
import potrace
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Filer" / "Emmerske Efterskole logo.png"
OUT_LOGO = ROOT / "assets" / "img" / "logo.svg"
OUT_ICON = ROOT / "assets" / "img" / "favicon.svg"

GREEN = "#007a53"   # skolens grønne farve, aflæst i logoet
SCALE = 4           # spores i 4x opløsning for bløde kurver
MARK_BOTTOM = 200   # alt grønt over denne linje er symbolet, resten er "efterskole"
PAD = 2

im = Image.open(SRC).convert("RGB")
W, H = im.size
big = im.filter(ImageFilter.GaussianBlur(1.1)).resize((W * SCALE, H * SCALE), Image.BICUBIC)
a = np.asarray(big).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
green = (g - r > 50) & (g > 50)
black = (r + g + b < 330) & ~green
row = np.arange(H * SCALE)[:, None]
mark = green & (row < MARK_BOTTOM * SCALE)
efter = green & (row >= MARK_BOTTOM * SCALE)


def bbox(mask):
    ys, xs = np.where(mask)
    return (xs.min() / SCALE - PAD, max(0, ys.min() / SCALE - PAD), xs.max() / SCALE + PAD, ys.max() / SCALE + PAD)


def trace(mask, dx, dy):
    # potracer udfylder de "mørke" (falske) pixels, derfor vendes masken
    curves = potrace.Bitmap(~mask).trace(turdsize=30, alphamax=1.15, opticurve=True, opttolerance=1.0)
    pt = lambda p: f"{round(p.x / SCALE - dx, 1):g} {round(p.y / SCALE - dy, 1):g}"
    out = []
    for c in curves:
        d = [f"M{pt(c.start_point)}"]
        for s in c.segments:
            d.append(f"L{pt(s.c)}L{pt(s.end_point)}" if s.is_corner else f"C{pt(s.c1)} {pt(s.c2)} {pt(s.end_point)}")
        out.append("".join(d) + "Z")
    return "".join(out)


x0, y0, x1, y1 = bbox(green | black)
lw, lh = round(x1 - x0), round(y1 - y0)
mx0, my0, mx1, my1 = bbox(mark)
mw, mh = round(mx1 - mx0), round(my1 - my0)

fill_green = f'style="fill:var(--ee-green,{GREEN})"'
mark_d = trace(mark, mx0, my0)
OUT_LOGO.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {lw} {lh}">\n'
    f'<title>Emmerske Efterskole</title>\n'
    f'<symbol id="ee-mark" viewBox="0 0 {mw} {mh}"><path {fill_green} d="{mark_d}"/></symbol>\n'
    f'<symbol id="ee-logo" viewBox="0 0 {lw} {lh}">'
    f'<path {fill_green} d="{trace(mark, x0, y0)}{trace(efter, x0, y0)}"/>'
    f'<path fill="currentColor" d="{trace(black, x0, y0)}"/></symbol>\n'
    f'<use href="#ee-logo" xlink:href="#ee-logo" width="{lw}" height="{lh}"/>\n'
    f'</svg>\n',
    encoding="utf-8",
)

# favicon: symbolet centreret på en lys, afrundet flade
size, inner = 64, 54
s = inner / mw
OUT_ICON.write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
    f'<rect width="{size}" height="{size}" rx="14" fill="#fffdf8"/>'
    f'<path fill="{GREEN}" transform="translate({(size - inner) / 2:g} {(size - mh * s) / 2:.2f}) scale({s:.4f})" d="{mark_d}"/>'
    f'</svg>\n',
    encoding="utf-8",
)
print(f"{OUT_LOGO.relative_to(ROOT)}: {OUT_LOGO.stat().st_size} bytes, {OUT_ICON.relative_to(ROOT)}: {OUT_ICON.stat().st_size} bytes")
