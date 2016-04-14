import datastore, Queue, threading, time, ConfigParser, logging
import ctypes
from datetime import datetime
import RPi.GPIO as GPIO
from RF24 import *

# Data structures
class TemperatureHumiditySupplyvoltageC(ctypes.Structure):
    _fields_ = [('temperature', ctypes.c_float), ('humidity', ctypes.c_float), ('supplyvoltage', ctypes.c_long)]

class KwhC(ctypes.Structure):
    _fields_ = [('voltage', ctypes.c_long), ('count', ctypes.c_long)]

# NRF24L01 equipped loggers
loggers = []
loggers.append({'identifier': 		0xF0F0F0F0AA,
                'name':			'kaelder',
		'measurement_object':	TemperatureHumiditySupplyvoltageC,
                'table':		'th_data',
               })
loggers.append({'identifier':           0xF0F0F0F066,
                'name':                 'stue',
                'measurement_object':   TemperatureHumiditySupplyvoltageC,
                'table':                'th_data',
               })
loggers.append({'identifier':           0xF0F0F0F033,
                'name':                 'elskab',
                'measurement_object':   KwhC,
                'table':                'kwh_data',
               })

def datapointFromData(logger, data):
    datastructure = logger['measurement_object'].from_buffer_copy(data)
    datapoint = {'logger': logger,
                 'datetime': datetime.now().replace(microsecond = 0),
                }
    for field, type in logger['measurement_object']._fields_:
        datapoint[field] = getattr(datastructure, field)
    return datapoint

class MySQL():
    def __init__(self, loggers_, server, database, user, password):
        import MySQLdb
        connected = False
        while connected is False:
            try:
                self.connection = MySQLdb.connect(server, user, password, database)
                self.connection.ping(True)
                self.cursor = self.connection.cursor()
                self.setup(loggers_)
                connected = True
            except Exception as e:
                log.error(e)
                pass
    def setup(self, loggers):
        for logger, table in [(logger, logger['table']) for logger in loggers]:
            self.cursor.execute("SHOW TABLES LIKE '%s';" % table)
            if self.cursor.fetchone() is None:
                sql = 'CREATE TABLE %s (device VARCHAR(255), timestamp INTEGER' % table
                fields = logger['measurement_object']._fields_
                for field, type in fields:
                    sql += ', %s INTEGER' % field
                log.debug(sql)
                sql += ');'
                self.cursor.execute(sql)
    def save(self, datapoint):
        try:
            self.connection.ping(True)
            sql = 'INSERT INTO %s VALUES ("%s", %s' % (datapoint['logger']['table'], datapoint['logger']['name'], int(time.mktime(datapoint['datetime'].timetuple())))
            fields = datapoint['logger']['measurement_object']._fields_
            for field, type in fields:
                value = datapoint[field]
                if type is ctypes.c_float:
                    value = int(value*100)
                sql += ', %s' % value
            sql += ');'
            log.debug(sql)
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            log.error(e)
            log.error(sql)
            return False

# Read user configuration
config = ConfigParser.RawConfigParser()
config.read('./config.cfg')

# Set up logging to std out
log = logging.getLogger("nrf24l01-htu21d-logger")
log.setLevel(logging.DEBUG) #logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s: %(message)s', '%H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)

# Queue of datapoints to be saved to datastore
q = Queue.Queue(0)

db = MySQL(loggers, config.get('mysql', 'server'), config.get('mysql', 'database'), config.get('mysql', 'user'), config.get('mysql', 'password'))
# Worker thread that saves a datapoint to a datastore.
def worker():
    db = MySQL(loggers, config.get('mysql', 'server'), config.get('mysql', 'database'), config.get('mysql', 'user'), config.get('mysql', 'password'))
    while True:
        datapoint = q.get()
        didSave = db.save(datapoint)
        if didSave is False:
            log.error('Could not save %s', datapoint)
            q.put(datapoint)
            time.sleep(10)
thread = threading.Thread(target=worker)
thread.daemon = True
thread.start()

# Start up radio
radio = RF24(RPI_V2_GPIO_P1_15, RPI_V2_GPIO_P1_24, BCM2835_SPI_SPEED_8MHZ)
radio.begin()
radio.setDataRate(RF24_250KBPS) # Maximum distance
radio.openWritingPipe(config.get('DeviceId', 'raspberrypi'))
pipes = {}
for i, logger in enumerate(loggers, 1):
    radio.openReadingPipe(i,logger['identifier'])
    pipes[i] = logger
    log.info('Setting up reading pipe for %s on %s', logger['name'], logger['identifier'])
radio.startListening()

# Set up interrupt on GPIO 17 to read incoming data
def acquireData(channel):
    null, pipe = radio.available_pipe()
    if pipe not in pipes:
        log.debug('Received data from unknown pipe.')
        return None
    logger = pipes[pipe]
    size = len(logger['measurement_object']._fields_)*4 # four bytes pr. float/long field
    data = radio.read(size)
    datapoint = datapointFromData(logger, data)
    q.put(datapoint)
    log.info('Logging %s', datapoint)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.add_event_detect(17, GPIO.FALLING, callback=acquireData)

# Run indefinitely
try:
    while True:
        time.sleep(1000)
except KeyboardInterrupt:
    pass
