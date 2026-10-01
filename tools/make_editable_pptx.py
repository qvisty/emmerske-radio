"""Gør præsentationen "Trivslens Arkitektur" redigerbar.

Hvert dias i den oprindelige fil er ét fladt billede. Scriptet:
  1. læser de oprindelige billeder fra tools/kilde (samme billeder som i den første PPTX),
  2. finder teksten med Windows' indbyggede OCR (tools/ocr.ps1),
  3. fjerner den valgte tekst fra billedet (inpainting),
  4. lægger teksten ind igen som tekstbokse med målt farve, størrelse og placering,
  5. eksporterer PDF og billeder til hjemmesiden via PowerPoint.

Håndskrevne noter og tekst inde i tegningerne forbliver en del af billedet.

Kør fra repoets rod (Windows):  python tools/make_editable_pptx.py
Kræver: pymupdf, python-pptx, opencv-python-headless, pillow
"""
import io, json, math, re, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "kilde" / "Trivslens Arkitektur - original.pdf"  # de oprindelige, flade dias
OUT = ROOT / "Filer" / "Trivslens Arkitektur Emmerske Efterskole.pptx"
OUT_PDF = OUT.with_suffix(".pdf")
SLIDE_IMG = ROOT / "assets" / "slides"            # billeder til hjemmesiden
WORK = ROOT / "tools" / ".pptx-work"          # mellemfiler (ignoreres af git)

W_PX, H_PX = 1376, 768                        # billedernes opløsning
SLIDE_W, SLIDE_H = 16256000, 9144000          # EMU, som i den oprindelige fil
PIC_TOP, PIC_H = 38100, 9067800               # billedets placering i den oprindelige fil
EMU_X = SLIDE_W / W_PX                        # EMU pr. pixel
EMU_Y = PIC_H / H_PX
PT = EMU_Y / 12700                            # punkt pr. pixel
OCR_UP = 2552                                 # OCR køres på opskaleret billede
# Dias hvor OCR kun skal se et udsnit (x0, y0, x1, y1), fx fordi skrå billeder
# ellers får OCR'en til at tro, at al tekst er roteret
OCR_CROP = {9: (0, 0, 720, 300)}

FONTS = {  # navn i PowerPoint -> (normal, fed) fontfil til målinger
    "Arial": ("arial.ttf", "arialbd.ttf"),
    "Arial Narrow": ("ARIALN.TTF", "ARIALNB.TTF"),
    "Georgia": ("georgia.ttf", "georgiab.ttf"),
    "Segoe Print": ("segoepr.ttf", "segoeprb.ttf"),
}
# Grundlinjens placering i en PowerPoint-tekstboks: B = a*linjeafstand + b*skriftstørrelse (målt)
BASELINE = {"Arial": (0.724, 0.044), "Arial Narrow": (0.714, 0.012),
            "Georgia": (0.714, -0.035), "Segoe Print": (0.765, -0.182)}

# --------------------------------------------------------------------------
# Opsætning pr. dias.  En blok = én tekstboks.
#   lines: OCR-linjenumre, eller dict(i=nr, text=rettet tekst, from_word=nr, box=(x0,y0,x1,y1))
#   **fed** markerer fede ord.  font: sans (Arial/Arial Narrow vælges automatisk),
#   serif, hand.  bold: hele blokken fed.  align: l/c.
#   erase: OCR-linjer der fjernes fra billedet uden at blive til tekst (fx en dobbelt linje).
# --------------------------------------------------------------------------
def B(lines, font="sans", bold=False, align="l", erase=()):
    return dict(lines=lines, font=font, bold=bold, align=align, erase=erase)

