# coding: utf-8
# Created on: 06.04.2016
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import sys
import unittest
from mock import MagicMock

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(basedir, 'service.subtitles.addic7ed', 'resources', 'lib'))

sys.modules['xbmc'] = MagicMock()

import functions


class ParseEpisodeTestCase(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
