#include "LowPower.h"
#include <avr/power.h>

#include <Wire.h>
#include "HTU21D.h"
HTU21D htu21d;

#include <SPI.h>
#include "RF24.h"
RF24 radio(7,8);

struct DataPoint{float temperature;float humidity;long supplyvoltage;};
const long InternalReferenceVoltage = 1056L; // Adjust this for your specific device

void setup() {
  htu21d.begin();
  radio.begin();
  radio.setDataRate(RF24_250KBPS);
  radio.openWritingPipe((uint8_t*) "1000a");
  radio.openReadingPipe(1,(uint8_t*) "1000r");
  radio.stopListening();
  // Power off adc
  //ADCSRA &= ~(1 << ADEN);
  //power_adc_disable();
  // Power off timers
  power_timer1_disable();
  TCCR2B &= ~(1 << CS22);
  TCCR2B &= ~(1 << CS21);
  TCCR2B &= ~(1 << CS20);
  power_timer2_disable();
  // Power off UART
  power_usart0_disable();
}

void loop() {
  // Measure bandgap
  analogRead(6);
  bitSet(ADMUX, 3);
  delayMicroseconds(250);
  bitSet(ADCSRA, ADSC);
  while (bit_is_set(ADCSRA, ADSC));
  long supplyVoltage = 1125300L/ADC;
  DataPoint datapoint = {htu21d.readTemperature(), htu21d.readHumidity(), supplyVoltage};
  radio.powerUp();
  radio.write(&datapoint, sizeof(DataPoint));
  radio.powerDown();
  LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
}
