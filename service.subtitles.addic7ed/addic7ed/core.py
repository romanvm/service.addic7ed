# coding: utf-8
# Created on: 07.04.2016
# Author: Roman Miroshnychenko aka Roman V.M. (roman1972@gmail.com)

from __future__ import absolute_import
#Standard modules
import os
import sys
import urlparse
import re
import urllib
import shutil
#XBMC modules
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmcvfs

from . import parser, functions
from .exceptions import *

__all__ = ['router']

_addon = xbmcaddon.Addon()
_id = _addon.getAddonInfo('id')
_path = _addon.getAddonInfo('path').decode('utf-8')
_profile = xbmc.translatePath(_addon.getAddonInfo('profile')).decode('utf-8')
_temp = os.path.join(_profile, 'temp')
_handle = int(sys.argv[1])
_icon = os.path.join(_path, 'icon.png')


VIDEOFILES = ('.avi', '.mkv', '.mp4', '.ts', '.m2ts', '.mov')
dialog = xbmcgui.Dialog()


def log(message, level=xbmc.LOGDEBUG):
    """
    Write message to the Kodi log
    for debuging purposes.
    """
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    xbmc.log('{0}: {1}'.format(_id, message), level)


def ui_string(string_id):
    """
    Get language string by ID

    :param string_id: UI string ID
    :return: UI string
    """
    return _addon.getLocalizedString(string_id)


def display_subs(subs_list, episode_url, filename):
    """
    Display the list of found subtitles

    :param subs_list: the list of named tuples with the following fields:

        - language: Kodi language name for the subtitles.
        - verison: a descriptive text for the subtitles.
        - hi (bool): ``True`` if subs for hearing impaired
        - link: download link for the subtitles.

    :param episode_url: the URL for the episode page on addic7ed.com.
        It is needed for downloading subs as 'Referer' HTTP header.
    :param filename: the name of the video-file being played.

    Each item in the displayed list is a ListItem instance with the following properties:

        - label: Kodi language name (e.g. 'English')
        - label2: a descriptive text for subs (e.g. 'LOL, works with DIMENSION release').
        - thumbnailImage: a 2-letter language code (e.g. 'en') to display a country flag.
        - 'hearing_imp': if 'true' then 'CC' icon is displayed for the list item.
        - 'sync': if 'true' then 'SYNC' icon is displayed for the list item.
        - url: a plugin call-back URL for downloading selected subs.
    """
    for item in subs_list:
        list_item = xbmcgui.ListItem(label=item.language,
                                     label2=item.version.encode('utf-8'),
                                     thumbnailImage=xbmc.convertLanguage(item.language, xbmc.ISO_639_1))
        if item.hi:
            list_item.setProperty('hearing_imp', 'true')
        # Check the release name in the filename (e.g. DIMENSION)
        # and compare it with the subs description on addic7ed.com.
        release_match = re.search(r'\-(.*?)\.', filename)
        if release_match is not None and release_match.group(1).lower() in item.version.lower():
            # Set 'sync' = 'true' if the subs for the same release.
            list_item.setProperty('sync', 'true')
        url = '{0}?{1}'.format(
            sys.argv[0],
            urllib.urlencode({'action': 'download', 'link': item.link, 'ref': episode_url, 'filename': filename}))
        xbmcplugin.addDirectoryItem(handle=_handle, url=url, listitem=list_item, isFolder=False)


def download_subs(link, referrer, filename):
    """
    Download selected subs

    :param link: str - a download link for the subs.
    :param referrer: str - a referer URL for the episode page (required by addic7ed.com).
    :param filename: str - the name of the video-file being played.
    :return: None

    The function must add a single ListItem instance with one property:
        label - the download location for subs.
    """
    # Re-create a download location in a temporary folder
    if xbmcvfs.exists(_temp):
        shutil.rmtree(_temp)
    xbmcvfs.mkdirs(_temp)
    # Combine a path where to download the subs
    subspath = os.path.join(_temp, filename[:-3] + 'srt')
    # Download the subs from addic7ed.com
    try:
        parser.download_subs(link, referrer, subspath)
    except ConnectionError:
        log('Unable to connect to addic7ed.com', xbmc.LOGERROR)
        dialog.notification(ui_string(32002), ui_string(32005), 'error')
    except DailyLimitError:
        dialog.notification(ui_string(32002), ui_string(32003), 'error', 3000)
        log('Exceeded daily limit for subs downloads.', xbmc.LOGERROR)
    else:
        # Create a ListItem for downloaded subs and pass it
        # to the Kodi subtitles engine to move the downloaded subs file
        # from the temp folder to the designated
        # location selected by 'Subtitle storage location' option
        # in 'Settings > Video > Subtitles' section.
        # A 2-letter language code will be added to subs filename.
        list_item = xbmcgui.ListItem(label=subspath)
        xbmcplugin.addDirectoryItem(handle=_handle, url=subspath, listitem=list_item, isFolder=False)
        dialog.notification(ui_string(32000), ui_string(32001), _icon, 3000, False)
        log('Subs downloaded.')


