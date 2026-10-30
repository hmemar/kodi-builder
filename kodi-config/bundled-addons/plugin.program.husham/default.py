# -*- coding: utf-8 -*-
# Husham Play companion add-on (GPL-2.0-or-later)
from __future__ import annotations

import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE = sys.argv[0] if sys.argv else 'plugin://plugin.program.husham/'

# TikTok: not listed on husham.com footer/site links as of 2026-10-30.
# PLACEHOLDER — replace once Husham confirms the profile URL.
TIKTOK_URL = None

STREAMING_SERVICES = [
    # label, website, android package, play store id (usually same as package)
    ('Netflix', 'https://www.netflix.com', 'com.netflix.mediaclient', 'com.netflix.mediaclient'),
    ('Disney+', 'https://www.disneyplus.com', 'com.disney.disneyplus', 'com.disney.disneyplus'),
    ('Hulu', 'https://www.hulu.com', 'com.hulu.plus', 'com.hulu.plus'),
    ('Prime Video', 'https://www.primevideo.com', 'com.amazon.avod.thirdpartyclient', 'com.amazon.avod.thirdpartyclient'),
    ('YouTube', 'https://www.youtube.com', 'com.google.android.youtube', 'com.google.android.youtube'),
]

VPN_LINKS = [
    ('NordVPN', 'https://husham.com/go/nordvpn'),
    ('Surfshark', 'https://husham.com/go/surfshark'),
    ('IPVanish', 'https://husham.com/ipvanishpromo'),
    ('CyberGhost', 'https://husham.com/cgdiscount'),
    ('PureVPN', 'https://husham.com/purevpn'),
    ('Ivacy', 'https://husham.com/ivacyvpn'),
]


def build_url(query):
    return BASE + '?' + urllib.parse.urlencode(query)


def open_url(url):
    if not url:
        return
    if url.startswith('plugin://'):
        xbmc.executebuiltin('ActivateWindow(10025,"%s",return)' % url.replace('"', ''))
        return
    if xbmc.getCondVisibility('System.Platform.Android'):
        xbmc.executebuiltin('StartAndroidActivity(,android.intent.action.VIEW,,%s)' % url)
        return
    try:
        import os
        import subprocess
        if xbmc.getCondVisibility('System.Platform.Windows'):
            os.startfile(url)  # type: ignore[attr-defined]
            return
        if xbmc.getCondVisibility('System.Platform.OSX'):
            subprocess.Popen(['open', url])
            return
        if xbmc.getCondVisibility('System.Platform.Linux'):
            subprocess.Popen(['xdg-open', url])
            return
    except Exception:
        pass
    xbmcgui.Dialog().ok('Husham', url)


def add_item(label, url=None, is_folder=False, plot='', art=None):
    li = xbmcgui.ListItem(label=label)
    li.setInfo('video', {'title': label, 'plot': plot})
    icon = ADDON.getAddonInfo('icon')
    fanart = ADDON.getAddonInfo('fanart')
    li.setArt(art or {'icon': icon, 'fanart': fanart, 'thumb': icon})
    xbmcplugin.addDirectoryItem(HANDLE, url, li, is_folder)


def list_root():
    add_item(
        'Add your own content…',
        build_url({'action': 'wizard'}),
        plot='Set up IPTV (Xtream or M3U) or add your own video folders. Husham Play ships with no content.',
    )
    add_item(
        'Official streaming services',
        build_url({'action': 'streaming_menu'}),
        is_folder=True,
        plot='Open Netflix, Disney+, Hulu, Prime Video or YouTube in the official app or website. Text names only — no logos bundled.',
    )
    add_item(
        'YouTube — @husham122',
        'plugin://plugin.video.youtube/channel/@husham122/',
        is_folder=True,
        plot='Open Dr Husham Memar’s YouTube channel via the official YouTube add-on.',
    )
    add_item('husham.com', build_url({'action': 'open', 'url': 'https://www.husham.com/'}),
             plot='Guides, news and articles')
    add_item('Husham Forum', build_url({'action': 'open', 'url': 'https://forum.husham.com/'}),
             plot='Community forum')
    add_item('Speed Test', build_url({'action': 'open', 'url': 'https://speedtest.husham.com/'}),
             plot='Husham speed test')
    add_item('Check for updates', build_url({'action': 'open', 'url': 'https://www.husham.com/husham-media/'}),
             plot='Husham Play download page')
    add_item('TikTok (link pending)', build_url({'action': 'tiktok_placeholder'}),
             plot='TikTok profile URL was not found on husham.com — awaiting confirmation.')
    add_item('VPN offers', build_url({'action': 'vpn_menu'}), is_folder=True,
             plot='Popular VPN offers (affiliate links)')
    add_item('Backup my settings', build_url({'action': 'backup'}),
             plot='Save a zip of your Husham Play settings/userdata to a folder you choose.')
    add_item('Restore my settings', build_url({'action': 'restore'}),
             plot='Restore settings from a backup zip created by Husham Play.')
    add_item('Parental controls (PIN)', build_url({'action': 'parental_guide'}),
             plot='How to set a parental PIN in system settings — no bypass tools included.')
    add_item('Check for Husham Play updates', build_url({'action': 'update_check'}),
             plot='Compare this build with the latest release notes on GitHub.')
    add_item('Privacy', build_url({'action': 'privacy'}),
             plot='Husham Play does not include tracking or analytics.')
    add_item('About Husham Play', build_url({'action': 'about'}),

             plot='Version, licence and project notes')
    xbmcplugin.endOfDirectory(HANDLE)


