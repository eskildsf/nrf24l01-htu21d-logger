from collections import namedtuple
import ctypes
from datetime import datetime
import time
import json
json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')

DataPoint = namedtuple('DataPoint', 'datetime temperature humidity supplyvoltage')

# Measurememnt object
class DataPointC(ctypes.Structure):
    _fields_ = [('temperature', ctypes.c_float), ('humidity', ctypes.c_float), ('supplyvoltage', ctypes.c_long)]

# Convert from c struct to named tuple
def dataPointFromRadioData(data):
    dataStructure = DataPointC.from_buffer_copy(data)
    datapoint = DataPoint(
        datetime = datetime.now().replace(microsecond = 0),
        temperature = dataStructure.temperature,
        humidity = dataStructure.humidity,
        supplyvoltage = dataStructure.supplyvoltage
    )
    return datapoint

## Databases that can be saved to

class GoogleSpreadsheet():
    def __init__(self, username, password, spreadsheet, worksheet_index = 0):
        import gspread
        self.gc = gspread.login(username, password)
        self.wks = self.gc.open(spreadsheet).get_worksheet(worksheet_index)
    def save(self, datapoint):
        date = datapoint.datetime.strftime('%Y-%m-%d %H:%M:%S')
        temperature = str(datapoint.temperature).replace('.',',')
        humidity = str(datapoint.humidity).replace('.',',')
        supplyvoltage = datapoint.supplyvoltage
        data = [date, temperature, humidity, supplyvoltage]
        try:
            self.wks.append_row(data)
            return True
        except:
            return False

class Memcached():
    def __init__(self, server, size=10800):
        import memcache
        from collections import deque
        self.mc = memcache.Client([server], debug=0)
        self.d = deque(maxlen=size)
    def save(self, datapoint):
        self.d.append(datapoint)
        data = data = [{
        'timestamp': int(time.mktime(e.datetime.timetuple())),
        'temperature': round(e.temperature,2),
        'humidity': round(e.humidity,2),
        'supplyvoltage': e.supplyvoltage,
        } for e in self.d]
        self.mc.set('temperature_humidity', json.dumps(data))

class Sqlite():
    def __init__(self, database_path):
        import sqlite3
        # Connect to database or create it if it doesn't exist.
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()
        self.setup()
    def setup(self):
        # Does the table exist?
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temperature_humidity';")
        # If it doesn't exist then we should create it
        if self.cursor.fetchone() is None:
            self.cursor.execute('CREATE TABLE temperature_humidity (timestamp INTEGER, temperature INTEGER, humidity INTEGER, supplyvoltage INTEGER);')
            self.connection.commit()
    def save(self, datapoint):
        self.cursor.execute('INSERT INTO temperature_humidity VALUES (?, ?, ?, ?)', (time.mktime(datapoint.datetime.timetuple()), int(datapoint.temperature*100), int(datapoint.humidity*100), datapoint.supplyvoltage))
        try:
            self.connection.commit()
            return True
        except:
            return False
    def getDataPoints(self):
        def DataPointFactory(cursor, row):
            # Format '2015-04-03 10:12:29.319435'
            date = datetime.fromtimestamp(int(row[0]))
            T = float(row[1])/100
            H = float(row[2])/100
            V = int(row[3])
            return DataPoint(datetime = date, temperature = T, humidity = H, supplyvoltage = V)
        self.connection.row_factory = DataPointFactory
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM temperature_humidity ORDER BY timestamp ASC;')
        return cursor.fetchall()

class CSV():
    def __init__(self, file):
        self.file = file
    def save(self, datapoint):
        import csv
        date = datapoint.datetime.strftime('%Y-%m-%d %H:%M:%S')
        temperature = str(datapoint.temperature).replace('.',',')
        humidity = str(datapoint.humidity).replace('.',',')
        supplyvoltage = str(datapoint.supplyvoltage).replace('.',',')
        data = [date, temperature, humidity, supplyvoltage]
        with open(self.file, 'ab') as f:
           writer = csv.writer(f, delimiter=';',quoting=csv.QUOTE_NONE)
           writer.writerow(data)
        return True

class MultipleStores:
    def __init__(self, stores):
        self.stores = stores
    def save(self, datapoint):
        result = True
        for store in self.stores:
            r = store.save(datapoint)
            if r is False:
                result = False
        return result
