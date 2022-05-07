from time import time, sleep
from ble_client import StimClient
from threading import Thread
from multiprocessing import Process, Manager

CHUNK_SIZE = 20  # samples
STIM_FREQUENCY = 20  # Hz
STIM_PERIOD = 1 / STIM_FREQUENCY


class StimThread(Thread):
    def run(self):
        """
        Play stim by buffering & sending track over BLE.
        To maintain calibration, play a zero-stim track while stim buffer is empty.

        Sends ~1-second chunks each ~1-second
        """

        self.msg_q = msg_q = Manager().Queue()
        self.client_bt_process = Process(target=ble_process, args=[msg_q])
        self.client_bt_process.start()

        self.stim_buffer = []
        self.ble_buffer = []
        self.active = True
        start_time = time()
        n_sent = 0
        n_added = 0

        try:
            # Maintain a constant zero-stim stream to keep timing aligned
            while self.active:
                sample_num = int((time() - start_time) * STIM_FREQUENCY)

                # Add stim data or zero-voltage to ble buffer
                n_to_add = sample_num - n_added
                for _ in range(n_to_add):
                    self.ble_buffer.append(
                        self.stim_buffer.pop(0) if self.stim_buffer else 0.5
                    )
                    n_added += 1

                # Send chunks to stimulator
                n_to_send = sample_num - n_sent
                if n_to_send >= CHUNK_SIZE:
                    to_send = self.ble_buffer[:n_to_send]
                    del self.ble_buffer[:n_to_send]
                    msg_q.put(encode(to_send))
                    n_sent += n_to_send

                sleep(STIM_PERIOD)
        except KeyboardInterrupt:
            print("exiting stim thread")
            self.stop()

    def stop(self):
        self.active = False
        self.msg_q.put("close")

    def stimulate(self, track):
        self.stim_buffer += track

    def reconnect(self):
        self.msg_q.put("reconnect")

    def config(self):
        self.msg_q.put("config")


def ble_process(msg_q):
    client = StimClient(msg_q)
    client.connect()
    client.async_sender()


def encode(stim_data):
    chunk_string = ""
    # incoming is floats form 0 to 1, convert this to integer 0-255, then to hex string
    for sample in stim_data:
        transform_sample = int(sample * 255)
        hex_sample_string = hex(transform_sample)[2:]
        if len(hex_sample_string) < 2:  # we want all hex numbers to have 2 digits
            hex_sample_string = "0" + hex_sample_string
        chunk_string += hex_sample_string

    return chunk_string
