from audiostim import AudioStim
from ble_client import StimClient


#these functions connects the AudioStim output to whatever frontend hardware you want
#used to decouple generation of stim and sending of the data
def connect_callback(chunk):
    print(chunk)
    chunk_string = ""
    #incoming is floats form 0 to 1, convert this to integer 0-255, then to hex string
    for sample in chunk:
        transform_sample = int(sample * 255)
        hex_sample_string = hex(transform_sample)[2:]
        print(hex_sample_string)
        chunk_string += hex_sample_string
    print(chunk_string)
    client.send_command(chunk_string)

def start_callback():
    print("Starting now")
    client.start_stim()

#open connection to GVS StimMusic++ ESP32 hardware
client = StimClient()
client.connect()

#setup music audio and generate stim track
audiostim = AudioStim(stim_data_callback=connect_callback, stim_start_callback=start_callback)
audiostim.open_audio_file("./Horse.webm")
audiostim.generate_stim_track()

#play music and stim
audiostim.play_music_plus_plus()

#disconnect client when done
client.disconnect()
