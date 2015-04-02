google_username = ''
google_password = ''
google_spreadsh = ''

import commands, datetime, gspread

def getTH():
    (stat, output) = commands.getstatusoutput("./requestData")
    if 'T' not in output and 'H' not in output:
        return None
    for l in output.splitlines():
        identifier = l[0]
        if identifier == 'T':
            temperature = l[2:].replace('.',',')
        elif identifier == 'H':
            humidity = l[2:].replace('.',',')
    return [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temperature, humidity]

def THtoGD(t):
    try:
        gc = gspread.login(google_username, google_password)
        wks = gc.open(google_spreadsh).get_worksheet(0)
        wks.append_row(t)
        return True
    except:
        print 'Could not save to Google spreadsheet'
        return False

if __name__ == "__main__":
    import Queue, threading, time
    q = Queue.Queue(0)
    def worker():
        while True:
            t = q.get()
            r = THtoGD(t)
            if r is False:
                q.put(t)
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

    n = time.time()
    while True:
        d = time.time() - n
        if d >= 10:
            n = n + 10
            t = getTH()
            if t is not None:
                print t
                q.put(t)
            else:
                print "Skipping"
        else:
            if d < 9:
                time.sleep(1)
            else:
                time.sleep(0.1)
