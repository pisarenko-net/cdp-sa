from collections import namedtuple
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import musicbrainzngs
import mutagen

from hifi_appliance.meta import LocalMeta
from hifi_appliance.meta import RemoteMeta


class MusicbrainzTestCase(unittest.TestCase):
    def setUp(self):
        self.client = RemoteMeta()
        patch('musicbrainzngs.set_useragent').start()
        patch('musicbrainzngs.auth').start()

    def test_response_error(self):
        with patch('musicbrainzngs.get_releases_by_discid', side_effect=musicbrainzngs.musicbrainz.ResponseError()):
            self.assertEqual(self.client.query('disc_id'), None)

    def test_cd_01(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_01').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('fGn7CK2HfkKOYybwXNlbA6KkQoo-')

            self.assertEqual(disc_meta['disc_id'], 'fGn7CK2HfkKOYybwXNlbA6KkQoo-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Legacy')
            self.assertEqual(disc_meta['duration'], 206961300)
            self.assertEqual(len(disc_meta['tracks']), 20)
            self.assertEqual(disc_meta['tracks'][0]['artist'], 'David Bowie')

    def test_cd_02(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_02').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('J9495l1WqKuqHW._xsMJls1BeJ0-')

            self.assertEqual(disc_meta['disc_id'], 'J9495l1WqKuqHW._xsMJls1BeJ0-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Eliminator')
            self.assertEqual(disc_meta['duration'], 119775600)
            self.assertEqual(len(disc_meta['tracks']), 11)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'ZZ Top')

    def test_cd_03(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_03').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('XQAh463sZzABy4NyOQrb2q1_G6Y-')

            self.assertEqual(disc_meta['disc_id'], 'XQAh463sZzABy4NyOQrb2q1_G6Y-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Greatest Hits II')
            self.assertEqual(disc_meta['duration'], 200522700)
            self.assertEqual(len(disc_meta['tracks']), 17)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Queen')

    def test_cd_04(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_04').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('JMAWOlcW89_vd9xIRoo3ty49jkA-')

            self.assertEqual(disc_meta['disc_id'], 'JMAWOlcW89_vd9xIRoo3ty49jkA-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 2)
            self.assertEqual(disc_meta['title'], 'The Complete Greatest Hits')
            self.assertEqual(disc_meta['duration'], 194040000)
            self.assertEqual(len(disc_meta['tracks']), 17)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Eagles')

    def test_cd_05(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_05').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('pmwbQHX3o4xA_NeZUHG_52.6wxY-')

            self.assertEqual(disc_meta['disc_id'], 'pmwbQHX3o4xA_NeZUHG_52.6wxY-')
            self.assertEqual(disc_meta['cd'], 2)
            self.assertEqual(disc_meta['total_cds'], 2)
            self.assertEqual(disc_meta['title'], 'The Complete Greatest Hits')
            self.assertEqual(disc_meta['duration'], 189056700)
            self.assertEqual(len(disc_meta['tracks']), 16)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Eagles')

    def test_cd_06(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_06').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('VYyHlY0Pj.OzVIZ2O08uuzsFOdw-')
            expected_artists = [
                'Space',
                'Cerrone',
                'Acos CoolKAs',
                'Whispers',
                'WaR',
                'Space',
                'Sare Havlicek',
                'Architeq',
                'Oliver Cheatham',
                'The Sugarhill Gang',
                'Peach',
                'Gibson Brothers'
            ]

            self.assertEqual(disc_meta['disc_id'], 'VYyHlY0Pj.OzVIZ2O08uuzsFOdw-')
            self.assertEqual(disc_meta['cd'], 2)
            self.assertEqual(disc_meta['total_cds'], 3)
            self.assertEqual(disc_meta['title'], 'The Many Faces of Daft Punk')
            self.assertEqual(disc_meta['duration'], 163390500)
            self.assertEqual(len(disc_meta['tracks']), 12)

            for index, track in enumerate(disc_meta['tracks']):
                self.assertEqual(expected_artists[index], track['artist'])

            self.assertEqual(disc_meta['tracks'][0]['artist'], 'Space')
            self.assertEqual(disc_meta['tracks'][1]['artist'], 'Cerrone')

    def test_cd_07(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_07').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('59h_gD9RVcuGFjIHwU62mQ243y8-')

            self.assertEqual(disc_meta['disc_id'], '59h_gD9RVcuGFjIHwU62mQ243y8-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Random Access Memories')
            self.assertEqual(disc_meta['duration'], 196862400)
            self.assertEqual(len(disc_meta['tracks']), 13)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Daft Punk')

    def test_cd_08(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_08').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('ArJP04VIOxEmbWb1V8zjhapCxQw-')

            self.assertEqual(disc_meta['disc_id'], 'ArJP04VIOxEmbWb1V8zjhapCxQw-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Psychic')
            self.assertEqual(disc_meta['duration'], 119070000)
            self.assertEqual(len(disc_meta['tracks']), 8)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Darkside')

    def test_cd_09(self):
        response = json.loads(
            Path(os.path.dirname(__file__)).joinpath('data', 'musicbrainz', 'cd_09').read_text()
        )

        with patch('musicbrainzngs.get_releases_by_discid', return_value=response) as mock_method:
            disc_meta = self.client.query('JI1DFDN5AAXBSqTT7Q2hvnMHpS0-')

            self.assertEqual(disc_meta['disc_id'], 'JI1DFDN5AAXBSqTT7Q2hvnMHpS0-')
            self.assertEqual(disc_meta['cd'], 1)
            self.assertEqual(disc_meta['total_cds'], 1)
            self.assertEqual(disc_meta['title'], 'Greatest Hits')
            self.assertEqual(disc_meta['duration'], 152806500)
            self.assertEqual(len(disc_meta['tracks']), 17)
            for track in disc_meta['tracks']:
                self.assertEqual(track['artist'], 'Queen')


class MutagenTestCase(unittest.TestCase):
    @patch('mutagen.File')
    def test_one_track(self, file_mock):
        track_files = ['fake1.flac']
        disc_id = 'disc_id'

        d = {'artist': ['Hokus'], 'title': ['Pokus'], 'album': 'Krokus'}
        file_mock.return_value.info.total_samples = 123442
        file_mock.return_value.__getitem__.side_effect = d.__getitem__

        client = LocalMeta()
        disc_meta = client.query(disc_id, track_files)

        self.assertEqual(disc_meta['disc_id'], disc_id)
        self.assertEqual(disc_meta['duration'], 123442)
        self.assertEqual(disc_meta['title'], 'Krokus')
        self.assertEqual(disc_meta['tracks'][0]['artist'], 'Hokus')
        self.assertEqual(disc_meta['tracks'][0]['title'], 'Pokus')
