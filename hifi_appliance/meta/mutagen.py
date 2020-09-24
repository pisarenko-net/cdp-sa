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
