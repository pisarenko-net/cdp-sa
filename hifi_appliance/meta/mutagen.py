import mutagen

from ..constants import CHANNELS


class MutagenTagReader(object):
	def query(self, disc_id, track_files):
		disc_meta = {
			'disc_id': disc_id,
			'tracks': []
		}

		for track_filename in track_files:
			flac_data = mutagen.File(track_filename)
			disc_meta['tracks'].append({
				'artist': flac_data['artist'][0],
				'title': flac_data['title'][0],
				'duration': flac_data.info.total_samples // CHANNELS
			})
			disc_meta['title'] = flac_data['album']

		disc_meta['duration'] = sum(track['duration'] for track in disc_meta['tracks'])

		return disc_meta


def write_meta(track_filename, artist, title, album_title, track_number, total_tracks):
	flac_data = mutagen.File(track_filename)
	flac_data['title'] = title
	flac_data['artist'] = artist
	flac_data['album'] = album_title
	flac_data['tracknumber'] = str(track_number)
	flac_data['tracktotal'] = str(total_tracks)
	flac_data.save()
