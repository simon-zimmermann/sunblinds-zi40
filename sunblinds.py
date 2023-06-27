from pysolar.solar import *
import datetime
import time
import RPi.GPIO as GPIO
import warnings
import pyowm
import json
import holidays

warnings.filterwarnings("ignore")
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

#https://openweathermap.org/city/2959927
city = 2959927
holidays = holidays.Germany()
lat = 48.837938
lon = 10.074317
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

f = open("owm_token.txt")
owm_token = f.read()
owm = pyowm.OWM(owm_token)

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

while(True):
    try:
        wea = json.loads(owm.weather_at_id(city).get_weather().to_JSON())
        date = datetime.datetime.now()
        sun_altitude = get_altitude(lat, lon, date)
        sun_azimuth = get_azimuth(lat, lon, date)
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

    except Exception as e:
        print("GOT AN ERROR!")
        print(e)
        go_up()

    
    time.sleep(delay)
