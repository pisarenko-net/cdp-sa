import sys

from .musicbrainz import MusicbrainzLookup as RemoteMeta
from .mutagen import MutagenTagReader as LocalMeta
from .mutagen import write_meta