# -*- coding: utf-8 -*-
# Module: functions
# Author: Roman V. M.
# Created on: 03.12.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import absolute_import
import json
import re
from collections import namedtuple
import xbmc
from .addon import ADDON_ID
from .exceptions import ParseError

__all__ = [
    'log_notice',
    'log_error',
    'log_debug',
    'get_now_played',
    'normalize_showname',
    'get_languages',
    'parse_filename',
]

episode_patterns = (
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?s(\d+)[ \.]?e(\d+)\.', re.I | re.U),
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?(\d+)x(\d+)\.', re.I | re.U),
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?(\d{1,2}?)[ \.]?(\d{2})\.', re.I | re.U),
    )
spanish_re = re.compile(r'Spanish \(.*?\)')

LanguageData = namedtuple('LanguageData', ['kodi_lang', 'add7_lang'])


def log(message, level):
    """
    Write message to the Kodi log
    for debuging purposes.
    """
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    xbmc.log('{0}: {1}'.format(ADDON_ID, message), level)


def log_notice(message):
    log(message, xbmc.LOGNOTICE)


def log_error(message):
    log(message, xbmc.LOGERROR)


def log_debug(message):
    log(message, xbmc.LOGDEBUG)


def get_now_played():
    """
    Get info about the currently played file via JSON-RPC.
    Alternatively this can be done via Kodi InfoLabels.

    :return: currently played item's data
    :rtype: dict
    """
    request = json.dumps({'jsonrpc': '2.0',
                          'method': 'Player.GetItem',
                          'params': {'playerid': 1,
                                     'properties': ['file', 'showtitle', 'season', 'episode']},
                          'id': '1'})
    return json.loads(xbmc.executeJSONRPC(request))['result']['item']


def normalize_showname(showname):
    """
    Normalize showname if there are differences
    between TheTVDB and Addic7ed

    :param showname: TV show name
    :type showname: str
    :return: normalized show name
    :rtype: str
    """
    if 'castle' in showname.lower():
        showname = showname.replace('(2009)', '')
    elif showname.lower() == 'law & order: special victims unit':
        showname = 'Law and order SVU'
    return showname.replace(':', '')


def get_languages(languages_raw):
    """
    Create the list of pairs of language names.
    The 1st item in a pair is used by Kodi.
    The 2nd item in a pair is used by
    the addic7ed web site parser.

    :param languages_raw: the list of subtitle languages from Kodi
    :type languages_raw: list
    :return: the list of language pairs
    :rtype: list
    """
    languages = []
    for language in languages_raw:
        kodi_lang = language
        if 'English' in kodi_lang:
            add7_lang = 'English'
        elif kodi_lang == 'Portuguese (Brazil)':
            add7_lang = 'Portuguese (Brazilian)'
        elif spanish_re.search(kodi_lang) is not None:
            add7_lang = 'Spanish (Latin America)'
        else:
            add7_lang = language
        languages.append(LanguageData(kodi_lang, add7_lang))
    return languages


def parse_filename(filename):
    """
    Filename parser for extracting show name, season # and episode # from a filename.

    :param filename: episode filename
    :type filename: str
    :return: parsed showname, season and episode
    :rtype: EpisodeData
    :raises: ParseError if the filename does not match any episode patterns
    """
    for regexp in episode_patterns:
        episode_data = regexp.search(filename)
        if episode_data is not None:
            showname = episode_data.group(1).replace('.', ' ')
            season = episode_data.group(2).zfill(2)
            episode = episode_data.group(3).zfill(2)
            return showname, season, episode
    raise ParseError

