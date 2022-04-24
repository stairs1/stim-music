from audiostim import AudioStim
import time
import sys
from ble_client import StimClient
from multiprocessing import Process, Manager

m = Manager()
msg_q = m.Queue()

#these functions connects the AudioStim output to whatever frontend hardware you want
#used to decouple generation of stim and sending of the data
def send_stim_data(chunk):
    chunk_string = ""
    #incoming is floats form 0 to 1, convert this to integer 0-255, then to hex string
    for sample in chunk:
        transform_sample = int(sample * 255)
        hex_sample_string = hex(transform_sample)[2:]
        if len(hex_sample_string) < 2: #we want all hex numbers to have 2 digits
            hex_sample_string = "0" + hex_sample_string
        chunk_string += hex_sample_string
    #client.send_command_async(chunk_string)
    msg_q.put(chunk_string)

def set_stim_mode(mode):
    """
    Send mode-change commands to stim device:

    stimulate - set stim device mode to stimulation
    inactive  - set stim device mode to off
    config    - set stim device mode to configuration
    """
    msg_q.put(mode)

#open connection to GVS StimMusic++ ESP32 hardware
client = None
def connect_client(msg_q):
    global client
    client = StimClient(msg_q)
    client.connect()
    client.async_sender()

client_bt_process = Process(target=connect_client, args=(msg_q,))
client_bt_process.start()
time.sleep(5)

#setup audio stim
audiostim = AudioStim(send_stim_data=send_stim_data, set_stim_mode=set_stim_mode)

#configure delay for music/audio and stim
#audiostim.audio_delay_config()
#audiostim.stim_delay_config()

#setup music audio and generate stim track
audiostim.open_audio_file(sys.argv[1])
audiostim.generate_stim_track()

#play music and stim
audiostim.play_music_plus_plus()
audiostim.kill()

#disconnect client when done
client.kill()
