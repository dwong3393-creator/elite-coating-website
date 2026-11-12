"""Makes ./upload/Elite-Coating-Website-Hosting-Pack.zip, the one file to send to a hosting person. The zip holds
HOSTING-INSTRUCTIONS.txt and a website/ folder (the built site plus a server settings file). The upload folder holds nothing else.
Run after building:  python build-site.py && python make-upload.py
To put the site online yourself, unzip it and upload everything inside website/ (including the hidden .htaccess) to the host's web folder, usually public_html.
"""
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
OUT = ROOT / "upload"
ZIP = OUT / "Elite-Coating-Website-Hosting-Pack.zip"

# Settings for Apache and LiteSpeed (most shared hosting and cPanel). Other servers ignore this file.
HTACCESS = """# Elite Coating website: server settings for Apache / LiteSpeed hosting.
# Every block is optional; a block for a module the host lacks is skipped.

Options -Indexes
DirectoryIndex index.html

# Shown for a missing page. Works when the site sits in the web root; in a sub-folder change it to /folder/404.html.
ErrorDocument 404 /404.html

<IfModule mod_mime.c>
  AddType image/webp .webp
  AddType font/woff2 .woff2
</IfModule>

# Send text files compressed
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css text/javascript application/javascript image/svg+xml text/plain text/xml application/xml
</IfModule>

# Browser caching. Pages are always re-checked. CSS and JS carry a ?v= number that changes when they change, so they can be kept a year.
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/html "access plus 0 seconds"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType image/webp "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/svg+xml "access plus 1 month"
</IfModule>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set X-Frame-Options "SAMEORIGIN"
</IfModule>

# Send every visitor to the secure (https) address. Remove the "#" at the start of the five lines below
# only AFTER the host has installed an SSL certificate, or the site will stop loading.
# <IfModule mod_rewrite.c>
#   RewriteEngine On
#   RewriteCond %{HTTPS} off
#   RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
# </IfModule>
"""


INSTRUCTIONS = """ELITE COATING SDN. BHD. - WEBSITE HOSTING INSTRUCTIONS
Prepared: {date}

WHAT YOU HAVE
This zip holds a finished static website: plain HTML, CSS, JavaScript, images and
fonts, in English, Chinese (/zh/) and Malay (/ms/). It needs no database, no PHP,
no Node and no build step. Any web server that can serve files will do.

    HOSTING-INSTRUCTIONS.txt    this file
    website/                    everything that goes online ({count} files, {size} MB)

WHAT TO DO
 1. On the hosting account, add the domain and point it at an empty web folder
    (usually public_html).
 2. Unzip. Upload everything INSIDE the "website" folder into that web folder. Do not
    upload the "website" folder itself: index.html must sit directly in the web folder.
 3. Make sure the hidden file ".htaccess" is uploaded too. In cPanel File Manager turn
    on "Show Hidden Files (dotfiles)". In an FTP program turn on "show hidden files".
 4. Install a free SSL certificate (AutoSSL or Let's Encrypt) for the domain and its
    www version.
 5. When https works, open .htaccess and remove the "#" from the five lines under
    "Send every visitor to the secure (https) address". Do this only after step 4,
    or the site will stop loading.
 6. Choose one address, with or without www, and redirect the other to it with a
    permanent (301) redirect. Ask the owner which one they prefer.
 7. File permissions: folders 755, files 644.

SERVER NEEDS
 - Static file serving over http and https. Nothing else.
 - Apache or LiteSpeed: the .htaccess file does the rest. It needs AllowOverride to
   be enabled, which is the default on shared hosting and cPanel.
 - nginx or another server: .htaccess is ignored. Please set up:
     * missing pages answer with status 404 and show /404.html
     * compression for text files (html, css, js, svg)
     * caching: css, js and fonts one year (their links carry a ?v= number that
       changes when they change); images 30 days; html always re-checked
     * file types: .webp as image/webp, .woff2 as font/woff2
     * no folder listing
   Example for nginx:
       error_page 404 /404.html;
       gzip on;  gzip_types text/css application/javascript image/svg+xml text/plain;
       location ~* \\.(css|js|woff2)$ {{ expires 1y; add_header Cache-Control "public, immutable"; }}
       location ~* \\.(webp|png|jpg|svg)$ {{ expires 30d; }}

CHECK AFTER UPLOAD
 - / , /zh/ and /ms/ show the English, Chinese and Malay home pages.
 - /about.html, /products.html, /contact.html and /privacy.html open.
 - /no-such-page.html shows the "Page not found" page.
 - The padlock shows and there are no browser warnings.
 - http:// goes to https:// (after step 5).
 - On a phone: the menu opens, and the moon button (top right) switches dark mode.

GOOD TO KNOW
 - {address_note}
 - The contact form has no server script. It opens the visitor's email program with
   the message ready to send. Nothing to install. The mailbox
   elite@elitecoating.com.my must exist; that is set up separately from the website.
 - The only outside service used is the Google Maps view on the Contact and About
   pages. There are no analytics, no advertising and no outside fonts or scripts.
 - Please do not edit the files by hand. The pages are generated, and a hand edit is
   lost at the next update. Ask the owner for a new zip instead.

QUESTIONS
Elite Coating Sdn. Bhd., elite@elitecoating.com.my
"""


def write_zip(stage, count, size_mb, base_url):
    note = (f"This copy was built for {base_url}. Keep that address, or ask the owner for a new build."
            if base_url else
            "This copy was built without a final web address, so it has no sitemap.xml and no canonical or share tags yet.\n"
            "   Tell the owner the live address and they will send a rebuilt zip.")
    text = INSTRUCTIONS.format(date=datetime.date.today().strftime("%d %B %Y"), count=count, size=f"{size_mb:.1f}", address_note=note)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("HOSTING-INSTRUCTIONS.txt", text.replace("\n", "\r\n"))  # Windows Notepad friendly
        for f in sorted(stage.rglob("*")):
            if f.is_file():
                z.write(f, "website/" + f.relative_to(stage).as_posix())


def main():
    if not (SITE / "index.html").exists():
        sys.exit("site/ is empty. Run: python build-site.py")
    if subprocess.run([sys.executable, str(ROOT / "check-site.py")]).returncode:
        sys.exit("check-site.py found problems. Fix them, rebuild, and run this again.")
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        shutil.copytree(SITE, stage, dirs_exist_ok=True)
        (stage / ".htaccess").write_text(HTACCESS, encoding="utf-8")
        files = [f for f in stage.rglob("*") if f.is_file()]
        size_mb = sum(f.stat().st_size for f in files) / 1e6
        sitemap_line = re.search(r"^Sitemap: (.+)/sitemap\.xml", (stage / "robots.txt").read_text(encoding="utf-8"), re.M)
        write_zip(stage, len(files), size_mb, sitemap_line.group(1) if sitemap_line else "")
        has_sitemap = (stage / "sitemap.xml").exists()
    print(f"upload/{ZIP.name} is ready: {len(files)} site files, zip {ZIP.stat().st_size / 1e6:.1f} MB")
    if not has_sitemap:
        print("note: SITE_URL is not set in build-site.py, so there is no sitemap.xml, canonical links or share pictures yet.")


if __name__ == "__main__":
    main()
