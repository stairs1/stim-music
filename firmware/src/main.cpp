#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <string.h>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <string>

using namespace std;

#define SERVICE_UUID "db70e3a8-6cdc-46da-a256-8e1dfedb4bde"
#define CHARACTERISTIC_UUID "49db2ddd-3691-44d3-a0e6-86d2c582ab7e"
#define DESCRIPTOR_UUID "6bdec572-c935-4b09-80de-de3c475d0763"

#define CONST_PIN 26    // D3 on beetle
#define VARIABLE_PIN 25 // D2 on beetle
#define LED_PIN 13      // D7 on beetle
#define STIM_RATE 20    // Hz

const float STIM_PERIOD = 1000 / STIM_RATE; // milliseconds
const int dac_buffer_len = STIM_RATE * 5;   // 5-second buffer capacity (circular)
const int dac_buffer_min = STIM_RATE * 1;   // 1-second ble-stim buffering
const float v_dac_8_bit_const = 255;
const float v_dac_8_bit_high = 141;
const float v_dac_8_bit_low = 186;
int dac_bufffer[dac_buffer_len];
int read_ptr = 0;
int write_ptr = 0;
enum states
{
    idle,
    config_cold,
    config_warm,
    stim_cold,
    stim_warm
};
int state = idle;

void set_state(states new_state)
{
    Serial.printf("Setting State to %d\n", new_state);
    state = new_state;
}

BLEServer *server;

class ServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *server)
    {
        Serial.println("connected");
    };

    void onDisconnect(BLEServer *server)
    {
        Serial.println("disco-connected");
        server->getAdvertising()->start();
    };
};

class CharacteristicCallbacks : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic)
    {
        std::string value = characteristic->getValue();
        if (value == "stim")
        {
            Serial.println("stimulation mode");
            read_ptr = 0;
            write_ptr = 0;
            set_state(states::stim_cold);
        }
        else if (value == "idle")
        {
            Serial.println("inactive mode");
            read_ptr = 0;
            write_ptr = 0;
            set_state(states::idle);
            digitalWrite(LED_PIN, LOW);
            dacWrite(VARIABLE_PIN, 0.5 * (v_dac_8_bit_high - v_dac_8_bit_low) + v_dac_8_bit_low);
        }
        else if (value == "config")
        {
            Serial.println("config mode");
            read_ptr = 0;
            write_ptr = 0;
            set_state(states::config_cold);
        }
        else
        {
            // decode and add to buffer
            // assume each value is 2 hex characters
            for (int i = 0; i < value.length(); i += 2)
            {
                char toConv[3];
                toConv[0] = value[i];
                toConv[1] = value[i + 1];
                toConv[2] = '\n';
                float stimVal = (float)strtol(toConv, 0, 16);

                int dacVal = state == states::config_cold || states::config_warm
                                 ? stimVal
                                 : stimVal / 255.0 * (v_dac_8_bit_high - v_dac_8_bit_low) + v_dac_8_bit_low;

                dac_bufffer[write_ptr] = dacVal;
                write_ptr = (write_ptr + 1) % dac_buffer_len;

                // Return to idle mode instead of overflowing buffer
                if (write_ptr == read_ptr)
                {
                    Serial.println("buffer full, stopping stim");
                    set_state(states::idle);
                }
            }
        }
    };
};

void setup()
{
    Serial.begin(9600);

    // Stim control signal setup
    pinMode(CONST_PIN, OUTPUT);
    pinMode(VARIABLE_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    dacWrite(CONST_PIN, v_dac_8_bit_const);

    // Server setup
    BLEDevice::init("Brain Stimulator 0.0.4");
    server = BLEDevice::createServer();
    server->setCallbacks(new ServerCallbacks());
    server->getAdvertising()->addServiceUUID(SERVICE_UUID);

    // Service setup
    BLEService *service = server->createService(SERVICE_UUID);

    // Characteristic setup
    BLECharacteristic *characteristic = service->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_WRITE);
    characteristic->setCallbacks(new CharacteristicCallbacks());
    BLEDescriptor HiLowOffDescriptor(DESCRIPTOR_UUID);
    HiLowOffDescriptor.setValue("low | med | high");
    characteristic->addDescriptor(&HiLowOffDescriptor);

    // Start
    service->start();
    server->getAdvertising()->start();
}

unsigned long start_time;
unsigned long stims_done = 0;
unsigned long flashes_done = 0;

void loop()
{
    switch (state)
    {
        case idle:
            break;

        case config_cold:
        {
            if (write_ptr > read_ptr + dac_buffer_min)
            {
                set_state(config_warm);
                start_time = millis();
                flashes_done = 0;
            }
            break;
        }
        case config_warm:
        {
            // Return to idle mode if buffer empties - stay in sync or die
            if (read_ptr == write_ptr)
            {
                Serial.println("Buffer emptied - pausing");
                set_state(idle);
                break;
            }

            // stim gradually drifts over time
            // stims_to_do will = 2 when it has drifted more than the sampling period
            int flashes_to_do = static_cast<int>((millis() - start_time) / 1000.0 * STIM_RATE) - flashes_done;
            if (flashes_to_do > 0)
            {
                flashes_done += flashes_to_do;
            }
            else
            {
                delay(STIM_PERIOD / 10);
                break;
            }

            // Write LED and increment read pointer
            int led_value = dac_bufffer[read_ptr] > 128 ? HIGH : LOW;
            Serial.printf("Configure value : %d\n", led_value);
            digitalWrite(LED_PIN, led_value);
            read_ptr = (read_ptr + flashes_to_do) % dac_buffer_len;
            break;
        }
        case stim_cold:
        {
            if (write_ptr > read_ptr + dac_buffer_min)
            {
                set_state(stim_warm);
                start_time = millis();
                stims_done = 0;
            }
            break;
        }
        case stim_warm:
        {
            // Return to idle mode if buffer empties - stay in sync or die
            if (read_ptr == write_ptr)
            {
                Serial.println("Buffer emptied - pausing");
                set_state(idle);
                break;
            }
            // stim gradually drifts over time
            // stims_to_do will = 2 when it has drifted more than the sampling period
            int stims_to_do = static_cast<int>((millis() - start_time) / 1000 * STIM_RATE) - stims_done;
            if (stims_to_do > 0)
            {
                stims_done += stims_to_do;
            }
            else
            {
                delay(STIM_PERIOD / 10);
                break;
            }

            // Write DAC & increment read pointer
            Serial.printf("DAC value: %d\n", dac_bufffer[read_ptr]);
            dacWrite(VARIABLE_PIN, dac_bufffer[read_ptr]);
            read_ptr = (read_ptr + stims_to_do) % dac_buffer_len;
            break;
        }
    }
}