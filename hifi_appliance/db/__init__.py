import sys

from .db import TrackDB


sys.modules[__name__] = TrackDB()
