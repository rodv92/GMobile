# coding: utf-8


import RPi.GPIO as GPIO
import scipy as sp
import signal
import sys
import time
import datetime
from collections import deque 
import struct
import statistics

# Module Imports
import mariadb
#from mariadb.connector.aio import connect
import sys
import re

# Lora Imports

from SX127x.LoRa import *
#from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def pulse_detected_callback(channel):
    global pulse_events
    pulse_events.append(time.time() - start_time_epoch)


def dms2dec(dms_str):
    
    
    dms_str = re.sub(r'\s', '', dms_str)
    
    sign = -1 if re.search('[swSW]', dms_str) else 1
    
    numbers = [*filter(len, re.split('\D+', dms_str, maxsplit=4))]

    degree = numbers[0]
    minute = numbers[1] if len(numbers) >= 2 else '0'
    second = numbers[2] if len(numbers) >= 3 else '0'
    frac_seconds = numbers[3] if len(numbers) >= 4 else '0'
    
    second += "." + frac_seconds
    return sign * (int(degree) + float(minute) / 60 + float(second) / 3600)

# Connect to MariaDB Platform
try:
    conn = mariadb.connect(
    #conn = connect(
        user="gmobile_user",
        password="gmobile_passwd",
        host="127.0.0.1",
        port=3306,
        database="gmobile"

    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Get Cursor
cur = conn.cursor()

start_time_epoch = time.time()
pulse_events = deque()
cps = 0
cpm = 0
#process_pulses = True

#paralyzable model
# m = n*exp(-nt)
# using lambert(w) 
#y =  w * exp(w)
#-nt = w

#y = -nt * exp(-nt)

#-nt = lambert(y)
#n = -lambert(y)/t

#scipy.special.lambertw(z, k=0, tol=1e-8)


#while True:
#    GPIO.wait_for_edge(PULSE_GPIO, GPIO.FALLING)
#    print("Button pressed!")
#    sp.special.lambertw(z, k=0, tol=1e-8)

PULSE_GPIO = 16
lat = dms2dec("50°11'28.50\"N")
long = dms2dec("19°45'56.02\"E")


def setupGPIOEventDetect():


    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PULSE_GPIO, GPIO.IN)
    GPIO.add_event_detect(PULSE_GPIO, GPIO.RISING, callback=pulse_detected_callback)


def removeGPIOEventDetect():

    GPIO.remove_event_detect(PULSE_GPIO)


def measurePulseWidth(total_pulses,max_fails=20,rise_timeout_ms=20000,fall_timeout_ms=20):

    removeGPIOEventDetect()
    s = 0
    fail = 0
    pulsewidths = []

    while(s < total_pulses and fail < max_fails):
        channel = GPIO.wait_for_edge(PULSE_GPIO,GPIO.RISING,timeout=rise_timeout_ms) # assuming there is at least one pulse registered every rise_timeout_ms
        if (channel is None):
            fail += 1
            continue
        pulsestart = time.time_ns()
        channel = GPIO.wait_for_edge(PULSE_GPIO,GPIO.FALLING,timeout=fall_timeout_ms) # assuming the pulse width is less fall_timeout_ms
        if (channel is None):
            fail += 1
            continue
        pulsewidths.append((time.time_ns() - pulsestart)/1000) # save pulsewidth value in µs
        s+= 1 # sucessful pulsewidth measure

        #this pulse timing method may be problematic if the real time separation between RISING and FALLING edge is shorter than execution time between the two
        #wait_for_edge calls. thread should be set to high priority. Overall, dead time will be overestimated.

    setupGPIOEventDetect()
    return (pulsewidths[int(len(pulsewidths)/2)],statistics.pstdev(pulsewidths)) # returns mean pulsewidth value in µs and standard deviation.



# LORA INIT

#BOARD.setup()
#BOARD.reset()
##parser = LoRaArgumentParser("Lora tester")







"""
class mylora(LoRa):
    
    global current_data
    
    def __init__(self, verbose=False):
        super(mylora, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        BOARD.led_on()
        #print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True )# Receive INF
        print ("Receive: ")
        mens=bytes(payload).decode("utf-8",'ignore')
        mens=mens[2:-1] #to discard \x00\x00 and \x00 at the end
        print(mens)
        BOARD.led_off()
        if mens=="INF":
            print("Received data request INF")
            time.sleep(2)
            print ("Send mens: DATA RASPBERRY PI")
            self.write_payload([255, 255, 0, 0, 68, 65, 84, 65, 32, 82, 65, 83, 80, 66, 69, 82, 82, 89, 32, 80, 73, 0]) # Send DATA RASPBERRY PI
            self.set_mode(MODE.TX)
        time.sleep(2)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("\nTxDone")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):          
        while True:
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT) # Receiver mode
            while True:
                pass;

    def send(data):
        data = [255, 255, 0, 0] + data + [0] 
        self.write_payload([data]) # Send DATA
        time.sleep(2)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

lora = mylora(verbose=False)
#args = parser.parse_args(lora) # configs in LoRaArgumentParser.py

#     Slow+long range  Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. 13 dBm
lora.set_pa_config(pa_select=1, max_power=21, output_power=15)
lora.set_bw(BW.BW125)
lora.set_coding_rate(CODING_RATE.CR4_8)
lora.set_spreading_factor(12)
lora.set_rx_crc(True)
#lora.set_lna_gain(GAIN.G1)
#lora.set_implicit_header_mode(False)
lora.set_low_data_rate_optim(True)

#  Medium Range  Defaults after init are 434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on 13 dBm
#lora.set_pa_config(pa_select=1)



assert(lora.get_agc_auto_on() == 1)

try:
    print("START")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("Exit")
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    print("Exit")
    lora.set_mode(MODE.SLEEP)
BOARD.teardown()
"""

   
signal.signal(signal.SIGINT, signal_handler)

def process_events(log=False,lorasend=False):
    global cps
    global cpm
    nowtime = time.time()
    prune_before_time = nowtime - start_time_epoch - 60.0
    for pulse in list(pulse_events):
        if(pulse < prune_before_time):
            pulse_events.popleft()
    cps = len(pulse_events)/60.0
    cpm = len(pulse_events)
    print(cpm)
    
    if not(int(time.time()) % 60) and prune_before_time > 0:
        # log last minute cpm to db. wait at least 60 sec from start
        # to get steady state data.
        print("last minute cpm:" + str(cpm))
        if(lorasend):        
            epoch_ms = int(time.time()*1000.0)
            buffer_data = struct.pack("<Q", epoch_ms) # pack epoch_ms into byte array little endian
            buffer_data += struct.pack("<L", cpm) # append cpm into byte array little endian
            #lora.send(buffer_data)
            print(buffer_data)
        if(log):
            sql = "INSERT INTO data_cpm (timestamp_utc,count_per_minute,coordinates) VALUES(%s, %s, ST_PointFromWKB(ST_AsBinary(POINT(" + str(lat) + "," + str(long) + ")), 4326))";
            val = (str(datetime.datetime.now()),str(cpm))
            cur.execute(sql, val)
            conn.commit()
    
    processing_delay = time.time() - nowtime
    print(processing_delay)
    proc_delay_mul = int(processing_delay)
    time.sleep(1 + proc_delay_mul - processing_delay)
    # ensure isochronous sampling, add n skip seconds in case of the block taking a really long time...
    # asynchronous mariadb cursor should prevent this occurence.
    if(prune_before_time > 0): # 60 sec have elapsed
        return cpm
    else:
        return -1

    
#while process_pulses:
#    process_events()
#signal.pause()
