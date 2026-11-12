"""Generates the static pages in ./site from shared header/footer templates.
Run:  python build-site.py
The generated .html files are the deliverable; this script only keeps
the header, footer and navigation identical across pages.
"""
import os
import re
from pathlib import Path

from PIL import Image

import i18n

SRC = Path(__file__).parent / "src"    # the CSS and JS you edit
OUT = Path(__file__).parent / "site"   # everything generated: pages, and the shrunk CSS and JS
MISSING = {"zh": set(), "ms": set()}


def minify_assets():
    """Writes the small versions the pages load (site/css/style.min.css, site/js/main.min.js) from src/css/style.css and src/js/main.js.
    Edit the files in src/, never the .min files.
    Needs `pip install rcssmin rjsmin`; without them the pages load the same code, just not shrunk."""
    try:
        import rcssmin, rjsmin
        shrink = {"css": rcssmin.cssmin, "js": rjsmin.jsmin}
    except ImportError:
        print("note: rcssmin / rjsmin not installed, pages load the full CSS and JS (pip install rcssmin rjsmin)")
        shrink = {"css": lambda t: t, "js": lambda t: t}
    for kind, src, dst in (("css", "css/style.css", "css/style.min.css"), ("js", "js/main.js", "js/main.min.js")):
        (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
        (OUT / dst).write_text(shrink[kind]((SRC / src).read_text(encoding="utf-8")), encoding="utf-8")


def asset_version(*names):
    """Short version string from file modification times, so browsers refetch changed CSS/JS."""
    return str(int(max((SRC / n).stat().st_mtime for n in names)))


NAV = [
    ("index.html", "Home"),
    ("about.html", "About"),
    ("services.html", "Services"),
    ("products.html", "Products"),
    ("facilities.html", "Facilities"),
    ("quality.html", "Quality"),
    ("customers.html", "Customers"),
    ("contact.html", "Contact"),
]

ADDRESS = "Plot 5 &amp; 6, Kawasan Perusahaan LPK Fasa 4, 08000 Sungai Petani, Kedah"
MAP_URL = "https://www.google.com/maps/search/?api=1&amp;query=Elite+Coating+Sdn+Bhd+08000+Sungai+Petani+Kedah"

CUSTOMERS = [
    "STX Precision (JB) Sdn Bhd",
    "Paramit Malaysia Sdn Bhd",
    "EKO Metal Industries Sdn Bhd",
    "EKO Industrial Parts Sdn Bhd",
    "Dialight Penang Sdn Bhd",
    "Dufusion Sdn. Bhd.",
    "Marelli Automotive Lighting Malaysia Sdn Bhd",
    "GKN Driveline (M) Sdn Bhd",
    "Actiforce Mechatronics Technology",
    "Flextronics Technology (Penang) Sdn Bhd",
    "AEL Engineering Sdn Bhd (Interplex)",
    "Wong Engineering Industries Sdn Bhd",
    "Zinc Alu Casting Sdn Bhd",
    "LVIO Precision Sdn Bhd",
    "E2E MFG Sdn Bhd",
    "Cheung Woh Technologies (M) Sdn Bhd",
    "Tekun Asas Sdn Bhd",
    "Eng Teknologi Sdn Bhd",
    "IKA Works (Asia) Sdn Bhd",
    "Malaysia Die Casting Industries (MDI) Sdn Bhd",
    "Precision Springs (M) Sdn Bhd",
    "Zero Mass Water Holdings Malaysia Sdn Bhd (Source)",
    "Ferummas Precision Engineering (M) Sdn Bhd",
]

CUSTOMER_LOGOS = [
    ("stx", "STX Precision"), ("eko", "EKO Group"), ("paramit", "Paramit"), ("actiforce", "Actiforce"),
    ("dialight", "Dialight"), ("tekun-asas", "Tekun Asas"), ("gkn", "GKN Driveline"), ("zinc-alu-casting", "Zinc Alu Casting"),
    ("marelli", "Marelli"), ("engtek", "Engtek Group"), ("source", "Source"), ("ika", "IKA"),
    ("flextronics", "Flextronics"), ("ferummas", "Ferummas"), ("wong-engineering", "Wong Engineering"),
    ("e2e", "End 2 End Manufacturing"), ("mdi", "MDI"), ("cheung-woh", "Cheung Woh Technologies"),
    ("interplex", "Interplex"), ("lvio", "Lvio"),
]

# (image, alt, title, from, detail)
AWARDS = [
    ("a3", "Framed Best Performance Award 2024 certificate from STX Precision", "Best Performance Award 2024",
     "STX Precision (JB) Sdn Bhd", "Quality, delivery and service."),
    ("a4", "Crystal Best Performance Award 2024 trophy from STX Precision", "Best Performance Award 2024",
     "STX Precision (JB) Sdn Bhd", "Trophy presented with the certificate."),
    ("a2", "Platinum Award trophy for Best Subcon 2017/2018 from STX Precision", "Best Subcon 2017/2018",
     "STX Precision (JB) Sdn Bhd", "Platinum Award."),
    ("a1", "Framed Platinum Award certificate from STX Precision", "Platinum Award 2017/2018",
     "STX Precision (JB) Sdn Bhd", "For a very good performance of quality, cost and delivery."),
    ("a6", "Plaque from Hicom-Honda Mfg. (M) Sdn Bhd in a red presentation box", "Heartfelt appreciation",
     "Hicom-Honda Mfg. (M) Sdn Bhd", "Vendor Conference 2013/2014."),
    ("a5", "Appreciation Award plaque from Armstrong Auto Parts in a blue presentation box", "Appreciation Award",
     "Armstrong Auto Parts Sdn Bhd", "In recognition of continuous support and services, November 2008."),
]

SUPPLIERS_POWDER = ["Oxyhin Sdn Bhd (Oxyplast)", "AkzoNobel Industrial Coatings", "Jotun Powder", "Cardinal Industrial Finishes",
                    "Tiger Drylac", "PPG Coatings", "Axalta Powder Coating Systems", "Sherwin-Williams",
                    "TCI Powder Coatings", "Platinum Phase"]
SUPPLIERS_PAINT = ["Nippon Paint", "Durachem", "Ever Bright Paint Coating", "PCI Genesis Industrial", "Sherwin-Williams",
                   "Musashi Paint", "Multi Square", "DNT Singapore Pte Ltd", "Asia Paint (Singapore)", "Cardinal Industrial Finishes"]

# (file, alt text, caption)
PRODUCT_GROUPS = [
    ("Die-cast and cast parts",
     "Housings, covers and casings with a durable, even finish.",
     [("product1", "Black coated die-cast housing", "Die-cast housing"),
      ("product2", "Die-cast engine cover", "Engine cover"),
      ("product3", "Silver coated sprocket cover", "Sprocket cover"),
      ("product4", "Die-cast casing", "Die-cast casing"),
      ("product5", "Black coated lighting housing", "Lighting housing"),
      ("product5-2", "White coated heat-sink", "Heat-sink")]),
    ("Sheet metal and enclosures",
     "Brackets, panels and equipment covers in solid colours and textures.",
     [("product6", "Brown coated metal bracket", "Metal bracket"),
      ("product8", "Coated control panel fascia", "Control panel"),
      ("product9", "Grey coated vented enclosure", "Vented enclosure"),
      ("product10", "Grey coated sheet-metal frame", "Sheet-metal frame"),
      ("product11", "Black coated sheet-metal cover", "Equipment cover"),
      ("product12", "Light green coated panel", "Panel")]),
    ("Reflectors and gloss finishes",
     "Mirror-bright reflectors and high-gloss colour finishes.",
     [("product14", "Orange glossy coated part", "Gloss colour finish"),
      ("product15", "Mirror finish lamp reflector", "Lamp reflector"),
      ("product16", "Mirror finish rectangular reflector", "Rectangular reflector"),
      ("product17", "Mirror finish headlamp housing", "Headlamp housing"),
      ("product18", "Mirror finish round reflector", "Round reflector")]),
    ("Telecom and CCTV castings",
     "Cast aluminium housings, covers and plates for telecommunication and CCTV equipment.",
     [
      ("pdf/telecom-1", "Round casting plate", "Round casting plate"),
      ("pdf/telecom-2", "Casting plate with mounting lugs", "Casting plate with mounting lugs"),
      ("pdf/telecom-3", "Casting housing, inside view", "Casting housing, inside view"),
      ("pdf/telecom-4", "Casting housing, inside view", "Casting housing, inside view"),
      ("pdf/telecom-5", "Cylindrical housing", "Cylindrical housing"),
      ("pdf/telecom-6", "Housing shell", "Housing shell"),
      ("pdf/telecom-7", "Housing with window cut-out", "Housing with window cut-out"),
      ("pdf/telecom-8", "White coated bracket", "White coated bracket")]),
    ("Lighting castings",
     "Cast aluminium lamp reflectors and housings in gloss colours and mirror finishes.",
     [
      ("pdf/lighting-1", "Red gloss reflector", "Red gloss reflector"),
      ("pdf/lighting-2", "Orange gloss reflector", "Orange gloss reflector"),
      ("pdf/lighting-3", "Mirror finish reflector", "Mirror finish reflector"),
      ("pdf/lighting-4", "Mirror finish headlamp housing", "Mirror finish headlamp housing"),
      ("pdf/lighting-5", "Dark red gloss reflector", "Dark red gloss reflector"),
      ("pdf/lighting-6", "Black gloss reflector", "Black gloss reflector"),
      ("pdf/lighting-7", "Black gloss reflector", "Black gloss reflector")]),
    ("Motorcycle parts",
     "Engine covers, chain covers and frames for motorcycles.",
     [
      ("pdf/moto-1", "Chain covers", "Chain covers"),
      ("pdf/moto-2", "Engine covers", "Engine covers"),
      ("pdf/moto-3", "Black coated frame", "Black coated frame"),
      ("pdf/moto-4", "Engine covers", "Engine covers")]),
    ("Other castings",
     "Cast aluminium housings, heat-sinks and fittings.",
     [
      ("pdf/cast-1", "Slotted casting housing", "Slotted casting housing"),
      ("pdf/cast-2", "Handle arm", "Handle arm"),
      ("pdf/cast-3", "Heat-sink housing", "Heat-sink housing"),
      ("pdf/cast-4", "Red coated housing with side ports", "Red coated housing with side ports"),
      ("pdf/cast-5", "Red coated housing with neck", "Red coated housing with neck"),
      ("pdf/cast-6", "Red coated open housing", "Red coated open housing"),
      ("pdf/cast-7", "Red coated open housing, side view", "Red coated open housing, side view")]),
    ("Machinery sheet metal",
     "Covers and plates for machinery.",
     [
      ("pdf/machinery-1", "Black coated cover plate", "Black coated cover plate"),
      ("pdf/machinery-2", "Light green coated cover", "Light green coated cover"),
      ("pdf/machinery-3", "Light grey coated cover", "Light grey coated cover"),
      ("pdf/machinery-4", "Dark grey coated cover", "Dark grey coated cover")]),
    ("Telecom sheet metal",
     "Brackets for telecommunication equipment.",
     [
      ("pdf/telecom-sheet-1", "Brown coated bracket", "Brown coated bracket"),
      ("pdf/telecom-sheet-2", "Black coated bracket", "Black coated bracket")]),
    ("Electronics and audio sheet metal",
     "Panels, covers and base plates for electronic and audio equipment.",
     [
      ("pdf/electronics-1", "Black coated front panel", "Black coated front panel"),
      ("pdf/electronics-2", "Light grey control panel", "Light grey control panel"),
      ("pdf/electronics-3", "Dark grey base plate", "Dark grey base plate"),
      ("pdf/electronics-4", "Dark grey cover plate", "Dark grey cover plate"),
      ("pdf/electronics-5", "Black coated side panel", "Black coated side panel")]),
]

PARTNERS = [
    ("paintlogo1", "Nippon Paint"), ("paintlogo2", "AkzoNobel"), ("paintlogo3", "Paint supplier logo"),
    ("paintlogo4", "Meridian Paint"), ("paintlogo5", "PCI"), ("paintlogo6", "Jotun"), ("paintlogo7", "Oxyplast"),
]

MAP_EMBED = "https://maps.google.com/maps?q=Elite%20Coating%20Sdn%20Bhd%2C%2008000%20Sungai%20Petani%2C%20Kedah&amp;z=15&amp;output=embed"
DIRECTIONS_URL = "https://www.google.com/maps/dir/?api=1&amp;destination=Elite+Coating+Sdn+Bhd+08000+Sungai+Petani+Kedah"
# Enquiry form. Leave FORM_ENDPOINT empty to open a ready-to-send email instead.
# To send messages directly from the page, create a form with a form service
# (for example Formspree) and paste its URL here, then run: python build-site.py
FORM_ENDPOINT = ""
FORM_TO = "elite@elitecoating.com.my"
FORM_CC = "elitecoating@yahoo.com"
PHONES = [("04-4411689", "+6044411689"), ("04-4412689", "+6044412689")]
FAX = "04-4422689"
EMAILS = ["elitecoating@yahoo.com", "elite@elitecoating.com.my"]
CONTACT_PERSON = "Mr Wong Ming Liong"
# Opening hours: change them here and the hours list, top bar, FAQ answer, Google data and open-now script all follow.
HOURS_MON_THU_SAT = ("08:00", "16:30")
HOURS_FRI = ("08:00", "17:00")
assert HOURS_FRI[0] == HOURS_MON_THU_SAT[0], "the top bar summary assumes every day opens at the same time"


def _clock(hhmm):
    h, m = map(int, hhmm.split(":"))
    return f"{(h + 11) % 12 + 1}{':%02d' % m if m else ''} {'am' if h < 12 else 'pm'}"


def _span(hours):
    return f"{_clock(hours[0])}-{_clock(hours[1])}"


def _minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


HOURS = [("Monday to Thursday", _span(HOURS_MON_THU_SAT)), ("Friday", _span(HOURS_FRI)),
         ("Saturday", _span(HOURS_MON_THU_SAT)), ("Sunday", "Closed")]
HOURS_SHORT = f"Mon-Sat {_span(HOURS_MON_THU_SAT)} (Fri to {_clock(HOURS_FRI[1])})"
# Sunday to Saturday as "open-close" minutes from midnight, "-" when closed; read by the open-now script in the top bar
HOURS_DATA = ",".join(["-"] + [f"{_minutes(h[0])}-{_minutes(h[1])}"
                               for h in [HOURS_MON_THU_SAT] * 4 + [HOURS_FRI, HOURS_MON_THU_SAT]])
HOURS_HTML = '<ul class="hours">' + "".join(f"<li><span>{d}</span>{t}</li>" for d, t in HOURS) + "</ul>"
PHONE_HTML = " / ".join(f'<a href="tel:{t}">{d}</a>' for d, t in PHONES)
EMAIL_HTML = "<br>".join(f'<a href="mailto:{e}">{e}</a>' for e in EMAILS)


SUB = [("powder", "Powder coating"), ("wetpaint", "Wet painting"), ("pretreatment", "Pre-treatment"),
       ("curing", "Curing"), ("printing", "Tampo and silkscreen printing")]


def header(active):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        if href == "services.html":
            subs = "".join(f'<li><a href="services.html#{i}">{t}</a></li>' for i, t in SUB)
            items.append(
                f'<div class="nav-item has-sub"><a href="{href}"{cur}>{label}</a>'
                f'<button class="sub-toggle" type="button" aria-expanded="false" aria-label="Services menu"><i aria-hidden="true"></i></button>'
                f'<ul class="submenu">{subs}</ul></div>')
        else:
            items.append(f'<a href="{href}"{cur}>{label}</a>')
    links = "\n        ".join(items)
    return f'''  <a class="skip" href="#main">Skip to content</a>
  <div class="topbar">
    <div class="wrap topbar-row">
      <div class="topbar-contact"><p>Tel: {PHONE_HTML}</p><p>{EMAIL_HTML.split("<br>")[1]}</p><p class="topbar-hours" title="{HOURS_SHORT}" data-hours="{HOURS_DATA}" data-msg-open="Open now · closes {{t}}" data-msg-closed="Closed · opens {{t}}" data-msg-tomorrow="Closed · opens tomorrow {{t}}" data-msg-monday="Closed · opens Monday {{t}}"><i class="dot" aria-hidden="true"></i><span>{HOURS_SHORT}</span></p></div>
      <div class="topbar-tools"><!--TOPBAR--><button class="theme-toggle" type="button" aria-pressed="false" aria-label="Dark mode" title="Dark mode"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-moon" d="M20.5 13.2A8.5 8.5 0 0 1 10.8 3.5a8.5 8.5 0 1 0 9.7 9.7z"/><g class="i-sun"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></g></svg></button></div>
    </div>
  </div>
  <header class="masthead">
    <div class="wrap masthead-row">
      <a class="brand" href="index.html" aria-label="Elite Coating Sdn. Bhd. home">
        <img class="logo-light" src="assets/img/logo.svg" alt="Elite Coating Sdn. Bhd." width="3052" height="570">
        <img class="logo-dark" src="assets/img/logo-dark.svg" alt="Elite Coating Sdn. Bhd." width="3052" height="570" loading="lazy">
      </a>
      <div class="masthead-tools"><button class="theme-toggle" type="button" aria-pressed="false" aria-label="Dark mode" title="Dark mode"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-moon" d="M20.5 13.2A8.5 8.5 0 0 1 10.8 3.5a8.5 8.5 0 1 0 9.7 9.7z"/><g class="i-sun"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></g></svg></button>
      <button class="nav-toggle" aria-expanded="false" aria-controls="nav" aria-label="Menu"><span></span><span></span><span></span></button>
      </div>
      <div class="navbar">
        <div class="wrap navbar-row">
          <nav id="nav" class="nav" aria-label="Main">
            {links}
          </nav>
          <a href="contact.html#enquiry" class="btn btn-red btn-sm nav-cta">Request a quote</a>
          <div class="lang-mobile"><!--TOPBAR--></div>
        </div>
      </div>
    </div>
  </header>'''


SERVICE_LINKS = "".join(
    f'<li><a href="services.html#{i}">{t}</a></li>'
    for i, t in [("powder", "Powder coating"), ("wetpaint", "Wet painting"), ("pretreatment", "Pre-treatment"),
                 ("curing", "Curing"), ("printing", "Tampo and silkscreen printing")])

FOOTER = '''  <footer class="site-footer">
    <div class="wrap footer-grid">
      <div class="footer-about">
        <span class="footer-logo"><img src="assets/img/logo.svg" alt="Elite Coating Sdn. Bhd." width="3052" height="570"></span>
        <p>ISO 9001 and ISO 14001 certified metal parts spraying and powder coating. Company no. 626493-K.</p>
        <div class="footer-iso"><img src="assets/img/certs/iso9001-badge.png" alt="ISO 9001:2015" loading="lazy"><img src="assets/img/certs/iso14001-badge.png" alt="ISO 14001:2015" loading="lazy"></div>
        <a class="btn btn-red btn-sm" href="contact.html#enquiry">Request a quote</a>
      </div>
      <nav aria-label="Footer">
        <h2>Pages</h2>
        <ul>
          <li><a href="about.html">About</a></li>
          <li><a href="services.html">Services</a></li>
          <li><a href="products.html">Products</a></li>
          <li><a href="facilities.html">Facilities</a></li>
          <li><a href="quality.html">Quality</a></li>
          <li><a href="customers.html">Customers</a></li>
          <li><a href="contact.html">Contact</a></li>
        </ul>
      </nav>
      <div>
        <h2>Services</h2>
        <ul>{services}</ul>
      </div>
      <div>
        <h2>Contact</h2>
        <ul>
          <li>{addr}</li>
          <li>Tel: {phone}</li>
          <li>Fax: {fax}</li>
          <li>{email}</li>
        </ul>
        <h2 class="footer-sub">Opening hours</h2>
        {hours}
      </div>
    </div>
    <div class="wrap footer-base">
      <p>&copy; <span id="year">2026</span> Elite Coating Sdn. Bhd. All rights reserved.</p>
      <p>Co. No. 200301024073 (626493-K) &middot; <a href="privacy.html">Privacy Notice</a></p>
    </div>
  </footer>

  <button class="to-top" type="button" aria-label="Back to top"></button>
  <!--QUOTEBAR-->
  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Image viewer" data-of="of" hidden>
    <button class="lb-close" aria-label="Close">&times;</button>
    <button class="lb-nav lb-prev" aria-label="Previous image" hidden>&#8249;</button>
    <img alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
    <button class="lb-nav lb-next" aria-label="Next image" hidden>&#8250;</button>
    <p class="lb-cap"></p>
  </div>
  <script src="js/main.min.js?v=JSVER"></script>'''.format(
    addr=ADDRESS, phone=PHONE_HTML, fax=FAX, email=EMAIL_HTML, services=SERVICE_LINKS, hours=HOURS_HTML)


# Fixed bar on phones: call or request a quote from any page
QUOTE_BAR = f'''<div class="quote-bar">
    <a class="btn btn-outline" href="tel:{PHONES[0][1]}">Call us</a>
    <a class="btn btn-red" href="contact.html#enquiry">Request a quote</a>
  </div>'''


def stat_band(items, label="Key facts"):
    """Dark strip of big numbers. items = [(number, label)]."""
    cells = "".join(f'<div><dt>{n}</dt><dd>{t}</dd></div>' for n, t in items)
    return f'''    <section class="statband" aria-label="{label}">
      <dl class="wrap">{cells}</dl>
    </section>'''


def trust_strip():
    """Seven customer logos with a link to the full list; sits above the quote band on pages where a buyer decides."""
    logos = "".join(
        f'<li><img src="assets/img/customers/{f}.png" alt="{a}" loading="lazy"></li>'
        for f, a in [("stx", "STX Precision"), ("paramit", "Paramit"), ("dialight", "Dialight"), ("marelli", "Marelli"),
                     ("gkn", "GKN Driveline"), ("flextronics", "Flextronics"), ("interplex", "Interplex")])
    return f'''    <section class="logos-band" aria-label="Customers">
      <div class="wrap">
        <p class="logos-title">Trusted by manufacturers including</p>
        <ul class="logos-grid">{logos}</ul>
      </div>
    </section>'''


_SIZES = {}


def add_dimensions(html):
    """Give every site image its real width and height so the page does not jump while photos load."""
    def fix(m):
        tag = m.group(0)
        if "width=" in tag and "height=" in tag:
            return tag
        sm = re.search(r'src="(assets/img/[^"?]+)', tag)
        if not sm:
            return tag
        path = OUT / sm.group(1)
        if not path.exists():
            return tag
        if path not in _SIZES:
            with Image.open(path) as im:
                _SIZES[path] = im.size
        w, h = _SIZES[path]
        tag = re.sub(r'\s(width|height)="[^"]*"', "", tag)
        return tag[:-1].rstrip() + f' width="{w}" height="{h}">'
    return re.sub(r"<img\b[^>]*>", fix, html)


LOCAL_BUSINESS = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Elite Coating Sdn. Bhd.",
  "description": "Pre-treatment, powder coating and wet painting for metal and plastic parts.",
  "telephone": "__TEL__",
  "email": "elite@elitecoating.com.my",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Plot 5 & 6, Kawasan Perusahaan LPK Fasa 4",
    "postalCode": "08000",
    "addressLocality": "Sungai Petani",
    "addressRegion": "Kedah",
    "addressCountry": "MY"
  },
  "openingHoursSpecification": [
    {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"], "opens": "__MTS_OPEN__", "closes": "__MTS_CLOSE__"},
    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Friday", "opens": "__FRI_OPEN__", "closes": "__FRI_CLOSE__"}
  ]
}
</script>
"""
for _key, _val in (("__TEL__", PHONES[0][1]), ("__MTS_OPEN__", HOURS_MON_THU_SAT[0]), ("__MTS_CLOSE__", HOURS_MON_THU_SAT[1]),
                   ("__FRI_OPEN__", HOURS_FRI[0]), ("__FRI_CLOSE__", HOURS_FRI[1])):
    LOCAL_BUSINESS = LOCAL_BUSINESS.replace(_key, _val)


# ---------------------------------------------------------------- search and sharing
# Website address, without a trailing slash. Leave empty until the domain is live; then type it in
# (for example "https://www.example.com.my") and run `python build-site.py`. Filling it in switches on
# sitemap.xml, canonical and hreflang links, and the picture and address in the share tags.
# It can also be set for one build: SITE_URL=https://www.example.com.my python build-site.py
SITE_URL = ""
SITE_URL = os.environ.get("SITE_URL", SITE_URL).strip().rstrip("/")
if SITE_URL and not SITE_URL.startswith(("https://", "http://")):
    raise SystemExit(f"SITE_URL must start with https:// (got {SITE_URL!r})")

OG_LOCALE = {"en": "en_MY", "zh": "zh_CN", "ms": "ms_MY"}
HREFLANG = {"en": "en", "zh": "zh-Hans", "ms": "ms"}
SHARE_ALT = {  # describes the share picture for screen readers (make-share-images.py draws the pictures)
    "en": "Elite Coating Sdn. Bhd.: powder coating and wet painting for metal and plastic parts, Sungai Petani, Kedah",
    "zh": "Elite Coating Sdn. Bhd.：金属与塑料零件的粉末喷涂与湿式喷漆，吉打双溪大年",
    "ms": "Elite Coating Sdn. Bhd.: salutan serbuk dan pengecatan basah untuk bahagian logam dan plastik, Sungai Petani, Kedah",
}


def page_url(lang, filename):
    """Full address of a page in one language (the home page of each language is its folder)."""
    folder = "" if lang == "en" else f"{lang}/"
    return f"{SITE_URL}/{folder}" + ("" if filename == "index.html" else filename)


def seo_head(lang, filename, html):
    """Canonical and language links plus share (Open Graph / Twitter) tags, from the finished page's own title and description."""
    if filename == "404.html":
        return ""
    title = re.search(r"<title>(.*?)</title>", html).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    tags = []
    if SITE_URL:
        tags.append(f'<link rel="canonical" href="{page_url(lang, filename)}">')
        tags += [f'<link rel="alternate" hreflang="{HREFLANG[c]}" href="{page_url(c, filename)}">' for c in HREFLANG]
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{page_url("en", filename)}">')
    tags += ['<meta property="og:type" content="website">',
             '<meta property="og:site_name" content="Elite Coating Sdn. Bhd.">',
             f'<meta property="og:title" content="{title}">',
             f'<meta property="og:description" content="{desc}">',
             f'<meta property="og:locale" content="{OG_LOCALE[lang]}">']
    tags += [f'<meta property="og:locale:alternate" content="{OG_LOCALE[c]}">' for c in OG_LOCALE if c != lang]
    if SITE_URL:
        img = f"{SITE_URL}/assets/img/share/share-{lang}.jpg"
        tags += [f'<meta property="og:url" content="{page_url(lang, filename)}">',
                 f'<meta property="og:image" content="{img}">',
                 '<meta property="og:image:type" content="image/jpeg">',
                 '<meta property="og:image:width" content="1200">',
                 '<meta property="og:image:height" content="630">',
                 f'<meta property="og:image:alt" content="{SHARE_ALT[lang]}">',
                 '<meta name="twitter:card" content="summary_large_image">',
                 f'<meta name="twitter:title" content="{title}">',
                 f'<meta name="twitter:description" content="{desc}">',
                 f'<meta name="twitter:image" content="{img}">']
    return "\n  " + "\n  ".join(tags) + "\n"


