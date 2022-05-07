"""
Invoke me as a file, I will throw up a prompt and respond to commands
"""
import sys
from cmd import Cmd
from audio_thread import AudioThread
import numpy as np
import math

from stim_thread import StimThread


class Cli(Cmd):
    def do_hi(self, line):
        """
        Say hello
        """
        print(f"sup guy")

    def do_quit(self, line):
        """
        Quit the program
        """
        print("ta-ta for now")
        stim_thread.stop()
        audio_thread.stop()
        sys.exit()

    def do_q(self, line):
        """
        Quit the program
        """
        self.do_quit(line)

    def do_h(self, line):
        """
        Print help menu
        """
        self.do_help(line)

    def do_connect(self, line):
        """
        Connect to Brain Stimulator
        """
        if not stim_thread.is_alive():
            stim_thread.start()
        else:
            stim_thread.reconnect()

    def do_co(self, line):
        """
        Connect to Brain Stimulator
        """
        self.do_connect(line)

    def do_calibrate(self, line):
        """
        Calibrate sound and stim to line up
        """
        stim_thread.config()

    def do_ca(self, line):
        """
        Calibrate sound and stim to line up
        """
        self.do_calibrate(line)

    def do_init(self, line):
        """
        Connect to stimulator and initialize audio. Called by default on load
        """
        self.do_connect(line)
        audio_thread.start()

    def do_i(self, line):
        """
        Connect to stimulator and initialize audio. Called by default on load
        """
        self.do_init(line)

    def do_l(self, line):
        """
        Shift sound to happen {milliseconds} later relative to stim (left-shift stim)
        """
        audio_thread.add_delay(int(line))

    def do_r(self, line):
        """
        Shift sound to happen {milliseconds} relative to stim (right-shift stim)
        """
        audio_thread.add_delay(-1 * int(line))

    def do_t(self, line):
        """
        Play a test impulse through audio and stim
        """
        stim_thread.stimulate([1, 1])  # 2*50ms = 100ms

        FREQUENCY = 698.46  # Hz, waves per second, 261.63=C4-note.
        LENGTH = 0.1  # 100ms, seconds to play sound
        NUMBEROFFRAMES = int(audio_thread.bitrate * LENGTH)
        beep = np.sin(
            np.linspace(0, 1, NUMBEROFFRAMES, dtype=np.float32)
            * FREQUENCY
            * LENGTH
            * (2 * math.pi)
        )
        audio_thread.play(beep)

    def do_play(self, line):
        """
        Play audio track with stim track
        """
        pass


stim_thread = StimThread()
audio_thread = AudioThread()


cli = Cli()
cli.do_init(None)
cli.cmdloop(intro="Welcome, Neural Jockey.\nEnter h for menu\n")
