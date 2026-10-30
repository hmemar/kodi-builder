# Third-party add-ons bundled with Husham Play 1.1

All of the following come from the **official** Kodi Omega repository mirror (`mirrors.kodi.tv/addons/omega/`), except `plugin.program.husham` and `skin.husham.play` which are maintained in this repository. No unofficial repositories are bundled.

| Add-on ID | Name | Licence | Source / notes |
|-----------|------|---------|----------------|
| plugin.video.youtube | YouTube | GPL-2.0-only | Official Omega; https://github.com/anxdpanic/plugin.video.youtube |
| plugin.video.archive.org | Internet Archive | GPL-2.0 | Official Omega |
| plugin.audio.radiobrowser | radio-browser.info | GPL-3.0-or-later | Official Omega; international station directory |
| plugin.audio.soundcloud | SoundCloud | MIT | Official Omega |
| plugin.audio.podcasts | RSS Podcasts | MIT | Official Omega |
| script.module.inputstreamhelper | InputStream Helper | MIT | Official Omega |
| script.module.requests | requests | Apache-2.0 | Official Omega (dependency) |
| script.module.xmltodict | xmltodict | MIT | Official Omega (dependency) |
| service.subtitles.opensubtitles-com | OpenSubtitles.com | (see add-on) | Official Omega; **user must register their own account** |
| weather.openmeteo | Open-Meteo | GPL-2.0-or-later | Official Omega; location set by user / system |
| pvr.iptvsimple | IPTV Simple Client | GPL-2.0-or-later | Official Omega binary; **no playlist shipped** |
| inputstream.adaptive | InputStream Adaptive | GPL-2.0-or-later | Official Omega binary |
| inputstream.ffmpegdirect | InputStream FFmpegDirect | GPL-2.0-or-later | Official Omega binary |
| inputstream.rtmp | InputStream RTMP | GPL-2.0-or-later | Official Omega binary |
| plugin.program.husham | Husham | GPL-2.0-or-later | This repo — wizard, links, backup, privacy |
| skin.husham.play | Husham Play | CC BY-SA 4.0 / GPL-2.0 | Fork of Estuary by phil65 / Ichabod Fletchman; Estuary credit retained |

### Platform notes

- Android / Windows / macOS: binary add-ons downloaded from the official per-platform Omega folders.
- Linux: binary add-ons are compiled during the workflow when possible; otherwise install IPTV Simple Client from the official repo after first launch.

### Explicitly not included

- No piracy, scrapers, or unofficial repos
- No IPTV Merge or other unofficial IPTV tools
- No region-locked broadcaster add-ons by default
- No Pluto TV plugin (marked broken/deprecated upstream)
- No bundled M3U playlists, Xtream credentials, or streaming service APKs/logos
