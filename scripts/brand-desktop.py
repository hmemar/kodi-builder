#!/usr/bin/env python3
"""Apply Husham Play branding to a desktop Kodi source tree (Linux/Windows/macOS).
Usage: brand-desktop.py <kodi-src> <kodi-config-dir> <out-images-dir>"""
import base64, io, os, re, shutil, sys, urllib.request, zipfile
src, cfg, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
# 1. images
for n in ("icon", "splash"):
    b = os.path.join(cfg, n + ".png.b64"); p = os.path.join(cfg, n + ".png")
    if not os.path.exists(p) and os.path.exists(b):
        open(p, "wb").write(base64.b64decode(open(b).read()))
    if os.path.exists(p):
        shutil.copy(p, os.path.join(out, n + ".png")); print("image", n)
try:
    from PIL import Image
    ic = os.path.join(out, "icon.png")
    if os.path.exists(ic):
        im = Image.open(ic).convert("RGBA")
        for s in (16, 32, 48, 64, 128, 256):
            im.resize((s, s)).save(os.path.join(src, "media", f"icon{s}x{s}.png")) if os.path.exists(os.path.join(src, "media", f"icon{s}x{s}.png")) else None
        im.save(os.path.join(out, "icon.ico"), sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    sp = os.path.join(out, "splash.png")
    if os.path.exists(sp):
        Image.open(sp).convert("RGB").resize((1920, 1080)).save(os.path.join(src, "media", "splash.jpg"), quality=92)
        print("splash.jpg replaced")
except ImportError:
    print("PIL missing; skipping icon resizes")
# 2. userdata defaults + copy-on-first-run
ud = os.path.join(src, "userdata"); os.makedirs(ud, exist_ok=True)
for f in ("sources.xml", "advancedsettings.xml"):
    if os.path.exists(os.path.join(cfg, f)):
        shutil.copy(os.path.join(cfg, f), ud); print("userdata", f)
app = os.path.join(src, "xbmc", "application", "Application.cpp")
a = open(app, encoding="utf-8").read()
anchor = 'CUtil::CopyUserDataIfNeeded("special://masterprofile/", "RssFeeds.xml");'
if anchor in a and "sources.xml\");" not in a:
    a = a.replace(anchor, anchor + '\n  CUtil::CopyUserDataIfNeeded("special://masterprofile/", "sources.xml");'
                  '\n  CUtil::CopyUserDataIfNeeded("special://masterprofile/", "advancedsettings.xml");')
    open(app, "w", encoding="utf-8").write(a); print("patched Application.cpp")
# 3. unknown sources default on
st = os.path.join(src, "system", "settings", "settings.xml")
s = open(st, encoding="utf-8").read()
s = re.sub(r'(<setting id="addons.unknownsources"[^>]*>\s*<level>0</level>\s*<default>)false', r'\1true', s)
open(st, "w", encoding="utf-8").write(s)
# 4. addons
man = os.path.join(src, "system", "addon-manifest.xml")
inst = os.path.join(src, "cmake", "installdata", "common", "addons.txt")
af = os.path.join(cfg, "addons.txt")
if os.path.exists(af):
    for url in open(af):
        url = url.strip()
        if not url or url.startswith("#"): continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Kodi"})
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()))
        z.extractall(os.path.join(src, "addons"))
        for aid in {n.split("/")[0] for n in z.namelist()}:
            t = open(inst).read()
            if f"addons/{aid}/*" not in t: open(inst, "a").write(f"\naddons/{aid}/*\n")
            m = open(man).read()
            if f"<addon>{aid}</addon>" not in m:
                open(man, "w").write(m.replace("</addons>", f"  <addon>{aid}</addon>\n</addons>"))
            print("addon", aid)
print("branding done")
