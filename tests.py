# coding: utf-8
# Created on: 06.04.2016
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import sys
import unittest
import codecs
from mock import MagicMock
from bs4 import BeautifulSoup

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(basedir, 'service.subtitles.addic7ed'))

sys.modules['xbmc'] = MagicMock()
sys.modules['xbmcvfs'] = MagicMock()
sys.modules['requests'] = MagicMock()

from addic7ed import parser, functions


class ParseEpisodeFileNameTestCase(unittest.TestCase):
    def test_parsing_sXXeYY_pattern(self):
        filename = 'FooBar.S02E05.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result[0], 'FooBar')
        self.assertEqual(result[1], '02')
        self.assertEqual(result[2], '05')

    def test_parsing_SSxEE_pattern(self):
        filename = 'FooBar.02x05.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result[0], 'FooBar')
        self.assertEqual(result[1], '02')
        self.assertEqual(result[2], '05')

    def test_parsing_SSEE_pattern(self):
        filename = 'FooBar.1205.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result[0], 'FooBar')
        self.assertEqual(result[1], '12')
        self.assertEqual(result[2], '05')

    def test_parsing_failed(self):
        filename = 'FooBar.Baz.mp4'
        self.assertRaises(functions.ParseError, functions.parse_filename, filename)


class ParseEpisodeTestCase(unittest.TestCase):
    def test_parsing_episode_page(self):
        with codecs.open(os.path.join(basedir, 'test_data', 'WalkingDead.S04E01.htm'), 'rb', 'utf-8') as fo:
            page_html = fo.read()
        english = functions.LanguageData('English', 'English')
        soup = BeautifulSoup(page_html, 'html5lib')
        cells = soup.find_all('table',
                          {'width': '100%', 'border': '0', 'align': 'center',
                           'class': 'tabel95'}
                          )
        subtitles = list(parser.parse_episode(cells, [english]))
        self.assertEqual(len(subtitles), 3)
        self.assertEqual(subtitles[0].version, 'ASAP, Works with IMMERSE, AFG, HDTV mSD')
        self.assertTrue(subtitles[0].hi)


class ParseSearchResultsTestCase(unittest.TestCase):
    def test_parse_search_results(self):
        with codecs.open(os.path.join(basedir, 'test_data', 'Six.htm'), 'rb', 'utf-8') as fo:
            page_html = fo.read()
        soup = BeautifulSoup(page_html, 'html5lib')
        table = soup.find('table',
                          {'class': 'tabel', 'align': 'center', 'width': '80%',
                           'border': '0'}
                          )
        episodes = list(parser.parse_search_results(table))
        print episodes
        self.assertEqual(len(episodes), 103)


if __name__ == '__main__':
    unittest.main()
