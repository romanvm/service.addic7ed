# -*- coding: utf-8 -*-
# Licence: GPL v.3 http://www.gnu.org/licenses/gpl.html

#Standard modules
import os
import sys
import urlparse
import json
import re
import urllib
import shutil
#XBMC modules
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmcvfs


_addon = xbmcaddon.Addon()
_id = _addon.getAddonInfo("id")
_path = _addon.getAddonInfo("path").decode("utf-8")
_profile = xbmc.translatePath(_addon.getAddonInfo("profile").decode("utf-8"))
_temp = os.path.join(_profile, "temp")
_handle = int(sys.argv[1])

sys.path.append(os.path.join(_path, "resources", "lib"))
import addic7ed


def _log(message):
    """
    Write message to the Kodi log
    for debuging purposes.
    """
    xbmc.log("{0}: {1}".format(_id, message))


def get_params():
    """
    Get the script call parameters as a dictionary.
    """
    paramstring = sys.argv[2].replace("?", "")
    params = urlparse.parse_qs(paramstring)
    for key in params.keys():
        params[key] = params[key][0]
    return params


def get_now_played():
    """
    Get info about the currently played file via JSON-RPC.
    Alternatively this can be done via Kodi InfoLabels.
    """
    request = json.dumps({"jsonrpc": "2.0",
                          "method": "Player.GetItem",
                          "params": {"playerid": 1,
                                     "properties": ["file", "showtitle", "season", "episode", "streamdetails"]},
                          "id": "1"})
    reply = json.loads(xbmc.executeJSONRPC(request))
    return reply["result"]["item"]


def show_message(title, message, icon="info", duration=5000):
    """
    Show a poup-up message.
    Alternatively this can be done via a Kodi Built-In function.
    """
    request = json.dumps({"jsonrpc": "2.0",
                          "method": "GUI.ShowNotification",
                          "params": {"title": title, "message": message, "image": icon, "displaytime": duration},
                          "id": "1"})
    xbmc.executeJSONRPC(request)


def normalize_showname(showtitle):
    """
    Normalize showname if there are differences
    between TheTVDB and Addic7ed
    """
    if "castle" in showtitle.lower():
        showtitle = showtitle.replace("(2009)", "")
    return showtitle.replace(":", "")


def get_languages(languages_raw):
    """
    Create the list of pairs of language names.
    The 1st item in a pair is used by Kodi.
    The 2nd item in a pair is used by
    the addic7ed web site parser.
    """
    languages = []
    for language in languages_raw:
        kodi_lang = language
        if "English" in kodi_lang:
            add7_lang = "English"
        elif kodi_lang == "Portuguese (Brazil)":
            add7_lang = "Portuguese (Brazilian)"
        elif re.match(r"Spanish \(.*?\)", kodi_lang) is not None:
            add7_lang = "Spanish (Latin America)"
        else:
            add7_lang = language
        languages.append((kodi_lang, add7_lang))
    return languages


def filename_parse(filename):
    """
    Filename parser for extracting show name, season # and episode # from a filename.
    """
    PATTERNS = (r"(.*?)[ \.](?:[\d]*?[ \.])?[Ss]([\d]+)[ \.]?[Ee]([\d]+)",
                r"(.*?)[ \.](?:[\d]*?[ \.])?([\d]+)[Xx]([\d]+)",
                r"(.*?)[ \.](?:[\d]*?[ \.])?[Ss]([\d]{2})[ \.]?([\d]{2})",
                r"(.*?)[ \.][\d]{4}()()",
                r"(.*?)[ \.]([\d])([\d]{2})")
    for regexp in PATTERNS:
        episode_data = re.search(regexp, filename)
        if episode_data is not None:
            show = episode_data.group(1).replace(".", " ")
            season = episode_data.group(2).zfill(2)
            episode = episode_data.group(3).zfill(2)
            break
    else:
        show = season = episode = ""
    return show, season, episode


