# -*- coding: utf-8 -*-
"""First-run / on-demand setup wizard for Husham Play."""
from __future__ import annotations

import json
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon('plugin.program.husham')
NOTICE = (
    'Husham Play provides no content. '
    'Only use services and media you have the right to access.'
)
PVR_ID = 'pvr.iptvsimple'

# Big, plain-English choices shown on first run (and from Favourites).
CHOICE_XTREAM = 0
CHOICE_M3U = 1
CHOICE_VIDEOS = 2
CHOICE_SKIP = 3

SETUP_CHOICES = [
    'I have an Xtream login\n'
    'Type the server, username and password your IPTV provider gave you.',
    'I have a playlist (M3U) link\n'
    'Paste the M3U URL you already have (TV guide URL is optional).',
    'I want to play my own videos\n'
    'Pick a folder on this device, a USB stick, or a network share.',
    'Skip for now\n'
    'You can open this setup again any time from Favourites.',
]


def _userdata(*parts):
    return xbmcvfs.translatePath(os.path.join('special://profile', *parts))


def _ensure_dir(path):
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdirs(path)


def _set_addon_setting(addon_id, key, value):
    try:
        xbmcaddon.Addon(addon_id).setSetting(key, str(value))
        return True
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard: setSetting %s.%s failed: %s' % (addon_id, key, exc), xbmc.LOGWARNING)
        return False


def _enable_addon(addon_id):
    try:
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': addon_id, 'enabled': True},
        }))
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard: enable %s failed: %s' % (addon_id, exc), xbmc.LOGWARNING)


def _write_iptv_instance(m3u_url, epg_url=''):
    """Write IPTV Simple instance settings (Omega multi-instance style) and enable PVR."""
    _enable_addon(PVR_ID)
    # Global-ish settings used by older and newer IPTV Simple
    _set_addon_setting(PVR_ID, 'm3uPathType', '1')  # remote URL
    _set_addon_setting(PVR_ID, 'm3uUrl', m3u_url)
    _set_addon_setting(PVR_ID, 'epgPathType', '1' if epg_url else '0')
    if epg_url:
        _set_addon_setting(PVR_ID, 'epgUrl', epg_url)
    # Also write instance settings file used by IPTV Simple 20+/21+
    inst_dir = _userdata('addon_data', PVR_ID)
    _ensure_dir(inst_dir)
    # Minimal instance XML — IPTV Simple reads instance-settings-N.xml
    xml = [
        '<?xml version=\'1.0\' encoding=\'UTF-8\'?>',
        '<settings version="2">',
        '    <setting id="m3uPathType">1</setting>',
        '    <setting id="m3uUrl">%s</setting>' % _xml_escape(m3u_url),
        '    <setting id="epgPathType">%s</setting>' % ('1' if epg_url else '0'),
    ]
    if epg_url:
        xml.append('    <setting id="epgUrl">%s</setting>' % _xml_escape(epg_url))
    xml.append('</settings>')
    path = os.path.join(inst_dir, 'instance-settings-1.xml')
    with xbmcvfs.File(path, 'w') as fh:
        fh.write('\n'.join(xml) + '\n')
    # Nudge PVR to reload
    xbmc.executebuiltin('PVR.UpdateAndRecordings')
    xbmcgui.Dialog().notification(
        'Husham Play',
        'Playlist saved. Open Live TV after a moment.',
        xbmcgui.NOTIFICATION_INFO,
        5000,
    )


def _xml_escape(value):
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def _normalize_xtream_server(server):
    server = (server or '').strip().rstrip('/')
    if not server:
        return ''
    if not server.startswith('http://') and not server.startswith('https://'):
        server = 'http://' + server
    return server


