# coding: utf-8

from __future__ import absolute_import, unicode_literals
from future import standard_library
standard_library.install_aliases()

import urllib.request as urllib2
from urllib.parse import urlencode
from contextlib import closing
from .exceptions import Add7ConnectionError
from .utils import logger

__all__ = ['Session']

SITE = 'http://www.addic7ed.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) '
                  'Gecko/20100101 Firefox/67.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Host': SITE[7:],
    'Accept-Charset': 'UTF-8',
}


class Session(object):
    """
    Webclient Session class
    """
    def __init__(self):
        self._headers = HEADERS.copy()
        self._last_url = ''

    @property
    def last_url(self):
        """
        Get actual url (with redirect) of the last loaded webpage

        :return: URL of the last webpage
        """
        return self._last_url

    def _open_url(self, url, params, referer):
        logger.debug('Opening URL: {0}'.format(url))
        self._headers['Referer'] = referer
        if params:
            url += '?' + urlencode(params)
        request = urllib2.Request(url, headers=self._headers)
        try:
            with closing(urllib2.urlopen(request)) as response:
                status = response.getcode()
                if status >= 400:
                    logger.error(
                        'Addic7ed.com returned status: {0}'.format(status)
                    )
                    raise Add7ConnectionError
                byte_content = response.read()
                self._last_url = response.geturl()
        except IOError:
            logger.error('Unable to connect to Addic7ed.com!')
            raise Add7ConnectionError
        logger.debug(
            'Addic7ed.com returned page:\n{}'.format(
                byte_content.decode('utf-8')
            )
        )
        return byte_content

    def load_page(self, path, params=None):
        """
        Load webpage by its relative path on the site

        :param path: relative path starting from '/'
        :param params: URL query params
        :return: webpage content as a Unicode string
        :raises ConnectionError: if unable to connect to the server
        """
        byte_content = self._open_url(SITE + path, params, referer=SITE + '/')
        return byte_content.decode('utf-8')

    def download_subs(self, path, referer):
        """
        Download subtitles by their URL

        :param path: relative path to .srt starting from '/'
        :param referer: referer page
        :return: subtitles file contents as a byte string
        :raises ConnectionError: if unable to connect to the server
        """
        return self._open_url(SITE + path, params=None, referer=referer)
