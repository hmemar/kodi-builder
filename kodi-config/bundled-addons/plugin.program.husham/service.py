# -*- coding: utf-8 -*-
"""First-run service: launch Add-your-own-content wizard once."""
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()


def run():
    monitor = xbmc.Monitor()
    # Wait for the home window, and for the PVR "starting up" progress
    # dialog to finish if a client was left enabled from a previous build.
    for _ in range(90):
        if monitor.waitForAbort(1):
            return
        on_home = xbmc.getCondVisibility('Window.IsActive(home)')
        pvr_busy = xbmc.getCondVisibility('Window.IsActive(extendedprogressdialog)')
        if on_home and not pvr_busy:
            break
    if monitor.abortRequested():
        return
    try:
        done = ADDON.getSettingBool('first_run_done')
    except Exception:
        done = ADDON.getSetting('first_run_done') == 'true'
    if done:
        return
    if monitor.waitForAbort(2):
        return
    # RunPlugin is enough: the wizard only uses xbmcgui.Dialog, not a
    # plugin directory handle. ActivateWindow is a fallback if the plugin
    # call is ignored on a given platform.
    xbmc.executebuiltin('RunPlugin(plugin://plugin.program.husham/?action=wizard)')
    if monitor.waitForAbort(8):
        return
    try:
        done = ADDON.getSettingBool('first_run_done')
    except Exception:
        done = ADDON.getSetting('first_run_done') == 'true'
    if not done and not xbmc.getCondVisibility('System.HasActiveModalDialog'):
        xbmc.executebuiltin(
            'ActivateWindow(Programs,plugin://plugin.program.husham/?action=wizard,return)'
        )


if __name__ == '__main__':
    run()
