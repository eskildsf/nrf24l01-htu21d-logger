#include "LowPower.h"
#include <avr/power.h>

#include <SPI.h>
#include "RF24.h"
RF24 radio(7,8);

struct DataPoint{long beep; long c;};

byte LDR = 0;
int count_low = 0;
int count_high = 0;
byte threshold_count_high = 10;
byte threshold_count_low = 50;

// Voltage divider model: V[out] = V[in] * Z2/(Z1 + Z2)
// where Z1 is the LDR and Z2 is the additional resistor
// LDR is activated for Z1 < 10.000 ohm. Reasonbalbe to read over 4 V
// hence Z2 = 40.000 ohm. Hence for Z2 = 47k voltages over 4.1 V
// correspond to a LDR resistance of less than 10.000 ohm.
// There are approximately 4.9 mV pr. unit of analogRead. Hence
// 4.1 V corresponds to 837 on the analogRead scale.

int LDR_value = 0;
int threshold_LDR_value = 650;

void setup() {
  //Serial.begin(115200);
  radio.begin();
  radio.setDataRate(RF24_250KBPS);
  radio.openWritingPipe(0xF0F0F0F033);
  radio.openReadingPipe(1,(uint8_t*) "1000r");
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
  //power_usart0_disable();
}

void loop() {
  LDR_value = analogRead(LDR);
  if ( count_high > threshold_count_high && count_low > threshold_count_low ) {
    //Serial.println(count);
    long beep = LDR_value;
    DataPoint datapoint = {beep, count_high};
    radio.write(&datapoint, sizeof(DataPoint));
    count_low = 0; count_high = 0;
  } else if ( LDR_value > threshold_LDR_value ) {
    //Serial.println(LDR_value);
    count_high = count_high + 1;
  } else if ( LDR_value < threshold_LDR_value && count_high > threshold_count_high ) {
    count_low = count_low + 1;
  }
}
