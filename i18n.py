"""Turns the generated English pages into Chinese (zh) and Malay (ms) pages.

English pages are the source. Every visible text node and text attribute (alt, title,
aria-label, meta description) is looked up in translations.py by its exact English text.
Anything not found is left in English and reported, so nothing is silently dropped.
"""
import re

import translations

HTML_LANG = {"en": "en", "zh": "zh-Hans", "ms": "ms"}
LANGUAGES = [("en", "English"), ("zh", "中文"), ("ms", "Bahasa Melayu")]
TITLE_SUFFIX = re.compile(r"^(.+) \| Elite Coating Sdn\. Bhd\.$")
TEXT_NODE = re.compile(r"(?<=>)([^<>]+)(?=<)")
ATTR = re.compile(r'\b(alt|title|aria-label|content|data-of|placeholder|data-subject|data-msg-[a-z]+)="([^"]*)"')


def page_href(from_lang, to_lang, filename):
    """Relative link from a page in one language to the same page in another."""
    up = "" if from_lang == "en" else "../"
    down = "" if to_lang == "en" else f"{to_lang}/"
    return f"{up}{down}{filename}"


def topbar(lang, filename):
    links = "".join(
        f'<a href="{page_href(lang, code, filename)}" lang="{HTML_LANG[code]}" hreflang="{HTML_LANG[code]}"'
        f'{" aria-current=\"true\"" if code == lang else ""}>{name}</a>'
        for code, name in LANGUAGES)
    return f'<nav class="lang" aria-label="Language">{links}</nav>'


def _skip(key):
    return (not re.search(r"[A-Za-z]", key) or "@" in key or key.startswith(("http", "#"))
            or "=" in key or key.startswith("assets/"))


def localize(html, lang, filename, missing):
    """Return the page in `lang`. Untranslated strings are added to `missing`."""
    html = html.replace("<!--TOPBAR-->", topbar(lang, filename))
    if lang == "en":
        return html

    tr = translations.TABLES[lang]

    def lookup(raw):
        key = raw.strip()
        if _skip(key):
            return raw
        m = TITLE_SUFFIX.match(key)
        if m and m.group(1) in tr:
            return raw.replace(key, f"{tr[m.group(1)]} | Elite Coating Sdn. Bhd.")
        if key in tr:
            return raw.replace(key, tr[key])
        if key not in translations.KEEP:
            missing.add(key)
        return raw

    html = TEXT_NODE.sub(lambda m: lookup(m.group(1)), html)
    html = ATTR.sub(lambda m: f'{m.group(1)}="{lookup(m.group(2))}"', html)
    html = html.replace('<html lang="en">', f'<html lang="{HTML_LANG[lang]}">')
    # CSS, JS and images live one folder up
    html = re.sub(r'\b(src|href)="(assets/|css/|js/)', r'\1="../\2', html)
    return html
