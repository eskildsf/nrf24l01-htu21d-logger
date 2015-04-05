from collections import namedtuple
import ctypes
from datetime import datetime

DataPoint = namedtuple('DataPoint', 'datetime temperature humidity')

# Measurememnt object
class DataPointC(ctypes.Structure):
    _fields_ = [("temperature", ctypes.c_float), ("humidity", ctypes.c_float)]

# Convert from c struct to named tuple
def dataPointFromRadioData(data):
    dataStructure = DataPointC.from_buffer_copy(data)
    datapoint = DataPoint(
        datetime = datetime.now(),
        temperature = dataStructure.temperature,
        humidity = dataStructure.humidity
    )
    return datapoint

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