def wizard_xtream():
    dialog = xbmcgui.Dialog()
    dialog.ok(
        'Xtream login',
        'You need three things from your IPTV provider:\n'
        '1) Server address (like http://example.com:8080)\n'
        '2) Username\n'
        '3) Password\n\n'
        + NOTICE,
    )
    server = dialog.input('1/3 Server address (host:port or full URL)', type=xbmcgui.INPUT_ALPHANUM)
    if not server:
        return
    username = dialog.input('2/3 Username', type=xbmcgui.INPUT_ALPHANUM)
    if not username:
        return
    password = dialog.input('3/3 Password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if not password:
        return
    base = _normalize_xtream_server(server)
    m3u = '%s/get.php?username=%s&password=%s&type=m3u_plus' % (base, username, password)
    epg = '%s/xmltv.php?username=%s&password=%s' % (base, username, password)
    _write_iptv_instance(m3u, epg)
    dialog.ok(
        'Done',
        'Your Xtream login was saved.\n'
        'Open Live TV from the home screen in a moment.\n'
        'Nothing is bundled — this is your own account.',
    )


def wizard_m3u():
    dialog = xbmcgui.Dialog()
    dialog.ok(
        'Playlist (M3U) link',
        'Paste the full M3U link your provider gave you.\n'
        'You can add a TV guide (EPG) link too, or leave it blank.\n\n'
        + NOTICE,
    )
    m3u = dialog.input('M3U playlist URL', type=xbmcgui.INPUT_ALPHANUM)
    if not m3u:
        return
    epg = dialog.input('TV guide URL (optional — leave blank to skip)', type=xbmcgui.INPUT_ALPHANUM)
    _write_iptv_instance(m3u.strip(), (epg or '').strip())
    dialog.ok('Done', 'Playlist saved. Open Live TV from the home screen in a moment.')


def wizard_videos():
    dialog = xbmcgui.Dialog()
    dialog.ok(
        'My own videos',
        'Pick a folder of videos you own or have rights to play.\n'
        'This can be on this device, a USB stick, or a network share.\n\n'
        + NOTICE,
    )
    name = dialog.input('Name for this folder (e.g. My Movies)', type=xbmcgui.INPUT_ALPHANUM)
    if not name:
        name = 'My Videos'
    path = dialog.browse(0, 'Select folder, USB or network share', 'video', '', False, False, '')
    if not path:
        return
    sources_path = _userdata('sources.xml')
    try:
        import xml.etree.ElementTree as ET
        if xbmcvfs.exists(sources_path):
            tree = ET.parse(sources_path)
            root = tree.getroot()
        else:
            root = ET.Element('sources')
            tree = ET.ElementTree(root)
        video = root.find('video')
        if video is None:
            video = ET.SubElement(root, 'video')
            ET.SubElement(video, 'default', pathversion='1')
        src = ET.SubElement(video, 'source')
        n = ET.SubElement(src, 'name'); n.text = name
        pth = ET.SubElement(src, 'path', pathversion='1'); pth.text = path
        ET.SubElement(src, 'allowsharing').text = 'true'
        _ensure_dir(_userdata())
        tree.write(sources_path, encoding='utf-8', xml_declaration=True)
        dialog.ok('Done', '"%s" was added.\nOpen Videos → Files to browse it.' % name)
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard sources.xml write failed: %s' % exc, xbmc.LOGERROR)
        dialog.ok(
            'Add folder manually',
            'Could not save automatically.\n'
            'Open Videos → Files → Add videos… and choose:\n%s' % path,
        )
    xbmc.executebuiltin('ActivateWindow(Videos,sources://video/,return)')


def _mark_first_run_done(skipped=False):
    try:
        ADDON.setSettingBool('first_run_done', True)
        if skipped:
            ADDON.setSettingBool('wizard_skipped', True)
    except Exception:
        ADDON.setSetting('first_run_done', 'true')
        if skipped:
            ADDON.setSetting('wizard_skipped', 'true')


def run_wizard(force=False):
    dialog = xbmcgui.Dialog()
    dialog.ok(
        'Welcome to Husham Play',
        'This setup helps you add your own content.\n\n'
        + NOTICE
        + '\n\nTap OK, then pick one of the three options (or Skip).',
    )
    choice = dialog.select('Husham Play setup', SETUP_CHOICES)
    if choice == CHOICE_XTREAM:
        wizard_xtream()
    elif choice == CHOICE_M3U:
        wizard_m3u()
    elif choice == CHOICE_VIDEOS:
        wizard_videos()
    elif choice == CHOICE_SKIP:
        _mark_first_run_done(skipped=True)
        return
    else:
        # User backed out of the list — treat like skip so we do not loop forever.
        _mark_first_run_done(skipped=True)
        return
    _mark_first_run_done(skipped=False)
