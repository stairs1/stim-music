"""
Each function takes in a raw audio array and uses that to generate a stim track, and then returns that stim track.

User can specify which specific feeling they want, and can try different feelings on the same song to find which is best.
"""
from sig_proc import SigProc

class Feelz:
    def __init__(self, stim_sf):
        #signal processing
        self.sig_proc = SigProc()
        self.stft_window = 100 #short time fourier transform window size in milliseconds
        self.stim_sf = stim_sf

    def notch_stft_power(self, audio, low_f, high_f, audio_sf):
        #do sliding window Short Time Fourier Transform
        window_size = int((self.stft_window / 1000) * audio_sf) #divide by 1000, because we are using milliseconds
        step_size = window_size
        self.sig_proc.sf = audio_sf
        stft_freqs, stft_ps = self.sig_proc.sliding_window_psd(audio, window_size, step_size=step_size)

        #plot one of the fourier transforms
        #plt.plot(stft_freqs[30], stft_ps[30])
        #plt.show()

        #get a time series signal representing the power of the input frequency band
        notch_power_series = self.sig_proc.get_band_power_series(stft_freqs, stft_ps, low_f, high_f)

        #the period (1 / samplingfrequency) of the power series is equal to the window size, so we resample to fit whatever sampling frequency our stim system is using
        current_sf = 1 / (self.stft_window / 1000)
        notch_power_series = self.sig_proc.resample_signal(notch_power_series, current_sf, self.stim_sf)

        return notch_power_series

    def wavey_envelope(self, audio, audio_sf):
        """ 
        Get the STFT/power time series/envelope of the song and feed directly as stim.
        """
        #the frequency range for the song
        envelope_band = (20, 20000) #frequency range in Hz

        #calculate STFT in a notch
        envelope = self.notch_stft_power(audio, *envelope_band, audio_sf)

        return envelope

    def bass_hit_square_wave(self, audio, audio_sf):
        """ 
        Detect bass drum hits and send alternating square wave sign change on every bass drum hit.

        Best Songs: Horse
        """
        #the frequency range for the kick drum
        kick_drum_band = (40, 800) #frequency range in Hz

        #calculate STFT in a notch
        kick_drum_power = self.notch_stft_power(audio, *kick_drum_band, audio_sf)

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

        #set the stim track from the previous calculations
        return kick_drum_power

