import io
import shutil
import subprocess
import threading

import miniaudio

from .stream_rw import StreamRW
from ..constants import BUFFER_REFRESH_THRESHOLD
from ..constants import CHANNELS
from ..constants import MEMORY_STREAM_GC_THRESHOLD
from ..constants import SAMPLE_RATE
from ..constants import SAMPLE_WIDTH


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

    Occassionally, the buffer is garbage collected to free up memory taken by played
    PCM frames.

    Supported commands are:
     * play_next -- read given track into memory and append to buffer. This won't start
       playback if the object is in paused or stopped state.
     * play_now -- read given track and start playing it immediately, clearing
       existing buffer. Starts playback even if was paused or stopped before.
     * pause -- pauses buffer at current position
     * resume -- resumes buffer at current position
     * stop -- halt playback
     * release -- stops everything and releases audio device. Object can't be used anymore
       and new one must be created.

    Callbacks are used to notify of 3 situations:
     1. track changed -- when the first frame from the next track from buffer is read
     2. buffer low -- when there's less than 45s worth of frames left in the buffer
     3. playback stopped -- buffer ran out and playback will stop
    """
    def __init__(
        self,
        track_file_name,
        track_changed_callback = lambda: print('track just changed'),
        need_data_callback = lambda: print('running out of data soon'),
        playback_stopped_callback = lambda: print('playback stopped')
    ):
        self._next_track_mark = None

        self.track_changed_callback = track_changed_callback
        self.need_data_callback = need_data_callback
        self.playback_stopped_callback = playback_stopped_callback

        # the audio stops and should be started
        # from scratch as soon as this lock is released
        self.running = threading.RLock()
        self.running.acquire()

        self.stream_lock = threading.RLock()

        self.playing = threading.Event()
        self.resume()

        self.refill_requested = threading.Event()
        self.refill_requested.clear()

        self.stream = StreamRW(io.BytesIO())
        self.play_next(track_file_name)

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

            while True:
                with self.stream_lock:
                    sample_data = self.stream.read(required_bytes)

                    if self._is_past_track_mark():
                        self._on_track_change()

                    self._maybe_gc()

                    if self._is_buffer_running_out():
                        self._on_buffer_low()

                if sample_data:
                    break

                self._on_buffer_empty()
                self.playing.wait()

            print(".", end="", flush=True)
            required_frames = yield sample_data

    def _is_past_track_mark(self):
        return self._next_track_mark and self.stream.tell() > self._next_track_mark

    def _on_track_change(self):
        self.track_changed_callback()
        self._next_track_mark = None

    def _maybe_gc(self):
        if self.stream.tell() < MEMORY_STREAM_GC_THRESHOLD:
            return

        if self._next_track_mark:
            return

        new_stream = StreamRW(io.BytesIO())
        shutil.copyfileobj(self.stream, new_stream)
        self.stream = new_stream

    def _is_buffer_running_out(self):
        current_position = self.stream.tell()
        buffer_size = self.stream.size()
        return ((buffer_size - current_position) < BUFFER_REFRESH_THRESHOLD)

    def _on_buffer_low(self):
        if self.refill_requested.is_set():
            return
        self.refill_requested.set()
        self.need_data_callback()

    def _on_buffer_empty(self):
        self.stop()
        self.playback_stopped_callback()

    def play_next(self, track_file_name):
        pcm_data = self._read_pcm(track_file_name)

        with self.stream_lock:
            self._next_track_mark = self.stream.size()
            self.stream.write(pcm_data)
            self.refill_requested.clear()

    def _read_pcm(self, track_file_name):
        ffmpeg = subprocess.Popen(
            [
                "ffmpeg", "-v", "fatal", "-hide_banner", "-nostdin",
                "-i", track_file_name, "-f", "s16le", "-acodec", "pcm_s16le",
                "-ac", str(CHANNELS), "-ar", str(SAMPLE_RATE), "-"
            ],
            stdin=None,
            stdout=subprocess.PIPE
        )
        pcm_data = ffmpeg.stdout.read()
        ffmpeg.terminate()
        return pcm_data

    def play_now(self, track_file_name):
        pcm_data = self._read_pcm(track_file_name)

        with self.stream_lock:
            self.stream = StreamRW(io.BytesIO(pcm_data))
            self.refill_requested.clear()

        self.resume()

    def pause(self):
        self.playing.clear()

    def resume(self):
        self.playing.set()

    def stop(self):
        """
        Deletes any buffered stream data and resets variables.
        """
        with self.stream_lock:
            self._next_track_mark = None
            self.stream = StreamRW(io.BytesIO())
            self.pause()
            self.refill_requested.clear()

    def release(self):
        """
        Once this has been called a new object should be created and the existing one
        cannot be used anymore.
        """
        self.running.release()
