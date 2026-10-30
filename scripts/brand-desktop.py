#!/usr/bin/env python3
"""Apply Husham Play branding to a desktop Kodi source tree (Linux/Windows/macOS).

Usage: brand-desktop.py <kodi-src> <kodi-config-dir> <out-images-dir> [platform]

platform defaults to env HUSHAM_PLATFORM or python-only.
Examples: windows-x86_64 | osx-arm64 | osx-x86_64 | linux | python-only
"""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys

src, cfg, out = sys.argv[1:4]
platform = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("HUSHAM_PLATFORM", "python-only")
os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))


def log(msg: str) -> None:
    print(msg, flush=True)


# 1. images
for n in ("icon", "splash"):
    b = os.path.join(cfg, n + ".png.b64")
    p = os.path.join(cfg, n + ".png")
    if not os.path.exists(p) and os.path.exists(b):
        open(p, "wb").write(base64.b64decode(open(b).read()))
    if os.path.exists(p):
        shutil.copy(p, os.path.join(out, n + ".png"))
        log(f"image {n}")
try:
    from PIL import Image

    ic = os.path.join(out, "icon.png")
    if os.path.exists(ic):
        im = Image.open(ic).convert("RGBA")
        for s in (16, 32, 48, 64, 128, 256):
            target = os.path.join(src, "media", f"icon{s}x{s}.png")
            if os.path.exists(target):
                im.resize((s, s)).save(target)
        im.save(
            os.path.join(out, "icon.ico"),
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        # vendor branding
        for name, size in (("vendor_icon.png", 128),):
            path = os.path.join(src, "media", name)
            if os.path.exists(path) or True:
                im.resize((size, size)).save(os.path.join(src, "media", name))
        # wide vendor logo
        canvas = Image.new("RGBA", (465, 128), (0, 0, 0, 0))
        mark = im.resize((128, 128))
        canvas.paste(mark, ((465 - 128) // 2, 0), mark)
        canvas.save(os.path.join(src, "media", "vendor_logo.png"))
    sp = os.path.join(out, "splash.png")
    if os.path.exists(sp):
        Image.open(sp).convert("RGB").resize((1920, 1080)).save(
            os.path.join(src, "media", "splash.jpg"), quality=92
        )
        log("splash.jpg replaced")
except ImportError:
    log("PIL missing; skipping icon resizes")

# 2. userdata defaults + copy-on-first-run
ud = os.path.join(src, "userdata")
os.makedirs(ud, exist_ok=True)
for f in ("sources.xml", "advancedsettings.xml", "favourites.xml"):
    if os.path.exists(os.path.join(cfg, f)):
        shutil.copy(os.path.join(cfg, f), ud)
        log(f"userdata {f}")

app = os.path.join(src, "xbmc", "application", "Application.cpp")
if os.path.isfile(app):
    a = open(app, encoding="utf-8").read()
    anchor = 'CUtil::CopyUserDataIfNeeded("special://masterprofile/", "RssFeeds.xml");'
    if anchor in a and 'sources.xml");' not in a:
        a = a.replace(
            anchor,
            anchor
            + '\n  CUtil::CopyUserDataIfNeeded("special://masterprofile/", "sources.xml");'
            + '\n  CUtil::CopyUserDataIfNeeded("special://masterprofile/", "advancedsettings.xml");'
            + '\n  CUtil::CopyUserDataIfNeeded("special://masterprofile/", "favourites.xml");',
        )
        open(app, "w", encoding="utf-8").write(a)
        log("patched Application.cpp")

# 3. unknown sources default on
st = os.path.join(src, "system", "settings", "settings.xml")
if os.path.isfile(st):
    s = open(st, encoding="utf-8").read()
    s = re.sub(
        r'(<setting id="addons\.unknownsources"[^>]*>\s*<level>0</level>\s*<default>)false',
        r"\1true",
        s,
    )
    open(st, "w", encoding="utf-8").write(s)

# 4. stage addons (python + binary + bundled)
subprocess.check_call([sys.executable, os.path.join(here, "stage-addons.py"), src, cfg, platform])

# 5. skin fork
subprocess.check_call([sys.executable, os.path.join(here, "brand-skin.py"), src, cfg])

log("branding done")
