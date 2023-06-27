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

#lat = 48.837938
#lon = 10.074317
city = 2959927
#obs = owm.weather_at_coords(lat, lon)

holidays = holidays.Germany()
#l = 600
#d = 2350
lat = 48.837938
lon = 10.074317
#t1 = 65.0
#t2 = 66.4
#v1 = float(d / t1)
#v2 = float(d / t2)
#cur_pos = 0
#last_move = True
#correct_up = 0.8
#correct_down = 0.8
#phi_a = -329
sun_azimuth_min = -335
sun_azimuth_max = -230
sun_altitude_threshold = 5
time_blinds_down = 55
time_blinds_up = 65
delay = 3600
clouds_threshold = 70
temperature_threshold = 25
wind_threshold = 10
wind_gust_threshold = 15
#clamp = lambda n, minn, maxn: max(min(maxn, n), minn)

f = open("owm_token.txt")
owm_token = f.read()


#def move_to(pos):
#    t = 0
#    global cur_pos
#    global last_move
#    if cur_pos < pos:
#        t = float(float(pos - cur_pos) / v1)
#        t = clamp(t, 0, 70)
#        print("Time to go down: %f", t)
#        go_down(t)
#        cur_pos +=  pos - cur_pos
#        print("Cur_pos before clamp: %f", cur_pos)
#        cur_pos = clamp(cur_pos, 0, d)
#        print("Cur_pos: %f", cur_pos)
#        last_move = True
#    else:
#        t = float(float(cur_pos - pos) / v2)
#        t = clamp(t, 0, 70)
#        print("Time to go up: %f", t)
#        go_up(t)
#        cur_pos -= cur_pos - pos
#        print("Cur_pos before clamp: %f", cur_pos)
#        cur_pos = clamp(cur_pos, 0, d)
#        print("Cur_pos: %f", cur_pos)
#        last_move = False

pos_up = False
pos_down = False

def go_up():
    global pos_up
    global pos_down
    if(not pos_up):
        print("Opening the blinds")
        GPIO.output(26, GPIO.LOW)
        GPIO.output(21, GPIO.HIGH)
        time.sleep(time_blinds_up)
        GPIO.output(21, GPIO.LOW)
        pos_up = True
        pos_down = False

def go_down():
    global pos_up
    global pos_down
    if(not pos_down):
        print("Closing the blinds")
        GPIO.output(21, GPIO.LOW)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(time_blinds_down)
        GPIO.output(26, GPIO.LOW)
        pos_up = False
        pos_down = True

#def correct(last_move):
#    global cur_pos
#    if last_move:
#        time.sleep(0.5)
#        go_up(correct_down)
#        cur_pos += correct_down * v1
#    else:
#        time.sleep(0.5)
#        go_down(correct_up)
#        cur_pos -= correct_up * v1


owm = pyowm.OWM(owm_token)

while(True):
    wea = json.loads(owm.weather_at_id(city).get_weather().to_JSON())
    date = datetime.datetime.now()
    sun_altitude = get_altitude(lat, lon, date)
    sun_azimuth = get_azimuth(lat, lon, date)
    #x = d - l * math.tan(math.radians(sun_altitude))
    #print("X-value: %f" % x)

    is_weekday = date.isoweekday() in range(1,6)
    is_sun_at_window = (sun_azimuth_min < sun_azimuth <= sun_azimuth_max)
    is_sunup = (sun_altitude > sun_altitude_threshold)
    is_sunny = wea["clouds"] < clouds_threshold
    is_hot = wea["temperature"]["temp"] > 273.15 + temperature_threshold
    is_windy = wea["wind"]["speed"] > wind_threshold or wea["wind"]["gust"] > wind_gust_threshold

    # if the blinds need to be up
    is_blinds_need_up = \
            is_windy or \
            (not is_sunup) or \
            (not is_weekday)
    # if we want the blinds to be down
    is_blinds_want_down = \
            (is_sunny or is_hot) \
            and \
            (is_sunup and is_sun_at_window)

    print("================================================================================")
    print("= %s" % date.strftime("%d/%m/%Y %H:%M:%S"))
    print("================================================================================")
    print("Current weather report:")
    print(json.dumps(wea, indent=2))
    print("Sun altitude: %f\nSun azimuth: %f" % (sun_altitude, sun_azimuth))
    print("is_weekday: %s" % is_weekday)
    print("is_sun_at_window: %s" % is_sun_at_window)
    print("is_sunup: %s" % is_sunup)
    print("is_sunny: %s" % is_sunny)
    print("is_hot: %s" % is_hot)
    print("is_windy: %s" % is_windy)
    print("is_blinds_need_up: %s" % is_blinds_need_up)
    print("is_blinds_want_down: %s" % is_blinds_want_down)


    if (is_blinds_want_down and not is_blinds_need_up):
        go_down()
    else:
        go_up()

#up
   # if (sun_azimuth >= 0 or sun_azimuth <= sun_azimuth_min) and not pos_up and date.isoweekday() in range(1,6):
   #     print("Going complete up!")
   #     #move_to(0)
   #     #go_up(t2)
   #     cur_pos = 0
   #     pos_up = True
   #     pos_down = False
#do#wn
   # if( sun_azimuth_min < sun_azimuth <= sun_azimuth_max) \
   #         and sun_altitude > 5 \
   #         and not date in holidays \
   #         and wea["clouds"] < clouds_threshold \
   #         and date.isoweekday() in range(1,6) \
   #         and wea["status"] == "Clear":
#  #          and (wea["status"] == "Clear" or (wea["status"] == "Clouds" and (wea["detailed_status"] == "broken clouds" or wea["detailed_status"] == "few clouds")))
   #     print("Setting position to ", x)
   #     delta = math.fabs(x - cur_pos)
   #     if (delta > 5 * correct_down * v2) and ( delta > 5 * correct_up * v2):
   #         pos_up = False
   #         #move_to(x)
   #         correct(last_move)
#
    time.sleep(delay)