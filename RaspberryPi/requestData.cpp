#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <RF24/RF24.h>

using namespace std;

RF24 radio(RPI_V2_GPIO_P1_15, RPI_V2_GPIO_P1_24, BCM2835_SPI_SPEED_8MHZ);

struct dataStruct{
  float temperature;
  float humidity;
}myData;

int main(int argc, char** argv) {
  radio.begin();
  //radio.printDetails();

  radio.openWritingPipe(0xF0F0F0F0E1);
  radio.openReadingPipe(1,0xF0F0F0F0D2);
  radio.stopListening();
  unsigned long msg = 1;
  bool ok = radio.write(&msg, sizeof(unsigned long));
  if ( !ok ) {
    printf("Failed sending.\n");
  }
  radio.startListening();
  unsigned long started_waiting_at = millis();
  bool timeout = false;
  while ( !radio.available() && !timeout ) {
    if (millis() - started_waiting_at > 200 ) {
      timeout = true;
    }
  }

  if ( timeout ) {
    printf("Failed timeout.\n");
  } else {
    radio.read( &myData, sizeof(myData) );
    printf("T:%4.2f\nH:%4.2f", myData.temperature, myData.humidity);
  }
  return 0;
}
