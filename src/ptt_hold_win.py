import serial, time, sys, os

port = sys.argv[1] if len(sys.argv) > 1 else "COM5"
stopfile = os.path.join(os.environ["TEMP"], "m17_ptt_off.flag")

try:
    os.remove(stopfile)
except FileNotFoundError:
    pass

s = serial.Serial(port, 9600, rtscts=False)
s.rts = True
print(f"PTT ON: {port} RTS=1")

try:
    while not os.path.exists(stopfile):
        time.sleep(0.1)
finally:
    s.rts = False
    s.close()
    print("PTT OFF")