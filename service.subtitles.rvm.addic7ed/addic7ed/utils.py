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

import json
import logging
import os
import re
from collections import namedtuple

import xbmc

from addic7ed.addon import ADDON_ID, ADDON_VERSION
from addic7ed.exception_logger import format_exception, format_trace
from addic7ed.exceptions import ParseError

__all__ = [
    'initialize_logging',
    'get_now_played',
    'normalize_showname',
    'get_languages',
    'parse_filename',
]

logger = logging.getLogger(__name__)

# Convert show names from TheTVDB format to Addic7ed.com format
# Keys must be all lowercase
NAME_CONVERSIONS = {
    'castle (2009)': 'castle',
    'law & order: special victims unit': 'Law and order SVU',
    'bodyguard (2018)': 'bodyguard',
}

LOG_FORMAT = '[{addon_id} v.{addon_version}] {filename}:{lineno} - {message}'

episode_patterns = (
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?s(\d+)[ \.]?e(\d+)\.', re.I | re.U),
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?(\d+)x(\d+)\.', re.I | re.U),
    re.compile(r'^(.*?)[ \.](?:\d*?[ \.])?(\d{1,2}?)[ \.]?(\d{2})\.', re.I | re.U),
    )
spanish_re = re.compile(r'Spanish \(.*?\)')

LanguageData = namedtuple('LanguageData', ['kodi_lang', 'add7_lang'])


class KodiLogHandler(logging.Handler):
    """
    Logging handler that writes to the Kodi log with correct levels

    It also adds {addon_id} and {addon_version} variables available to log format.
    """
    LEVEL_MAP = {
        logging.NOTSET: xbmc.LOGNONE,
        logging.DEBUG: xbmc.LOGDEBUG,
        logging.INFO: xbmc.LOGINFO,
        logging.WARN: xbmc.LOGWARNING,
        logging.WARNING: xbmc.LOGWARNING,
        logging.ERROR: xbmc.LOGERROR,
        logging.CRITICAL: xbmc.LOGFATAL,
    }

    def emit(self, record):
        record.addon_id = ADDON_ID
        record.addon_version = ADDON_VERSION
        extended_trace_info = getattr(self, 'extended_trace_info', False)
        if extended_trace_info:
            if record.exc_info is not None:
                record.exc_text = format_exception(record.exc_info[1])
            if record.stack_info is not None:
                record.stack_info = format_trace(7)
        message = self.format(record)
        kodi_log_level = self.LEVEL_MAP.get(record.levelno, xbmc.LOGDEBUG)
        xbmc.log(message, level=kodi_log_level)


def initialize_logging(extended_trace_info=True):
    """
    Initialize the root logger that writes to the Kodi log

    After initialization, you can use Python logging facilities as usual.

    :param extended_trace_info: write extended trace info when exc_info=True
        or stack_info=True parameters are passed to logging methods.
    """
    handler = KodiLogHandler()
    # pylint: disable=attribute-defined-outside-init
    handler.extended_trace_info = extended_trace_info
    logging.basicConfig(
        format=LOG_FORMAT,
        style='{',
        level=logging.DEBUG,
        handlers=[handler],
        force=True
    )


def get_now_played():
    """
    Get info about the currently played file via JSON-RPC

    :return: currently played item's data
    :rtype: dict
    """
    request = json.dumps({
        'jsonrpc': '2.0',
        'method': 'Player.GetItem',
        'params': {
            'playerid': 1,
            'properties': ['showtitle', 'season', 'episode']
         },
        'id': '1'
    })
    response = xbmc.executeJSONRPC(request)
    item = json.loads(response)['result']['item']
    path = xbmc.getInfoLabel('Window(10000).Property(videoinfo.current_path)')
    if path:
        item['file'] = os.path.basename(path)
        logger.debug("Using file path from addon: %s", item['file'])
    else:
        item['file'] = xbmc.Player().getPlayingFile()  # It provides more correct result
    return item


def normalize_showname(showname):
    """
    Normalize showname if there are differences
    between TheTVDB and Addic7ed

    :param showname: TV show name
    :return: normalized show name
    """
    showname = showname.strip().lower()
    if showname in NAME_CONVERSIONS:
        showname = NAME_CONVERSIONS[showname]
    return showname.replace(':', '')


def get_languages(languages_raw):
    """
    Create the list of pairs of language names.
    The 1st item in a pair is used by Kodi.
    The 2nd item in a pair is used by
    the addic7ed web site parser.

    :param languages_raw: the list of subtitle languages from Kodi
    :return: the list of language pairs
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
    Filename parser for extracting show name, season # and episode # from
    a filename.

    :param filename: episode filename
    :return: parsed showname, season and episode
    :raises ParseError: if the filename does not match any episode patterns
    """
    filename = filename.replace(' ', '.')
    for regexp in episode_patterns:
        episode_data = regexp.search(filename)
        if episode_data is not None:
            showname = episode_data.group(1).replace('.', ' ')
            season = episode_data.group(2).zfill(2)
            episode = episode_data.group(3).zfill(2)
            return showname, season, episode
    raise ParseError
