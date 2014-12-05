# -*- coding: utf-8 -*-
# Licence: GPL v.3 http://www.gnu.org/licenses/gpl.html

#Standard modules
import os
import sys
import urlparse
import re
import urllib
import shutil
from urllib import quote_plus
#XBMC modules
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmcvfs


_addon = xbmcaddon.Addon()
_id = _addon.getAddonInfo('id')
_path = _addon.getAddonInfo('path').decode('utf-8')
_profile = xbmc.translatePath(_addon.getAddonInfo('profile').decode('utf-8'))
_temp = os.path.join(_profile, 'temp')
_handle = int(sys.argv[1])

sys.path.append(os.path.join(_path, 'resources', 'lib'))
import addic7ed
import functions


def _log(message):
    """
    Write message to the Kodi log
    for debuging purposes.
    """
    xbmc.log('{0}: {1}'.format(_id, message.encode('utf-8')))


def _string(string_id):
    """
    Get language string by ID

    :param string_id: string
    :return: None
    """
    return _addon.getLocalizedString(string_id).encode('utf-8')


def get_params():
    """
    Get the script call parameters as a dictionary.
    Note that a subtitles plugin always receives a paramstring,
    so we don't check if it is actually present.
    """
    paramstring = sys.argv[2].replace('?', '')
    params = {}
    for pair in urlparse.parse_qsl(paramstring):
        params[pair[0]] = pair[1]
    return params


def display_subs(subs_list, episode_url, filename):
    """
    Display the list of found subtitles

    :param subs_list: list
    the list of dictionaries with the following keys:
        language: Kodi language name for the subtitles.
        verison: a descriptive text for the subtitles.
        hi (bool): are the subs for hearing impaired?
        link: download link for the subtitles.
    :param episode_url: str
    the URL for the episode page on addic7ed.com.
        Needed for downloading subs as 'Referer' HTTP header.
    :param filename: str
    the name of the video-file being played.
    :return: None

    Each item in the list is a ListItem instance with the following properties:
        label: Kodi language name (e.g. 'English')
        label2: a descriptive test for subs (e.g. 'LOL, works with DIMENSION release').
        thumbnailImage: a 2-letter language code (e.g. 'en') to display a country flag.
        'hearing_imp': if 'true' then (CC) icon is displayed for the list item.
        'sync': if 'true' then (SYNC) icon is displayed for the list item.

    url: a plugin call-back URL for downloading selected subs.
    """
    for item in subs_list:
        list_item = xbmcgui.ListItem(label=item['language'], label2=item['version'],
                                     thumbnailImage=xbmc.convertLanguage(item['language'], xbmc.ISO_639_1))
        if item['hi']:
            list_item.setProperty('hearing_imp', 'true')
        # Check the release name in the filename (e.g. DIMENSION)
        # and compare it with the subs description on addic7ed.com.
        release_match = re.search(r'\-(.*?)\.', filename)
        if release_match is not None and release_match.group(1).lower() in item['version'].lower():
            # Set 'sunc' = 'true' if the subs for the same release.
            list_item.setProperty('sync', 'true')
        url = 'plugin://{0}/?action=download&link={1}&ref={2}&filename={3}'.format(
            _id, item['link'], episode_url, urllib.quote_plus(filename))
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
    result = addic7ed.download_subs(link, referrer, subspath)
    if result == 1:
        # Create a ListItem for downloaded subs and pass it
        # to the Kodi subtitles engine to move the downloaded subs file
        # from the temp folder to the designated
        # location selected by 'Subtitle storage location' option
        # in 'Settings > Video > Subtitles' section.
        # A 2-letter language code will be added to subs filename.
        list_item = xbmcgui.ListItem(label=subspath)
        xbmcplugin.addDirectoryItem(handle=_handle, url=subspath, listitem=list_item, isFolder=False)
        functions.show_message(_string(32000), _string(32001), 'info', 3000)
        _log('Subs downloaded.')
    elif result == -1:
        functions.show_message(_string(32002), _string(32003), 'error', 3000)
        _log('Exceeded daily limit for subs downloads.')
    else:
        _log('Unable to download subs.')


if __name__ == '__main__':
    _log('Searching for subs...')
    params = get_params()
    if params['action'] in ('search', 'manualsearch'):
        # Search for subs
        languages = functions.get_languages(urllib.unquote_plus(params['languages']).split(','))
        now_played = functions.get_now_played()
        filename = os.path.basename(now_played['file'])
        if _addon.getSetting('use_filename') == 'true' or now_played['file'][:4] in ('http', 'plug'):
            # Try to get showname/season/episode data from
            # the filename if 'use_filename' setting is true
            # or the video-file is being played
            # by a video plugin via a network link.
            if _addon.getSetting('use_filename') == 'false':
                filename = now_played['label']
            _log('Using filename: {0}'.format(filename))
            show, season, episode = functions.filename_parse(filename)
        else:
            # Get get showname/season/episode data from
            # Kodi if the video-file is being played from
            # the TV-Shows library.
            show = now_played['showtitle']
            season = str(now_played['season']).zfill(2)
            episode = str(now_played['episode']).zfill(2)
            _log(u'Using library metadata: {0} - {1}x{2}'.format(show, season, episode))
        # Search subtitles in Addic7ed.com.
        if params['action'] == 'search':
            # Create a search query string
            query = '{0}+{1}x{2}'.format(
                quote_plus(functions.normalize_showname(show.encode('utf-8'))), season, episode)
        else:
            # Get the query string typed on the on-screen keyboard
            query = params['searchstring']
        if query:
            _log('Search query: {0}'.format(query))
            found_list, episode_url = addic7ed.search_episode(query, languages)
            if found_list != -1 and episode_url:
                _log('Subs found: {0}'.format(len(found_list)))
                display_subs(found_list, episode_url, filename)
            elif found_list == -1:
                functions.show_message(_string(32002), _string(32005), 'error')
                _log('No subs found.')
    elif params['action'] == 'download':
        # Display subs.
        download_subs(params['link'], params['ref'], urllib.unquote_plus(params['filename']))
    xbmcplugin.endOfDirectory(_handle)
