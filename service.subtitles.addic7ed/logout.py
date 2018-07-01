# coding: utf-8

import os
from xbmcgui import Dialog
from addic7ed import addon
from addic7ed.functions import log_error, log_debug


cookies = os.path.join(addon.profile, 'cookies.pickle')
dialog = Dialog()


def do_logout():
    """
    Clean cookie file to logout from the site
    """
    if dialog.yesno(addon.get_ui_string(32013), addon.get_ui_string(32014),
                    addon.get_ui_string(32015)):
        if os.path.exists(cookies):
            try:
                os.remove(cookies)
            except OSError:
                pass
            else:
                dialog.notification(addon.ADDON_ID, addon.get_ui_string(32016))
                log_debug('Cookies removed successfully.')
                return
        dialog.notification(addon.ADDON_ID, addon.get_ui_string(32017), icon='error')
        log_error('Unable to remove cookies!')


if __name__ == '__main__':
    do_logout()
