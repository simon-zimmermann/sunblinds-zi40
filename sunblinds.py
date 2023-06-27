from pysolar.solar import *
import datetime
import time
import RPi.GPIO as GPIO
import warnings
import pyowm
import math
import json
import holidays

warnings.filterwarnings("ignore")
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

lat = 48.837938
lon = 10.074317
city = 2959927
#obs = owm.weather_at_coords(lat, lon)

holidays = holidays.Germany()
l = 600
d = 2350
lat = 48.837938
lon = 10.074317
t1 = 65.0
t2 = 66.4
v1 = float(d / t1)
v2 = float(d / t2)
cur_pos = 0
last_move = True
correct_up = 0.8
correct_down = 0.8
#phi_a = -329
phi_a = -335
phi_b = -230
delay = 3600
clouds = 70
clamp = lambda n, minn, maxn: max(min(maxn, n), minn)

f = open("owm_token.txt")
owm_token = f.read()


def move_to(pos):
    t = 0
    global cur_pos
    global last_move
    if cur_pos < pos:
        t = float(float(pos - cur_pos) / v1)
        t = clamp(t, 0, 70)
        print("Time to go down: %f", t)
        go_down(t)
        cur_pos +=  pos - cur_pos
        print("Cur_pos before clamp: %f", cur_pos)
        cur_pos = clamp(cur_pos, 0, d)
        print("Cur_pos: %f", cur_pos)
        last_move = True
    else:
        t = float(float(cur_pos - pos) / v2)
        t = clamp(t, 0, 70)
        print("Time to go up: %f", t)
        go_up(t)
        cur_pos -= cur_pos - pos
        print("Cur_pos before clamp: %f", cur_pos)
        cur_pos = clamp(cur_pos, 0, d)
        print("Cur_pos: %f", cur_pos)
        last_move = False

def go_up(sec):
    GPIO.output(26, GPIO.LOW)
    GPIO.output(21, GPIO.HIGH)
    time.sleep(sec)
    GPIO.output(21, GPIO.LOW)

def go_down(sec):
    GPIO.output(21, GPIO.LOW)
    GPIO.output(26, GPIO.HIGH)
    time.sleep(sec)
    GPIO.output(26, GPIO.LOW)

def correct(last_move):
    global cur_pos
    if last_move:
        time.sleep(0.5)
        go_up(correct_down)
        cur_pos += correct_down * v1
    else:
        time.sleep(0.5)
        go_down(correct_up)
        cur_pos -= correct_up * v1

pos_up = True
pos_down = False

while(True):
    owm = pyowm.OWM(owm_token)
    obs = owm.weather_at_id(city)
    date = datetime.datetime.now()
    alt = get_altitude(lat, lon, date)
    azi = get_azimuth(lat, lon, date)
    w = obs.get_weather()
    wea = json.loads(w.to_JSON())
    x = d - l * math.tan(math.radians(alt))
    print(alt, azi)
    print(x)
    print(wea)
#up
    if (azi >= 0 or azi <= phi_a) and not pos_up and date.isoweekday() in range(1,6):
        print("Going complete up!")
        #move_to(0)
        #go_up(t2)
        cur_pos = 0
        pos_up = True
        pos_down = False
#down
    if( phi_a < azi <= phi_b) \
            and alt > 5 \
            and not date in holidays \
            and wea["clouds"] < clouds \
            and date.isoweekday() in range(1,6) \
            and wea["status"] == "Clear":
#            and (wea["status"] == "Clear" or (wea["status"] == "Clouds" and (wea["detailed_status"] == "broken clouds" or wea["detailed_status"] == "few clouds")))
        print("Setting position to ", x)
        delta = math.fabs(x - cur_pos)
        if (delta > 5 * correct_down * v2) and ( delta > 5 * correct_up * v2):
            pos_up = False
            #move_to(x)
            correct(last_move)

    time.sleep(delay)