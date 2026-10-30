# -*- coding: utf-8 -*-
"""First-run / on-demand 'Add your own content' wizard for Husham Play."""
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
        'IPTV playlist saved. Open TV / Live TV after a moment.',
        xbmcgui.NOTIFICATION_INFO,
        5000,
    )


def _xml_escape(value):
    return (
        value.replace('&', '&')
        .replace('<', '<')
        .replace('>', '>')
        .replace('"', '"')
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
    if not dialog.yesno('Add IPTV (Xtream Codes)', NOTICE + '\n\nContinue?'):
        return
    server = dialog.input('Server URL (host:port or full URL)', type=xbmcgui.INPUT_ALPHANUM)
    if not server:
        return
    username = dialog.input('Username', type=xbmcgui.INPUT_ALPHANUM)
    if not username:
        return
    password = dialog.input('Password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if not password:
        return
    base = _normalize_xtream_server(server)
    m3u = '%s/get.php?username=%s&password=%s&type=m3u_plus' % (base, username, password)
    epg = '%s/xmltv.php?username=%s&password=%s' % (base, username, password)
    _write_iptv_instance(m3u, epg)
    dialog.ok('IPTV added', 'Xtream playlist and EPG URLs were saved to IPTV Simple Client.\nNo provider is bundled — this is your own account.')


def wizard_m3u():
    dialog = xbmcgui.Dialog()
    if not dialog.yesno('Add IPTV (M3U URL)', NOTICE + '\n\nContinue?'):
        return
    m3u = dialog.input('M3U playlist URL', type=xbmcgui.INPUT_ALPHANUM)
    if not m3u:
        return
    epg = dialog.input('EPG URL (optional — leave blank to skip)', type=xbmcgui.INPUT_ALPHANUM)
    _write_iptv_instance(m3u.strip(), (epg or '').strip())
    dialog.ok('IPTV added', 'Playlist saved to IPTV Simple Client.')


def wizard_videos():
    dialog = xbmcgui.Dialog()
    if not dialog.yesno(
        'Add my own videos/movies',
        NOTICE + '\n\nPick a local folder, USB drive or network share (SMB/NFS/UPnP).',
    ):
        return
    name = dialog.input('Source name (e.g. My Movies)', type=xbmcgui.INPUT_ALPHANUM)
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
        dialog.ok('Source added', '"%s" was added to Videos.\nBrowse it under Videos → Files.' % name)
    except Exception as exc:  # noqa: BLE001
        xbmc.log('Husham wizard sources.xml write failed: %s' % exc, xbmc.LOGERROR)
        dialog.ok(
            'Add source manually',
            'Could not write sources automatically.\n'
            'Open Videos → Files → Add videos… and choose:\n%s' % path,
        )
    xbmc.executebuiltin('ActivateWindow(Videos,sources://video/,return)')


def run_wizard(force=False):
    dialog = xbmcgui.Dialog()
    dialog.ok('Add your own content', NOTICE)
    choice = dialog.select(
        'Add your own content',
        [
            'Add IPTV with Xtream Codes login',
            'Add IPTV via M3U playlist URL',
            'Add my own videos/movies (folder / USB / network)',
            'Skip for now',
        ],
    )
    if choice == 0:
        wizard_xtream()
    elif choice == 1:
        wizard_m3u()
    elif choice == 2:
        wizard_videos()
    # Mark first-run done unless caller wants to keep showing
    try:
        ADDON.setSettingBool('first_run_done', True)
        if choice == 3:
            ADDON.setSettingBool('wizard_skipped', True)
    except Exception:
        ADDON.setSetting('first_run_done', 'true')
        if choice == 3:
            ADDON.setSetting('wizard_skipped', 'true')
