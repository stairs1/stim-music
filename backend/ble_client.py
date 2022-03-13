from simplepyble import Adapter
import time
import threading
from queue import Queue, Empty
import multiprocessing

SERVICE_UUID = "db70e3a8-6cdc-46da-a256-8e1dfedb4bde"
CHARACTERISTIC_UUID = "49db2ddd-3691-44d3-a0e6-86d2c582ab7e"

class StimClient:

    def __init__(self, msg_q):
        self.state = 'off'
        self.peripheral = None
        self.msg_q = msg_q

    def kill(self):
        pass

    def async_sender(self):
        while True:
            #wait for next chunk in queue and send it
            msg = self.msg_q.get()
            self.send_command(msg)

    def connect(self):
        self.adapter = Adapter.get_adapters()[0]
        self.adapter.set_callback_on_scan_start(lambda: print("Scan started."))
        self.adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))

        self.adapter.scan_for(3000)
        peripherals = self.adapter.scan_get_results()

        try:
            self.peripheral = next(p for p in peripherals if "Brain Stimulator" in p.identifier())
        except StopIteration:
            print("Failed to find Brain Stimulator")
            return

        print(f"Connecting to: {self.peripheral.identifier()} [{self.peripheral.address()}]")
        self.peripheral.connect()
        print(f"Brain Stimulator Connected")

    def disconnect(self):
        if self.peripheral:
            self.peripheral.disconnect()

    def send_command(self, cmd):
        print("BLE - sending command: {}".format(cmd))
        self.peripheral.write_request(SERVICE_UUID, CHARACTERISTIC_UUID, str.encode(cmd))

    def send_command_async(self, cmd):
        self.packets_to_send_queue.put(cmd)

    def off(self):
        self.send_command('off')

    def flip(self):
        self.state = 'pos' if self.state == 'neg' else 'neg'
        self.send_command(self.state)

    def start_stim(self):
        command = "start"
        self.send_command(command)

    def send_stim_chunk(self, chunk):
        """
        Chunk should be a string of hex numbers
        """
        self.send_command(chunk)

class DualStimClient:
    def __init__(self):
        self.state_1 = 'off'
        self.state_2 = 'off'
        self.peripheral_1 = None
        self.peripheral_2 = None

    def connect(self):
        self.adapter = Adapter.get_adapters()[0]
        self.adapter.set_callback_on_scan_start(lambda: print("Scan started."))
        self.adapter.set_callback_on_scan_stop(lambda: print("Scan complete."))

        self.adapter.scan_for(3000)
        peripherals = self.adapter.scan_get_results()

        try:
            peripheral_gen = (p for p in peripherals if "Brain Stimulator" in p.identifier())
            self.peripheral_1 = next(peripheral_gen)
            self.peripheral_2 = next(peripheral_gen)
            # self.peripheral = next(p for p in peripherals if "Cayden" in p.identifier())
        except StopIteration:
            print("Failed to find Brain Stimulator(s)")
            return

        print(f"Connecting to: {self.peripheral_1.identifier()} [{self.peripheral_1.address()}]")
        self.peripheral_1.connect()
        print(f"Brain Stimulator Connected")
        print(f"Connecting to: {self.peripheral_2.identifier()} [{self.peripheral_2.address()}]")
        self.peripheral_2.connect()
        print(f"Brain Stimulator Connected")

    # def disconnect(self):
    #     if self.peripheral:
    #         self.peripheral.disconnect()

    def send_command(self, cmd, peripheral):
        peripheral.write_request(SERVICE_UUID, CHARACTERISTIC_UUID, str.encode(cmd))

    def off(self):
        self.send_command('off', self.peripheral_1)
        self.send_command('off', self.peripheral_2)

    def flip_1(self):
        self.state_1 = 'pos' if self.state_1 == 'neg' else 'neg'
        self.send_command(self.state_1, self.peripheral_1)

    def flip_2(self):
        self.state_2 = 'pos' if self.state_2 == 'neg' else 'neg'
        self.send_command(self.state_2, self.peripheral_2)
    
    def pos_1(self):
        self.state_1 = 'pos'
        self.send_command('pos', self.peripheral_1)

    def pos_2(self):
        self.state_2 = 'pos'
        self.send_command('pos', self.peripheral_2)

    def neg_1(self):
        self.state_1 = 'neg'
        self.send_command('neg', self.peripheral_1)

    def neg_2(self):
        self.state_2 = 'neg'
        self.send_command('neg', self.peripheral_2)
    
    def off_1(self):
        self.state_1 = 'off'
        self.send_command('off', self.peripheral_1)

    def off_2(self):
        self.state_2 = 'off'
        self.send_command('off', self.peripheral_2)
    
    def seizure(self):
        self.off()
        actions = [
            self.off,
            self.pos_1,
            self.flip_1,
            self.pos_2,
            self.flip_1,
            self.flip_2,
            self.flip_1,
            self.flip_2
        ]
        for action in actions:
            action()
            time.sleep(0.05)



if __name__ == "__main__":
    client = StimClient()
    client.connect()
    time.sleep(3)
    client.disconnect()
