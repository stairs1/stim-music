from audiostim import AudioStim
import time
from ble_client import StimClient
from multiprocessing import Process, Manager

m = Manager()
msg_q = m.Queue()

#these functions connects the AudioStim output to whatever frontend hardware you want
#used to decouple generation of stim and sending of the data
def connect_callback(chunk):
    chunk_string = ""
    #incoming is floats form 0 to 1, convert this to integer 0-255, then to hex string
    for sample in chunk:
        transform_sample = int(sample * 255)
        hex_sample_string = hex(transform_sample)[2:]
        chunk_string += hex_sample_string
    #client.send_command_async(chunk_string)
    msg_q.put(chunk_string)

def start_callback():
    print("Starting now")
    #client.start_stim()
    msg_q.put("start")

#open connection to GVS StimMusic++ ESP32 hardware
def connect_client(msg_q):
    client = StimClient(msg_q)
    client.connect()
    client.async_sender()

client_bt_process = Process(target=connect_client, args=(msg_q,))
client_bt_process.start()
time.sleep(5)

#setup music audio and generate stim track
audiostim = AudioStim(stim_data_callback=connect_callback, stim_start_callback=start_callback)
audiostim.open_audio_file("./Horse.webm")
audiostim.generate_stim_track()

#play music and stim
audiostim.play_music_plus_plus()

#disconnect client when done
#client.disconnect()