SLIDES = {
    1: [B([0, 1]),
        B([4, dict(i=5, text="Efterskole – Trivslens Arkitektur.")]),
        B([7, 8, 9])],
    2: [B([0], bold=True), B([3], bold=True, align="c"), B([12], bold=True, align="c"),
        B([1], align="c"), B([2], align="c"), B([8], align="c"), B([10], align="c"),
        B([4, 5], align="c"), B([6, 7], align="c"), B([9], align="c"), B([11], align="c"),
        B([13, 14], align="c"), B([15, 16], align="c"), B([17, 18], align="c"), B([19, 20], align="c")],
    3: [B([0], bold=True), B([1, 2]),
        B([3, 4, 5, 7], font="hand"), B([6, 8, 9, 10], font="hand"),
        B([dict(i=11, text="Fase 1 (Start):"), 12, 13, 14, 15], font="hand"),
        B([16]), B([17], align="c")],
    4: [B([dict(i=0, text="Du er aldrig alene: Vores voksen-økosystem.")], bold=True),
        B([dict(i=1, text="**Mellemste ring**"), dict(i=2, text="**(Specialiseret Støtte):**"),
           dict(i=9, text="Tobias (AKT-teamet -", from_word="Tobias"), 10, 11, 12, 13]),
        B([dict(i=3, text="**Eleven**"), 4], align="c"),
        B([dict(i=5, text="**Inderste ring (Nærværende Lærere):**"),
           dict(i=6, text="Kjeld (Matematik/Håndværk) - Har tid til"), 7, 8]),
        B([dict(i=14, text="**Yderste ring (Det Holistiske Hjem):**"), 15, 16])],
    5: [B([0], bold=True),
        B([dict(i=1, text="**KRAP** (Kognitiv, Ressourcefokuseret,"), 2, 3, 4]),
        B([dict(i=5, text="**4. Evaluering & Vækst:**"), 6, 7, 8, 9]),
        B([dict(i=10, text="**1. Kort Samtale & Observation:**"), 11, 12]),
        B([dict(i=13, text="**2. Perspektivering:**"), 14, 15, 16], erase=[17]),  # "forståelse." stod to gange
        B([dict(i=18, text="**3. Skræddersyet Plan (2-4 Uger):**"), 19, 20])],
    6: [B([0], bold=True),
        B([dict(i=1, text="**Færre Elever**"), 2, 3, 4, 5]),
        B([7, 8], bold=True, align="c"),
        B([dict(i=9, text="**Hjælpemidler**"), dict(i=10, text="**Integreret**"), 11, 12, 13, 14, 15]),
        B([dict(i=16, text="**Det Modige Fællesskab**"), 17, 18, 19])],
    7: [B([0]), B([1])],
    8: [B([0], bold=True),
        B([dict(i=1, text="**8. & 9.**", box=(415, 198, 478, 221)), dict(i=1, text="**Klasse**"), 2], align="c"),
        B([dict(i=3, text="**10. Klasse**"), 4], align="c"),
        B([dict(i=6, text="• **Fokus:** Genfinde lysten til at lære. Bygge selvtillid.")]),
        B([dict(i=7, text="• **Afslutning:** Ordinære afgangsprøver (med tilpassede"), 8, 9]),
        B([dict(i=11, text="• **Fokus:** Erhvervsrettet og virkelighedsnært fokus.")]),
        B([dict(i=14, text="• **Samarbejde:** Afvikles i tæt samarbejde med EUC Tønder.")]),
        B([dict(i=15, text="• **Resultat:** Praktisk erfaring og et fuldgyldigt 10. klasses bevis.")]),
        B([12, 13], bold=True, align="c")],
    9: [B([0, 1]), B([2, 3, 4])],
    10: [B([0]), B([1, dict(i=2, text="eksempel er elevernes egen Kærestevæg – et overblik over"), 3]),
         B([dict(i=4, text="**Solen:** For dem med"), 5], align="c"),
         B([dict(i=6, text="**Skyen:** For dem, der"), 7], align="c"),
         B([dict(i=9, text="**Skibet:** For flirts"), 10, 11], align="c"),
         B([dict(i=12, text="**Øen:** For skolens"), 13], align="c"),
         B([dict(i=14, text="**Havet:** For alle os"), 15], align="c")],
    11: [B([0]), B([1, 2], align="c"), B([3, 4], align="c"), B([5, 6], align="c"), B([7, 8], align="c"),
         B([10], bold=True, align="c")],
    12: [B([0], font="serif"), B([1, 2]), B([3], align="c"), B([4], align="c"), B([8], align="c"),
         B([10], bold=True), B([11, dict(i=12, text="økonomi og støttemuligheder (Tlf: 74 72 44 33).")]),
         B([dict(i=13, to_word="Rundvisning:")], bold=True), B([14, 15, 16]),
         B([dict(i=18, text="Mærk Forskellen:", box=(846, 613, 1050, 638))], bold=True), B([19, 20])],
}


