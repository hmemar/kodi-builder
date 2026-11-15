#!/usr/bin/env python3
"""Copy packed Estuary texture bundles into skin.husham.play.

Kodi's TexturePacker / cmake install only emits Textures.xbt (and theme
.xbt files) for skin.estuary. brand-skin.py forks Estuary into
skin.husham.play before that pack runs, so the fork is installed without
media/. The 1.5 APK shipped zero files under skin.husham.play/media/,
which made the home-menu focus bar, dialog panels, and sidemenu icons
invisible.

Usage:
  copy-skin-textures.py <addons-dir> [<addons-dir> ...]

Each addons-dir must contain skin.estuary/media/*.xbt (source) and
skin.husham.play (destination). Exits 2 if no .xbt is copied.
"""
from __future__ import annotations

import os
import shutil
import sys

ESTUARY = "skin.estuary"
FORK = "skin.husham.play"


def _log(msg: str) -> None:
    print(msg, flush=True)


def copy_packed_textures(addons_dir: str) -> int:
    estuary_media = os.path.join(addons_dir, ESTUARY, "media")
    dest_skin = os.path.join(addons_dir, FORK)
    dest_media = os.path.join(dest_skin, "media")
    if not os.path.isdir(dest_skin):
        _log(f"WARN: {dest_skin} not found — skip")
        return 0
    if not os.path.isdir(estuary_media):
        _log(f"WARN: {estuary_media} not found")
        return 0
    names = sorted(n for n in os.listdir(estuary_media) if n.endswith(".xbt"))
    if not names:
        _log(f"WARN: no .xbt in {estuary_media}")
        return 0
    os.makedirs(dest_media, exist_ok=True)
    copied = 0
    for name in names:
        src = os.path.join(estuary_media, name)
        dst = os.path.join(dest_media, name)
        shutil.copy2(src, dst)
        _log(f"copied {src} -> {dst} ({os.path.getsize(dst)} bytes)")
        copied += 1
    return copied


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    total = 0
    for d in sys.argv[1:]:
        d = os.path.abspath(d)
        if not os.path.isdir(d):
            _log(f"ERROR: not a directory: {d}")
            return 2
        total += copy_packed_textures(d)
    if total == 0:
        _log("ERROR: copied 0 .xbt files — skin.husham.play would ship without textures")
        return 2
    _log(f"copy-skin-textures: {total} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
