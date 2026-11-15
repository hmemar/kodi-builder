#!/usr/bin/env python3
"""Fork Estuary into skin.husham.play with Husham Play branding.

Usage: brand-skin.py <kodi-src> <kodi-config-dir>
"""
from __future__ import annotations

import base64
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

SKIN_ID = "skin.husham.play"
SKIN_NAME = "Husham Play"
# Brand colours from icon: navy #0F1738, orange #FF5E3A.
# dialog_tint must CONTRAST with primary_background / the navy wallpaper.
# Stock Estuary uses FF1A2123 (charcoal) on a teal wallpaper; 1.5 used the
# same navy for both, so once textures are present the OK dialog panel would
# still vanish into the home background.
COLORS = {
    "primary_background": "FF0F1738",
    "secondary_background": "33FF5E3A",
    "dialog_tint": "FF1A2123",
    "button_focus": "FFFF5E3A",
    "button_alt_focus": "80FF5E3A",
    "selected": "FFFF5E3A",
    "blue": "FFFF5E3A",
}


def _log(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)

def _ensure_asset(cfg: str, name: str) -> str:
    """Return path to asset, decoding .b64 sibling if needed."""
    path = os.path.join(cfg, name)
    b64 = path + ".b64"
    if not os.path.isfile(path) and os.path.isfile(b64):
        open(path, "wb").write(base64.b64decode(open(b64, "rb").read()))
    return path




def fork_estuary(src: str) -> str:
    estuary = os.path.join(src, "addons", "skin.estuary")
    dest = os.path.join(src, "addons", SKIN_ID)
    if not os.path.isdir(estuary):
        raise SystemExit(f"skin.estuary not found at {estuary}")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(estuary, dest)
    _log(f"copied Estuary -> {SKIN_ID}")
    return dest


def rewrite_addon_xml(skin_dir: str) -> None:
    path = os.path.join(skin_dir, "addon.xml")
    text = open(path, encoding="utf-8").read()
    text = text.replace('id="skin.estuary"', f'id="{SKIN_ID}"')
    text = re.sub(r'name="Estuary"', f'name="{SKIN_NAME}"', text, count=1)
    # Keep phil65 credit; clarify fork
    text = text.replace(
        'provider-name="phil65, Ichabod Fletchman"',
        'provider-name="Husham Play (fork of Estuary by phil65, Ichabod Fletchman)"',
    )
    # Summaries: replace default-skin claims lightly in en_GB if present
    text = re.sub(
        r'(<summary lang="en_GB">)[^<]+',
        rf'\1{SKIN_NAME} skin - based on Estuary (GPL / CC BY-SA). Not affiliated with the Kodi Foundation.',
        text,
        count=1,
    )
    # Ensure licence line mentions Estuary
    if "Estuary" not in text.split("<license>")[1].split("</license>")[0] if "<license>" in text else "":
        text = text.replace(
            "<license>CC BY-SA 4.0, GNU GENERAL PUBLIC LICENSE Version 2.0</license>",
            "<license>CC BY-SA 4.0, GNU GENERAL PUBLIC LICENSE Version 2.0 - based on Estuary</license>",
        )
    open(path, "w", encoding="utf-8").write(text)
    _log("addon.xml rewritten")


def patch_colors(skin_dir: str) -> None:
    path = os.path.join(skin_dir, "colors", "defaults.xml")
    if not os.path.isfile(path):
        _log("no colors/defaults.xml")
        return
    text = open(path, encoding="utf-8").read()
    for name, value in COLORS.items():
        text = re.sub(
            rf'(<color name="{name}">)[^<]+',
            rf"\g<1>{value}",
            text,
        )
    open(path, "w", encoding="utf-8").write(text)
    _log("colors patched")


def replace_media(skin_dir: str, cfg: str) -> None:
    wallpaper = _ensure_asset(cfg, "skin-wallpaper.jpg")
    fanart = _ensure_asset(cfg, "skin-fanart.jpg")
    logo = _ensure_asset(cfg, "skin-home-logo.png")
    icon = _ensure_asset(cfg, "icon.png")
    # Backgrounds
    bg_dir = os.path.join(skin_dir, "extras", "backgrounds")
    if os.path.isdir(bg_dir) and os.path.isfile(wallpaper):
        shutil.copy(wallpaper, os.path.join(bg_dir, "primary.jpg"))
        # Replace other patterns with the same wallpaper for a consistent look
        for name in os.listdir(bg_dir):
            if name.endswith(".jpg") and name != "primary.jpg":
                shutil.copy(wallpaper, os.path.join(bg_dir, name))
        _log("backgrounds replaced")
    res = os.path.join(skin_dir, "resources")
    if os.path.isdir(res):
        if os.path.isfile(fanart):
            shutil.copy(fanart, os.path.join(res, "fanart.jpg"))
        if os.path.isfile(icon):
            shutil.copy(icon, os.path.join(res, "icon.png"))
        _log("resources icon/fanart replaced")
    # Home logo used via vendor_logo already; also drop into extras
    extras = os.path.join(skin_dir, "extras")
    os.makedirs(extras, exist_ok=True)
    if os.path.isfile(logo):
        shutil.copy(logo, os.path.join(extras, "husham-logo.png"))
        _log("home logo staged")