# --------------------------------------------------------------------------
def font_file(family, bold):
    return "C:/Windows/Fonts/" + FONTS[family][1 if bold else 0]

_font_cache = {}
def pil_font(family, bold, size=200):
    k = (family, bold, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(font_file(family, bold), size)
    return _font_cache[k]

def runs(text, block_bold):
    """'**a** b' -> [('a', True), (' b', False)]"""
    out = []
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            out.append((part, block_bold or i % 2 == 1))
    return out

def text_len(rs, family, size_px):
    return sum(pil_font(family, b).getlength(t) for t, b in rs) * size_px / 200

def ink_top(rs, family, size_px):
    """Afstand fra grundlinje op til blæk-top (positiv)."""
    tops = [pil_font(family, b).getbbox(t, anchor="ls")[1] for t, b in rs if t.strip()]
    return -min(tops) * size_px / 200 if tops else 0.7 * size_px

def ink_height(rs, family, size_px):
    boxes = [pil_font(family, b).getbbox(t, anchor="ls") for t, b in rs if t.strip()]
    return (max(b[3] for b in boxes) - min(b[1] for b in boxes)) * size_px / 200


def run_ocr(n, img):
    WORK.mkdir(exist_ok=True)
    js = WORK / f"ocr-{n:02d}.json"
    x0, y0, x1, y1 = OCR_CROP.get(n, (0, 0, W_PX, H_PX))
    f = OCR_UP / W_PX
    if not js.exists():
        up = WORK / f"up-{n:02d}.png"
        img.crop((x0, y0, x1, y1)).resize((round((x1 - x0) * f), round((y1 - y0) * f)), Image.LANCZOS).save(up)
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(ROOT / "tools" / "ocr.ps1"), str(up), str(js)], check=True)
    data = json.loads(js.read_text(encoding="utf-8"))
    if abs(data["angle"]) > 0.5:
        print(f"  advarsel: OCR fandt teksten roteret {data['angle']:.1f}° på dias {n} – brug OCR_CROP")
    lines = data["lines"]
    for l in lines:
        for w in l["words"]:
            w.update(x=w["x"] / f + x0, y=w["y"] / f + y0, w=w["w"] / f, h=w["h"] / f)
    return lines


def line_geometry(spec, ocr):
    """-> dict(text, x0, y0, x1, y1, words)"""
    if isinstance(spec, int):
        spec = dict(i=spec)
    words = ocr[spec["i"]]["words"]
    if "from_word" in spec:
        k = next(j for j, w in enumerate(words) if w["t"] == spec["from_word"])
        words = words[k:]
    if "to_word" in spec:
        k = next(j for j, w in enumerate(words) if w["t"] == spec["to_word"])
        words = words[:k + 1]
    text = spec.get("text") or " ".join(w["t"] for w in words)
    if "box" in spec:
        x0, y0, x1, y1 = spec["box"]
        words = [dict(t=text, x=x0, y=y0, w=x1 - x0, h=y1 - y0)]
    x0 = min(w["x"] for w in words); y0 = min(w["y"] for w in words)
    x1 = max(w["x"] + w["w"] for w in words); y1 = max(w["y"] + w["h"] for w in words)
    # breddemåling er kun pålidelig, når teksten svarer til det OCR målte
    fit = "box" in spec or abs(len(text.replace("*", "")) - len(" ".join(w["t"] for w in words))) <= 2
    return dict(text=text, x0=x0, y0=y0, x1=x1, y1=y1, words=words, fit=fit)


