# -*- coding: utf-8 -*-
# Module: functions
# Author: Roman V. M.
# Created on: 03.12.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import json
import re
import xbmc
import xbmcgui


def get_now_played():
    """
    Get info about the currently played file via JSON-RPC.
    Alternatively this can be done via Kodi InfoLabels.
    :return: dict
    """
    request = json.dumps({'jsonrpc': '2.0',
                          'method': 'Player.GetItem',
                          'params': {'playerid': 1,
                                     'properties': ['file', 'showtitle', 'season', 'episode']},
                          'id': '1'})
    reply = json.loads(xbmc.executeJSONRPC(request))
    return reply['result']['item']


def show_message(title, message, icon='info', duration=3000):
    """
    Show a poup-up message.
    Alternatively this can be done via a Kodi Built-In function.
    :param title: str
    :param message: str
    :param icon: str
    :param duration: int
    """
    xbmcgui.Dialog().notification(title, message, icon, duration)


def normalize_showname(showtitle):
    """
    Normalize showname if there are differences
    between TheTVDB and Addic7ed
    :param showtitle: str
    """
    if 'castle' in showtitle.lower():
        showtitle = showtitle.replace('(2009)', '')
    return showtitle.replace(':', '')


def get_languages(languages_raw):
    """
    Create the list of pairs of language names.
    The 1st item in a pair is used by Kodi.
    The 2nd item in a pair is used by
    the addic7ed web site parser.
    :param languages_raw: str
    """
    languages = []
    for language in languages_raw:
        kodi_lang = language
        if 'English' in kodi_lang:
            add7_lang = 'English'
        elif kodi_lang == 'Portuguese (Brazil)':
            add7_lang = 'Portuguese (Brazilian)'
        elif re.match(r'Spanish \(.*?\)', kodi_lang) is not None:
            add7_lang = 'Spanish (Latin America)'
        else:
            add7_lang = language
        languages.append((kodi_lang, add7_lang))
    return languages


def filename_parse(filename):
    """
    Filename parser for extracting show name, season # and episode # from a filename.
    :param filename: str
    """
    PATTERNS = (r'(.*?)[ \.](?:[\d]*?[ \.])?[Ss]([\d]+)[ \.]?[Ee]([\d]+)',
                r'(.*?)[ \.](?:[\d]*?[ \.])?([\d]+)[Xx]([\d]+)',
                r'(.*?)[ \.](?:[\d]*?[ \.])?[Ss]([\d]{2})[ \.]?([\d]{2})',
                r'(.*?)[ \.][\d]{4}()()',
                r'(.*?)[ \.]([\d])([\d]{2})')
    for regexp in PATTERNS:
        episode_data = re.search(regexp, filename)
        if episode_data is not None:
            show = episode_data.group(1).replace('.', ' ')
            season = episode_data.group(2).zfill(2)
            episode = episode_data.group(3).zfill(2)
            break
    else:
        show = season = episode = ''
    return show, season, episode