def patch_home_logo(skin_dir: str) -> None:
    """Point Home vendor logo texture at our logo; add favourites-focused note via Includes if needed."""
    home = os.path.join(skin_dir, "xml", "Home.xml")
    if not os.path.isfile(home):
        return
    text = open(home, encoding="utf-8").read()
    # Prefer our extras logo over xbmc vendor_logo where referenced
    text2 = text.replace(
        "special://xbmc/media/vendor_logo.png",
        "special://skin/extras/husham-logo.png",
    )
    if text2 != text:
        open(home, "w", encoding="utf-8").write(text2)
        _log("Home.xml logo path updated")
    else:
        _log("Home.xml had no vendor_logo reference to patch")


def register_skin(src: str) -> None:
    inst = os.path.join(src, "cmake", "installdata", "common", "addons.txt")
    man = os.path.join(src, "system", "addon-manifest.xml")
    entry = f"addons/{SKIN_ID}/*"
    if os.path.isfile(inst) and entry not in open(inst, encoding="utf-8").read():
        with open(inst, "a", encoding="utf-8") as fh:
            fh.write(f"\n{entry}\n")
    if os.path.isfile(man):
        text = open(man, encoding="utf-8").read()
        if f"<addon>{SKIN_ID}</addon>" not in text:
            # Keep estuary too (dependency/fallback); enable our skin
            text = text.replace("</addons>", f"  <addon>{SKIN_ID}</addon>\n</addons>")
            open(man, "w", encoding="utf-8").write(text)
    # Default skin setting
    settings = os.path.join(src, "system", "settings", "settings.xml")
    if os.path.isfile(settings):
        s = open(settings, encoding="utf-8").read()
        s2 = re.sub(
            r'(<setting id="lookandfeel\.skin"[^>]*>\s*<level>[^<]+</level>\s*<default>)[^<]+',
            rf"\1{SKIN_ID}",
            s,
            count=1,
            flags=re.S,
        )
        if s2 == s:
            # try simpler default line
            s2 = s.replace(
                "<default>skin.estuary</default>",
                f"<default>{SKIN_ID}</default>",
            )
        open(settings, "w", encoding="utf-8").write(s2)
        _log(f"default skin -> {SKIN_ID}")


SETUP_ITEM = """						<!-- HUSHAM_SETUP_MENU -->
						<item>
							<label>Setup</label>
							<onclick>RunPlugin(plugin://plugin.program.husham/?action=wizard)</onclick>
							<property name="menu_id">$NUMBER[22000]</property>
							<thumb>icons/sidemenu/addons.png</thumb>
							<property name="id">hushamsetup</property>
						</item>
"""

SETUP_PANEL = """				<!-- HUSHAM_SETUP_PANEL -->
				<control type="group" id="22000">
					<visible>String.IsEqual(Container(9000).ListItem.Property(id),hushamsetup)</visible>
					<include content="Visible_Right_Delayed">
						<param name="id" value="hushamsetup"/>
					</include>
					<include content="ImageWidget">
						<param name="text_label" value="Add your own content: an Xtream login, an M3U playlist link, or a folder of videos you have the right to play. Husham Play provides no content." />
						<param name="button_label" value="Open setup" />
						<param name="button_onclick" value="RunPlugin(plugin://plugin.program.husham/?action=wizard)"/>
						<param name="button_id" value="22100"/>
						<param name="visible" value="true"/>
						<param name="button2_label" value="Open Husham menu"/>
						<param name="button2_onclick" value="ActivateWindow(Programs,plugin://plugin.program.husham/,return)"/>
					</include>
				</control>
"""