def text_color(img, line):
    """Median-farve af de pixels der afviger mest fra baggrunden i linjens ord."""
    a = np.asarray(img).astype(float)
    pix = []
    for w in line["words"]:
        x0, y0 = int(w["x"]), int(w["y"]); x1, y1 = int(math.ceil(w["x"] + w["w"])), int(math.ceil(w["y"] + w["h"]))
        box = a[y0:y1, x0:x1].reshape(-1, 3)
        if len(box) == 0:
            continue
        bg = np.median(box, axis=0)
        d = np.linalg.norm(box - bg, axis=1)
        pix.append(box[d > max(40, np.percentile(d, 80))])
    pix = np.concatenate(pix) if pix else np.zeros((1, 3))
    return tuple(int(v) for v in np.median(pix, axis=0))


def layout_block(block, ocr, img):
    lines = [line_geometry(s, ocr) for s in block["lines"]]
    for l in lines:
        l["runs"] = runs(l["text"], block["bold"])
    fams = {"sans": ["Arial", "Arial Narrow"], "serif": ["Georgia"], "hand": ["Segoe Print"]}[block["font"]]

    def fit_size(l, fam):
        ref = 100.0
        if l["fit"]:
            return ref * (l["x1"] - l["x0"]) / text_len(l["runs"], fam, ref)
        return ref * (l["y1"] - l["y0"]) / ink_height(l["runs"], fam, ref)

    best = None
    for fam in fams:
        ref = 100.0
        sizes_w = [fit_size(l, fam) for l in lines if l["fit"]]
        sizes_h = [ref * (l["y1"] - l["y0"]) / ink_height(l["runs"], fam, ref) for l in lines]
        sw = float(np.median(sizes_w)) if sizes_w else float(np.median(sizes_h))
        sh = float(np.median(sizes_h))
        score = abs(math.log(sw / sh))
        if best is None or score < best[0]:
            best = (score, fam, sw)
    _, fam, size = best
    # linjer der tydeligt er større/mindre end resten (fx en overskrift) får egen størrelse
    sizes = []
    for l in lines:
        s_l = fit_size(l, fam)
        sizes.append(s_l if abs(s_l / size - 1) > 0.08 else size)

    # linjeafstand pr. linje, så hver grundlinje rammer den målte
    a, b = BASELINE[fam]
    bases = [l["y0"] + ink_top(l["runs"], fam, s_l) for l, s_l in zip(lines, sizes)]
    n = len(lines)
    # løses forfra (stabilt, da (1-a)/a < 1): afstand mellem grundlinje k og k+1 er
    # L[k] + a*(L[k+1]-L[k]) + b*(s[k+1]-s[k])
    pitches = [bases[1] - bases[0] if n > 1 else 1.2 * sizes[0]]
    for k in range(n - 1):
        d = bases[k + 1] - bases[k]
        nxt = (d - (1 - a) * pitches[k] - b * (sizes[k + 1] - sizes[k])) / a
        pitches.append(max(0.6 * sizes[k + 1], nxt))
    top = bases[0] - (a * pitches[0] + b * sizes[0])

    widths = [text_len(l["runs"], fam, s_l) for l, s_l in zip(lines, sizes)]
    if block["align"] == "c":
        cx = float(np.median([(l["x0"] + l["x1"]) / 2 for l in lines]))
        bw = max(widths) * 1.08 + 8
        left = cx - bw / 2
        indents = [0] * len(lines)
    else:
        lsb = [pil_font(fam, l["runs"][0][1]).getbbox(l["runs"][0][0], anchor="ls")[0] * s_l / 200 for l, s_l in zip(lines, sizes)]
        starts = [l["x0"] - s for l, s in zip(lines, lsb)]
        left = min(starts)
        indents = [x - left if x - left > 0.4 * size else 0 for x in starts]
        bw = max(w + i for w, i in zip(widths, indents)) * 1.08 + 8
    return dict(fam=fam, sizes=sizes, pitches=pitches, left=left, top=top, width=bw,
                height=sum(pitches) + 4, lines=lines, indents=indents,
                color=text_color(img, lines[0]), align=block["align"],
                erase=[line_geometry(i, ocr) for i in block["erase"]])


