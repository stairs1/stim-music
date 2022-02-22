from simplepyble import Adapter
from time import sleep

SERVICE_UUID = "db70e3a8-6cdc-46da-a256-8e1dfedb4bde"
CHARACTERISTIC_UUID = "49db2ddd-3691-44d3-a0e6-86d2c582ab7e"

class StimClient:

    def __init__(self):
        self.state = 'off'
        self.peripheral = None

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
        self.peripheral.write_request(SERVICE_UUID, CHARACTERISTIC_UUID, str.encode(cmd))

    def off(self):
        self.send_command('off')

    def flip(self):
        self.send_command('pos' if self.state == 'neg' else 'neg')


if __name__ == "__main__":
    client = StimClient()
    client.connect()
    sleep(3)
    client.disconnect()