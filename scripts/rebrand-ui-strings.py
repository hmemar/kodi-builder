#!/usr/bin/env python3
"""Replace user-visible 'Kodi' with 'Husham Play' in UI language / metadata / skin XML.

Usage: rebrand-ui-strings.py <kodi-src>

Patches:
  - all **/strings.po (core, skins, add-ons)
  - addon.xml / addon.xml.in summary/description/disclaimer/name
  - skin and dialog XML label attributes / text that mention Kodi

Keeps Kodi for legal credits (Foundation, Team Kodi, Translation Team,
open-source Kodi project, kodi.tv URLs, LICENSE files).

Does NOT touch: LICENSE/COPYING, C/C++/headers, JSON-RPC, lib names,
package IDs, or binary add-on IDs.
"""
from __future__ import annotations

import os
import re
import sys

DISPLAY = "Husham Play"

PROTECT = [
    ("Kodi Foundation", "\x00KF\x00"),
    ("Team Kodi", "\x00TK\x00"),
    ("Kodi Translation Team", "\x00KTT\x00"),
    ("open-source Kodi project", "\x00OSKP\x00"),
    ("open source Kodi project", "\x00OSKP2\x00"),
    ("XBMC Foundation", "\x00XF\x00"),
]

URL_PROTECT = [
    (re.compile(r"https?://[^\s\"<>]*kodi[^\s\"<>]*", re.I), "\x00URL%d\x00"),
    (re.compile(r"\b(?:forum\.)?kodi\.(?:tv|wiki)\b", re.I), "\x00HOST%d\x00"),
]

KODI_WORD = re.compile(r"\bKodi\b")
KODI_POSSESSIVE = re.compile(r"\bKodi's\b")
EN_LANG = re.compile(r"resource\.language\.en_[a-z]{2}", re.I)
XML_TEXT_TAGS = ("summary", "description", "disclaimer", "name", "news")


def _protect(s: str) -> tuple[str, list[tuple[str, str]]]:
    saved: list[tuple[str, str]] = []
    for src, tok in PROTECT:
        if src in s:
            s = s.replace(src, tok)
            saved.append((tok, src))
    n = 0
    for rx, tmpl in URL_PROTECT:
        def repl(m, _tmpl=tmpl, _n=[n]):
            tok = _tmpl % _n[0]
            _n[0] += 1
            saved.append((tok, m.group(0)))
            return tok
        s = rx.sub(repl, s)
        n = len(saved)
    return s, saved


def _restore(s: str, saved: list[tuple[str, str]]) -> str:
    for tok, src in saved:
        s = s.replace(tok, src)
    return s


def replace_visible_kodi(s: str) -> str:
    s, saved = _protect(s)
    s = KODI_POSSESSIVE.sub(DISPLAY + "'s", s)
    s = KODI_WORD.sub(DISPLAY, s)
    return _restore(s, saved)


def patch_po(path: str) -> tuple[int, int]:
    original = open(path, encoding="utf-8", errors="replace").read()
    is_en = bool(EN_LANG.search(path.replace("\\", "/")))
    if "/resource.language.en_" in path.replace("\\", "/"):
        is_en = True

    out: list[str] = []
    in_msgid = False
    in_msgstr = False

    for line in original.splitlines(keepends=True):
        if line.startswith("msgid "):
            in_msgid, in_msgstr = True, False
        elif line.startswith("msgstr "):
            in_msgid, in_msgstr = False, True
        elif line.startswith("msgctxt "):
            in_msgid, in_msgstr = False, False
        elif line.startswith("#") or (line.strip() == "" and not (in_msgid or in_msgstr)):
            in_msgid = in_msgstr = False

        do = False
        if in_msgstr and (line.startswith("msgstr ") or line.startswith('"')):
            do = True
        elif is_en and in_msgid and (line.startswith("msgid ") or line.startswith('"')):
            do = True
        elif line.startswith("#.") and KODI_WORD.search(line):
            do = True

        if do and (KODI_WORD.search(line) or KODI_POSSESSIVE.search(line)):
            line = replace_visible_kodi(line)
        out.append(line)

    text = "".join(out)
    if text != original:
        open(path, "w", encoding="utf-8", newline="\n").write(text)
        before = len(KODI_WORD.findall(original)) + len(KODI_POSSESSIVE.findall(original))
        after = len(KODI_WORD.findall(text)) + len(KODI_POSSESSIVE.findall(text))
        return max(0, before - after), 1
    return 0, 0


