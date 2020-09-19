import sys

from .musicbrainz import MusicbrainzLookup


sys.modules[__name__] = MusicbrainzLookup()
