# coding: utf-8
# Created on: 06.04.2016
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import sys
import unittest
import codecs
from mock import MagicMock

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(basedir, 'service.subtitles.addic7ed', 'resources', 'lib'))

sys.modules['xbmc'] = MagicMock()
sys.modules['xbmcvfs'] = MagicMock()
sys.modules['requests'] = MagicMock()

import functions
import addic7ed


class ParseEpisodeFileNameTestCase(unittest.TestCase):
    def test_parsing_sXXeYY_pattern(self):
        filename = 'FooBar.S02E05.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result.showname, 'FooBar')
        self.assertEqual(result.season, '02')
        self.assertEqual(result.episode, '05')

    def test_parsing_SSxEE_pattern(self):
        filename = 'FooBar.02x05.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result.showname, 'FooBar')
        self.assertEqual(result.season, '02')
        self.assertEqual(result.episode, '05')

    def test_parsing_SSEE_pattern(self):
        filename = 'FooBar.1205.mp4'
        result = functions.parse_filename(filename)
        self.assertEqual(result.showname, 'FooBar')
        self.assertEqual(result.season, '12')
        self.assertEqual(result.episode, '05')

    def test_parsing_failed(self):
        filename = 'FooBar.Baz.mp4'
        self.assertRaises(functions.ParseError, functions.parse_filename, filename)


class ParseEpisodeTestCase(unittest.TestCase):
    def test_parsing_episode_page(self):
        with codecs.open(os.path.join(basedir, 'test_data', 'WalkingDead.S04E01.htm'), 'rb', 'utf-8') as fo:
            page_html = fo.read()
        subtitles = list(addic7ed.parse_episode(page_html, [('English', 'English')]))
        self.assertEqual(len(subtitles), 3)
        self.assertEqual(subtitles[0].version, 'ASAP, Works with IMMERSE, AFG, HDTV mSD')
        self.assertTrue(subtitles[0].hi)


if __name__ == '__main__':
    unittest.main()
