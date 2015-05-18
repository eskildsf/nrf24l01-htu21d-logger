import datastore, Queue, threading, time, ConfigParser, logging
from RF24 import *

# Read user configuration
config = ConfigParser.RawConfigParser()
config.read('./config.cfg')

# Set up logging to std out
log = logging.getLogger("nrf24l01-htu21d-logger")
log.setLevel(logging.INFO) #logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s: %(message)s', '%H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)

seconds_between_measurements = 10

# Queue of datapoints to be saved to datastore
q = Queue.Queue(0)

# Worker thread that saves datapoints to a datastore.
def worker():
    #db = datastore.GoogleSpreadsheet(config.get('GoogleSpreadsheet', 'username'), config.get('GoogleSpreadsheet', 'password'), config.get('GoogleSpreadsheet', 'spreadsheet'))
    #db = datastore.Sqlite(config.get('sqlite', 'file'))
    db = datastore.CSV(config.get('csv', 'file'))
    while True:
        datapoint = q.get()
        didSave = db.save(datapoint)
        if didSave is False:
            log.error('Could not save %s', datapoint)
            q.put(datapoint)
thread = threading.Thread(target=worker)
thread.daemon = True
thread.start()

# Set up radio
radio = RF24(RPI_V2_GPIO_P1_15, RPI_V2_GPIO_P1_24, BCM2835_SPI_SPEED_8MHZ)
radio.begin()
radio.setDataRate(RF24_250KBPS)
radio.openWritingPipe(config.get('DeviceId', 'raspberrypi'))
radio.openReadingPipe(1,config.get('DeviceId', 'arduino'))

def acquireData():
    radio.stopListening()
    # Send 4 bytes, length of an unsigned long
    # as a signal to make a measurement
    radio.write(b"11")
    radio.startListening()
    anow = time.time()
    timeout = False
    while radio.available() is False and timeout is False:
        if time.time() - anow > 0.5:
            log.warning('Timeout')
            return None
    data = radio.read(8)
    datapoint = datastore.dataPointFromRadioData(data)
    log.info('Logging %s', datapoint)
    q.put(datapoint)
    
# Run indefinitely
now = time.time()
try:
    while True:
        delta = time.time() - now
        if delta >= seconds_between_measurements:
            now = now + 10
            acquireData()
        else:
            if (seconds_between_measurements - delta) > 1.2:
                time.sleep(1)
            else:
                time.sleep(0.1)
except KeyboardInterrupt:
    pass
