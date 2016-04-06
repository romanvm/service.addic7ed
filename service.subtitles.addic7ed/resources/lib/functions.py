# -*- coding: utf-8 -*-
# Module: functions
# Author: Roman V. M.
# Created on: 03.12.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import json
import re
from collections import namedtuple
import xbmc
from add7_exceptions import ParseError

EPISODE_PATTERNS = (
    r'^(.*?)[ \.](?:\d*?[ \.])?s(\d+)[ \.]?e(\d+)\.',
    r'^(.*?)[ \.](?:\d*?[ \.])?(\d+)x(\d+)\.',
    r'^(.*?)[ \.](?:\d*?[ \.])?(\d{1,2}?)[ \.]?(\d{2})\.',
    )

LanguageData = namedtuple('LanguageData', ['kodi_lang', 'add7_lang'])
EpisodeData = namedtuple('EpisodeData', ['showname', 'season', 'episode'])


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
        elif re.search(r'Spanish \(.*?\)', kodi_lang) is not None:
            add7_lang = 'Spanish (Latin America)'
        else:
            add7_lang = language
        languages.append(LanguageData(kodi_lang, add7_lang))
    return languages


def filename_parse(filename):
    """
    Filename parser for extracting show name, season # and episode # from a filename.

    :param filename: episode filename
    :type filename: str
    :return: parsed showname, season and episode
    :rtype: EpisodeData
    :raises: ParseError if the filename does not match any episode patterns
    """
    for regexp in EPISODE_PATTERNS:
        episode_data = re.search(regexp, filename, re.I | re.U)
        if episode_data is not None:
            showname = episode_data.group(1).replace('.', ' ')
            season = episode_data.group(2).zfill(2)
            episode = episode_data.group(3).zfill(2)
            return EpisodeData(showname, season, episode)
    raise ParseError

