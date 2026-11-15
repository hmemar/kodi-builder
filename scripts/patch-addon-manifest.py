#!/usr/bin/env python3
"""Normalize addon-manifest.xml for Husham Play.

- Ensure plugin.program.husham and skin.husham.play are registered (enabled).
- Register pvr.iptvsimple as optional="true" so PVR Manager does not start
  with an empty playlist (the 1.5 "PVR manager is starting up: 0%" banner).
  The setup wizard enables it after the user adds an M3U / Xtream login.

Usage: patch-addon-manifest.py <addon-manifest.xml> [<addon-manifest.xml> ...]
"""
from __future__ import annotations

import os
import re
import sys

ENABLED = ("plugin.program.husham", "skin.husham.play")
OPTIONAL = ("pvr.iptvsimple",)

ADDON_RE = re.compile(
    r"[ \t]*<addon(?:\s+optional=\"(?:true|false)\")?>([^<]+)</addon>\s*",
    re.I,
)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _tag(addon_id: str, optional: bool) -> str:
    if optional:
        return f'  <addon optional="true">{addon_id}</addon>\n'
    return f"  <addon>{addon_id}</addon>\n"


def patch(path: str) -> bool:
    original = open(path, encoding="utf-8").read()
    # Drop any existing entries for the add-ons we manage, then re-insert
    # in a consistent form just before </addons>.
    managed = set(ENABLED) | set(OPTIONAL)
    text = original

    def drop(m: re.Match) -> str:
        return "" if m.group(1) in managed else m.group(0)

    text = ADDON_RE.sub(drop, text)
    if "</addons>" not in text:
        _log(f"WARN: no </addons> in {path}")
        return False
    block = "".join(_tag(i, optional=False) for i in ENABLED)
    block += "".join(_tag(i, optional=True) for i in OPTIONAL)
    text = text.replace("</addons>", block + "</addons>")
    # Collapse leftover blank lines from dropped tags (cosmetic)
    text = re.sub(r"\n{3,}", "\n", text)
    if text != original:
        open(path, "w", encoding="utf-8").write(text)
        _log(f"patched {path}")
        return True
    _log(f"unchanged {path}")
    return False


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    for p in sys.argv[1:]:
        if not os.path.isfile(p):
            _log(f"ERROR: not a file: {p}")
            return 2
        patch(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
