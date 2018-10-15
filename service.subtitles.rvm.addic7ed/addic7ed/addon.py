# coding: utf-8

import os
import xbmc
from xbmcaddon import Addon

__all__ = ['ADDON_ID', 'addon', 'path', 'profile', 'icon', 'get_ui_string']

ADDON_ID = 'service.subtitles.addic7ed'
addon = Addon(ADDON_ID)
path = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')
profile = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
icon = os.path.join(path, 'icon.png')


def get_ui_string(string_id):
    """
    Get language string by ID

    :param string_id: UI string ID
    :return: UI string
    """
    return addon.getLocalizedString(string_id)
