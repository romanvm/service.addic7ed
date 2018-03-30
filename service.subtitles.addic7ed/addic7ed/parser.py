# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        addic7ed
# Purpose:     Parsing and downloading subs from addic7ed.com
# Author:      Roman Miroshnychenko
# Created on:  05.03.2013
# Copyright:   (c) Roman Miroshnychenko, 2013
# Licence:     GPL v.3 http://www.gnu.org/licenses/gpl.html
#-------------------------------------------------------------------------------

from __future__ import absolute_import
import re
from contextlib import closing
from collections import namedtuple
import requests
from bs4 import BeautifulSoup
from xbmcvfs import File
from .exceptions import ConnectionError, SubsSearchError, DailyLimitError
from .functions import LanguageData

SITE = 'http://www.addic7ed.com'
SubsSearchResult = namedtuple('SubsSearchResult', ['subtitles', 'episode_url'])
EpisodeItem = namedtuple('EpisodeItem', ['title', 'link'])
SubsItem = namedtuple('SubsItem', ['language', 'version', 'link', 'hi'])


def open_url(url, ref=SITE, params=None):
    """
    Open webpage from url

    :param url: URL to open
    :type url: str
    :param ref: referer header contents
    :type ref: str
    :param params: query params
    :type params: dict
    :return: response object
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Host': SITE[7:],
        'Referer': ref,
        'Accept-Charset': 'UTF-8',
        'Accept-Encoding': 'gzip,deflate'
        }
    return requests.get(url, params=params, headers=headers)


def search_episode(query, languages=None):
    """
    Search episode function. Accepts a TV show name, a season #, an episode # and language.
    Note that season and episode #s must be strings, not integers!
    For better search results relevance, season and episode #s should be 2-digit, e.g. 04.
    languages param must be a list of tuples
    ('Kodi language name', 'addic7ed language name')
    If search returns only 1 match, addic7ed.com redirects to the found episode page.
    In this case the function returns the list of available subs and an episode page URL.

    :param query: subs search query
    :type query: str
    :param languages: the list of languages to search
    :type languages: list
    :return: search results as the list of subtitles and episode page URL
    :rtype: SubsSearchResult
    :raises: ConnectionError if addic7ed.com cannot be opened
    :raises: SubsSearchError if search returns ambiguous results or no results
    """
    if languages is None:
        languages = [LanguageData('English', 'English')]
    try:
        response = open_url(SITE + '/search.php', params={'search': query, 'Submit': 'Search'})
    except requests.RequestException:
        raise ConnectionError
    else:
        soup = BeautifulSoup(response.text, 'html5lib')
        table = soup.find('table',
                          {'class': 'tabel', 'align': 'center', 'width': '80%',
                           'border': '0'}
                          )
        if table is not None:
            return list(parse_search_results(table))
        else:
            sub_cells = soup.find_all('table',
                                  {'width': '100%', 'border': '0', 'align': 'center', 'class': 'tabel95'}
                                  )
            if sub_cells:
                return SubsSearchResult(parse_episode(sub_cells , languages), response.url)
            else:
                raise SubsSearchError


def parse_search_results(table):
    """
    
    :param table: 
    :return: 
    """
    a_tags = table.find_all('a', href=re.compile(r'^serie'))
    for tag in a_tags:
        yield EpisodeItem(tag.text, tag['href'])


def get_episode(link, languages=None):
    """
    
    :param link: 
    :return: 
    """
    if languages is None:
        languages = [LanguageData('English', 'English')]
    try:
        response = open_url(SITE + '/' + link)
    except requests.RequestException:
        raise ConnectionError
    else:
        soup = BeautifulSoup(response.text, 'html5lib')
        sub_cells = soup.find_all('table',
                                  {'width': '100%', 'border': '0', 'align': 'center',
                                   'class': 'tabel95'})
        if sub_cells:
            return SubsSearchResult(parse_episode(sub_cells, languages), response.url)
        else:
            raise SubsSearchError


def parse_episode(sub_cells, languages):
    """
    Parse episode page. Accepts an episode page and a language.
    languages param must be a list of tuples
    ('Kodi language name', 'addic7ed language name')
    Returns the generator of available subs where each item is a named tuple
    with the following fields:

    - ``language``: subtitles language (Kodi)
    - ``version``: subtitles version (description on addic7ed.com)
    - ``link``: subtitles link
    - ``hi``: ``True`` for subs for hearing impaired, else ``False``

    :param sub_cell: BS nodes with episode subtitles
    :param languages: the list of languages to search
    :type languages:
    :return: generator function that yields :class:`SubsItem` items.
    """
    for sub_cell in sub_cells:
        version = re.search(r'Version (.*?),',
                            sub_cell.find('td',
                                          {'colspan': '3',
                                           'align': 'center',
                                           'class': 'NewsTitle'}).text
                            ).group(1)
        works_with = sub_cell.find('td', {'class': 'newsDate', 'colspan': '3'}).get_text(strip=True)
        if works_with:
            version += ', ' + works_with
        lang_cells = sub_cell.find_all('td', {'class': 'language'})
        for lang_cell in lang_cells:
            for language in languages:
                if language.add7_lang in lang_cell.text:
                    download_cell = lang_cell.find_next('td', {'colspan': '3'})
                    download_button = download_cell.find(text='most updated')
                    if download_button is None:
                        download_button = download_cell.find(text='Download')
                    download_tag = download_button.parent.parent
                    yield SubsItem(language=language.kodi_lang,
                                   version=version,
                                   link=SITE + download_tag['href'],
                                   hi=(download_tag.find_next('tr').contents[1].find(
                                       'img', title='Hearing Impaired') is not None))
                    break


def download_subs(url, referer, filename='subtitles.srt'):
    """
    Download subtitles from addic7ed.com

    :param url: subtitles URL
    :type url: str
    :param referer: episode page for referer header
    :type referer: str
    :param filename: file name for subtitles
    :type filename: str
    :raises: ConnectionError if addic7ed.com cannot be opened
    :raises: DailyLimitError if a user exceeded their daily download quota (10 subtitles).
    """
    try:
        subtitles = open_url(url, ref=referer).content
    except requests.RequestException:
        raise ConnectionError
    else:
        if subtitles[:9].lower() != '<!doctype':
            with closing(File(filename, 'w')) as fo:
                fo.write(subtitles)
        else:
            raise DailyLimitError
