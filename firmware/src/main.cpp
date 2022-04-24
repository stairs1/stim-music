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
const int dac_buffer_len = STIM_RATE * 3;   // 3-second buffer
const float v_dac_8_bit_const = 255;
const float v_dac_8_bit_high = 141;
const float v_dac_8_bit_low = 186;
int dac_bufffer[dac_buffer_len];
int read_ptr = 0;
int write_ptr = 0;
bool stimulate = false;
bool configure = false;

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
        // if (value.length() > 0)
        // {
        //     Serial.println("*********");
        //     //Serial.print("New value: ");
        //     // for (int i = 0; i < value.length(); i++)
        //         //Serial.print(value[i]);

        //     //Serial.println();
        //     //Serial.println("*********");
        // }

        if (value == "stimulate")
        {
            Serial.println("stimulation mode");
            read_ptr = 0;
            write_ptr = 0;
            configure = false;
            stimulate = true;
        }
        else if (value == "inactive")
        {
            Serial.println("inactive mode");
            stimulate = false;
            configure = false;
            digitalWrite(LED_PIN, LOW);
            dacWrite(VARIABLE_PIN, 0.5 * (v_dac_8_bit_high - v_dac_8_bit_low) + v_dac_8_bit_low);
        }
        else if (value == "config")
        {
            Serial.println("config mode");
            read_ptr = 0;
            write_ptr = 0;
            stimulate = false;
            configure = true;
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

                int dacVal = configure ? stimVal : stimVal / 255.0 * (v_dac_8_bit_high - v_dac_8_bit_low) + v_dac_8_bit_low;

                // Serial.printf("%f\n", stimVal);
                // Serial.printf("%d\n", dacVal);

                dac_bufffer[write_ptr] = dacVal;
                write_ptr = (write_ptr + 1) % dac_buffer_len;
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
    BLEDevice::init("Brain Stimulator 0.0.3");
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

int ticker = 0;
unsigned long ptime = 0;

void loop()
{
    if (ticker % STIM_RATE == 0)
    {
        ticker = 0;
    }

    // protect against unexpected outputs
    if (stimulate && (read_ptr != write_ptr))
    {
        Serial.printf("DAC value: %d", dac_bufffer[read_ptr]);
        Serial.println();
        dacWrite(VARIABLE_PIN, dac_bufffer[read_ptr]);
        read_ptr = (read_ptr + 1) % dac_buffer_len;
    }
    else if (configure && (read_ptr != write_ptr))
    {
        int led_value = dac_bufffer[read_ptr] > 128 ? HIGH : LOW;
        Serial.printf("Configure value : %d\n", led_value);
        digitalWrite(LED_PIN, led_value);
        read_ptr = (read_ptr + 1) % dac_buffer_len;
    }

    unsigned long ctime = millis();
    // Serial.println(ctime - ptime);
    ptime = ctime;

    ticker++;
    delay(STIM_PERIOD);
}