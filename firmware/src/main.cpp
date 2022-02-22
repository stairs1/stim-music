#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <string.h>

#define SERVICE_UUID "db70e3a8-6cdc-46da-a256-8e1dfedb4bde"
#define CHARACTERISTIC_UUID "49db2ddd-3691-44d3-a0e6-86d2c582ab7e"
#define DESCRIPTOR_UUID "6bdec572-c935-4b09-80de-de3c475d0763"

BLEServer *server;

int PIN_A = 22;
int PIN_B = 23;

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
        if (value.length() > 0)
        {
            Serial.println("*********");
            Serial.print("New value: ");
            for (int i = 0; i < value.length(); i++)
                Serial.print(value[i]);

            Serial.println();
            Serial.println("*********");
        }
        if(value == "pos"){
            Serial.println("Setting pos");
            digitalWrite(PIN_A, LOW);
            delay(10);
            digitalWrite(PIN_B, HIGH);
        } else if(value == "neg") {
            Serial.println("Setting neg");
            digitalWrite(PIN_B, LOW);
            delay(10);
            digitalWrite(PIN_A, HIGH);
        } else if(value == "off"){
            Serial.println("Setting off");
            digitalWrite(PIN_A, LOW);
            digitalWrite(PIN_B, LOW);
        }
    };
};

void setup()
{
    Serial.begin(9600);

    // Stim control signal setup
    pinMode(PIN_A, OUTPUT);
    pinMode(PIN_B, OUTPUT);

    // Server setup
    BLEDevice::init("Brain Stimulator 0.0.2");
    server = BLEDevice::createServer();
    server->setCallbacks(new ServerCallbacks());
    server->getAdvertising()->addServiceUUID(SERVICE_UUID);

    // Service setup
    BLEService *service = server->createService(SERVICE_UUID);

    // Characteristic setup
    BLECharacteristic *characteristic = service->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_WRITE
    );
    characteristic->setCallbacks(new CharacteristicCallbacks());
    BLEDescriptor HiLowOffDescriptor(DESCRIPTOR_UUID);
    HiLowOffDescriptor.setValue("pos | neg | off");
    characteristic->addDescriptor(&HiLowOffDescriptor);

    // Start
    service->start();
    server->getAdvertising()->start();
}

int ticker = 0;

void loop()
{
    ticker++;
    if (ticker % 100 == 0)
    {
        if (ticker == 200)
        {
            Serial.println("Still alive");
            ticker = 1;
        }
        else
        {
            Serial.println("I be livin");
        }
    }
    delay(100);
}