def patch_addon_xml(path: str) -> tuple[int, int]:
    original = open(path, encoding="utf-8", errors="replace").read()
    text = original

    def repl_tag(m: re.Match) -> str:
        inner = m.group(2)
        if not (KODI_WORD.search(inner) or KODI_POSSESSIVE.search(inner)):
            return m.group(0)
        return m.group(1) + replace_visible_kodi(inner) + m.group(3)

    for tag in XML_TEXT_TAGS:
        text = re.sub(
            rf"(<{tag}\b[^>]*>)(.*?)(</{tag}>)",
            repl_tag,
            text,
            flags=re.I | re.S,
        )
    if text != original:
        open(path, "w", encoding="utf-8", newline="\n").write(text)
        before = len(KODI_WORD.findall(original))
        after = len(KODI_WORD.findall(text))
        return max(0, before - after), 1
    return 0, 0


def patch_gui_xml(path: str) -> tuple[int, int]:
    original = open(path, encoding="utf-8", errors="replace").read()
    if not (KODI_WORD.search(original) or KODI_POSSESSIVE.search(original)):
        return 0, 0
    text = original

    def repl_attr(m: re.Match) -> str:
        val = m.group(3)
        if not (KODI_WORD.search(val) or KODI_POSSESSIVE.search(val)):
            return m.group(0)
        return m.group(1) + m.group(2) + replace_visible_kodi(val) + m.group(2)

    for attr in ("label", "label2", "description", "value", "tooltip"):
        text = re.sub(
            rf'({attr}\s*=\s*)([\'"])(.*?)\2',
            repl_attr,
            text,
            flags=re.I | re.S,
        )

    def repl_tag(m: re.Match) -> str:
        inner = m.group(2)
        if not (KODI_WORD.search(inner) or KODI_POSSESSIVE.search(inner)):
            return m.group(0)
        return m.group(1) + replace_visible_kodi(inner) + m.group(3)

    for tag in ("label", "label2", "description"):
        text = re.sub(
            rf"(<{tag}\b[^>]*>)([^<]*)(</{tag}>)",
            repl_tag,
            text,
            flags=re.I,
        )

    if text != original:
        open(path, "w", encoding="utf-8", newline="\n").write(text)
        before = len(KODI_WORD.findall(original)) + len(KODI_POSSESSIVE.findall(original))
        after = len(KODI_WORD.findall(text)) + len(KODI_POSSESSIVE.findall(text))
        return max(0, before - after), 1
    return 0, 0


def should_skip(path: str) -> bool:
    norm = path.replace("\\", "/").lower()
    base = os.path.basename(norm)
    if base in {"copying", "license", "license.txt", "license.md", "copying.txt", "gpl.txt"}:
        return True
    if "/licenses/" in norm:
        return True
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    po_files = xml_files = gui_files = 0
    po_repl = xml_repl = gui_repl = 0
    po_changed = xml_changed = gui_changed = 0

    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            if should_skip(path):
                continue
            norm = path.replace("\\", "/")
            if fn == "strings.po":
                r, c = patch_po(path)
                po_files += 1
                po_repl += r
                po_changed += c
            elif fn in ("addon.xml", "addon.xml.in"):
                r, c = patch_addon_xml(path)
                xml_files += 1
                xml_repl += r
                xml_changed += c
            elif fn.endswith(".xml") and (
                "/addons/skin." in norm
                or "/xbmc/dialogs/" in norm
                or "/xbmc/window/" in norm
                or "/guilib/" in norm
            ):
                # Skin XML + a few GUI XML templates under source
                r, c = patch_gui_xml(path)
                gui_files += 1
                gui_repl += r
                gui_changed += c

    msg = (
        f"rebrand-ui-strings: scanned {po_files} strings.po ({po_changed} changed, ~{po_repl} Kodi->{DISPLAY}), "
        f"{xml_files} addon.xml ({xml_changed} changed, ~{xml_repl}), "
        f"{gui_files} gui/skin xml ({gui_changed} changed, ~{gui_repl})"
    )
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
