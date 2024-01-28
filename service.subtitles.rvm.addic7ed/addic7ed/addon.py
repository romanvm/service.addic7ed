# Copyright (C) 2016, Roman Miroshnychenko aka Roman V.M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

import xbmcaddon
from xbmcvfs import translatePath

__all__ = ['ADDON_ID', 'ADDON', 'PATH', 'PROFILE', 'ICON', 'get_ui_string']

ADDON_ID = 'service.subtitles.rvm.addic7ed'
ADDON = xbmcaddon.Addon(ADDON_ID)
PATH = translatePath(ADDON.getAddonInfo('path'))
PROFILE = translatePath(ADDON.getAddonInfo('profile'))
ICON = os.path.join(PATH, 'icon.png')


def get_ui_string(string_id):
    """
    Get language string by ID

    :param string_id: UI string ID
    :return: UI string
    """
    return ADDON.getLocalizedString(string_id)
