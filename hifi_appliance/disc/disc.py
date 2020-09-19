import os
from pathlib import Path
import subprocess
import tempfile

import discid
from coolname import generate

from .toc import Toc, TOCError
from ..config import CD_DEVICE


def read_disc_id():
    try:
        disc = discid.read(CD_DEVICE)
        return disc.id
    except discid.disc.DiscError:
        return None


def _read_toc_into_file(toc_filepath):
    with open(os.devnull, 'w') as dev_null:
        try:
            subprocess.call(['cdrdao', 'read-toc', '--fast-toc', toc_filepath], stdout=dev_null, stderr=dev_null)
        except subprocess.CalledProcessError as e:
            pass


def _convert_track_info(toc_track_info):
    duration = toc_track_info['file_length']
    if 'pregap_silence' in toc_track_info.keys():
        duration += toc_track_info['pregap_silence']

    artist = toc_track_info['artist'] if 'artist' in toc_track_info.keys() else 'Unknown Artist'
    title = toc_track_info['title'] if 'title' in toc_track_info.keys() else 'Unknown Title'

    return {
        'duration': duration,
        'artist': artist,
        'title': title
    }


def read_disc_meta(disc_id, toc_filepath=tempfile.NamedTemporaryFile().name):
    _read_toc_into_file(toc_filepath)

    try:
        toc = Toc(Path(toc_filepath).read_text())
        disc_meta = toc.disc_meta
        if 'title' not in disc_meta.keys():
            disc_meta['title'] = 'Unknown Album %s' % ''.join(x.capitalize() for x in generate())

        tracks = [_convert_track_info(track) for track in disc_meta['tracks']]
        duration = sum(track['duration'] for track in tracks)

        return {
            'disc_id': disc_id,
            'title': disc_meta['title'],
            'tracks': tracks,
            'duration': duration,
            'cd': 1,
            'total_cds': 1
        }
    except TOCError:
        return None
