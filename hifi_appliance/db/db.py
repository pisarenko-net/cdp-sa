import logging
import os
import re
from pathlib import Path
import threading
import time

from filelock import FileLock
import pickledb

from ..config import DB_FILE_PATH
from ..config import DB_REBUILD_INTERVAL
from ..config import MUSIC_PATH_NAME


_TRACK_REGEX = re.compile(r'^\d\d .*\.flac$', re.IGNORECASE)


logger = logging.getLogger(__name__)


class TrackDB(object):
    def __init__(self):
        self._lock = FileLock('%s%s' % (DB_FILE_PATH, '.lock'))
        self._db = pickledb.load(DB_FILE_PATH, False)
        if not Path(DB_FILE_PATH).is_file():
            self.rebuild()

        self.updater = threading.Thread(
            target=self._rebuild_loop,
            name='db builder'
        )
        self.updater.daemon = True
        self.updater.start()

    def has_disc(self, disc_id):
        return self._db.exists(disc_id)

    def get_track_list(self, disc_id):
        return self._db.get(disc_id)['track_files']

    def store_track_list(self, disc_id, track_files):
        self._db.set(disc_id, track_files)

    def persist(self):
        with self._lock:
            self._db().dump()

    def count(self):
        return self._db.totalkeys()

    def rebuild(self):
        logger.info('Rebuilding track database')

        discs = {}
        for root, _, files in os.walk(MUSIC_PATH_NAME):
            if '.disc_id' in files:
                disc_id = Path(root).joinpath('.disc_id').read_text().replace('\n', '')
                track_files = sorted([str(Path(root).joinpath(file)) for file in files if _TRACK_REGEX.match(file)])
                discs[disc_id] = {
                    'track_files': track_files
                }

        with self._lock:
            self._db.deldb()
            for disc_id in discs:
                self.store_track_list(disc_id, discs[disc_id])
            self._db.dump()

        logger.info('Track database rebuilt, %s discs indexed', self.count())

    def _rebuild_loop(self):
        while True:
            time.sleep(DB_REBUILD_INTERVAL)
            self.rebuild()