def write_search_files():
    """robots.txt always; sitemap.xml only once SITE_URL is set (it needs full addresses)."""
    robots = "User-agent: *\nAllow: /\n"
    sitemap = OUT / "sitemap.xml"
    if SITE_URL:
        robots += f"\nSitemap: {SITE_URL}/sitemap.xml\n"
        pages = [f for f, _ in NAV] + ["privacy.html"]
        rows = []
        for f in pages:
            for lang in HREFLANG:
                alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{HREFLANG[c]}" href="{page_url(c, f)}"/>' for c in HREFLANG)
                alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{page_url("en", f)}"/>'
                rows.append(f"  <url>\n    <loc>{page_url(lang, f)}</loc>{alts}\n  </url>")
        sitemap.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
                           + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8")
    elif sitemap.exists():
        sitemap.unlink()
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")


def page(filename, title, description, body, active=None):
    full_title = "Elite Coating Sdn. Bhd. | Industrial Powder Coating &amp; Painting" if filename == "index.html" \
        else f"{title} | Elite Coating Sdn. Bhd."
    hero = re.search(r'<img class="(?:hero-bg|ph-bg)" src="([^"]+)"', body)
    preload = f'\n  <link rel="preload" as="image" href="{hero.group(1)}">' if hero else ""
    if hero:
        body = body.replace(hero.group(0), hero.group(0) + ' fetchpriority="high"', 1)
    robots = '\n  <meta name="robots" content="noindex">' if filename == "404.html" else ""
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{full_title}</title>
  <meta name="description" content="{description}">{robots}
  <meta name="theme-color" content="#ffffff">
  <script>try{{var t=localStorage.getItem("elite-theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
  <link rel="icon" type="image/png" href="assets/img/favicon.png">
  <link rel="preload" as="font" type="font/woff2" href="assets/fonts/dm-sans-latin.woff2" crossorigin>
  <link rel="preload" as="font" type="font/woff2" href="assets/fonts/space-grotesk-latin.woff2" crossorigin>
  <link rel="stylesheet" href="css/style.min.css?v={asset_version("css/style.css")}">{preload}
</head>
<body>
{header(active)}

  <main id="main">
{body}
  </main>

{FOOTER.replace('JSVER', asset_version('js/main.js')).replace('<!--QUOTEBAR-->', '' if active == 'contact.html' else QUOTE_BAR)}
</body>
</html>
'''
    html = add_dimensions(html)
    for lang in ("en", "zh", "ms"):
        folder = OUT if lang == "en" else OUT / lang
        folder.mkdir(exist_ok=True)
        out = i18n.localize(html, lang, filename, MISSING.get(lang, set()))
        out = out.replace("</head>", seo_head(lang, filename, out) + "</head>", 1)
        if filename in ("index.html", "contact.html"):
            business = LOCAL_BUSINESS
            if SITE_URL:
                business = business.replace('"name": "Elite Coating Sdn. Bhd.",',
                                            f'"name": "Elite Coating Sdn. Bhd.",\n  "url": "{page_url(lang, "index.html")}",\n  "image": "{SITE_URL}/assets/img/share/share-{lang}.jpg",', 1)
            out = out.replace("</head>", business + "</head>", 1)
        (folder / filename).write_text(out, encoding="utf-8")


# Hero photo for each inner page: (image under assets/img, object-position)
PAGE_HERO = {
    "Page not found": ("company/company1.webp", "50% 55%"),
    "About": ("company/company1.webp", "50% 55%"),
    "Services": ("plant/f4.webp", "50% 50%"),
    "Products": ("facilities/fac_mainpic.webp", "50% 50%"),
    "Facilities": ("plant/f9.webp", "50% 55%"),
    "Quality": ("plant/f8.webp", "50% 30%"),
    "Customers": ("company/company2.webp", "50% 50%"),
    "Contact": ("company/company3.webp", "50% 60%"),
    "Privacy Notice": ("company/company1.webp", "50% 55%"),
}


def page_head(title, lead, crumb):
    img, pos = PAGE_HERO[crumb]
    return f'''    <section class="page-head">
      <img class="ph-bg" src="assets/img/{img}" alt="" aria-hidden="true" style="object-position:{pos}">
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a><span aria-hidden="true">/</span><span>{crumb}</span></nav>
        <h1>{title}</h1>
        <p class="lead">{lead}</p>
      </div>
      <span class="ph-tri" aria-hidden="true"></span>
    </section>'''


def _cta(h, p):
    return f'''    <section class="cta">
      <div class="wrap cta-row">
        <div>
          <h2>{h}</h2>
          <p>{p}</p>
        </div>
        <div class="btn-row">
          <a class="btn btn-red" href="contact.html#enquiry">Request a quote</a>
        </div>
      </div>
    </section>'''


CTA = _cta("Have parts that need coating?", "Send us your drawings, quantities and colour requirements and we will reply with a quotation.")
CTA_SERVICES = _cta("Which service do you need?", "Tell us the service, material, quantity, colour and finish. Attach drawings or photos, and we will reply with a quotation.")
CTA_PRODUCTS = _cta("Send us your part", "Include a drawing or sample, the material, size, quantity, colour and finish, and we will reply with a quotation.")


# ---------------------------------------------------------------- helpers
def shot(path, alt, caption):
    return f'<figure><img src="assets/img/{path}" alt="{alt}" loading="lazy"><figcaption>{caption}</figcaption></figure>'


def gallery(items, cols=3):
    figs = "".join(shot(*it) for it in items)
    return f'<div class="gallery g{cols}" data-lightbox>{figs}</div>'


def award_cards(items):
    return "".join(
        f'<figure class="award"><div class="award-img"><img src="assets/img/awards/{f}.webp" alt="{alt}" loading="lazy"></div>'
        f'<figcaption><strong>{title}</strong><span>{who}</span><em>{detail}</em></figcaption></figure>'
        for f, alt, title, who, detail in items)


def map_block():
    return f'''<div class="map">
          <iframe title="Map showing the location of Elite Coating Sdn. Bhd. in Sungai Petani, Kedah" src="{MAP_EMBED}"
                  loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
        </div>'''


def map_actions():
    return f'''<div class="btn-row">
            <a class="btn btn-primary" href="{DIRECTIONS_URL}" target="_blank" rel="noopener">Get directions</a>
            <a class="btn btn-outline" href="{MAP_URL}" target="_blank" rel="noopener">Open in Google Maps</a>
          </div>'''


def core_block(heading="Our core business"):
    items = [
        ("Pre-treatment", "Clear chromate or iron phosphate"),
        ("Powder coating", "Aluminium and steel parts"),
        ("Wet painting", "Aluminium, steel and plastic parts"),
    ]
    cards = "".join(f"<article><h3>{t}</h3><p>{d}</p></article>" for t, d in items)
    return f'''    <section class="section section-mist" id="core">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>{heading}</h2>
          <p>Elite Coating specialises in surface coating and painting for metal and plastic parts. We serve a wide range of industries for coating and painting products.</p>
        </div>
        <div class="core-items">{cards}</div>
        <div class="mix" role="img" aria-label="Current running work: 70 percent powder coating, 30 percent wet paint">
          <p class="mix-title">Current running work</p>
          <div class="mix-bar"><span class="mix-a" style="width:70%">70%</span><span class="mix-b" style="width:30%">30%</span></div>
          <ul class="mix-legend"><li><i class="a"></i>Powder coating</li><li><i class="b"></i>Wet paint</li></ul>
        </div>
      </div>
    </section>'''


def cat_nav(title, items):
    """Side menu for catalogue pages. items = [(anchor id, label, count or None)]."""
    links = "".join(
        f'<a href="#{i}">{label}{f"<span>{n}</span>" if n else ""}</a>' for i, label, n in items)
    return (f'<aside class="cat-nav" aria-label="{title}"><h2>{title}</h2>{links}'
            '<div class="cat-cta"><a class="btn btn-red btn-sm" href="contact.html#enquiry">Request a quote</a></div></aside>')


# ---------------------------------------------------------------- HOME
def home():
    n_suppliers = len(set(SUPPLIERS_POWDER + SUPPLIERS_PAINT))   # Sherwin-Williams and Cardinal appear in both lists
    steps = [
        ("Pre-treatment", "plant/mac3.webp", "Iron phosphate pre-treatment tunnel", "50% 12%",
         "Parts are cleaned and treated so the coating bonds well.", "services.html#pretreatment"),
        ("Coating", "plant/f4.webp", "Automatic powder coating booth", "50% 50%",
         "Powder coating or wet painting, by hand or automatically.", "services.html#powder"),
        ("Curing", "plant/mac2.webp", "Curing oven with conveyor belt", "50% 50%",
         "Conveyor ovens bake each batch evenly.", "services.html#curing"),
        ("Inspection and delivery", "plant/f5.webp", "Operators handling finished metal parts", "50% 40%",
         "Parts are checked, marked where needed and returned to you.", "quality.html"),
    ]
    steps_html = "".join(
        f'<li><a class="stage" href="{href}"><img src="assets/img/{im}" alt="{alt}" style="object-position:{pos}" loading="lazy">'
        f'<span class="stage-text"><h3>{t}</h3><span>{d}</span></span></a></li>'
        for i, (t, im, alt, pos, d, href) in enumerate(steps, 1))
    industries = [
        ("Automotive", "Engine covers, sprocket covers and casings with a durable, even finish.",
         [("product2", "Die-cast engine cover"), ("product3", "Silver coated sprocket cover")]),
        ("Electronics", "Control panels, enclosures and brackets in solid colours and textures.",
         [("product8", "Coated control panel fascia"), ("product9", "Grey coated vented enclosure")]),
        ("Lighting", "Mirror-finish reflectors, lamp housings and heat-sinks.",
         [("product15", "Mirror finish lamp reflector"), ("product5", "Black coated lighting housing")]),
    ]
    industries_html = "".join(
        f'<li><a class="irow" href="products.html"><h3>{t}</h3><span class="irow-text"><span>{d}</span><span class="more">See related parts</span></span>'
        f'<span class="irow-imgs">' + "".join(f'<img src="assets/img/products/{f}.png" alt="{a}" loading="lazy">' for f, a in imgs) + '</span></a></li>'
        for t, d, imgs in industries)
    body = f"""    <section class="hero">
      <img class="hero-bg" src="assets/img/products/services_mainpic.webp" alt="" aria-hidden="true">
      <div class="wrap hero-inner">
        <div class="hero-copy">
          <h1>Powder coating and wet painting, start to finish</h1>
          <p class="lead">Pre-treatment, powder coating and wet painting for automotive, electronics and lighting manufacturers.</p>
          <div class="btn-row">
            <a class="btn btn-red" href="contact.html#enquiry">Request a quote</a>
            <a class="btn btn-ghost" href="products.html">See our products</a>
          </div>
        </div>
      </div>
      <span class="hero-tri" aria-hidden="true"></span>
    </section>

{stat_band([("2008", "ISO 9001 certified since"), (n_suppliers, "Coating suppliers"), ("20+", "Manufacturers served"), ("6", "Awards from customers")])}

{trust_strip()}

    <section class="section" id="about-snapshot">
      <div class="wrap split split-media">
        <figure class="photo" data-lightbox><img src="assets/img/company/company1.webp" alt="Elite Coating building with company signage" loading="lazy"></figure>
        <div class="prose">
          <h2>About Elite Coating</h2>
          <p>Elite Coating Sdn. Bhd. specialises in surface coating and painting for metal and plastic parts, serving a wide range of industries including automotive, electronics and lighting.</p>
          <p>Our coating line brings pre-treatment, spray booths and curing ovens together, so each part moves through every stage in one place. Our work ranges from die-cast housings and sheet-metal enclosures to mirror-finish lamp reflectors, with tampo and silkscreen printing for markings.</p>
          <div class="btn-row"><a class="btn btn-primary" href="quality.html">Quality and certifications</a><a class="more" href="facilities.html">Tour the facilities</a></div>
        </div>
      </div>
    </section>

{core_block()}

    <section class="section stages-band">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>From bare metal to finished part</h2>
          <p>One conveyor line, four stages. Every part follows the same controlled sequence, so parts come back clean, consistent and ready to assemble.</p>
        </div>
        <ol class="stages">{steps_html}</ol>
        <p class="after">Tampo and silkscreen printing is also available. <a class="more" href="services.html">All services</a></p>
      </div>
    </section>

    <section class="section section-mist">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Why manufacturers choose Elite Coating</h2>
          <p>Evidence you can check, not just claims.</p>
        </div>
        <div class="bento">
          <article class="bento-iso">
            <div class="proof-media"><img src="assets/img/certs/iso9001-badge.png" alt="ISO 9001:2015" loading="lazy"><img src="assets/img/certs/iso14001-badge.png" alt="ISO 14001:2015" loading="lazy"></div>
            <div class="bento-text">
              <h3>ISO 9001 and ISO 14001</h3>
              <p>Certified for metal parts spraying and powder coating services.</p>
              <a class="more" href="quality.html">Certifications</a>
            </div>
          </article>
          <article class="bento-lab">
            <img src="assets/img/plant/f8.webp" alt="Technician checking chemicals in the laboratory" loading="lazy">
            <div class="bento-text">
              <h3>In-house laboratory</h3>
              <p>Chemical concentration is checked so process chemicals meet the defined standard.</p>
              <a class="more" href="facilities.html#laboratory">Testing laboratory</a>
            </div>
          </article>
          <article class="bento-award">
            <div class="proof-media proof-award"><img class="photo-badge" src="assets/img/awards/a4.webp" alt="Crystal Best Performance Award 2024 trophy from STX Precision" loading="lazy"></div>
            <div class="bento-text">
              <h3>Awarded by customers</h3>
              <p>Awards for quality, delivery and service from STX Precision, Hicom-Honda and Armstrong Auto Parts.</p>
              <a class="more" href="customers.html#awards">Awards</a>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Industries we serve</h2>
          <p>Coated parts for the sectors our customers work in.</p>
        </div>
        <ul class="industry-rows">{industries_html}</ul>
        <p class="after"><a class="more" href="products.html">View all products</a></p>
      </div>
    </section>

    <section class="section section-mist">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Inside the plant</h2>
          <p>Pre-treatment tanks, powder booths, curing ovens and printing, all under one roof.</p>
        </div>
        <div class="mosaic" data-lightbox>
          <figure class="m-a"><img src="assets/img/plant/f9.webp" alt="Powder coating line with overhead conveyor" loading="lazy"></figure>
          <figure class="m-b"><img src="assets/img/plant/mac4.webp" alt="Metal parts hanging on the pre-treatment line" loading="lazy"></figure>
          <figure class="m-c"><img src="assets/img/plant/f6.webp" alt="Overhead conveyor line carrying parts" loading="lazy"></figure>
          <figure class="m-d"><img src="assets/img/plant/mac1.webp" alt="Process line with stairs and tanks" loading="lazy"></figure>
        </div>
        <p class="after"><a class="more" href="facilities.html">Tour the facilities</a></p>
      </div>
    </section>

{CTA}"""
    page("index.html", "Home", "ISO-certified pre-treatment, powder coating and wet painting for metal and plastic parts in Sungai Petani, Kedah, for automotive, electronics and lighting.", body, "index.html")


# ---------------------------------------------------------------- ABOUT
def about():
    premises = gallery([
        ("company/company1.webp", "Elite Coating building with company signage", "Company building"),
        ("company/company2.webp", "Reception with illuminated Elite Coating logo and product display", "Reception"),
        ("company/company3.webp", "Plant entrance with loading area", "Plant entrance"),
        ("company/company4.webp", "Warehouse racking in the incoming store", "Incoming store"),
        ("company/company5.webp", "Warehouse racking in the finished goods store", "Finished goods store"),
        ("company/company6.webp", "Warehouse office beside the roller door", "Warehouse office"),
    ])
    # Company development roadmap, from the company profile (page 8)
    ICONS = {
        "building": '<path d="M4 21V4h10v17M14 9h6v12M3 21h18M8 8h2M8 12h2M8 16h2"/>',
        "iso": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3.2 3 3.2 15 0 18M12 3c-3.2 3-3.2 15 0 18"/>',
        "factory": '<path d="M3 21V11l6 4v-4l6 4V5h4v16zM16 5V3"/>',
        "spray": '<path d="M3 8h10l3-2h3v4h-3l-3-1H8l-1 8H4l1-8M20 13h2M19 17h2M17 20h2"/>',
        "printer": '<path d="M7 9V3h10v6M7 17H4v-7h16v7h-3M7 14h10v7H7z"/>',
        "leaf": '<path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15zM5 19l8-8"/>',
    }
    roadmap = [  # (year, kind, icon, text): kind grow = new plant or line, cert = certification
        ("2003", "grow", "building", "Incorporated in October 2003 and started business operations."),
        ("2008", "cert", "iso", "ISO 9001:2008 certified in October 2008."),
        ("2013", "grow", "factory", "Moved to a new plant with 50,000 sq ft built-up area. Added a powder coating overhead conveyor line and a powder coating auto spray line."),
        ("2017", "cert", "iso", "ISO 9001:2015 certified."),
        ("2019", "grow", "spray", "New wet paint auto spray line with a spindle rotation spraying gun."),
        ("2022", "grow", "printer", "New printing line for tampo and silkscreen printing."),
        ("2024", "cert", "leaf", "ISO 14001:2015 certified in September 2024."),
    ]
    roadmap_html = "".join(
        f'<li class="rm-{kind}"><span class="rm-year">{year}</span><div class="rm-card">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[icon]}</svg><p>{text}</p></div></li>'
        for year, kind, icon, text in roadmap)
    recognised = [
        ("2008", "Armstrong Auto Parts", "Appreciation Award"),
        ("2013/2014", "Hicom-Honda", "Vendor Conference appreciation"),
        ("2017/2018", "STX Precision", "Platinum Award, Best Subcon"),
        ("2024", "STX Precision", "Best Performance Award"),
    ]
    recognised_html = "".join(f'<li><time>{y}</time><strong>{n}</strong><span>{d}</span></li>' for y, n, d in recognised)
    body = page_head("About Elite Coating",
                     "An ISO-certified industrial coating company in Sungai Petani, Kedah, serving manufacturers who need consistent, repeatable finishes on metal and plastic components.",
                     "About") + f'''

{stat_band([("2003", "Company registered"), ("2008", "ISO 9001 certified since"), ("2024", "ISO 14001 certified since"), ("20+", "Manufacturers served")])}

    <section class="section">
      <div class="wrap split">
        <div class="prose">
          <p>Elite Coating Sdn. Bhd. specialises in surface coating and painting for metal and plastic parts, serving a wide range of industries including automotive, electronics and lighting.</p>
          <p>Our coating line brings pre-treatment, spray booths and curing ovens together, so each part moves through every stage in one place. Our work ranges from die-cast housings and sheet-metal enclosures to mirror-finish lamp reflectors, with tampo and silkscreen printing for markings.</p>
          <p>We are certified to ISO 9001:2015 and ISO 14001:2015, and have received awards from customers for quality, delivery and service.</p>
          <p class="after"><a class="btn btn-primary" href="quality.html">Quality and certifications</a></p>
        </div>
        <dl class="facts">
          <div><dt>Company</dt><dd>Elite Coating Sdn. Bhd.</dd></div>
          <div><dt>Company no.</dt><dd>200301024073 (626493-K)</dd></div>
          <div><dt>Location</dt><dd>Sungai Petani, Kedah</dd></div>
          <div><dt>Certifications</dt><dd>ISO 9001:2015, ISO 14001:2015</dd></div>
          <div><dt>Industries served</dt><dd>Automotive, electronics, lighting</dd></div>
          <div><dt>Processes</dt><dd>Pre-treatment (clear chromate or iron phosphate), powder coating, wet painting, curing, tampo and silkscreen printing</dd></div>
          <div><dt>Materials</dt><dd>Aluminium, steel and plastic</dd></div>
        </dl>
      </div>
    </section>

    <section class="section section-mist">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Our premises</h2>
          <p>Our building, reception and warehouse in Sungai Petani. Select an image to enlarge it.</p>
        </div>
        {premises}
      </div>
    </section>

    <section class="section">
      <div class="wrap split split-media">
        <figure class="photo" data-lightbox><img src="assets/img/plant/f5.webp" alt="Elite Coating operators handling metal parts at a work table" loading="lazy"></figure>
        <div class="prose">
          <h2>Skilled people on the line</h2>
          <p>Coating quality depends on the people who handle it. Our operators work with every batch from preparation and coating through to final checks, all under one roof.</p>
          <p><a class="more" href="facilities.html">Tour the facilities</a></p>
        </div>
      </div>
    </section>

    <section class="section section-mist" id="environment">
      <div class="wrap env-grid">
        <div class="prose">
          <h2 class="rule">Caring for the environment</h2>
          <p>Coating involves chemicals, waste water and energy, so we manage them carefully. Looking after the environment is part of how Elite Coating runs every day, and our environmental management system is certified to ISO 14001:2015.</p>
          <p>Our plant treats its waste water on site, and our laboratory checks process chemicals so they stay within standard. Getting each job right the first time protects the quality of your parts and avoids unnecessary rework and waste. <a class="more" href="quality.html">See our certifications</a></p>
        </div>
        <aside class="env-card">
          <h3>Our efforts focus on</h3>
          <ul class="marks">
            <li>Minimising waste throughout the coating process</li>
            <li>Preventing pollution from our processes</li>
            <li>Meeting applicable environmental laws and regulations</li>
            <li>Improving our environmental performance over time</li>
          </ul>
        </aside>
      </div>
    </section>

    <section class="section" id="milestones">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Company development roadmap</h2>
          <p>From incorporation in 2003 to ISO 14001 in 2024.</p>
        </div>
        <p class="rm-legend"><span class="k-grow">New plant or line</span><span class="k-cert">Certification</span></p>
        <ol class="roadmap">{roadmap_html}</ol>
        <div class="rm-awards">
          <div class="rm-awards-head">
            <h3>Recognised by customers</h3>
            <a class="more" href="customers.html#awards">See the awards</a>
          </div>
          <ul>{recognised_html}</ul>
        </div>
      </div>
    </section>

    <section class="section section-mist" id="visit">
      <div class="wrap split split-map">
        {map_block()}
        <div class="prose">
          <h2>Visit us</h2>
          <p>{ADDRESS}</p>
          <p class="hours-line">Open Monday to Saturday, closed on Sunday. <a class="more" href="contact.html">Opening hours and contact</a></p>
          {map_actions()}
        </div>
      </div>
    </section>

{CTA}'''
    page("about.html", "About", "About Elite Coating Sdn. Bhd., an ISO 9001 and ISO 14001 certified pre-treatment, powder coating and wet painting company in Sungai Petani, Kedah.", body, "about.html")


# ---------------------------------------------------------------- SERVICES
SPECS = {
    "powder": [("Suitable for", "Aluminium and steel parts"), ("Typical parts", "Housings, covers, brackets and enclosures"),
               ("Finishes", "Gloss, matt and textured finishes")],
    "wetpaint": [("Suitable for", "Aluminium, steel and plastic parts"), ("Colour", "Colour-matched finishes"),
                 ("Finishes", "Gloss and special-effect coats")],
    "pretreatment": [("Treatments", "Clear chromate or iron phosphate"), ("Benefit", "Better adhesion and corrosion resistance")],
    "curing": [("Heat", "Even, controlled heat"), ("Handling", "Continuous conveyor handling"),
               ("Result", "Consistent batch-to-batch results")],
    "printing": [("Used for", "Logos, markings and graphics"), ("Methods", "Pad and screen printing"),
                 ("Room", "Dedicated printing room")],
}


def services():
    rows = [
        ("powder", "Powder coating", "plant/f4.webp", "Automatic powder coating booth",
         "Dry powder is applied electrostatically, by hand or in our automatic booth, and baked into a hard, even finish. It is durable, consistent and suited to a wide range of colours and textures."),
        ("wetpaint", "Wet painting", "products/services_mainpic.webp", "Spray gun applying wet paint",
         "Wet paint is sprayed onto parts that need a specific colour, sheen or effect, matched to the specification you give us. It suits plastic as well as metal."),
        ("pretreatment", "Pre-treatment", "plant/mac3.webp", "Iron phosphate pre-treatment tunnel",
         "Parts are cleaned and given a clear chromate or iron phosphate treatment before coating, so the finish bonds well and holds up against corrosion. Our laboratory checks the chemical concentration to keep the process on standard."),
        ("curing", "Curing", "plant/mac2.webp", "Curing oven with conveyor belt",
         "Conveyor ovens bake coatings evenly, so every batch comes out with the same hardness and appearance."),
        ("printing", "Tampo and silkscreen printing", "plant/mac5.webp", "Tampo and silkscreen printing machines in a clean room",
         "Pad (tampo) and screen printing for logos, markings and graphics on finished parts."),
    ]
    panels = "".join(f'''
        <article class="spec" id="{id_}" data-cat>
          <header class="spec-head"><h2>{name}</h2><a class="spec-link" href="contact.html#enquiry">Request a quote</a></header>
          <div class="spec-body">
            <figure class="photo" data-lightbox><img src="assets/img/{img_}" alt="{alt}" loading="lazy"></figure>
            <div class="spec-text">
              <p>{text}</p>
              <dl class="specs">{"".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in SPECS[id_])}</dl>
            </div>
          </div>
        </article>''' for id_, name, img_, alt, text in rows)
    menu = cat_nav("Our services", [(id_, name, None) for id_, name, *_ in rows])
    steps = [("Pre-treatment", "Parts are cleaned and treated."),
             ("Coating", "Powder coating or wet painting is applied in the booth."),
             ("Curing", "Parts are baked in the oven until the coating is hard."),
             ("Inspection and delivery", "Finished parts are checked and sent back to you.")]
    ol = "".join(f'<li><b>{i}</b><h3>{t}</h3><p>{d}</p></li>' for i, (t, d) in enumerate(steps, 1))
    brands = "".join(f'<li><img src="assets/img/supplies/{f}.png" alt="{a}" loading="lazy"></li>' for f, a in PARTNERS)
    body = page_head("Services",
                     "Pre-treatment, powder coating, wet painting, curing and printing, all in one plant.",
                     "Services") + f'''

    <section class="section">
      <div class="wrap cat-shell">
        {menu}
        <div class="cat-main">{panels}
        </div>
      </div>
    </section>

    <section class="section section-mist">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>How a job moves through the line</h2>
          <p>Every part follows the same four stages.</p>
        </div>
        <ol class="flow">{ol}</ol>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Coating brands we work with</h2>
          <p>We apply coatings from established paint manufacturers. <a class="more" href="customers.html#suppliers">See the full supplier list</a></p>
        </div>
        <ul class="brands">{brands}</ul>
      </div>
    </section>

{trust_strip()}

{CTA_SERVICES}'''
    page("services.html", "Services", "Pre-treatment, powder coating, wet painting, curing and tampo and silkscreen printing from Elite Coating Sdn. Bhd.", body, "services.html")


# ---------------------------------------------------------------- PRODUCTS
def products():
    sections = []
    menu_items = []
    for gi, (title, blurb, items) in enumerate(PRODUCT_GROUPS):
        gid = f"group{gi + 1}"
        menu_items.append((gid, title, len(items)))
        tiles = "".join(
            f'<figure class="tile"><img src="assets/img/products/{f}.{"webp" if "/" in f else "png"}" alt="{a}" loading="lazy"><figcaption>{c}</figcaption></figure>'
            for f, a, c in items)
        sections.append(f'''
          <section class="cat-group" id="{gid}" data-cat>
            <header class="cat-head"><h2>{title}</h2><p>{blurb}</p><span class="cat-count">{len(items)} parts</span></header>
            <div class="tiles tiles-cat" data-lightbox>{tiles}</div>
          </section>''')
    menu = cat_nav("Product groups", menu_items)
    more = '''
          <aside class="more-parts boxed">
            <div>
              <h2>Do not see your part?</h2>
              <p>Send us a drawing or sample and we will tell you what we can do.</p>
            </div>
            <a class="btn btn-red" href="contact.html#enquiry">Request a quote</a>
          </aside>'''
    body = page_head("Products",
                     "A selection of the parts we coat. Select an image to enlarge it.",
                     "Products") + f'''

    <section class="section">
      <div class="wrap cat-shell">
        {menu}
        <div class="cat-main">{"".join(sections)}{more}
        </div>
      </div>
    </section>

{trust_strip()}

{CTA_PRODUCTS}'''
    page("products.html", "Products", "Parts coated by Elite Coating: die-cast housings, sheet-metal enclosures and mirror-finish reflectors.", body, "products.html")


# ---------------------------------------------------------------- FACILITIES
def facilities():
    def block(id_, title, blurb, items, cols):
        return f'''          <section class="cat-group" id="{id_}" data-cat>
            <header class="cat-head"><h2>{title}</h2><p>{blurb}</p></header>
            {gallery(items, cols)}
          </section>'''

    blocks = [
        block("pretreatment", "Pre-treatment",
              "Parts are cleaned and given a clear chromate or iron phosphate treatment before they are coated.",
              [("plant/mac3.webp", "Iron phosphate pre-treatment tunnel", "Iron phosphate treatment tunnel"),
               ("plant/mac4.webp", "Metal parts hanging on the pre-treatment line", "Parts on the pre-treatment line")], 2),
        block("powder", "Powder coating",
              "Hand-spray and automatic booths along an overhead conveyor line.",
              [("plant/f9.webp", "Powder coating line with overhead conveyor", "Powder coating line"),
               ("plant/f4.webp", "Automatic powder coating booth", "Automatic powder booth"),
               ("plant/f11.webp", "Inside the automatic powder booth", "Automatic booth interior"),
               ("plant/f10.webp", "Powder booth seen through a viewing window", "Powder booth"),
               ("plant/mac1.webp", "Process line with stairs and tanks", "Process line"),
               ("plant/f6.webp", "Overhead conveyor line carrying parts", "Overhead conveyor")], 3),
        f'''          <section class="cat-group" id="curing" data-cat>
            <header class="cat-head"><h2>Curing</h2><p>Conveyor ovens bake coatings evenly, so every batch comes out with the same hardness and appearance.</p></header>
            <div class="gallery g2" data-lightbox><figure><img src="assets/img/plant/mac2.webp" alt="Curing oven with conveyor belt" loading="lazy"><figcaption>Curing oven with conveyor belt</figcaption></figure></div>
          </section>''',
        block("printing", "Tampo and silkscreen",
              "A dedicated room for pad and screen printing of logos and markings.",
              [("plant/mac5.webp", "Tampo and silkscreen printing machines", "Printing machines"),
               ("plant/mac6.webp", "Tampo and silkscreen printing area", "Printing area")], 2),
        block("laboratory", "Testing laboratory",
              "Our lab checks chemical concentration so that process chemicals meet the defined standard solution.",
              [("plant/f7.webp", "Lab room door with concentration and pH signage", "Lab room"),
               ("plant/f8.webp", "Technician checking chemicals in the laboratory", "Chemical testing")], 2),
        block("wastewater", "Waste water treatment",
              "Waste water from the process is treated on site.",
              [("plant/f12.webp", "Waste water treatment plant with tanks and tower", "Waste water treatment plant"),
               ("plant/f13.webp", "Treatment tank with pipework", "Treatment tank")], 2),
        block("floor", "Production floor",
              "Handling and finishing areas where parts are prepared and checked.",
              [("plant/f1.webp", "Operators at workstations under lights", "Workstation"),
               ("plant/f2.webp", "Production room seen through glass doors", "Production room"),
               ("plant/f3.webp", "Conveyor and work tables in a finishing area", "Conveyor and work tables"),
               ("plant/f5.webp", "Operators handling metal parts at a table", "Handling parts")], 2),
    ]
    area_list = [("pretreatment", "Pre-treatment"), ("powder", "Powder coating"), ("curing", "Curing"),
                 ("printing", "Tampo and silkscreen"), ("laboratory", "Testing laboratory"),
                 ("wastewater", "Waste water treatment"), ("floor", "Production floor")]
    menu = cat_nav("Explore the plant", [(i, n, None) for i, n in area_list])
    band = "".join(f'<img src="assets/img/{p}" alt="" loading="lazy">' for p in
                   ("plant/f9.webp", "plant/mac1.webp", "plant/f12.webp", "plant/f3.webp"))
    body = page_head("Facilities",
                     "Pre-treatment, powder coating, curing, printing, testing and waste water treatment, all in one plant. Select an image to enlarge it.",
                     "Facilities") + f'''

    <section class="section">
      <div class="wrap cat-shell">
        {menu}
        <div class="cat-main">
{chr(10).join(blocks)}
        </div>
      </div>
    </section>

    <div class="photo-band" aria-hidden="true">{band}</div>

{CTA}'''
    page("facilities.html", "Facilities", "Inside Elite Coating's plant in Sungai Petani: pre-treatment, powder coating, curing, printing, testing laboratory and waste water treatment.", body, "facilities.html")


# ---------------------------------------------------------------- QUALITY
def quality():
    certs = [
        ("iso9001", "ISO 9001:2015 certificate of registration for Elite Coating", "ISO 9001:2015", "Quality management system",
         [("Scope", "Provision of metal parts spraying and powder coating services"),
          ("Certificate no.", "MY1469-Q-2"),
          ("Certified since", "October 2008")]),
        ("iso14001", "ISO 14001:2015 certificate of registration for Elite Coating", "ISO 14001:2015", "Environmental management system",
         [("Scope", "Provision of metal parts spraying and powder coating services"),
          ("Certificate no.", "MY1469-E-1"),
          ("Certified since", "September 2024")]),
    ]
    cert_html = "".join(f'''        <article class="cert">
          <figure class="cert-img" data-lightbox><img src="assets/img/certs/{f}.webp" alt="{alt}" loading="lazy"></figure>
          <div>
            <h3>{name}</h3>
            <p class="cert-sub">{sub}</p>
            <dl class="facts">{"".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)}</dl>
          </div>
        </article>''' for f, alt, name, sub, rows in certs)
    metro = gallery([
        ("quality/m1.webp", "BYK measuring instruments in a foam-lined case", "BYK measuring instruments"),
        ("quality/m2.webp", "Byko-test 8500 coating thickness gauge in a case", "Coating thickness gauge"),
        ("quality/m3.webp", "BYK instrument with brush accessory in a case", "Instrument accessories"),
        ("quality/m4.webp", "Colour assessment cabinet", "Colour assessment cabinet"),
    ], 2)
    lab = gallery([
        ("plant/f7.webp", "Lab room door with concentration and pH signage", "Lab room"),
        ("plant/f8.webp", "Technician checking chemicals in the laboratory", "Chemical testing"),
    ], 2)
    body = page_head("Quality",
                     "ISO 9001 and ISO 14001 certified, with an in-house laboratory and measuring instruments.",
                     "Quality") + f'''

    <section class="section section-mist">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Certified, tested and measured</h2>
          <p>Two ISO management systems, an in-house laboratory and measuring instruments.</p>
        </div>
        <ul class="trust">
          <li><a href="#certifications"><img class="trust-badge" src="assets/img/certs/iso9001-badge.png" alt="ISO 9001:2015" loading="lazy"><h3>ISO 9001:2015</h3><p>Quality management system</p><strong>Certified since October 2008</strong></a></li>
          <li><a href="#certifications"><img class="trust-badge" src="assets/img/certs/iso14001-badge.png" alt="ISO 14001:2015" loading="lazy"><h3>ISO 14001:2015</h3><p>Environmental management system</p><strong>Certified since September 2024</strong></a></li>
          <li><a href="#laboratory"><span class="trust-badge trust-num"><svg class="trust-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 6h10M21 6v13L9.5 38.5A3 3 0 0 0 12.1 43h23.8a3 3 0 0 0 2.6-4.5L27 19V6"/><path d="M14.5 31h19"/></svg></span><h3>In-house laboratory</h3><p>Chemical concentration is checked so process chemicals meet the defined standard.</p></a></li>
          <li><a href="#measuring"><span class="trust-badge trust-num"><svg class="trust-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="15" width="40" height="18" rx="2"/><path d="M11 15v7M18 15v5M25 15v7M32 15v5M39 15v7"/></svg></span><h3>Measuring equipment</h3><p>Instruments for checking coating thickness and colour on finished parts.</p></a></li>
        </ul>
      </div>
    </section>

    <section class="section" id="certifications">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Certifications</h2>
          <p>Our management systems are certified by Global Compliance Certification, accredited by JAS-ANZ. Select a certificate to enlarge it.</p>
        </div>
        <div class="certs">
{cert_html}
        </div>
      </div>
    </section>

    <section class="section section-mist" id="laboratory">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Testing laboratory</h2>
          <p>Our laboratory checks chemical concentration to make sure the process chemicals meet the defined standard solution.</p>
        </div>
        {lab}
      </div>
    </section>

    <section class="section" id="measuring">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Measuring equipment</h2>
          <p>Instruments for checking coating thickness and colour on finished parts.</p>
        </div>
        {metro}
      </div>
    </section>

{CTA}'''
    page("quality.html", "Quality", "ISO 9001:2015 and ISO 14001:2015 certification, in-house testing laboratory and measuring equipment at Elite Coating.", body, "quality.html")


# ---------------------------------------------------------------- CUSTOMERS
def customers():
    logos = "".join(f'<li><img src="assets/img/customers/{f}.png" alt="{a}" loading="lazy"></li>' for f, a in CUSTOMER_LOGOS)
    names = "".join(f"<li>{n}</li>" for n in CUSTOMERS)
    brands = "".join(f'<li><img src="assets/img/supplies/{f}.png" alt="{a}" loading="lazy"></li>' for f, a in PARTNERS)
    powder = "".join(f"<li>{n}</li>" for n in SUPPLIERS_POWDER)
    paint = "".join(f"<li>{n}</li>" for n in SUPPLIERS_PAINT)
    awards = award_cards(AWARDS)
    body = page_head("Customers",
                     "Manufacturers in the automotive, electronics and lighting industries trust us with their parts.",
                     "Customers") + f'''

{stat_band([("20+", "Manufacturers served"), ("6", "Awards from customers"), ("3", "Customers who have awarded us"), ("2008", "ISO 9001 certified since")])}

    <section class="section">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Who we coat for</h2>
          <p>A selection of our customers.</p>
        </div>
        <ul class="logo-wall">{logos}</ul>
        <ul class="name-list">{names}</ul>
      </div>
    </section>

    <section class="section section-mist" id="awards">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Awards and recognition</h2>
          <p>Awards our customers have presented to Elite Coating for quality, delivery and service. Select an image to enlarge it.</p>
        </div>
        <div class="awards" data-lightbox>{awards}</div>
      </div>
    </section>

    <section class="section" id="suppliers">
      <div class="wrap">
        <div class="section-head split-head">
          <h2>Our coating suppliers</h2>
          <p>We apply powder and paint from established manufacturers.</p>
        </div>
        <ul class="brands">{brands}</ul>
        <div class="supplier-cols">
          <div><h3>Powder</h3><ul class="name-list one">{powder}</ul></div>
          <div><h3>Paint</h3><ul class="name-list one">{paint}</ul></div>
        </div>
      </div>
    </section>

{CTA}'''
    page("customers.html", "Customers", "Customers, awards and coating suppliers of Elite Coating Sdn. Bhd.", body, "customers.html")


FAQ = [
    ("What materials can you coat?", [
        "Powder coating is available for aluminium and steel parts. Wet painting covers aluminium, steel and plastic parts.",
        "Typical work includes die-cast housings and covers, sheet-metal enclosures and brackets, and mirror-finish lamp reflectors. Examples are on our Products page.",
        "If your part is made of something else, send us a drawing or sample and we will tell you what we can do."]),
    ("What is the difference between powder coating and wet painting?", [
        "Powder coating applies dry powder electrostatically, by hand or in our automatic booth, and bakes it in a conveyor oven into a hard, even finish. Gloss, matt and textured finishes are available.",
        "Wet painting sprays liquid paint matched to the colour you specify, in gloss or special-effect coats. It can be used on plastic as well as metal.",
        "Not sure which one suits your part? Tell us how the part is used when you send your enquiry."]),
    ("What pre-treatment do you offer?", [
        "We offer clear chromate and iron phosphate pre-treatment. Parts are cleaned and treated before coating so the finish bonds well and resists corrosion.",
        "Our laboratory checks the concentration of the process chemicals, and waste water from the process is treated on site.",
        "When you request a quote, tell us the material and the finish you need."]),
    ("Do you offer printing on finished parts?", [
        "Yes. We offer tampo (pad) and silkscreen printing for logos, markings and graphics.",
        "Printing is done in a dedicated printing room in our plant. Send us your artwork or a sample part when you request a quote."]),
    ("Which industries do you serve?", [
        "We serve a wide range of industries, including automotive, electronics and lighting.",
        "In automotive, that means parts such as engine covers, sprocket covers and casings. In electronics, it means control panels, enclosures and brackets. In lighting, it means reflectors, lamp housings and heat-sinks.",
        "More than 20 manufacturers have trusted us with their parts, including STX Precision, Paramit, Dialight, GKN Driveline, Flextronics and Interplex. The Customers page has more."]),
    ("Are you ISO certified?", [
        "Yes. Elite Coating is certified to ISO 9001:2015 for quality management and ISO 14001:2015 for environmental management, both for the provision of metal parts spraying and powder coating services.",
        "ISO 9001 certification dates from October 2008 (certificate no. MY1469-Q-2) and ISO 14001 from September 2024 (certificate no. MY1469-E-1). Both are certified by Global Compliance Certification, accredited by JAS-ANZ.",
        "You can view and enlarge both certificates on our Quality page."]),
    ("How do you check quality?", [
        "Our laboratory checks the concentration of process chemicals so they meet the defined standard solution.",
        "Measuring instruments are used to check coating thickness and colour on finished parts, including a Byko-test 8500 coating thickness gauge, other BYK instruments and a colour assessment cabinet.",
        "Photos of the laboratory and instruments are on our Quality page."]),
    ("Which coating brands do you use?", [
        "We apply powder and paint from established manufacturers. Powder suppliers include AkzoNobel Industrial Coatings, Jotun Powder, Axalta Powder Coating Systems and Tiger Drylac. Paint suppliers include Nippon Paint, Sherwin-Williams, Musashi Paint and Durachem.",
        "The full supplier list is on our Customers page."]),
    ("How do you look after the environment?", [
        "Our environmental management system is certified to ISO 14001:2015. Waste water from the process is treated on site, and our laboratory checks process chemicals so they stay within standard.",
        "Our efforts focus on minimising waste, preventing pollution, meeting applicable environmental laws and regulations, and improving our environmental performance over time."]),
    ("How do I request a quote?", [
        "The quickest way is the quotation form on this page. Tell us what you need (powder coating, wet painting, pre-treatment or printing), the material, approximate part size, estimated quantity, colour and finish, and the date you need the parts.",
        "You can add up to 5 files of 10 MB each, such as drawings (PDF, DWG, DXF or STEP), photos or a zip file. You can also reach us by phone or email, and we will reply with a quotation.",
        "It also helps to say whether the order is a one-off sample, a trial batch or regular production."]),
    ("Where are you located?", [
        "Our plant is at Plot 5 &amp; 6, Kawasan Perusahaan LPK Fasa 4, 08000 Sungai Petani, Kedah. Use the map above to get directions."]),
    ("What are your opening hours?", [
        f"We are open Monday to Thursday and on Saturday from {_span(HOURS_MON_THU_SAT)}, and on Friday from {_span(HOURS_FRI)}. We are closed on Sunday."]),
]


def faq_block():
    items = "".join(
        f'<details{" open" if i == 0 else ""}><summary>{q}</summary><div class="faq-a">{"".join(f"<p>{p}</p>" for p in paras)}</div></details>'
        for i, (q, paras) in enumerate(FAQ))
    return f'''    <section class="section" id="faq">
      <div class="wrap faq-grid">
        <div class="faq-intro">
          <h2>Frequently asked questions</h2>
          <p>Quick answers about our services, quality and how to get a quote.</p>
        </div>
        <div class="faq-list">{items}</div>
      </div>
    </section>'''


def enquiry_form():
    FILE_HINT = ("Up to 5 files, 10 MB each. Sent with your enquiry." if FORM_ENDPOINT else
                 "Up to 5 files, 10 MB each. In your email app, attach the same files before you press Send.")
    needs = "".join(
        f'<label class="check"><input type="checkbox" name="needs" value="{n}"> {n}</label>'
        for n in ("Powder coating", "Wet painting", "Pre-treatment", "Tampo and silkscreen printing", "Not sure yet"))
    return f'''<form class="form" id="enquiry-form" novalidate data-endpoint="{FORM_ENDPOINT}" data-mailto="{FORM_TO}" data-cc="{FORM_CC}"
              data-subject="Quotation request" data-msg-sending="Sending…"
              data-msg-success="Thank you. Your message has been sent. We will reply soon."
              data-msg-error="Sorry, your message could not be sent. Please email or call us instead."
              data-msg-mailto="Your email program should open with your message ready to send. If it does not, please email us at">
          <h3 class="form-section">Your details</h3>
          <div class="form-row">
            <div class="field"><label for="f-name">Name <span aria-hidden="true">*</span></label>
              <input id="f-name" name="name" type="text" autocomplete="name" required aria-describedby="f-name-error" data-msg-required="Enter your name">
              <p class="field-error" id="f-name-error" aria-live="polite"></p></div>
            <div class="field"><label for="f-company">Company</label>
              <input id="f-company" name="company" type="text" autocomplete="organization"></div>
          </div>
          <div class="form-row">
            <div class="field"><label for="f-email">Email <span aria-hidden="true">*</span></label>
              <input id="f-email" name="email" type="email" autocomplete="email" required aria-describedby="f-email-error"
                data-msg-required="Enter your email address" data-msg-invalid="Enter a valid email address">
              <p class="field-error" id="f-email-error" aria-live="polite"></p></div>
            <div class="field"><label for="f-phone">Phone</label>
              <input id="f-phone" name="phone" type="tel" autocomplete="tel"></div>
          </div>
          <h3 class="form-section">About your parts</h3>
          <fieldset class="field field-group"><legend>What do you need?</legend>
            <div class="checks">{needs}</div></fieldset>
          <div class="form-row">
            <div class="field"><label for="f-material">Material</label>
              <select id="f-material" name="material">
                <option value="">Choose one</option>
                <option>Aluminium</option>
                <option>Steel</option>
                <option>Plastic</option>
                <option>Other or not sure</option>
              </select></div>
            <div class="field"><label for="f-qty">Estimated quantity</label>
              <input id="f-qty" name="quantity" type="text" placeholder="For example, 5,000 a month"></div>
          </div>
          <div class="form-row">
            <div class="field"><label for="f-size">Approximate part size</label>
              <input id="f-size" name="size" type="text" placeholder="For example, 200 × 120 mm"></div>
            <div class="field"><label for="f-order">Order type</label>
              <select id="f-order" name="order">
                <option value="">Choose one</option>
                <option>One-off sample</option>
                <option>Trial batch</option>
                <option>Regular production</option>
                <option>Not sure yet</option>
              </select></div>
          </div>
          <div class="form-row">
            <div class="field"><label for="f-finish">Colour and finish</label>
              <input id="f-finish" name="finish" type="text" placeholder="For example, black textured"></div>
            <div class="field"><label for="f-date">Date needed</label>
              <input id="f-date" name="date" type="date"></div>
          </div>
          <div class="field field-file"><label for="f-files">Drawings or photos</label>
            <input id="f-files" name="attachments" type="file" multiple accept="image/*,.pdf,.dwg,.dxf,.step,.stp,.zip"
              data-max-files="5" data-max-mb="10" data-msg-limit="Please choose up to 5 files of 10 MB or less." aria-describedby="f-files-hint f-files-error">
            <p class="field-hint" id="f-files-hint">{FILE_HINT}</p>
            <p class="form-status error file-error" id="f-files-error" role="alert"></p></div>
          <div class="field"><label for="f-message">Additional details</label>
            <textarea id="f-message" name="message" rows="5"
              placeholder="Standards to meet, packing needs or anything else we should know."></textarea></div>
          <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button class="btn btn-red" type="submit">Send quotation request</button>
          <p class="form-note">Required fields are marked *. We use your details only to reply to your enquiry.</p>
          <p class="form-status" role="status" aria-live="polite"></p>
          <div class="form-result" hidden role="status" aria-live="polite" tabindex="-1" data-msg-copied="Copied">
            <h3>Enquiry ready to send</h3>
            <p>Your email app should open with this enquiry filled in. Press Send in your email app to finish.</p>
            <p class="form-result-files" hidden><span>Attach these files before you send:</span> <b data-files></b></p>
            <p class="form-result-row"><span>Nothing opened?</span> <button type="button" class="linkish" data-reopen>Open email app again</button> <button type="button" class="btn btn-outline btn-sm" data-copy>Copy enquiry text</button></p>
            <p class="form-result-row"><span>Or call us on</span> {PHONE_HTML}</p>
          </div>
        </form>'''


# ---------------------------------------------------------------- CONTACT
# ---------------------------------------------------------------- PRIVACY NOTICE
def privacy():
    """Plain-language notice under Malaysia's PDPA 2010. It describes only what the site does today; update it if the form,
    cookies, analytics or retention change. Have it checked before relying on it legally."""
    def block(title, *paras):
        return f"<h2>{title}</h2>" + "".join(f"<p>{x}</p>" for x in paras)
    body = page_head("Privacy Notice",
                     "How Elite Coating Sdn. Bhd. looks after the personal information you give us.",
                     "Privacy Notice") + f'''

    <section class="section">
      <div class="wrap"><div class="legal">
        <p>Elite Coating Sdn. Bhd. (Company No. 200301024073 (626493-K)) runs this website. This notice explains how we handle your personal data under the Personal Data Protection Act 2010 (PDPA).</p>
        {block("What we collect", "When you send us an enquiry, we collect what you enter in the form: your name, company, email address, phone number, details of the parts you want coated, and any message or files you add. Your name and email address are needed so that we can reply.")}
        {block("Why we use it", "We use your details to reply to your enquiry, prepare a quotation and talk to you about your order. We do not use them for anything else without asking you first.")}
        {block("Who sees it", "Your enquiry goes to our staff by email. We share personal data only where it is needed to deal with your enquiry, or where the law requires it.")}
        {block("This website", "This website does not use advertising or analytics tools, and its own pages do not set cookies. Your choice of light or dark theme is saved in your browser and stays on your device. Pages with a map load Google Maps, and Google may collect information about your visit under its own privacy policy.")}
        {block("How long we keep it", "We keep enquiry details for as long as we need them to deal with your enquiry and to keep our business records. After that we delete them.")}
        {block("Your rights", "You can ask to see the personal data we hold about you, ask us to correct it, or ask us to stop using it. Contact us using the details below and we will reply as the PDPA requires.")}
        <h2>Contact us</h2>
        <p>Questions or requests about your personal data? Write, call or email us:</p>
        <p>{ADDRESS}</p>
        <p>Tel: {PHONE_HTML}<br>{EMAIL_HTML.replace("<br>", " / ")}</p>
        {block("Changes to this notice", "We may update this notice. The date below shows when it was last changed.")}
        <p>Last updated: October 2026</p>
      </div></div>
    </section>'''
    page("privacy.html", "Privacy Notice",
         "How Elite Coating Sdn. Bhd. collects, uses and protects the personal data you give us through this website.", body)


def contact():
    body = page_head("Contact",
                     "Tell us about your parts and we will reply with a quotation.",
                     "Contact") + f'''

    <section class="section">
      <div class="wrap contact-grid">
        <div>
          <h2>Get in touch</h2>
          <dl class="facts contact-facts">
            <div><dt>Address</dt><dd>{ADDRESS}</dd></div>
            <div><dt>Telephone</dt><dd>{PHONE_HTML}</dd></div>
            <div><dt>Fax</dt><dd>{FAX}</dd></div>
            <div><dt>Email</dt><dd>{EMAIL_HTML}</dd></div>
            <div><dt>Opening hours</dt><dd>{HOURS_HTML}</dd></div>
            <div><dt>Person in charge</dt><dd>{CONTACT_PERSON}</dd></div>
          </dl>
        </div>
        <div class="map-col">
          {map_block()}
          {map_actions()}
        </div>
      </div>
    </section>

    <section class="section section-mist" id="enquiry">
      <div class="wrap enquiry-grid">
        <div class="prose">
          <h2>Request a quotation</h2>
          <p>Tell us about your parts and we will reply with a quotation.</p>
          <p>To quote quickly, include as much of this as you can.</p>
          <ul class="marks">
            <li>Drawings or sample parts</li>
            <li>Material and part size</li>
            <li>Quantity and batch size</li>
            <li>Colour, finish and any standards to meet</li>
            <li>Delivery date</li>
          </ul>
        </div>
        {enquiry_form()}
      </div>
    </section>

{faq_block()}'''
    page("contact.html", "Contact", "Contact Elite Coating Sdn. Bhd. in Sungai Petani, Kedah for a coating quotation. Find us on the map.", body, "contact.html")


# ---------------------------------------------------------------- PAGE NOT FOUND
def not_found():
    links = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[1:-1])
    body = page_head("Page not found",
                     "That page does not exist or has moved. Use the menu, or go back to the home page.",
                     "Page not found") + f'''

    <section class="section">
      <div class="wrap nf">
        <p class="nf-code" aria-hidden="true">404</p>
        <div class="btn-row">
          <a class="btn btn-primary" href="index.html">Back to home</a>
          <a class="btn btn-outline" href="contact.html">Contact us</a>
        </div>
        <ul class="nf-links">{links}</ul>
      </div>
    </section>'''
    page("404.html", "Page not found", "This page could not be found.", body)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    minify_assets()
    for fn in (home, about, services, products, facilities, quality, customers, contact, privacy, not_found):
        fn()
    write_search_files()
    print("built:", ", ".join(sorted(p.name for p in OUT.glob("*.html"))), "+ zh/ + ms/")
    for lang, items in MISSING.items():
        if items:
            print(f"UNTRANSLATED ({lang}): {len(items)}")
            if "--list" in __import__("sys").argv:
                for t in sorted(items):
                    print("   ", repr(t))
    if any(MISSING.values()):
        raise SystemExit(1)  # pages are written, but the build is marked failed so untranslated text is not missed
