# nrf24l01-htu21d-logger
Wireless temperature and humidity logging to Google Spreadsheet (or sqlite3 database or csv file) by measurement with HTU21D and wireless data transfer with NRF24L01.

#### Purpose
To log temperature and humidity data in a Google Spreadsheet.

I do it by measuring with a HTU21D on an Arduino nano, then transmitting the data to a Raspberry Pi via. NRF24L01 and then finally saving the data to Google Spreadsheet.

There are two parts to this:
* Measuring temperature and humidity
* Getting this data to Google Spreadsheet

There are a LOT of different temperature/humidity sensors but I've chosen the HTU21D. It is very accurate and just a little bit more expensive than the well-known DHT22. Both can be bought cheaply on ebay which I highly recommend.
I've chosen to use the NRF24L01 because it does two-way communication cheaply. You can also use a 433 MHz RF transmitter/receiver but that doesn't give the same reliable protocol that the NRF24L01 offers. They cost about the same anyway however the NRF24L01 seems to have a bit shorter range which I guess can be an issue for some applications. I will use one in the basement just below my apartment so range is not an issue for me.

#### In action:
Getting readings from the logger.py program that is actively logging to Google Spreadsheet.

<a href="https://cloud.githubusercontent.com/assets/5280714/6962722/7818ee02-d937-11e4-9577-0dcc71df5571.png"><img width="200" src="https://cloud.githubusercontent.com/assets/5280714/6962722/7818ee02-d937-11e4-9577-0dcc71df5571.png" /></a>

Data and live plot in Google Spreadsheet.

<a href="https://cloud.githubusercontent.com/assets/5280714/6962721/7800578e-d937-11e4-8a36-0442c393270a.png"><img width="400" src="https://cloud.githubusercontent.com/assets/5280714/6962721/7800578e-d937-11e4-8a36-0442c393270a.png" /></a>

## Organization of the code
Since there are different devices (Arduino and Raspberry Pi) I thought it would be convenient to separate the code and documentation for each device.

### Arduino
#### Dependencies
The Arduino code depends on the following libraries:
* https://github.com/TMRh20/RF24
* https://github.com/sparkfun/HTU21D_Breakout

#### Setup
Upload the Arduino program. That's it :-).

#### Connections
Connect the NRF24L01 as described in the documentation for the RF24 library by TMRh20.
Connect the HTU21D as desribed in the documentation for the HTU21D_Breakout library by Sparkfun.

### Raspberry Pi
#### Dependencies
The Raspberry Pi code depends on the following libraries
* https://github.com/TMRh20/RF24
* https://pypi.python.org/pypi/gspread

#### Setup
Install the RF24 library:
```bash
git clone https://github.com/TMRh20/RF24
cd RF24
make
sudo make install
```
Install the gspread module for Python:
```bash
pip install gspread
```
Compile the requestData program by issuing make.

Set the username, password and the name of the Google Spreadsheet that you want to save the data to in the config.cfg file.
Use the readme in https://github.com/burnash/gspread as a guide to set these settings properly.

The logger can now be run by issuing
```bash
sudo python logger.py
```

The program can be conveniently run in the background by using screen

#### Connections
Connect the NRF24L01 as described in the documentation for the RF24 library by TMRh20.
