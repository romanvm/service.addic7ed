# coding: utf-8

import os
import xbmc
from xbmcaddon import Addon
from xbmcgui import Dialog

ADDON_ID = 'service.subtitles.addic7ed'
addon = Addon(ADDON_ID)
profile_dir = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
cookies = os.path.join(profile_dir, 'cookies.pickle')
dialog = Dialog()


def ui_string(string_id):
    """
    Get language string by ID

    :param string_id: UI string ID
    :return: UI string
    """
    return addon.getLocalizedString(string_id)


def do_logout():
    """
    Clean cookie file to logout from the site
    """
    if dialog.yesno(ui_string(32013), ui_string(32014), ui_string(32015)):
        if os.path.exists(cookies):
            try:
                os.remove(cookies)
            except OSError:
                pass
            else:
                dialog.notification(ADDON_ID, ui_string(ui_string(32016)))
                xbmc.log(ADDON_ID + ': Cookies removed successfully.', xbmc.LOGDEBUG)
                return
        dialog.notification(ADDON_ID, ui_string(32017), icon='error')
        xbmc.log(ADDON_ID + ': Unable to remove cookies!', xbmc.LOGERROR)


if __name__ == '__main__':
    do_logout()
