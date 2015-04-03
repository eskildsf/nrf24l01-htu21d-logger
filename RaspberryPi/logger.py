import commands, logging, ConfigParser
from datetime import datetime
from collections import namedtuple

config = ConfigParser.RawConfigParser()
config.read('./config.cfg')

# Set up logging
log = logging.getLogger("nrf24l01-htu21d-logger")
log.setLevel(logging.WARNING) #logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
# Log to std.out
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s: %(message)s', '%H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)

# Measurememnt object
DataPoint = namedtuple('DataPoint', 'datetime temperature humidity')

# Measurement routine
def getTemperatureAndHumidity():
    (stat, output) = commands.getstatusoutput("./requestData")
    if 'T' not in output or 'H' not in output:
        log.warning('No data in output from NRF24L01')
        return None
    for l in output.splitlines():
        identifier = l[0]
        if identifier == 'T':
            T = float(l[2:])
        elif identifier == 'H':
            H = float(l[2:])
    return DataPoint(datetime = datetime.now(), temperature = T, humidity = H)

## Databases that can be saved to

class GoogleSpreadsheet():
    def __init__(self, username, password, spreadsheet, worksheet_index = 0):
        import gspread
        self.gc = gspread.login(username, password)
        self.wks = self.gc.open(spreadsheet).get_worksheet(worksheet_index)
    def save(self, datapoint):
        date = datapoint.datetime.strftime("%Y-%m-%d %H:%M:%S")
        temperature = str(datapoint.temperature).replace('.',',')
        humidity = str(datapoint.humidity).replace('.',',')
        data = [date, temperature, humidity]
        try:
            self.wks.append_row(data)
            return True
        except:
            log.error('Could not save %s to Google Spreadsheet', data)
            return False

class Sqlite():
    def __init__(self, database_path):
        import sqlite3
        # Connect to database or create it if it doesn't exist.
        # Parse with type awareness so dates can be compared.
        self.connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.connection.cursor()
        self.setup()
    def setup(self):
        # Does the table exist?
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temperature_humidity';")
        # If it doesn't exist then we should create it
        if self.cursor.fetchone() is None:
            self.cursor.execute('CREATE TABLE temperature_humidity (datetime DATETIME, temperature FLOAT, humidity FLOAT);')
            self.connection.commit()
            log.info('Created sqlite table')
    def save(self, datapoint):
        self.cursor.execute('INSERT INTO temperature_humidity VALUES (?, ?, ?)', datapoint)
        self.connection.commit()
        return True
    def getDataPoints(self):
        def DataPointFactory(cursor, row):
            # Format '2015-04-03 10:12:29.319435'
            date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
            T = row[1]
            H = row[2]
            return DataPoint(datetime = date, temperature = T, humidity = H)
        self.connection.row_factory = DataPointFactory
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM temperature_humidity ORDER BY datetime ASC;')
        return cursor.fetchall()

class CSV():
    def __init__(self, file):
        self.file = file
    def save(self, datapoint):
        import csv
        date = datapoint.datetime.strftime("%Y-%m-%d %H:%M:%S")
        temperature = str(datapoint.temperature).replace('.',',')
        humidity = str(datapoint.humidity).replace('.',',')
        data = [date, temperature, humidity]
        with open(self.file, 'ab') as f:
           writer = csv.writer(f, delimiter=';',quoting=csv.QUOTE_NONE)
           writer.writerow(data)
        return True

if __name__ == "__main__":
    import Queue, threading, time
    seconds_between_measurements = 10
    q = Queue.Queue(0)

    def worker():
        db = GoogleSpreadsheet(config.get('GoogleSpreadsheet', 'username'), config.get('GoogleSpreadsheet', 'password'), config.get('GoogleSpreadsheet', 'spreadsheet'))
        #db = Sqlite(config.get('sqlite', 'file'))
        #db = CSV(config.get('csv', 'file'))
        while True:
            datapoint = q.get()
            didSave = db.save(datapoint)
            if didSave is False:
                q.put(datapoint)
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    
    now = time.time()
    while True:
        delta = time.time() - now
        if delta >= seconds_between_measurements:
            now = now + 10
            datapoint = getTemperatureAndHumidity()
            if datapoint is not None:
                log.info('Logging %s', datapoint)
                q.put(datapoint)
        else:
            if (seconds_between_measurements - delta) > 1.2:
                time.sleep(1)
            else:
                time.sleep(0.1)
