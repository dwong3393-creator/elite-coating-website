"""Makes the 1200x630 pictures shown when a page link is shared (WhatsApp, Facebook, LinkedIn).
One picture per language goes to site/assets/img/share/. Run again after changing the wording or the photo:
    python make-share-images.py
Needs Pillow and PyMuPDF (pip install pymupdf), used only to draw the SVG logo.
"""
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).parent
IMG = ROOT / "site" / "assets" / "img"
OUT = IMG / "share"
FONTS = Path("C:/Windows/Fonts")
W, H = 1200, 630
NAVY, RED = (15, 23, 42), (220, 38, 38)
PHOTO = IMG / "plant" / "f4.webp"          # automatic powder coating booth
LOGO = IMG / "logo-dark.svg"              # logo with light lettering for dark backgrounds

BREAK = "|"  # marks where each line of text ends
TEXT = {  # headline and detail lines per language
    "en": ("Powder coating|and wet painting", "Metal and plastic parts|Sungai Petani, Kedah", "Segoe UI", "segoeuib.ttf", "segoeui.ttf"),
    "zh": ("粉末喷涂|与湿式喷漆", "金属与塑料零件|吉打双溪大年", "YaHei", "msyhbd.ttc", "msyh.ttc"),
    "ms": ("Salutan serbuk dan|pengecatan basah", "Bahagian logam dan plastik|Sungai Petani, Kedah", "Segoe UI", "segoeuib.ttf", "segoeui.ttf"),
}


def fit(draw, lines, font_file, size, max_w):
    """Largest font up to `size` at which every line fits the width."""
    while size > 24:
        font = ImageFont.truetype(str(FONTS / font_file), size, index=0)
        if all(draw.textlength(line, font=font) <= max_w for line in lines):
            return font
        size -= 2
    return font


def logo_image(width):
    page = pymupdf.open(str(LOGO))[0]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def make(lang):
    head, sub, _, bold, regular = TEXT[lang]
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # photo on the right, behind an angled edge with a red stripe (the same cut as the site's hero)
    photo = Image.open(PHOTO).convert("RGB")
    scale = max(660 / photo.width, H / photo.height)
    photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
    x0 = (photo.width - 660) // 2
    photo = photo.crop((x0, 0, x0 + 660, H))
    photo = ImageEnhance.Brightness(photo).enhance(0.9)
    layer = Image.new("RGB", (W, H), NAVY)
    layer.paste(photo, (W - 660, 0))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(700, 0), (W, 0), (W, H), (560, H)], fill=255)
    d.polygon([(688, 0), (700, 0), (560, H), (548, H)], fill=RED)
    img.paste(layer, (0, 0), mask)

    # logo, headline, one line of detail
    logo = logo_image(500)
    img.paste(logo, (64, 64), logo)
    max_w = 470
    head_lines, sub_lines = head.split(BREAK), sub.split(BREAK)
    hf = fit(d, head_lines, bold, 58, max_w)
    sf = fit(d, sub_lines, regular, 30, max_w)
    y = 236
    for line in head_lines:
        d.text((64, y), line, font=hf, fill=(255, 255, 255))
        y += 74
    y += 14
    d.rectangle([64, y, 64 + 72, y + 5], fill=RED)
    y += 30
    for line in sub_lines:
        d.text((64, y), line, font=sf, fill=(203, 213, 225))
        y += 42
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"share-{lang}.jpg"
    img.save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return path


if __name__ == "__main__":
    for code in TEXT:
        p = make(code)
        print(p.name, p.stat().st_size // 1024, "KB")
