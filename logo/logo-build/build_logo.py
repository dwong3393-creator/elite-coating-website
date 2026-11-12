"""Rebuilds the Elite Coating logo as a vector SVG (text converted to outlines)."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import sys

RED, BLUE = "#ED1C24", "#2E3092"
F = "C:/Windows/Fonts/"

def text_path(font_file, text, x, baseline, cap_h, width=None, spacing=0, xscale=1.0):
    """Outline `text`; if width is given, stretch horizontally to fit it exactly."""
    ft = TTFont(F + font_file); gs = ft.getGlyphSet(); cmap = ft.getBestCmap()
    cap = getattr(ft["OS/2"], "sCapHeight", 0) or ft["head"].unitsPerEm * .7
    s = cap_h / cap
    adv = [gs[cmap[ord(c)]].width for c in text]
    nat = (sum(adv) * s * xscale) + spacing * (len(text) - 1)
    xs = xscale * (width / nat if width else 1)
    d, cx = [], x
    for c, a in zip(text, adv):
        pen = SVGPathPen(gs)
        gs[cmap[ord(c)]].draw(TransformPen(pen, (s * xs, 0, 0, -s, cx, baseline)))
        d.append(pen.getCommands())
        cx += a * s * xs + spacing * (width / nat if width else 1)
    return " ".join(d), cx

# ---- geometry (units: triangle is 555 wide x 480 tall, base at y=480) ----
TW, TH = 555, 480
TXT_X = 636
words = []
d1, e1 = text_path("segoeuib.ttf", "ELITE COATING", TXT_X, TH, 120, width=1194)
d2, e2 = text_path("segoeui.ttf", "SDN BHD", e1 + 42, TH, 120, width=700)
d3, e3 = text_path("ARIALN.TTF", "(626493-K)", e2 + 60, TH, 56, width=390)

# "ELITE" under the triangle base, justified to the triangle width
letters = "ELITE"
ft = TTFont(F + "segoeuib.ttf"); gs = ft.getGlyphSet(); cmap = ft.getBestCmap()
cap = ft["OS/2"].sCapHeight; s = 54 / cap; xs = 1.35
ws = [gs[cmap[ord(c)]].width * s * xs for c in letters]
gap = (TW - sum(ws)) / (len(letters) - 1)
d4, cx = [], 0
for c, w in zip(letters, ws):
    pen = SVGPathPen(gs)
    gs[cmap[ord(c)]].draw(TransformPen(pen, (s * xs, 0, 0, -s, cx, 548)))
    d4.append(pen.getCommands()); cx += w + gap
d4 = " ".join(d4)

W = int(e3) + 20
H = 560
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -10 {W+10} {H+10}" role="img" aria-label="Elite Coating Sdn Bhd">
  <g transform="translate(-25 -30) scale(0.5968)">
    <defs><clipPath id="tri"><path d="M490 30 L955 830 L25 830 Z"/></clipPath></defs>
    <path d="M490 30 L955 830 L25 830 Z" fill="{RED}"/>
    <g clip-path="url(#tri)">
      <path fill="#fff" d="M233 470 C300 395 420 335 600 325 C700 320 755 350 750 420 L740 455 L805 612 L808 625 C780 680 720 735 620 790 C570 812 540 822 520 832 L250 840 C190 815 130 760 110 680 Z"/>
      <path fill="{RED}" d="M330 668 C420 665 500 650 570 620 C650 585 710 530 740 455 L900 455 L900 620 L805 612 C780 640 700 700 620 745 C540 790 450 815 380 822 C320 820 285 790 290 730 C293 695 305 672 330 668 Z"/>
      <path fill="{RED}" d="M345 618 C380 545 470 440 560 392 C600 372 635 368 646 376 C652 392 625 470 565 545 C505 600 430 628 350 632 Q340 630 345 618 Z"/>
    </g>
  </g>
  <path d="{d4}" fill="{BLUE}"/>
  <path d="{d1}" fill="{BLUE}"/>
  <path d="{d2}" fill="{BLUE}"/>
  <path d="{d3}" fill="{BLUE}"/>
</svg>'''
open(sys.argv[1], "w").write(svg)
a = svg.index('  <g transform="translate(-25'); b = svg.index('  <path d="{}"'.format(d4))
mark_only = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 555 480" role="img" aria-label="Elite Coating">'
             + chr(10) + svg[a:b] + '</svg>')
open(sys.argv[2], "w").write(mark_only)
print("W,H", W, H)
