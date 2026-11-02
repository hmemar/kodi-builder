# -*- coding: utf-8 -*-
"""First-run / on-demand setup wizard for Husham Play."""
from __future__ import annotations

import json
import os
import urllib.parse

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
INPUTSTREAM_DEPS = (
    'inputstream.ffmpegdirect',
    'inputstream.adaptive',
    'inputstream.rtmp',
)

CHOICE_XTREAM = 0
CHOICE_M3U = 1
CHOICE_VIDEOS = 2
CHOICE_SKIP = 3

# Short labels only — Estuary's select dialog mangles multiline items.
SETUP_CHOICES = [
    'I have an Xtream login',
    'I have a playlist (M3U) link',
    'I want to play my own videos',
    'Skip for now',
]


def _userdata(*parts):
    return xbmcvfs.translatePath(os.path.join('special://profile', *parts))


def _ensure_dir(path):
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdirs(path)


def _enable_addon(addon_id):
    try:
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': addon_id, 'enabled': True},
        }))
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard: enable %s failed: %s' % (addon_id, exc), xbmc.LOGWARNING)


def _disable_addon(addon_id):
    try:
        xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': addon_id, 'enabled': False},
        }))
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard: disable %s failed: %s' % (addon_id, exc), xbmc.LOGWARNING)


def _xml_escape(value):
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def _write_text(path, text):
    # xbmcvfs.File write expects str on Py3 Kodi
    with xbmcvfs.File(path, 'w') as fh:
        fh.write(text)


def _write_iptv_instance(m3u_url, epg_url=''):
    """Write IPTV Simple v21 instance-settings-1.xml and (re)start PVR cleanly.

    Omega IPTV Simple is multi-instance: Addon.setSetting() hits obsolete
    addon-level keys and does not configure the live instance. Settings must
    live in userdata/addon_data/pvr.iptvsimple/instance-settings-1.xml.
    """
    # Stop PVR so the client reloads settings from disk.
    try:
        xbmc.executebuiltin('StopPVRManager')
    except Exception:
        pass
    xbmc.sleep(800)

    for dep in INPUTSTREAM_DEPS:
        _enable_addon(dep)
    _enable_addon(PVR_ID)

    inst_dir = _userdata('addon_data', PVR_ID)
    _ensure_dir(inst_dir)

    # Settings version 2 — same shape the GUI writes for Omega.
    pairs = [
        ('m3uPathType', '1'),          # remote URL
        ('m3uUrl', m3u_url),
        ('m3uCache', 'true'),
        ('startNum', '1'),
        ('numberByOrder', 'false'),
        ('m3uRefreshMode', '0'),
        ('epgPathType', '1' if epg_url else '0'),
    ]
    if epg_url:
        pairs.append(('epgUrl', epg_url))
        pairs.append(('epgCache', 'true'))
    # Avoid long connection-check stalls on bad networks
    pairs.append(('connectionchecktimeout', '10'))
    pairs.append(('connectioncheckinterval', '20'))

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        '<settings version="2">',
    ]
    for key, val in pairs:
        lines.append('    <setting id="%s">%s</setting>' % (key, _xml_escape(val)))
    lines.append('</settings>')
    lines.append('')
    inst_path = os.path.join(inst_dir, 'instance-settings-1.xml')
    _write_text(inst_path, '\n'.join(lines))
    xbmc.log('Husham wizard: wrote %s' % inst_path, xbmc.LOGINFO)

    # Bounce the client so PVR manager reloads the instance file.
    _disable_addon(PVR_ID)
    xbmc.sleep(500)
    _enable_addon(PVR_ID)
    xbmc.sleep(500)
    try:
        xbmc.executebuiltin('StartPVRManager')
    except Exception:
        pass

    xbmcgui.Dialog().notification(
        'Husham Play',
        'Playlist saved. Open Live TV after a moment.',
        xbmcgui.NOTIFICATION_INFO,
        5000,
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
    user_q = urllib.parse.quote(username, safe='')
    pass_q = urllib.parse.quote(password, safe='')
    m3u = '%s/get.php?username=%s&password=%s&type=m3u_plus' % (base, user_q, pass_q)
    epg = '%s/xmltv.php?username=%s&password=%s' % (base, user_q, pass_q)
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
        _mark_first_run_done(skipped=True)
        return
    _mark_first_run_done(skipped=False)