def search_subs(params):
    log('Searching for subs...', xbmc.LOGNOTICE)
    languages = functions.get_languages(urllib.unquote_plus(params['languages']).split(','))
    now_played = functions.get_now_played()
    filename = os.path.basename(urllib.unquote(now_played['file']))
    if _addon.getSetting('use_filename') == 'true' or not now_played['showtitle']:
        # Try to get showname/season/episode data from
        # the filename if 'use_filename' setting is true
        # or if the video-file does not have library metadata.
        try:
            log('Using filename: {0}'.format(filename))
            showname, season, episode = functions.parse_filename(filename)
        except ParseError:
            log('Filename {0} failed. Trying ListItem.Label...'.format(filename))
            try:
                filename = now_played['label']
                log('Using filename: {0}'.format(filename))
                showname, season, episode = functions.parse_filename(filename)
            except ParseError:
                log('Unable to determine episode data for {0}'.format(filename), xbmc.LOGERROR)
                dialog.notification(ui_string(32002), ui_string(32006), 'error', 3000)
                return
    else:
        # Get get showname/season/episode data from
        # Kodi if the video-file is being played from
        # the TV-Shows library.
        showname = now_played['showtitle']
        season = str(now_played['season']).zfill(2)
        episode = str(now_played['episode']).zfill(2)
        if not os.path.splitext(filename)[1].lower() in VIDEOFILES:
            filename = '{0}.{1}x{2}.foo'.format(showname.encode('utf-8'), season, episode)
        log('Using library metadata: {0} - {1}x{2}'.format(showname.encode('utf-8'), season, episode))
    # Search subtitles in Addic7ed.com.
    if params['action'] == 'search':
        # Create a search query string
        query = '{0}+{1}x{2}'.format(
            urllib.quote_plus(
                functions.normalize_showname(showname).encode('utf-8')
            ),
            season, episode
        )
    else:
        # Get the query string typed on the on-screen keyboard
        query = params['searchstring']
    if query:
        log('Search query: {0}'.format(query))
        try:
            results = parser.search_episode(query, languages)
        except ConnectionError:
            log('Unable to connect to addic7ed.com', xbmc.LOGERROR)
            dialog.notification(ui_string(32002), ui_string(32005), 'error')
        except SubsSearchError:
            log('No subs found.', xbmc.LOGNOTICE)
        else:
            if isinstance(results, list):
                log('Multiple episode found:\n{0}'.format(results), xbmc.LOGNOTICE)
                i = dialog.select(ui_string(32008), [item.title for item in results])
                if i >= 0:
                    try:
                        results = parser.get_episode(results[i].link, languages)
                    except ConnectionError:
                        log('Unable to connect to addic7ed.com', xbmc.LOGERROR)
                        dialog.notification(ui_string(32002), ui_string(32005),
                                            'error')
                        return
                    except SubsSearchError:
                        log('No subs found.', xbmc.LOGNOTICE)
                        return
                else:
                    log('Episode selection cancelled.', xbmc.LOGNOTICE)
                    return
            log('Found subs for "{0}"'.format(query), xbmc.LOGNOTICE)
            display_subs(results.subtitles, results.episode_url, filename)


def router(paramstring):
    """
    Dispatch plugin functions depending on the call paramstring

    :param paramstring: URL-encoded plugin call parameters
    :type paramstring: str
    """
    # Get plugin call params
    params = dict(urlparse.parse_qsl(paramstring))
    if params['action'] in ('search', 'manualsearch'):
        # Search and display subs.
        search_subs(params)
    elif params['action'] == 'download':
        download_subs(params['link'], params['ref'], urllib.unquote_plus(params['filename']))
    xbmcplugin.endOfDirectory(_handle)
