import discid

from ..config import CD_DEVICE


def read_disc_id():
	try:
		disc = discid.read(CD_DEVICE)
		return disc.id
	except discid.disc.DiscError:
		return None
