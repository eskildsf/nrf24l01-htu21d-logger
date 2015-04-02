#include <Wire.h>
#include "HTU21D.h"
HTU21D myHumidity;

#include <SPI.h>
#include "RF24.h"
RF24 radio(7,8);

struct dataStruct{
  float temperature;
  float humidity;
}myData;

unsigned long recv;
unsigned long lastMeasurement;

void setup() {
  myHumidity.begin();

  radio.begin();
  radio.openWritingPipe(0xF0F0F0F0D2);
  radio.openReadingPipe(1,0xF0F0F0F0E1);
  radio.startListening();
  lastMeasurement = millis();
}

void loop() {
  // Measure and return data on request.
  while (radio.available()) {
    radio.read(&recv, sizeof(unsigned long));
    // Only do measurements once every second.
    if ( (unsigned long)(millis() - lastMeasurement) > 1000 ) {
      radio.stopListening();
      myData.humidity = myHumidity.readHumidity();
      myData.temperature = myHumidity.readTemperature();
      radio.write(&myData, sizeof(myData));
      lastMeasurement = millis();
      radio.startListening();
    }
  }
}