def list_streaming():
    add_item(
        'Note',
        build_url({'action': 'streaming_note'}),
        plot='Opens the official website (or Android app / Play Store). Husham Play does not embed these services. Text labels only.',
    )
    for label, website, pkg, store in STREAMING_SERVICES:
        add_item(
            label,
            build_url({'action': 'open_streaming', 'key': label}),
            plot='Open %s' % website,
        )
    xbmcplugin.endOfDirectory(HANDLE)


def open_streaming(key):
    match = None
    for row in STREAMING_SERVICES:
        if row[0] == key:
            match = row
            break
    if not match:
        return
    label, website, pkg, store = match
    if xbmc.getCondVisibility('System.Platform.Android'):
        choice = xbmcgui.Dialog().select(
            label,
            ['Open official app', 'Open Play Store page', 'Open website'],
        )
        if choice == 0:
            xbmc.executebuiltin('StartAndroidActivity(%s)' % pkg)
        elif choice == 1:
            xbmc.executebuiltin(
                'StartAndroidActivity(,android.intent.action.VIEW,,market://details?id=%s)' % store
            )
        elif choice == 2:
            xbmc.executebuiltin(
                'StartAndroidActivity(,android.intent.action.VIEW,,%s)' % website
            )
        return
    open_url(website)



def list_vpn():
    add_item(
        'Affiliate disclosure',
        build_url({'action': 'vpn_disclosure'}),
        plot='Some VPN links are affiliate links. Husham Play / husham.com may earn a commission at no extra cost to you.',
    )
    for name, url in VPN_LINKS:
        add_item(name, build_url({'action': 'open', 'url': url}), plot='Open %s offer page' % name)
    xbmcplugin.endOfDirectory(HANDLE)


def run_wizard_action():
    # Import from resources/lib
    addon_path = ADDON.getAddonInfo('path')
    if addon_path not in sys.path:
        sys.path.insert(0, xbmc.translatePath(addon_path) if hasattr(xbmc, 'translatePath') else addon_path)
    lib = addon_path.rstrip('/\\') + '/resources/lib'
    if lib not in sys.path:
        sys.path.insert(0, lib)
    from wizard import run_wizard  # noqa: WPS433
    run_wizard(force=True)



def _profile_path(*parts):
    import xbmcvfs
    return xbmcvfs.translatePath(('/'.join(('special://profile',) + parts)))


def do_backup():
    import os
    import time
    import zipfile
    import xbmcvfs
    dialog = xbmcgui.Dialog()
    dest_dir = dialog.browse(0, 'Choose folder for backup zip', 'files', '', False, False, '')
    if not dest_dir:
        return
    profile = xbmcvfs.translatePath('special://profile')
    stamp = time.strftime('%Y%m%d-%H%M%S')
    dest = os.path.join(dest_dir, 'husham-play-settings-%s.zip' % stamp)
    # zip key userdata files (not thumbnails cache)
    include_dirs = ('addon_data',)
    include_files = (
        'guisettings.xml', 'sources.xml', 'favourites.xml', 'advancedsettings.xml',
        'profiles.xml', 'passwords.xml', 'mediasources.xml',
    )
    try:
        with zipfile.ZipFile(xbmcvfs.translatePath(dest) if dest.startswith('special://') else dest, 'w', zipfile.ZIP_DEFLATED) as zf:
            for name in include_files:
                path = os.path.join(profile, name)
                if os.path.isfile(path):
                    zf.write(path, name)
            for d in include_dirs:
                root = os.path.join(profile, d)
                if not os.path.isdir(root):
                    continue
                for dirpath, _, filenames in os.walk(root):
                    for fn in filenames:
                        full = os.path.join(dirpath, fn)
                        rel = os.path.relpath(full, profile)
                        zf.write(full, rel)
        dialog.ok('Backup saved', 'Settings backup written to:\n%s' % dest)
    except Exception as exc:  # noqa: BLE001
        dialog.ok('Backup failed', str(exc))