def display_subs(subs_list, episode_url, filename):
    """
    Display the list of found subtitles

    :param subs_list: the list of dictionaries with the following keys:
        language: Kodi language name for the subtitles.
        verison: a descriptive text for the subtitles.
        hi (bool): are the subs for hearing impaired?
        link: download link for the subtitles.
    :param episode_url: the URL for the episode page on addic7ed.com.
        Needed for downloading subs as "Referer" HTTP header.
    :param filename: the name of the video-file being played.
    :return: None

    Each item in the list is a ListItem instance with the following properties:
        label: Kodi language name (e.g. "English")
        label2: a descriptive test for subs (e.g. "LOL, works with DIMENSION release").
        thumbnailImage: a 2-letter language code (e.g. "en") to display a country flag.
        "hearing_imp": if "true" then (CC) icon is displayed for the list item.
        "sync": if "true" then (SYNC) icon is displayed for the list item.

    url: a plugin call-back URL for downloading selected subs.
    """
    for item in subs_list:
        list_item = xbmcgui.ListItem(label=item["language"], label2=item["version"],
                                     thumbnailImage=xbmc.convertLanguage(item["language"], xbmc.ISO_639_1))
        if item["hi"]:
            list_item.setProperty("hearing_imp", "true")
        # Check the release name in the filename (e.g. DIMENSION)
        # and compare it with the subs description on addic7ed.com.
        release_match = re.search(r"\-(.*?)\.", filename)
        if release_match is not None and release_match.group(1).lower() in item["version"].lower():
            # Set "sunc" = "true" if the subs for the same release.
            list_item.setProperty("sync", "true")
        url = "plugin://{0}/?action=download&link={1}&ref={2}&filename={3}".format(
            _id, item["link"], episode_url, urllib.quote_plus(filename))
        xbmcplugin.addDirectoryItem(handle=_handle, url=url, listitem=list_item, isFolder=False)


def download_subs(link, referrer, filename):
    """
    Download selected subs

    :param link: a download link for the subs.
    :param referrer: a referer URL for the episode page (required by addic7ed.com).
    :param filename: the name of the video-file being played.
    :return: None

    The function must add a single ListItem instance with one property:
    label: the download location for subs.
    """
    # Re-create a download location in a temporary folder
    if xbmcvfs.exists(_temp):
        shutil.rmtree(_temp)
    xbmcvfs.mkdirs(_temp)
    # Combine a path where to download the subs
    subspath = os.path.join(_temp, filename[:-3] + "srt")
    # Download the subs from addic7ed.com
    result = addic7ed.download_subs(link, referrer, subspath)
    if result == 1:
        # Create a ListItem for downloaded subs and pass it
        # to the Kodi subtitles engine to move the downloaded subs file
        # from the temp folder to the designated
        # location selected by "Subtitle storage location" option
        # in "Settings > Video > Subtitles" section.
        # A 2-letter language code will be added to subs filename.
        list_item = xbmcgui.ListItem(label=subspath)
        xbmcplugin.addDirectoryItem(handle=_handle, url=subspath, listitem=list_item, isFolder=False)
        title = "Success!"
        message = "Subtitles for {0} downloaded.".format(filename)
        icon = "info"
    elif result == -1:
        title = "Error!"
        message = "Exceeded daily limit for subs downloads."
        icon = "error"
    else:
        title = "Error!"
        message = "Unable to download subtitles for {0}.".format(filename)
        icon = "error"
    show_message(title, message, icon)


if __name__ == "__main__":
    params = get_params()
    if params["action"] == "search":
        languages = get_languages(urllib.unquote_plus(params["languages"]).split(","))
        now_played = get_now_played()
        if now_played["file"][:4] in ("http", "plug"):
            # Try to get showname/season/episode data from
            # the filename if the video-file is being played
            # by a video plugin via a network link.
            filename = now_played["label"]
            show, season, episode = filename_parse(filename)
        else:
            # Get get showname/season/episode data from
            # Kodi if the video-file is being played from
            # the TV-Shows library.
            filename = os.path.basename(now_played["file"])
            show = now_played["showtitle"]
            season = str(now_played["season"]).zfill(2)
            episode = str(now_played["episode"]).zfill(2)
        # Search subtitles in Addic7ed.com.
        found_list, episode_url = addic7ed.search_episode(normalize_showname(show), season, episode, languages)
        if found_list != -1 and episode_url:
            display_subs(found_list, episode_url, filename)
        elif found_list == -1:
            show_message("Error!", "Unable to connect to addic7ed.com.", "error")
    elif params["action"] == "download":
        download_subs(params["link"], params["ref"], urllib.unquote_plus(params["filename"]))
    elif params["action"] == "manualsearch":
        # Manual search is not supported!
        show_message("Error!", "Manual search is not implemented.", "error")
    xbmcplugin.endOfDirectory(_handle)
