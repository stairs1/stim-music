"""
Thread to play audio.
Constantly plays silence when not in use to maintain stim calibration
"""

from pyaudio import PyAudio, paContinue
from time import sleep
import numpy as np


class AudioThread:
    def __init__(self):
        self.bitrate = 48000
        self.audiobuf = b""
        self.p = PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(4),
            channels=1,
            rate=self.bitrate,
            output=True,
            stream_callback=self.get_chunk,
        )
        self.delay = 0

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def play(self, sound):
        sleep(self.delay)
        self.audiobuf += sound.tobytes()

    def get_chunk(self, in_data, frame_count, time_info, status):
        sample_count = frame_count * 4
        sound_len = min(sample_count, len(self.audiobuf))
        silence_len = sample_count - sound_len

        frame = self.audiobuf[:sound_len] + np.zeros(silence_len).tobytes()
        self.audiobuf = self.audiobuf[sound_len:]
        return (frame, paContinue)
    
    def add_delay(self, delay):
        self.delay += delay / 1000