def do_restore():
    import os
    import zipfile
    import xbmcvfs
    dialog = xbmcgui.Dialog()
    if not dialog.yesno('Restore settings', 'This replaces settings files in your profile. Continue?'):
        return
    path = dialog.browse(1, 'Select Husham Play backup zip', 'files', '.zip', False, False, '')
    if not path or not path.lower().endswith('.zip'):
        return
    profile = xbmcvfs.translatePath('special://profile')
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            zf.extractall(profile)
        dialog.ok('Restore complete', 'Restart Husham Play for all changes to apply.')
    except Exception as exc:  # noqa: BLE001
        dialog.ok('Restore failed', str(exc))


def do_update_check():
    import json
    import urllib.request
    dialog = xbmcgui.Dialog()
    local = '1.1'
    try:
        ver_file = xbmcaddon.Addon().getAddonInfo('path').rstrip('/\\') + '/../../../userdata/../'
    except Exception:
        pass
    # Read bundled VERSION from a known release API
    try:
        req = urllib.request.Request(
            'https://api.github.com/repos/hmemar/kodi-builder/releases/latest',
            headers={'User-Agent': 'HushamPlay/1.1', 'Accept': 'application/vnd.github+json'},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        tag = data.get('tag_name') or ''
        name = data.get('name') or tag
        url = data.get('html_url') or 'https://www.husham.com/husham-media/'
        body = (data.get('body') or '')[:300]
        dialog.ok(
            'Update check',
            'This build: Husham Play %s\nLatest GitHub release: %s (%s)\n\n%s\n\nDownloads: %s'
            % (local, name, tag, body, url),
        )
    except Exception as exc:  # noqa: BLE001
        dialog.ok(
            'Update check',
            'This build: Husham Play %s\nCould not reach GitHub (%s).\n'
            'Check manually: https://www.husham.com/husham-media/'
            % (local, exc),
        )


def main():
    params = {}
    if len(sys.argv) > 2 and sys.argv[2]:
        params = dict(urllib.parse.parse_qsl(sys.argv[2].lstrip('?')))
    action = params.get('action')
    if not action:
        list_root()
        return
    if action == 'wizard':
        run_wizard_action()
        return
    if action == 'open':
        open_url(params.get('url', ''))
        return
    if action == 'streaming_menu':
        list_streaming()
        return
    if action == 'open_streaming':
        open_streaming(params.get('key', ''))
        return
    if action == 'vpn_menu':
        list_vpn()
        return
    if action == 'streaming_note':
        xbmcgui.Dialog().ok(
            'Official streaming services',
            'These tiles open the official website in your system browser.\n'
            'On Android they try the official app, then the Play Store page.\n'
            'Husham Play does not include these apps or any of their logos.',
        )
        return
    if action == 'vpn_disclosure':
        xbmcgui.Dialog().ok(
            'Affiliate disclosure',
            'Some VPN links are affiliate links. Husham Play / husham.com may earn a commission '
            'if you buy through them, at no extra cost to you.',
        )
        return
    if action == 'tiktok_placeholder':
        xbmcgui.Dialog().ok(
            'TikTok (pending)',
            'No TikTok profile URL was found in the husham.com footer or site links '
            '(checked 2026-10-30).\n\nPlaceholder left for Husham to confirm.',
        )
        return
    if action == 'backup':
        do_backup()
        return
    if action == 'restore':
        do_restore()
        return
    if action == 'parental_guide':
        xbmcgui.Dialog().ok(
            'Parental PIN',
            'Husham Play uses the built-in master lock.\n\n'
            'Open Settings → System → Master lock → Master lock code\n'
            'Set a PIN and choose what it protects (settings, add-ons, files, etc.).\n\n'
            'No bypass or unlock tools are included.',
        )
        return
    if action == 'update_check':
        do_update_check()
        return
    if action == 'privacy':
        xbmcgui.Dialog().ok(
            'Privacy',
            'Husham Play does not ship tracking, analytics or advertising SDKs.\n'
            'Optional add-ons you enable (YouTube, OpenSubtitles, weather, VPNs) '
            'use their own services under their own policies.\n'
            'IPTV and media sources are provided by you — nothing is preloaded.',
        )
        return
    if action == 'about':
        xbmcgui.Dialog().ok(
            'Husham Play 1.1',
            'Free media player by Dr Husham Memar.\n'
            'Based on the open-source Kodi project (GPL-2.0-or-later).\n'
            'Not affiliated with or endorsed by the Kodi Foundation / XBMC Foundation.\n'
            'Husham Play provides no content — only use media you have the right to access.\n'
            'Source: github.com/hmemar/kodi-builder\n'
            'Downloads: husham.com/husham-media/',
        )
        return


if __name__ == '__main__':
    main()
