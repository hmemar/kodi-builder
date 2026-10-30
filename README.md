# Husham Play — custom media player builder

**Husham Play 1.1** is a free, international media player by Dr Husham Memar.

It is based on the open-source Kodi project. Do not use the name "Kodi" or official Kodi logos in distribution marketing. Husham Play is **not affiliated with or endorsed by** the Kodi Foundation / XBMC Foundation.

Package ID (Android): `com.husham.media` (unchanged from the earlier Husham Media name so installs update in place). Unrelated to the paid HushPlay smart-TV app.

## What 1.1 includes

- Branding: Husham Play icon, splash, and **skin.husham.play** (Estuary fork, GPL / CC BY-SA — Estuary credit retained)
- **PVR IPTV Simple Client** pre-installed with **no playlist** (add your own legal M3U / Xtream)
- Official international add-ons only (YouTube, Internet Archive, Radio Browser, SoundCloud, Podcasts, OpenSubtitles.com, Open-Meteo weather, InputStream Helper + Adaptive/FFmpegDirect/RTMP where platform binaries exist)
- **plugin.program.husham**: first-run “Add your own content” wizard, links, VPN offers (affiliate disclosure), backup/restore, privacy note, update check, official streaming website/app launchers (text names only)
- International defaults (no forced UK language/region/timezone)
- Favourites home tiles: Add your own content, YouTube, Husham, husham.com

See [THIRD-PARTY-ADDONS.md](THIRD-PARTY-ADDONS.md) for licences and sources.

## Build

1. Enable Actions on this repository if needed.
2. Run the platform workflow you need (`build-kodi.yml` Android, `build-windows.yml`, `build-macos.yml`, `build-linux.yml`).
3. Recommended Android inputs: App name **Husham Play**, package **com.husham.media**, Unknown sources true, Publish release true.

Engine: upstream Omega (21.3).

## Licence

GPL-2.0-or-later, matching upstream [xbmc/xbmc](https://github.com/xbmc/xbmc). Bundled third-party add-ons keep their own licences (see THIRD-PARTY-ADDONS.md). Skin based on Estuary (CC BY-SA 4.0 / GPL-2.0).

Husham Play provides **no** films, TV, sports or IPTV playlists. Only use services and media you have the right to access.
