"""Checks the built site in ./site and exits with an error if something is broken.
Run after building:  python build-site.py && python check-site.py

Errors (exit code 1): broken links or anchors, missing images or files, duplicate ids, a page without exactly one h1,
skipped heading levels, images without alt text, form fields without a label, duplicate titles or descriptions.
Warnings (printed, exit code 0): long titles, odd description lengths, files nothing uses.
"""
import collections
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SITE = Path(__file__).parent / "site"
EXTERNAL = re.compile(r"(https?:|mailto:|tel:|javascript:|data:)")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.headings, self.imgs, self.assets = [], [], [], [], []
        self.title = self.desc = ""
        self.fields, self.labels, self.buttons = [], set(), []
        self._in_title, self._button = False, None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a: self.ids.append(a["id"])
        if tag == "a": self.links.append(a)
        if tag in ("h1", "h2", "h3", "h4"): self.headings.append(int(tag[1]))
        if tag == "img": self.imgs.append(a)
        if tag in ("link", "script") and (a.get("href") or a.get("src")): self.assets.append(a.get("href") or a.get("src"))
        if tag == "title": self._in_title = True
        if tag == "meta" and a.get("name") == "description": self.desc = a.get("content", "")
        if tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit", "checkbox", "radio") and a.get("name") != "website":
            self.fields.append(a)
        if tag == "label" and "for" in a: self.labels.add(a["for"])
        if tag == "button": self._button = [a, ""]

    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
        if tag == "button" and self._button:
            self.buttons.append(self._button); self._button = None

    def handle_data(self, d):
        if self._in_title: self.title += d
        if self._button: self._button[1] += d


def local(page, ref):
    """File a local link or asset points to, or None for external ones."""
    if not ref or EXTERNAL.match(ref): return None
    return (page.parent / urlsplit(ref).path).resolve()


errors, warnings = [], []
pages = {p: Page() for p in sorted(SITE.rglob("*.html"))}
for p, q in pages.items():
    q.feed(p.read_text(encoding="utf-8"))
ids = {p.resolve(): set(q.ids) for p, q in pages.items()}

for p, q in pages.items():
    name = p.relative_to(SITE).as_posix()
    err = lambda msg: errors.append(f"{name}: {msg}")
    for i, c in collections.Counter(q.ids).items():
        if c > 1: err(f"duplicate id {i!r}")
    if q.headings.count(1) != 1: err(f"{q.headings.count(1)} h1 headings")
    prev = 0
    for h in q.headings:
        if prev and h > prev + 1: err(f"heading jumps from h{prev} to h{h}"); break
        prev = h
    for im in q.imgs:
        if "alt" not in im: err(f"image without alt: {im.get('src')}")
        f = local(p, im.get("src"))
        if f and not f.exists(): err(f"missing image {im.get('src')}")
    for ref in q.assets:
        f = local(p, ref)
        if f and not f.exists(): err(f"missing file {ref}")
    for a in q.links:
        href = a.get("href", "")
        if a.get("target") == "_blank" and "noopener" not in a.get("rel", ""): err(f"_blank link without rel=noopener: {href}")
        if href.startswith("#"):
            if len(href) > 1 and href[1:] not in ids[p.resolve()]: err(f"broken anchor {href}")
            continue
        f = local(p, href)
        if f is None: continue
        if not f.exists(): err(f"broken link {href}"); continue
        frag = urlsplit(href).fragment
        if frag and f.suffix == ".html" and frag not in ids.get(f, set()): err(f"broken anchor {href}")
    for fld in q.fields:
        if fld.get("id") not in q.labels and "aria-label" not in fld: err(f"form field without a label: {fld.get('name') or fld.get('id')}")
    for a, text in q.buttons:
        if not text.strip() and "aria-label" not in a: err("button without a name")
    if name.endswith("404.html"): continue
    if len(q.title) > 65: warnings.append(f"{name}: title is {len(q.title)} characters")
    if not name.startswith("zh/") and not 50 <= len(q.desc) <= 170: warnings.append(f"{name}: description is {len(q.desc)} characters")

for field in ("title", "desc"):
    seen = collections.defaultdict(list)
    for p, q in pages.items():
        if not p.name == "404.html": seen[getattr(q, field)].append(p.relative_to(SITE).as_posix())
    errors += [f"same {field} on {', '.join(v)}" for v in seen.values() if len(v) > 1]

used = {local(p, r) for p, q in pages.items() for r in q.assets + [i.get("src") for i in q.imgs]}
for css in SITE.glob("css/*.css"):
    used |= {(css.parent / u).resolve() for u in re.findall(r"url\(['\"]?([^)'\"?#]+)", css.read_text(encoding="utf-8"))}
unused = [f for f in (SITE / "assets").rglob("*.*") if f.resolve() not in used and "share" not in f.parts]
warnings += [f"unused file: {f.relative_to(SITE).as_posix()}" for f in unused]

for w in warnings: print("warning:", w)
for e in errors: print("ERROR:", e)
print(f"{len(pages)} pages checked: {len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