def clean_image(img, blocks_layout):
    a = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    mask = np.zeros(a.shape[:2], np.uint8)
    for bl in blocks_layout:
        for l in bl["lines"] + bl["erase"]:
            for w in l["words"]:
                pad = max(2, int(w["h"] * 0.12))
                cv2.rectangle(mask, (int(w["x"]) - pad, int(w["y"]) - pad),
                              (int(w["x"] + w["w"]) + pad, int(w["y"] + w["h"]) + pad), 255, -1)
    out = cv2.inpaint(a, mask, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


def add_textbox(slide, bl, name):
    tb = slide.shapes.add_textbox(Emu(int(bl["left"] * EMU_X)), Emu(int(PIC_TOP + bl["top"] * EMU_Y)),
                                  Emu(int(bl["width"] * EMU_X)), Emu(int(bl["height"] * EMU_Y)))
    tb.name = name
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = True
    for k, (l, ind) in enumerate(zip(bl["lines"], bl["indents"])):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.line_spacing = Pt(bl["pitches"][k] * PT)
        p.space_before = p.space_after = Pt(0)
        p.alignment = PP_ALIGN.CENTER if bl["align"] == "c" else PP_ALIGN.LEFT
        if ind:
            p._p.get_or_add_pPr().set("marL", str(int(ind * EMU_X)))
        for t, bold in l["runs"]:
            r = p.add_run(); r.text = t
            f = r.font; f.name = bl["fam"]; f.bold = bold
            f.size = Pt(round(bl["sizes"][k] * PT * 2) / 2)
            f.color.rgb = RGBColor(*bl["color"])
    return tb


def main():
    WORK.mkdir(exist_ok=True)
    doc = pymupdf.open(SOURCE)
    prs = Presentation(); prs.slide_width = SLIDE_W; prs.slide_height = SLIDE_H
    for n, page in enumerate(doc, 1):
        xref = page.get_images(full=True)[0][0]
        img = Image.open(io.BytesIO(doc.extract_image(xref)["image"])).convert("RGB")
        assert img.size == (W_PX, H_PX), img.size
        ocr = run_ocr(n, img)
        layouts = [layout_block(b, ocr, img) for b in SLIDES.get(n, [])]
        bg = clean_image(img, layouts)
        buf = io.BytesIO(); bg.save(buf, "PNG"); buf.seek(0)
        bg.save(WORK / f"bg-{n:02d}.png")
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        pic = slide.shapes.add_picture(buf, 0, PIC_TOP, SLIDE_W, PIC_H); pic.name = "Baggrund"
        for k, bl in enumerate(layouts, 1):
            add_textbox(slide, bl, f"Tekst {k}")
        print(f"dias {n:2d}: {len(layouts)} tekstbokse")
    prs.save(OUT)
    print("Skrev", OUT)
    export_assets()


def export_assets():
    """PDF og slide-billeder til hjemmesiden, renderet af PowerPoint selv."""
    png_dir = WORK / "export"
    png_dir.mkdir(exist_ok=True)
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(ROOT / "tools" / "export_slides.ps1"), str(OUT), str(OUT_PDF), str(png_dir)], check=True)
    for png in sorted(png_dir.glob("slide-*.png")):
        im = Image.open(png).convert("RGB")
        im.save(SLIDE_IMG / png.with_suffix(".webp").name, "WEBP", quality=82)
        t = im.copy(); t.thumbnail((480, 480))
        t.save(SLIDE_IMG / png.name.replace("slide-", "thumb-").replace(".png", ".webp"), "WEBP", quality=75)
    print("Skrev", OUT_PDF, "og billeder i", SLIDE_IMG)


if __name__ == "__main__":
    main()
