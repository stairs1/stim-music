import pyaudio
import wave
import sys
import os
import subprocess
from keeb_async import KeyboardThread
from sig_proc import SigProc
import numpy as np
import matplotlib.pyplot as plt
import time
import asyncio

class AudioStim:
    def __init__(self, send_stim_data, set_stim_mode):
        #audio
        self.CHUNK = 1024
        self.wf = None #wave file in memory
        self.p = None # pyaudio instance
        self.stream = None #pyaudio output audio stream
        self.audio_data = None #raw song data
        self.audio_sf = None #Hz, audio signal sampling frequency

        #stim
        self.send_stim_data = send_stim_data #where to send our stim chunks to
        self.set_stim_mode = set_stim_mode #when to start / stop playing stim, configuration mode
        self.stim_chunk_time = 1000 # milliseconds, period of chunk time
        self.stim_sf = 20 #Hz, brain stim signal sampling frequency
        self.latency_adjust = 0 #signed int to adjust the latency by self.latency_step_size
        self.latency_step_size = 5 #milliseconds, quantized to the nearest sample
        self.stim_track = None #the values to send to our stimulator, at stim_sf
        self.stim_offset = 0 #our current offset in our stim array
        self.num_samples_per_stim_packet = int((self.stim_chunk_time / 1000) * self.stim_sf) #how many samples to send per chunk for stim

        #delay config
        self.space_receive_times = list()
        self.audio_bt_delay = 0.115
        self.stim_bt_delay = 0.105

        #signal processing
        self.sig_proc = SigProc()
        self.stft_window = 100 #short time fourier transform window size in milliseconds
        self.kick_drum_band = (40, 800) #frequency range in Hz

        #setup keyboard thread
        self.keeb_thread = KeyboardThread(self.audio_config_handle_keyboard_input) #a thread which listen for keyboard commands and throws an event on this thread when one is seen

    def kill(self):
        self.keeb_thread.kill()

    def download_youtube_video(self, url):
        print("Downloading youtube video...")
        command = "youtube-dlc -f 251 {}".format(url)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        out, err = process.communicate()
        process.wait()
        if process.returncode != 0: #0 is success
            print("youtube-dlc failed to get this video. Is youtube-vlc installed (see README)")
            sys.exit()
        out = out.decode("utf-8").split("\n")

        video_name = None
        for line in out:
            dl_str = "Destination: "
            already_have_str = " has already been downloaded"
            ah_start_string = "[download] "
            file_end = ".webm"
            dl_loc = line.find(dl_str)
            ah_loc = line.find(already_have_str)
            if dl_loc != -1:
                video_name = line[dl_loc+len(dl_str):]
                video_name = video_name[:video_name.find(file_end)+len(file_end)]
                fixed_video_name = video_name.replace("(", "_").replace(")", "_").replace(" ", "_").replace("-", "_")
                mv_cmd = "mv \"{}\" {}".format(video_name, fixed_video_name)
                print(mv_cmd)
                video_name = fixed_video_name
                process = subprocess.Popen(mv_cmd, shell=True, stdout=subprocess.PIPE)
                process.wait()
                print("process return code:")
                print(process.returncode)
                if process.returncode != 0: #0 is success
                    print("mv command failed. Exiting.")
                    sys.exit()
            elif ah_loc != -1:
                video_name = line[len(ah_start_string):]
                video_name = video_name[:video_name.find(file_end)+len(file_end)]
        return video_name

    def open_audio_file(self, filename):
        if "http" in filename: #if http, it's a link, and we parse it
            if "youtube" in filename:
                filename = self.download_youtube_video(filename)
                if filename is None:
                    print("Failed to get Youtube video. Exiting.")
                    sys.exit()

        filename_no_ext, file_extension = os.path.splitext(filename)

        #if the passed in file isn't a wav, convert it to one
        if file_extension != "wav":
            if not os.path.exists(filename_no_ext + ".wav"):
                command = "ffmpeg -i '{}' {}.wav".format(filename, filename_no_ext.strip(" ").strip("-"))
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
                process.wait()
                if process.returncode != 0: #0 is success
                    print("Audio file format not supported, use WAV, MP3, WEBM, etc. Exiting.")
                    sys.exit()
        #use wav file instead
        filename = filename_no_ext + ".wav"

        #read in the audio data
        self.wf = wave.open(filename, 'rb')
        self.audio_data = self.wf.readframes(self.CHUNK)
        self.audio_sf = self.wf.getframerate()

        #open pyaudio and open an output stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                        channels=self.wf.getnchannels(),
                        rate=self.wf.getframerate(),
                        output=True)

    def generate_stim_track(self):
        #get audio data in numpy format
        audio_left, audio_right = self.get_numpy_audio()

        #do sliding window Short Time Fourier Transform
        window_size = int((self.stft_window / 1000) * self.audio_sf) #divide by 1000, because we are using milliseconds
        step_size = window_size
        audio = audio_left + audio_right
        self.sig_proc.sf = self.wf.getframerate()
        stft_freqs, stft_ps = self.sig_proc.sliding_window_psd(audio, window_size, step_size=step_size)

        #plot one of the fourier transforms
        #plt.plot(stft_freqs[30], stft_ps[30])
        #plt.show()

        #get a time series signal representing the power of the input frequency band
        kick_drum_power = self.sig_proc.get_band_power_series(stft_freqs, stft_ps, *self.kick_drum_band)

        #problem : the period (1 / samplingfrequency) of the power series is equal to the window size, so we resample to fit whatever sampling frequency our stim system is using
        current_sf = 1 / (self.stft_window / 1000)
        kick_drum_power = self.sig_proc.resample_signal(kick_drum_power, current_sf, self.stim_sf)

        #threshold that power
        kick_drum_low_threshold = 0.24
        kick_drum_high_threshold = 0.24
        kick_drum_power[kick_drum_power <= kick_drum_low_threshold] = 0
        kick_drum_power[kick_drum_power > kick_drum_high_threshold] = 1
        #kick_drum_power[(kick_drum_power < kick_drum_high_threshold) & (kick_drum_power > kick_drum_low_threshold)] = 0.5

        #flip from 1 to -1
        flip = True
        series = -1
        series_count = 3
        for i, val in enumerate(kick_drum_power):
            if val == 0 and ((series == -1) or (series > series_count)):
                if series > series_count: #if we were just in a series of 1's and now a zero, change flip and end the series
                    flip = not flip
                    series = -1
            else: #val is 1, or we are running in a series
                if flip:
                    kick_drum_power[i] = -1.0
                series += 1

        #now that we've thresholded the values and made them negative and positive, we reset by normalizing
        kick_drum_power = self.sig_proc.normalize(kick_drum_power)
        kick_drum_power[kick_drum_power > 0.8] = 0.8
        kick_drum_power[kick_drum_power < 0.2] = 0.2

        #set the stim track from the previous calculations
        self.stim_track = kick_drum_power

    def get_numpy_audio(self):
        """
        Convert audio wav file to numpy array.
        
        return tuple with (audio_left, audio_right), as numpy arrays
        """
        samples = self.wf.getnframes()
        audio = self.wf.readframes(samples)
        self.wf.rewind()

        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2**15
        audio_normalised = audio_as_np_float32 / max_int16
        channels = self.wf.getnchannels()
        audio_stereo = np.empty((int(len(audio_normalised)/channels), channels))
        audio_stereo[:,0] = audio_normalised[range(0,len(audio_normalised),2)]
        audio_stereo[:,1] = audio_normalised[range(1,len(audio_normalised),2)]
        return audio_stereo[:,0], audio_stereo[:,1]

    def add_stim_offset(self, phase_shift_seconds):
        """
        Add a positive or negative phase shift to the stim track signal
        """
        #self.stim_offset += max(0, int(self.stim_sf * phase_shift_seconds)) #does not allow for negative phase shift at start of song
        self.stim_offset += int(self.stim_sf * phase_shift_seconds)

        #if stim_offset is negative, then we must insert new values at the beginning of the stim track to create a phase delay
        if self.stim_offset < 0:
            self.stim_track = self.stim_track.insert(np.zeros(-self.stim_offset)) #insert zeros to cause a phase offset at the beginning of the song
            self.stim_offset = 0

    def send_next_stim_chunk(self):
        #send stim packet
        self.send_stim_data(self.stim_track[self.stim_offset:self.stim_offset+self.num_samples_per_stim_packet])
        self.stim_offset = self.stim_offset + self.num_samples_per_stim_packet

    def audio_delay_config(self):
        """
        Figure out the total delay between PyAudio playing audio on laptop and user hearing that audio on their bluetooth headphones/speaker.
        """
        #first, load the diract delta measure/impulse sound we are playing to the user
        self.open_audio_file("./Closed-Hi-Hat-2.wav")

        #take over the keyboard control to listen for space bar
        self.set_keeb_callback(self.audio_config_handle_keyboard_input)

        #then, play that impulse every n seconds
        impulse_freq = 1.5 #Hz
        impulse_period = 1 / impulse_freq
        audio_play_times = list()
        self.space_receive_times = list()
        print("\n\nPress the space bar in time with the beat 15 times, like you're playing a drum on the space bar...")
        time.sleep(3)
        for i in range(15):
            #play the impulse, record the time we play it
            curr_time = time.time()
            audio_play_times.append(curr_time)

            #get the audio and send it out to be played
            self.wf.rewind() #go back to beginning of sound
            self.audio_data = self.wf.readframes(self.CHUNK)
            self.stream.write(self.audio_data)

            #delay our period before we play the next impulse
            time.sleep(impulse_period)

        #compute the average delay
        drop_n = 3 #get rid of first n as that's when the user was adjusting to the speed of the rhythm
        avg_delay = np.mean(np.abs(np.array(audio_play_times[drop_n:]) - np.array(self.space_receive_times[drop_n:]))) 
        self.audio_bt_delay = avg_delay

        print("AUDIO DELAY IS: {}".format(self.audio_bt_delay))

        self.close_audio()

    def stim_delay_config(self):
        """
        Calculate delay between stim track on laptop and current output on stim device.
        """
        self.space_receive_times = []
        light_flash_times = []
        self.set_stim_mode("config")

        #take over the keyboard control to listen for space bar
        self.set_keeb_callback(self.stim_config_handle_keyboard_input)

        print("\n\n Press the space bar in time with the flashing light on your device 15 times")

        # flashes at a known frequency
        for _ in range(15):
            light_flash_times.append(time.time())
            to_send = np.zeros(20)
            to_send[:2] = 1
            self.send_stim_data(to_send)
            time.sleep(1)

        drop_n = 3 #get rid of first n as that's when the user was adjusting to the speed of the rhythm
        avg_delay = np.mean(np.abs(np.array(light_flash_times[drop_n:]) - np.array(self.space_receive_times[drop_n:]))) 
        self.stim_bt_delay = avg_delay

        print("STIM DELAY CONFIG IS: {}".format(self.stim_bt_delay))

        self.set_stim_mode("inactive")

    def set_keeb_callback(self, callback):
        self.keeb_thread.set_keeb_callback(callback)

    def play_handle_keyboard_input(self, key):
        if key == 200: #up arrow
            self.latency_adjust += 1
        elif key == 201: #down arrow
            self.latency_adjust -= 1
        print(self.latency_adjust)

    def stim_config_handle_keyboard_input(self, key):
        self.space_receive_times.append(time.time())

    def audio_config_handle_keyboard_input(self, key):
        self.space_receive_times.append(time.time())

    def close_audio(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def play_music_plus_plus(self):
        if self.audio_data == None:
            print("Called `play_music_plus_plus()` without any data loaded. Please load a song first.")
            return

        #set the starting phase adjustment
        self.add_stim_offset(self.audio_bt_delay - self.stim_bt_delay)

        #set the keyboard callback to handle latency adjustments during playback
        self.set_keeb_callback(self.play_handle_keyboard_input)

        #send first n stim packets so the ESP32 has some packets in its buffer
        n = 2
        for i in range(n): self.send_next_stim_chunk()
        time.sleep(0.3)

        #count our frames to tell the current time in the audio data
        frames = 0

        #start the stim now
        #self.set_stim_mode("stimulate")
        self.set_stim_mode("config")

        #chunk through the song, sending off stim packets as we go
        last_stim_send = 0
        while self.audio_data != '':
            #send the next stim chunk if enough time has elapsed
            audio_time_elapsed = (frames * self.CHUNK) / self.audio_sf
            if (audio_time_elapsed - last_stim_send) > (self.stim_chunk_time / 1000):
                #adjust our offset by the current latency offset that user has live set
                #phase_shift_seconds = (self.latency_adjust * self.latency_step_size) / 1000
                #self.latency_adjust = 0
                #self.add_stim_offset(phase_shift_seconds)
                self.send_next_stim_chunk()
                last_stim_send = audio_time_elapsed

            #get the audio and send it out to be played
            self.stream.write(self.audio_data)
            self.audio_data = self.wf.readframes(self.CHUNK)
            frames += 1

        self.close_audio()

if __name__ == "__main__":
    audiostim = AudioStim()
    audiostim.open_audio_file("./Horse.webm")
    #audiostim.generate_stim_track()
    audiostim.play_music_plus_plus()
