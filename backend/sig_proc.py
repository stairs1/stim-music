import numpy as np
from scipy import signal

class SigProc:
    def __init__(self, sf = 5):
        self.sf = 5

    def calculate_psd(self, array):
        ps = np.abs(np.fft.fft(array))**2

        time_step = 1 / self.sf
        freqs = np.fft.fftfreq(array.size, time_step)
        idx = np.argsort(freqs)

        freqs = freqs[idx]
        ps = ps[idx]

        #take out negative frequencies
        ps = ps[freqs > 0]
        freqs = freqs[freqs > 0]

        return freqs, ps

    def sliding_window_psd(self, array, window_size, step_size=1):
        result_freqs = list()
        result_ps = list()
        start = 0
        end = len(array) - window_size
        for i in range(0,end,step_size):
            freqs, ps = self.calculate_psd(array[i:i+window_size])
            result_freqs.append(freqs)
            result_ps.append(ps)
        return np.array(result_freqs), np.array(result_ps)

    def get_band_power_series(self, sw_freqs, sw_ps, lowcut, highcut):
        """
        Take in result of sliding_window_psd and output a 1D signal which is the power in that band, normalized.
        """
        result = list()
        for i, curr_freq in enumerate(sw_freqs):
            #get the current ps
            curr_ps = sw_ps[i]

            #notch filter
            curr_ps = curr_ps[(curr_freq > lowcut) & (curr_freq < highcut)]

            #get average power
            avg_power = np.mean(curr_ps)
            result.append(avg_power)

        #normalize
        result = self.normalize(result)

        return result

    def resample_signal(self, array, in_sf, out_sf):
        num_samples = int(len(array) * (out_sf / in_sf))
        resampled_array = self.normalize(signal.resample(array, num_samples))
        return resampled_array

    def normalize(self, array):
        """
        Normalize between 0 and 1
        """
        mini = np.amin(array)
        array = array - mini
        maxi = np.amax(array)
        array = array / maxi
        return array


















