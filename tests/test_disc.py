from collections import namedtuple
import logging
import os
import unittest
from unittest.mock import patch

import discid

from hifi_appliance.disc import read_disc_id
from hifi_appliance.disc import read_disc_meta
from hifi_appliance.disc.toc import Toc, TOCError


class DiscIdTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_read_disc_id_ok(self):
        return_object = namedtuple('MockDisc', ['id'])
        return_object.id = 'disc_id'
        with patch('discid.read', return_value=return_object) as mock_method:
            self.assertEqual(read_disc_id(), 'disc_id')

    def test_fail_returns_none(self):
        with patch('discid.read') as mock_method:
            mock_method.side_effect = discid.disc.DiscError()
            self.assertEqual(read_disc_id(), None)


class DiscMetaTestCase(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    @patch('hifi_appliance.disc.disc._read_toc_into_file')
    def test_no_cdtext(self, mocked_read_toc):
        toc_path = os.path.join(os.path.dirname(__file__), 'data', 'toc', 'notext')
        disc_meta = read_disc_meta('disc_id', str(toc_path))

        self.assertEqual(len(disc_meta['tracks']), 29)
        self.assertRegex(disc_meta['title'], r'^Unknown Album.*$')
        self.assertEqual(disc_meta['duration'], 197067024)

        for track in disc_meta['tracks']:
            self.assertEqual(track['title'], 'Unknown Title')
            self.assertEqual(track['artist'], 'Unknown Artist')

    @patch('hifi_appliance.disc.disc._read_toc_into_file')
    def test_cdtext(self, mocked_read_toc):
        toc_path = os.path.join(os.path.dirname(__file__), 'data', 'toc', 'cdtext')
        disc_meta = read_disc_meta('disc_id', str(toc_path))

        self.assertEqual(len(disc_meta['tracks']), 11)
        self.assertEqual(disc_meta['title'], 'The Division Bell')
        self.assertEqual(disc_meta['duration'], 175854336)

        for track in disc_meta['tracks']:
            self.assertNotEqual(track['title'], 'Unknown Track')
            self.assertEqual(track['artist'], 'Pink Floyd')

    @patch('hifi_appliance.disc.disc._read_toc_into_file')
    def test_toc_error(self, mocked_read_toc):
        toc_path = os.path.join(os.path.dirname(__file__), 'data', 'toc', 'cdtext')
        with patch.object(Toc, '__init__', side_effect=TOCError()) as mock_method:
            disc_meta = read_disc_meta('disc_id', str(toc_path))
            self.assertEqual(None, disc_meta)
