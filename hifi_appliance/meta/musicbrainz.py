import musicbrainzngs
from retrying import retry

from ..constants import SAMPLE_RATE


class MusicbrainzLookup(object):
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=100)
    def query(self, disc_id):
        musicbrainzngs.set_useragent('cdp-sa', '0.0.1')
        musicbrainzngs.auth('', '')

        disc_meta = {
            'disc_id': disc_id,
            'tracks': []
        }

        try:
            response = musicbrainzngs.get_releases_by_discid(
                disc_id,
                includes=["artists", "artist-credits", "recordings"]
            )
        except musicbrainzngs.musicbrainz.ResponseError:
            return None

        if not 'disc' in response.keys() or not 'release-list' in response['disc'].keys():
            return None

        this_release = response['disc']['release-list'][0]
        disc_meta['title'] = this_release['title']
        disc_meta['total_cds'] = len(list(
            filter(
                lambda medium: medium['format'] == 'CD',
                this_release['medium-list']
            )
        ))

        for medium in this_release['medium-list']:
            for disc in medium['disc-list']:
                if disc['id'] == disc_id:
                    disc_meta['cd'] = int(medium['position'])
                    tracks = medium['track-list']
                    for track in tracks:
                        artist = track['recording']['artist-credit'][0]['artist']['name']
                        disc_meta['tracks'].append({
                            'artist': artist,
                            'title': track['recording']['title'],
                            'duration': (int(track['length']) // 1000) * SAMPLE_RATE
                        })
                    break

        if not disc_meta['tracks']:
            return None

        disc_meta['duration'] = sum(track['duration'] for track in disc_meta['tracks'])

        return disc_meta
