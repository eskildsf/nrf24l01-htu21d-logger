#include "LowPower.h"

#include <Wire.h>
#include "HTU21D.h"
HTU21D myHumidity;

#include <SPI.h>
#include "RF24.h"
RF24 radio(7,8);

struct DataPoint{float temperature;float humidity;};

void setup() {
  myHumidity.begin();
  radio.begin();
  radio.maskIRQ(1,1,0); // Only give signal on rx
  radio.setDataRate(RF24_250KBPS);
  radio.openWritingPipe(0xF0F0F0F0D2);
  radio.openReadingPipe(1,0xF0F0F0F0E1);
  radio.startListening();
}

void loop() {
  // Measure and return data on request.
  while (radio.available()) {
    unsigned long recv;
    radio.read(&recv, sizeof(unsigned long));
    radio.stopListening();
    radio.powerDown();
    DataPoint datapoint = {myHumidity.readTemperature(), myHumidity.readHumidity()};
    radio.powerUp();
    radio.write(&datapoint, sizeof(DataPoint));
    radio.startListening();
  }
  attachInterrupt(0, check_radio, FALLING);
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF); 
  detachInterrupt(0);
}

void check_radio(void) {}
