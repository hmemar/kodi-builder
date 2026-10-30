# -*- coding: utf-8 -*-
"""First-run service: launch Add-your-own-content wizard once."""
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()


def run():
    monitor = xbmc.Monitor()
    for _ in range(90):
        if monitor.waitForAbort(1):
            return
        if xbmc.getCondVisibility('Window.IsActive(home)'):
            break
    if monitor.abortRequested():
        return
    try:
        done = ADDON.getSettingBool('first_run_done')
    except Exception:
        done = ADDON.getSetting('first_run_done') == 'true'
    if done:
        return
    if monitor.waitForAbort(4):
        return
    xbmc.executebuiltin('RunPlugin(plugin://plugin.program.husham/?action=wizard)')


if __name__ == '__main__':
    run()
