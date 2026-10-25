# Husham Media Player - Custom Kodi Fork Builder

This is a customized fork of the Kodi Android APK Builder for **Husham Media Player** by Dr Husham Memar.

It is based on the open-source Kodi media center software. Do not use the name "Kodi" or official logos in distribution.

### Build your custom APK

1. Go to the **Actions** tab and enable workflows if needed.
2. Run the **Build Kodi APK** workflow.
3. Recommended settings:
   - App display name: **Husham Media**
   - Package ID: **com.husham.media**
   - Pre-enable Unknown sources: true
   - Publish as Release: true

The build includes:
- Pre-installed YouTube addon (easy access to @husham122)
- File Manager sources for husham.com, forum.husham.com, speedtest.husham.com, and the YouTube channel

Upload a custom `icon.png` and `splash.png` to `kodi-config/` for full branding.

Download the APK from Releases after the build completes, then host it on your website.

---

*Based on the open-source Kodi project. Source code available in this repository.*

## Engine

Built from the upstream Piers branch (Kodi 22 prerelease, rolling master), so builds are marked as prerelease.

## License

This project is licensed under GPL-2.0-or-later, matching upstream [xbmc/xbmc](https://github.com/xbmc/xbmc).

Husham Media is not affiliated with or endorsed by the XBMC Foundation. Kodi is a trademark of the XBMC Foundation.
