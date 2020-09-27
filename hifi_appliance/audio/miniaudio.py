from concurrent.futures import ThreadPoolExecutor
import io
import logging
import subprocess
import threading

import miniaudio
from ringbuf import RingBuffer

from ..constants import BUFFER_SIZE
from ..constants import CHANNELS
from ..constants import SAMPLE_RATE
from ..constants import SAMPLE_WIDTH


logger = logging.getLogger(__name__)


class MiniaudioSink(object):
    """
    Audio device interface. Internally uses a stream from which frames are read
    into an output sound device. The stream is backed by a buffer. This buffer
    is appended to with track PCM data. This object doesn't care about the overall
    state of the application -- it just feeds frames into sound card and expects
    an outside actor to tell it what other file to load. Since the buffer maintains
    a healthy headroom gapless playback is achieved with no special effort.

    `ffmpeg` is invoked to perform conversion to PCM. Tracks are loaded at once into
    memory.
    """
    def __init__(
        self,
        playback_stopped_callback = lambda: print('playback stopped'),
        frames_played_callback = lambda: print(".", end="", flush=True)
    ):
        self.playback_stopped_callback = playback_stopped_callback
        self.frames_played_callback = frames_played_callback

        # the audio stops and should be started
        # from scratch as soon as this lock is released
        self.running = threading.RLock()
        self.running.acquire()

        self.playing = threading.Event()
        self.pause()

        self.stream = RingBuffer(format='B', capacity=BUFFER_SIZE)

        self.frames_callback_executor = ThreadPoolExecutor(max_workers=1)

        self.thread = threading.Thread(
            target=self._start_device,
            name='audio device'
        )
        self.thread.daemon = True
        self.thread.start()

    def _start_device(self):
        with miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=CHANNELS,
            sample_rate=SAMPLE_RATE) as device:

            generator = self._read_frames()
            next(generator)
            device.start(generator)
            self.running.acquire()  # keep the thread running or else audio stops

    def _read_frames(self):
        required_frames = yield b''
        while True:
            self.playing.wait()
            required_bytes = required_frames * CHANNELS * SAMPLE_WIDTH
            sample_data = self.stream.pop(required_bytes)

            if not sample_data:
                self.playback_stopped_callback()
                break

            self._on_frames_played(required_frames)
            required_frames = yield sample_data

    def _on_frames_played(self, frames):
        self.frames_callback_executor.submit(self.frames_played_callback, frames)

    def buffer_track(self, track_file_name):
        logger.debug('Loading track %s into buffer', track_file_name)

        pcm_data = subprocess.run(
            [
                "ffmpeg", "-v", "fatal", "-hide_banner", "-nostdin",
                "-i", track_file_name, "-f", "s16le", "-acodec", "pcm_s16le",
                "-ac", str(CHANNELS), "-ar", str(SAMPLE_RATE), "-"
            ],
            capture_output=True
        ).stdout

        self.stream.push(pcm_data)
        return self.get_frame_count(pcm_data)

    def get_frame_count(self, pcm_data):
        return len(pcm_data) // (CHANNELS * SAMPLE_WIDTH)

    def pause(self):
        self.playing.clear()

    def resume(self):
        self.playing.set()

    def release(self):
        """
        Once this has been called a new object should be created and the existing one
        cannot be used anymore.
        """
        self.running.release()
