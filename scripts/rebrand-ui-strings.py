#!/usr/bin/env python3
"""Replace user-visible 'Kodi' with 'Husham Play' in UI language / metadata files.

Usage: rebrand-ui-strings.py <kodi-src>

Patches:
  - all **/strings.po under the source tree (core, skins, add-ons)
  - addon.xml / addon.xml.in summary/description/disclaimer/name text that mentions Kodi

Keeps Kodi where credit / attribution / legal identity is required, e.g.:
  Kodi Foundation, Team Kodi, Kodi Translation Team, open-source Kodi project,
  kodi.tv / kodi.wiki / forum.kodi URLs, SPDX/copyright headers that name Team Kodi.

Does NOT touch: LICENSE/COPYING files, C/C++/headers, JSON-RPC schemas, lib names,
package IDs, or binary add-on IDs.
"""
from __future__ import annotations

import os
import re
import sys

DISPLAY = "Husham Play"

# Phrases that must keep the word Kodi (placeholders must not contain \bKodi\b).
PROTECT = [
    ("Kodi Foundation", "\x00KF\x00"),
    ("Team Kodi", "\x00TK\x00"),
    ("Kodi Translation Team", "\x00KTT\x00"),
    ("open-source Kodi project", "\x00OSKP\x00"),
    ("open source Kodi project", "\x00OSKP2\x00"),
    ("XBMC Foundation", "\x00XF\x00"),  # unrelated but leave intact near credits
]

# URL / host forms — protect before word replace.
URL_PROTECT = [
    (re.compile(r"https?://[^\s\"<>]*kodi[^\s\"<>]*", re.I), "\x00URL%d\x00"),
    (re.compile(r"\b(?:forum\.)?kodi\.(?:tv|wiki)\b", re.I), "\x00HOST%d\x00"),
]

KODI_WORD = re.compile(r"\bKodi\b")
KODI_POSSESSIVE = re.compile(r"\bKodi's\b")

# Lines in .po / xml we rewrite.
PO_LINE = re.compile(
    r'^(\s*(?:msgid|msgstr|msgctxt)\s+|")(.*)$'
)
# Only rewrite msgid for English packs (source language shown as fallback).
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
    """Return (replacements, changed_flag)."""
    original = open(path, encoding="utf-8", errors="replace").read()
    is_en = bool(EN_LANG.search(path.replace("\\", "/"))) or path.replace("\\", "/").endswith(
        "/resource.language.en_gb/resources/strings.po"
    )
    # Also treat generic en_gb path under skins
    if "/resource.language.en_" in path.replace("\\", "/"):
        is_en = True

    out: list[str] = []
    replacements = 0
    in_msgid = False
    in_msgstr = False

    for line in original.splitlines(keepends=True):
        raw = line
        # Track which field we are in
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
        # Developer comments that mention Kodi in help — optional polish
        elif line.startswith("#.") and KODI_WORD.search(line):
            do = True

        if do and (KODI_WORD.search(line) or KODI_POSSESSIVE.search(line)):
            new = replace_visible_kodi(line)
            if new != line:
                replacements += len(KODI_WORD.findall(line)) + len(KODI_POSSESSIVE.findall(line))
                # recount after protect is hard; just count word hits before
                replacements = replacements  # noqa: keep simple
                line = new
        out.append(line)

    text = "".join(out)
    # Recount properly
    # Compare unprotected visible... simpler recount via before/after on msgstr only
    if text != original:
        open(path, "w", encoding="utf-8", newline="\n").write(text)
        # Count remaining vs original for reporting
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
    # provider-name="Team Kodi" must stay — protected inside replace if we hit attributes
    # Also rewrite plain >Kodi< label leftovers carefully
    if text != original:
        open(path, "w", encoding="utf-8", newline="\n").write(text)
        before = len(KODI_WORD.findall(original))
        after = len(KODI_WORD.findall(text))
        return max(0, before - after), 1
    return 0, 0


def should_skip(path: str) -> bool:
    norm = path.replace("\\", "/").lower()
    base = os.path.basename(norm)
    if base in {"copying", "license", "license.txt", "license.md", "copying.txt", "gpl.txt"}:
        return True
    if "/licenses/" in norm or norm.endswith(".md") and "license" in base:
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

    po_files = 0
    xml_files = 0
    po_repl = 0
    xml_repl = 0
    po_changed = 0
    xml_changed = 0

    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            if should_skip(path):
                continue
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

    print(
        f"rebrand-ui-strings: scanned {po_files} strings.po ({po_changed} changed, ~{po_repl} Kodi→{DISPLAY}), "
        f"{xml_files} addon.xml ({xml_changed} changed, ~{xml_repl} replacements)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
