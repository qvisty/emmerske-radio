"""Tegner forsidens illustration af Emmerske Efterskole set fra Aabenraavej:
det hvidkalkede, stråtækte Emmerske Bedehus forrest og det røde skolehus bag ved.

Skriver assets/img/skolen.svg. Renderes til webp med Chrome (se bunden af filen).
Kør:  python tools/forside_illustration.py
"""
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "skolen.svg"
R = random.Random(1730)  # bedehusets byggeår
W = H = 1000
INK = "#3e3128"

parts = []
add = parts.append


def jitter(pts, a=1.5):
    return " ".join(f"{x + R.uniform(-a, a):.1f},{y + R.uniform(-a, a):.1f}" for x, y in pts)


def poly(pts, fill, stroke=INK, sw=2.2, extra=""):
    add(f'<polygon points="{jitter(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
        f'stroke-linejoin="round" {extra}/>')


def rect(x, y, w, h, fill, stroke=INK, sw=2, extra=""):
    poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw, extra)


def blob(cx, cy, r, fill, opacity=1.0, n=9):
    pts = []
    for k in range(n):
        import math
        a = 2 * math.pi * k / n
        rr = r * R.uniform(0.82, 1.12)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.85))
    d = "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    add(f'<path d="{d}Z" fill="{fill}" opacity="{opacity}" stroke-linejoin="round" filter="url(#soft)"/>')


def foliage(x0, x1, ytop, ybot, palette, count, rmin, rmax, ink=False):
    for _ in range(count):
        cx, cy = R.uniform(x0, x1), R.uniform(ytop, ybot)
        blob(cx, cy, R.uniform(rmin, rmax), R.choice(palette), R.uniform(0.85, 1))
    if ink:  # løse blækkonturer øverst i kronerne
        for _ in range(count // 3):
            cx, cy, r = R.uniform(x0, x1), R.uniform(ytop, ytop + (ybot - ytop) * 0.4), R.uniform(rmin, rmax)
            add(f'<path d="M{cx - r:.0f},{cy:.0f} q{r * .5:.0f},{-r * .9:.0f} {r:.0f},{-r * .2:.0f} '
                f'q{r * .5:.0f},{-r * .6:.0f} {r:.0f},{r * .2:.0f}" fill="none" stroke="{INK}" '
                f'stroke-width="1.6" opacity=".55" stroke-linecap="round"/>')


def window(x, y, w, h, cols=2, rows=3, frame="#fbfaf6", glass="#a9bcc6", arched=False):
    if arched:
        r = w / 2
        add(f'<path d="M{x},{y + h} V{y + r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h} Z" fill="{frame}" '
            f'stroke="{INK}" stroke-width="2"/>')
    else:
        rect(x, y, w, h, frame, sw=2)
    pad = 4
    gw, gh = (w - pad * (cols + 1)) / cols, (h - pad * (rows + 1)) / rows
    for c in range(cols):
        for r_ in range(rows):
            gx, gy = x + pad + c * (gw + pad), y + pad + r_ * (gh + pad)
            if arched and r_ == 0:
                continue
            shade = R.choice([glass, "#b9cad2", "#93a9b5"])
            add(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" fill="{shade}"/>')
            add(f'<line x1="{gx + 2:.1f}" y1="{gy + gh - 3:.1f}" x2="{gx + gw * .6:.1f}" y2="{gy + 3:.1f}" '
                f'stroke="#ffffff" stroke-width="1.4" opacity=".55"/>')


def bricks(x0, y0, x1, y1, step=9):
    y = y0 + step
    row = 0
    while y < y1:
        add(f'<line x1="{x0}" y1="{y:.0f}" x2="{x1}" y2="{y:.0f}" stroke="#8e3f2a" stroke-width=".7" opacity=".35"/>')
        x = x0 + (row % 2) * 11
        while x < x1:
            add(f'<line x1="{x:.0f}" y1="{y - step:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="#8e3f2a" '
                f'stroke-width=".6" opacity=".25"/>')
            x += 22
        y += step
        row += 1


# ---------------------------------------------------------------- defs
add(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#9fbfd6"/><stop offset=".55" stop-color="#cfe0e8"/><stop offset="1" stop-color="#eef0e6"/>
  </linearGradient>
  <linearGradient id="thatch" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#9a8a6c"/><stop offset="1" stop-color="#77684f"/>
  </linearGradient>
  <linearGradient id="tiles" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#e98a4a"/><stop offset="1" stop-color="#c9602f"/>
  </linearGradient>
  <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ddd6c6"/><stop offset=".3" stop-color="#f7f4ec"/><stop offset="1" stop-color="#ebe4d4"/>
  </linearGradient>
  <filter id="soft" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="3" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="9"/>
  </filter>
  <filter id="wash" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency=".02" numOctaves="3" seed="7" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="4"/>
  </filter>
  <filter id="paper">
    <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="11"/>
    <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .38  0 0 0 0 .3  0 0 0 .09 0"/>
  </filter>
  <filter id="blotch">
    <feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="3" seed="5"/>
    <feColorMatrix values="0 0 0 0 .55  0 0 0 0 .45  0 0 0 0 .3  0 0 0 .3 -.05"/>
  </filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>''')

# ---------------------------------------------------------------- himmel og skyer
for cx, cy, s in [(190, 150, 1.0), (760, 250, 0.85), (520, 90, 0.5)]:
    for _ in range(9):
        blob(cx + R.uniform(-120, 120) * s, cy + R.uniform(-25, 25) * s, R.uniform(45, 85) * s, "#f8ecc9", .95)
    for _ in range(4):
        blob(cx + R.uniform(-100, 100) * s, cy + 25 * s, R.uniform(30, 55) * s, "#ead39e", .55)

# ---------------------------------------------------------------- træer bagved
foliage(-40, 1040, 400, 560, ["#7d9a5a", "#6b8a4c", "#8fab68", "#5f7d45"], 70, 35, 75)

# ---------------------------------------------------------------- det røde skolehus (bagved, til højre)
poly([(540, 690), (1010, 690), (1010, 820), (540, 820)], "#e6dbc4", sw=0)  # gårdsplads bag bedehuset
add('<g filter="url(#wash)">')
poly([(560, 470), (970, 470), (970, 690), (560, 690)], "#b8573b")
add('</g>')
bricks(560, 470, 970, 690)
poly([(530, 478), (610, 360), (930, 360), (1000, 478)], "url(#tiles)")
for x in range(625, 925, 18):  # tegl-rækker
    add(f'<line x1="{x}" y1="362" x2="{x - 20 + (x - 625) * 0.12:.0f}" y2="476" stroke="#a9471f" stroke-width=".8" opacity=".35"/>')
for y in range(380, 476, 14):
    add(f'<line x1="{560 - (y - 478) * 0.6:.0f}" y1="{y}" x2="{1000 - (478 - y) * 0.6:.0f}" y2="{y}" stroke="#a9471f" stroke-width=".7" opacity=".3"/>')
for dx in (700, 790, 880):  # hvide kviste
    poly([(dx - 30, 446), (dx - 30, 410), (dx, 392), (dx + 30, 410), (dx + 30, 446)], "#f6f3ea", sw=2)
    window(dx - 21, 414, 42, 28, cols=3, rows=2)
# gavl med svungne kanter mod højre
poly([(930, 360), (1000, 478), (1000, 690), (970, 690), (970, 478)], "#a94f35", sw=2)
for x, y in [(740, 520), (820, 520), (900, 520), (740, 600), (820, 600), (900, 600)]:
    window(x, y, 44, 60, cols=2, rows=3)
add('<path d="M748,692 v-48 a22,22 0 0 1 44,0 v48" fill="#3f4a3c" stroke="#3e3128" stroke-width="2"/>')

# ---------------------------------------------------------------- træer i siderne
add('<path d="M40,700 C45,600 30,520 50,430" stroke="#5a4535" stroke-width="12" fill="none" stroke-linecap="round"/>')
foliage(-60, 110, 330, 560, ["#6b8a4c", "#7f9d5b", "#58763f"], 22, 35, 70)
# ---------------------------------------------------------------- træ til højre
add('<path d="M955,800 C950,700 965,640 940,560" stroke="#5a4535" stroke-width="16" fill="none" stroke-linecap="round"/>')
foliage(890, 1070, 330, 600, ["#6b8a4c", "#7f9d5b", "#91ae6a", "#58763f"], 40, 40, 80)

# ---------------------------------------------------------------- Emmerske Bedehus (forrest)
# hvidkalket væg
add('<g filter="url(#wash)">')
poly([(30, 568), (700, 568), (700, 790), (30, 790)], "url(#wall)")
add('</g>')
poly([(30, 568), (700, 568), (700, 790), (30, 790)], "none", sw=2.4)
poly([(30, 790), (700, 790), (700, 818), (30, 818)], "#2f2a27", sw=2)  # sort sokkel
# stråtag (valmtag)
poly([(0, 580), (115, 300), (615, 300), (730, 580)], "url(#thatch)", sw=2.6)
for _ in range(900):  # strå
    y = R.uniform(305, 575)
    t = (y - 300) / 280
    xl, xr = 115 - 115 * t, 615 + 115 * t
    x = R.uniform(xl + 4, xr - 4)
    ln = R.uniform(10, 26)
    col = R.choice(["#665843", "#a39373", "#5b4e3b", "#b2a382"])
    add(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + R.uniform(-2, 2):.1f}" y2="{y + ln:.1f}" stroke="{col}" '
        f'stroke-width="{R.uniform(.6, 1.4):.1f}" opacity=".7" stroke-linecap="round"/>')
add(f'<path d="M0,580 Q365,600 730,580" fill="none" stroke="{INK}" stroke-width="2.6"/>')  # tykke tagskæg
add(f'<path d="M115,300 Q365,288 615,300" fill="none" stroke="{INK}" stroke-width="3"/>')  # rygning
# skygge under tagskægget
add('<path d="M30,582 Q365,606 700,582 L700,600 Q365,622 30,600 Z" fill="#6f6556" opacity=".25"/>')
# vinduer med hvide sprosser
for x in (60, 135, 210, 470, 545, 620):
    window(x, 640, 50, 104, cols=2, rows=4)
# murankre over vinduerne
for x in (85, 160, 235, 495, 570, 645):
    add(f'<path d="M{x + 4},604 c-8,0 -8,10 0,11 c8,1 8,11 0,11" fill="none" stroke="{INK}" '
        f'stroke-width="2.6" stroke-linecap="round"/>')
# frontkvist i røde sten med indgang
add('<g filter="url(#wash)">')
poly([(305, 818), (305, 500), (365, 420), (425, 500), (425, 818)], "#b5553a")
add('</g>')
bricks(305, 470, 425, 790, step=8)
poly([(305, 818), (305, 500), (365, 420), (425, 500), (425, 818)], "none", sw=2.4)
poly([(296, 504), (365, 412), (434, 504)], "none", sw=3)
window(345, 520, 40, 50, cols=2, rows=2)
add(f'<path d="M335,818 V735 A30,30 0 0 1 395,735 V818 Z" fill="#33403a" stroke="{INK}" stroke-width="2.2"/>')
add(f'<path d="M365,708 V818" stroke="{INK}" stroke-width="1.4" opacity=".7"/>')
# flagstang med Dannebrog (proportioner 3:1:4,5 x 3:1:3)
add(f'<path d="M478,820 V440" stroke="#ecebe6" stroke-width="6"/><path d="M478,820 V440" stroke="{INK}" stroke-width="1.2" opacity=".55"/>')
add(f'<circle cx="478" cy="436" r="6" fill="#d9b44a" stroke="{INK}" stroke-width="1.4"/>')
FX, FY, FW, FH = 481, 446, 92, 62
u = FW / 8.5
def wave(x, y):  # let bølgende flag
    import math
    t = (x - FX) / FW
    return x, y + 7 * math.sin(t * 3.2) * t
def flagpoly(x0, y0, x1, y1, fill, sw=0):
    pts = [wave(x0 + (x1 - x0) * k / 8, y0) for k in range(9)] + [wave(x1 - (x1 - x0) * k / 8, y1) for k in range(9)]
    add(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" '
        f'stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
add('<g filter="url(#wash)">')
flagpoly(FX, FY, FX + FW, FY + FH, "#c8102e")
flagpoly(FX + 3 * u, FY, FX + 4 * u, FY + FH, "#f7f3ea")                     # lodret kors
flagpoly(FX, FY + FH * 3 / 7, FX + FW, FY + FH * 4 / 7, "#f7f3ea")           # vandret kors
add('</g>')
flagpoly(FX, FY, FX + FW, FY + FH, "none", sw=2)

# ---------------------------------------------------------------- forgrund: gårdsplads, vej, græs
add('<g filter="url(#wash)">')
poly([(-10, 818), (1010, 818), (1010, 870), (-10, 870)], "#e6dbc4", sw=0)
poly([(-10, 870), (1010, 870), (1010, 940), (-10, 940)], "#b4b1a8", sw=0)
poly([(-10, 940), (1010, 940), (1010, 1010), (-10, 1010)], "#98b766", sw=0)
add('</g>')
for _ in range(260):  # grus
    add(f'<circle cx="{R.uniform(0, 1000):.0f}" cy="{R.uniform(822, 866):.0f}" r="{R.uniform(.6, 1.6):.1f}" fill="#b8a98b" opacity=".6"/>')
for x in range(40, 1000, 150):  # vejstriber
    add(f'<rect x="{x}" y="902" width="70" height="5" fill="#f4f2ec" opacity=".9"/>')
add(f'<path d="M-10,870 H1010 M-10,940 H1010" stroke="{INK}" stroke-width="1.4" opacity=".45"/>')
for _ in range(220):  # græsstrå
    x, y = R.uniform(0, 1000), R.uniform(945, 1000)
    add(f'<path d="M{x:.0f},{y:.0f} q{R.uniform(-3, 3):.1f},-8 {R.uniform(-4, 4):.1f},-{R.uniform(8, 16):.0f}" '
        f'stroke="{R.choice(["#6f9147", "#82a457", "#5d7e3c"])}" stroke-width="1.3" fill="none"/>')
# skiltet ved indkørslen
for px in (752, 948):
    rect(px, 790, 10, 74, "#7a5a3c", sw=1.6)
add('<g filter="url(#wash)">')
rect(730, 748, 240, 48, "#9b4f2b", sw=2.4)
add('</g>')
rect(730, 748, 240, 48, "none", sw=2.4)
add(f'<text x="850" y="779" text-anchor="middle" font-family="Georgia, serif" font-size="14" letter-spacing="1.5" '
    f'fill="#f3e3c8" opacity=".92" font-weight="bold">EMMERSKE EFTERSKOLE</text>')
# buske ved husets hjørner
foliage(-30, 70, 760, 840, ["#6b8a4c", "#7f9d5b", "#58763f"], 14, 25, 45)

# ---------------------------------------------------------------- papir og akvarel-pletter
add(f'<rect width="{W}" height="{H}" filter="url(#blotch)" style="mix-blend-mode:multiply"/>')
add(f'<rect width="{W}" height="{H}" filter="url(#paper)" style="mix-blend-mode:multiply"/>')
add('</svg>')

OUT.write_text("\n".join(parts), encoding="utf-8")
print("Skrev", OUT)

# Rendering til webp (Windows, Chrome):
#   chrome --headless=new --window-size=1000,1000 --screenshot=skolen.png assets/img/skolen.svg
#   python -c "from PIL import Image; Image.open('skolen.png').convert('RGB').save('assets/img/forside.webp', quality=88)"
