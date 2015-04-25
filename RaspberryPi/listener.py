import datastore, Queue, threading, time, ConfigParser, logging
import RPi.GPIO as GPIO
from RF24 import *

# Read user configuration
config = ConfigParser.RawConfigParser()
config.read('./config.cfg')

# Set up logging to std out
log = logging.getLogger("nrf24l01-htu21d-logger")
log.setLevel(logging.WARNING) #logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s: %(message)s', '%H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)

# Queue of datapoints to be saved to datastore
q = Queue.Queue(0)

# Worker thread that saves datapoints to a datastore.
def worker():
    #db = datastore.GoogleSpreadsheet(config.get('GoogleSpreadsheet', 'username'), config.get('GoogleSpreadsheet', 'password'), config.get('GoogleSpreadsheet', 'spreadsheet'))
    db = datastore.Sqlite(config.get('sqlite', 'file'))
    #db = datastore.CSV(config.get('csv', 'file'))
    while True:
        datapoint = q.get()
        didSave = db.save(datapoint)
        if didSave is False:
            log.error('Could not save %s', datapoint)
            q.put(datapoint)
thread = threading.Thread(target=worker)
thread.daemon = True
thread.start()

# Start up radio
radio = RF24(RPI_V2_GPIO_P1_15, RPI_V2_GPIO_P1_24, BCM2835_SPI_SPEED_8MHZ)
radio.begin()
radio.setDataRate(RF24_250KBPS)
radio.openWritingPipe(config.get('DeviceId', 'raspberrypi'))
radio.openReadingPipe(1,config.get('DeviceId', 'arduino'))
radio.startListening()

# Set up interrupt on GPIO 17 to read incoming data
def acquireData(channel):
    data = radio.read(12)
    datapoint = datastore.dataPointFromRadioData(data)
    log.info('Logging %s', datapoint)
    q.put(datapoint)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.add_event_detect(17, GPIO.FALLING, callback=acquireData)

# Run indefinitely
try:
    while True:
        time.sleep(100)
except KeyboardInterrupt:
    pass