def add_home_setup_item(skin_dir: str) -> None:
    """Put a visible Setup item at the top of the Estuary home menu.

    1.5 only exposed the wizard under Favourites, so it was easy to miss on
    a TV. Also contrast the focused vs unfocused menu labels so the
    selection is obvious at sofa distance once lists/focus.png is packed.
    """
    home = os.path.join(skin_dir, "xml", "Home.xml")
    if not os.path.isfile(home):
        return
    text = open(home, encoding="utf-8").read()
    changed = False

    if "<!-- HUSHAM_SETUP_MENU -->" not in text:
        # First item in the main menu list (id 9000) is Movies ($LOCALIZE[342]).
        needle = "\t\t\t\t\t<content>\n\t\t\t\t\t\t<item>\n\t\t\t\t\t\t\t<label>$LOCALIZE[342]</label>"
        if needle not in text:
            # Fall back to a looser match
            needle = "<content>\n\t\t\t\t\t\t<item>\n\t\t\t\t\t\t\t<label>$LOCALIZE[342]</label>"
            repl = "<content>\n" + SETUP_ITEM + "\t\t\t\t\t\t<item>\n\t\t\t\t\t\t\t<label>$LOCALIZE[342]</label>"
        else:
            repl = "\t\t\t\t\t<content>\n" + SETUP_ITEM + "\t\t\t\t\t\t<item>\n\t\t\t\t\t\t\t<label>$LOCALIZE[342]</label>"
        if needle not in text:
            _log("WARN: Home.xml movies item not found — Setup menu item not inserted")
        else:
            text = text.replace(needle, repl, 1)
            changed = True
            _log("Home.xml Setup menu item inserted")

    if "<!-- HUSHAM_SETUP_PANEL -->" not in text:
        # Insert the right-hand panel just before the left menu ContentPanel group.
        anchor = "\t\t\t<control type=\"group\">\n\t\t\t\t<depth>DepthContentPanel</depth>"
        if anchor not in text:
            _log("WARN: Home.xml ContentPanel group not found — Setup panel not inserted")
        else:
            text = text.replace(anchor, SETUP_PANEL + anchor, 1)
            changed = True
            _log("Home.xml Setup widget panel inserted")

    # Focused label stays bright white; unfocused items go grey so the
    # current item is obvious even if the orange focus texture is faint.
    unfocused_label = """\t\t\t\t\t\t<control type="label">
\t\t\t\t\t\t\t<left>104</left>
\t\t\t\t\t\t\t<top>0</top>
\t\t\t\t\t\t\t<height>95</height>
\t\t\t\t\t\t\t<width>560</width>
\t\t\t\t\t\t\t<aligny>center</aligny>
\t\t\t\t\t\t\t<font>font37</font>
\t\t\t\t\t\t\t<label>$INFO[ListItem.Label]</label>
\t\t\t\t\t\t\t<shadowcolor>text_shadow</shadowcolor>
\t\t\t\t\t\t</control>
\t\t\t\t\t</itemlayout>"""
    unfocused_repl = """\t\t\t\t\t\t<control type="label">
\t\t\t\t\t\t\t<left>104</left>
\t\t\t\t\t\t\t<top>0</top>
\t\t\t\t\t\t\t<height>95</height>
\t\t\t\t\t\t\t<width>560</width>
\t\t\t\t\t\t\t<aligny>center</aligny>
\t\t\t\t\t\t\t<font>font37</font>
\t\t\t\t\t\t\t<textcolor>grey</textcolor>
\t\t\t\t\t\t\t<label>$INFO[ListItem.Label]</label>
\t\t\t\t\t\t\t<shadowcolor>text_shadow</shadowcolor>
\t\t\t\t\t\t</control>
\t\t\t\t\t</itemlayout>"""
    if "<textcolor>grey</textcolor>" not in text and unfocused_label in text:
        text = text.replace(unfocused_label, unfocused_repl, 1)
        changed = True
        _log("Home.xml unfocused menu labels set to grey")

    focused_label = """\t\t\t\t\t\t<control type="label">
\t\t\t\t\t\t\t<left>104</left>
\t\t\t\t\t\t\t<top>0</top>
\t\t\t\t\t\t\t<height>95</height>
\t\t\t\t\t\t\t<width>560</width>
\t\t\t\t\t\t\t<aligny>center</aligny>
\t\t\t\t\t\t\t<font>font37</font>
\t\t\t\t\t\t\t<label>$INFO[ListItem.Label]</label>
\t\t\t\t\t\t\t<shadowcolor>text_shadow</shadowcolor>
\t\t\t\t\t\t</control>
\t\t\t\t\t</focusedlayout>"""
    focused_repl = """\t\t\t\t\t\t<control type="label">
\t\t\t\t\t\t\t<left>104</left>
\t\t\t\t\t\t\t<top>0</top>
\t\t\t\t\t\t\t<height>95</height>
\t\t\t\t\t\t\t<width>560</width>
\t\t\t\t\t\t\t<aligny>center</aligny>
\t\t\t\t\t\t\t<font>font37</font>
\t\t\t\t\t\t\t<textcolor>white</textcolor>
\t\t\t\t\t\t\t<label>$INFO[ListItem.Label]</label>
\t\t\t\t\t\t\t<shadowcolor>text_shadow</shadowcolor>
\t\t\t\t\t\t</control>
\t\t\t\t\t</focusedlayout>"""
    if "<textcolor>white</textcolor>" not in text and focused_label in text:
        text = text.replace(focused_label, focused_repl, 1)
        changed = True
        _log("Home.xml focused menu labels set to white")

    if changed:
        open(home, "w", encoding="utf-8").write(text)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, cfg = sys.argv[1], sys.argv[2]
    skin_dir = fork_estuary(src)
    rewrite_addon_xml(skin_dir)
    patch_colors(skin_dir)
    replace_media(skin_dir, cfg)
    patch_home_logo(skin_dir)
    add_home_setup_item(skin_dir)
    register_skin(src)
    _log("skin branding done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
