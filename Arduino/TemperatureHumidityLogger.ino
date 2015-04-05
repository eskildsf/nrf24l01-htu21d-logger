#include "LowPower.h"

#include <Wire.h>
#include "HTU21D.h"
HTU21D htu21d;

#include <SPI.h>
#include "RF24.h"
RF24 radio(7,8);

struct DataPoint{float temperature;float humidity;};
unsigned long recv;

void setup() {
  htu21d.begin();
  radio.begin();
  radio.maskIRQ(1,1,0); // Only give signal on rx
  radio.setDataRate(RF24_250KBPS);
  radio.openWritingPipe((uint8_t*) "1000a");
  radio.openReadingPipe(1,(uint8_t*) "1000r");
  radio.startListening();
}

void loop() {
  // Measure and return data on request.
  while (radio.available()) {
    radio.read(&recv, sizeof(unsigned long));
    radio.stopListening();
    //radio.powerDown();
    DataPoint datapoint = {htu21d.readTemperature(), htu21d.readHumidity()};
    //radio.powerUp();
    radio.write(&datapoint, sizeof(DataPoint));
    radio.startListening();
  }
  attachInterrupt(0, check_radio, FALLING);
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF); 
  detachInterrupt(0);
}

void check_radio(void) {}
