# Husham Play - Custom Kodi Fork Builder

This is a customized fork of the Kodi Android APK Builder for **Husham Play** by Dr Husham Memar.

It is based on the open-source Kodi media center software. Do not use the name "Kodi" or official logos in distribution.

### Build your custom APK

1. Go to the **Actions** tab and enable workflows if needed.
2. Run the **Build Kodi APK** workflow.
3. Recommended settings:
   - App display name: **Husham Play**
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

Husham Play was previously called Husham Media (package ID `com.husham.media` is unchanged, so existing installs update in place). It is a free app and is unrelated to the paid HushPlay smart TV player.

## Engine

Built from the stable upstream Omega (21.x) branch. Piers (22, prerelease) is available but currently fails upstream.

## License

This project is licensed under GPL-2.0-or-later, matching upstream [xbmc/xbmc](https://github.com/xbmc/xbmc).

Husham Play is not affiliated with or endorsed by the XBMC Foundation. Kodi is a trademark of the XBMC Foundation.
