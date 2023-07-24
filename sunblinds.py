from pysolar.solar import *
import datetime
import time
import RPi.GPIO as GPIO
import warnings
import pyowm
import json
import holidays
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S", 
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("sunblinds.log"),
        logging.StreamHandler()
    ])

logging.info("Starting sunblinds.py")

#warnings.filterwarnings("ignore")
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
time_blinds_down = 65
time_blinds_up = 75
delay = 600
clouds_threshold = 70
temperature_threshold = 10
wind_threshold = 10
wind_gust_threshold = 15
rain_threshold = 2
work_start_h = 8
work_end_h = 17
work_end_d = 4

f = open("owm_token.txt")
owm_token = f.read()
logging.info("Using Token: %s" % owm_token)

pos_up = False
pos_down = False

def go_up():
    global pos_up
    global pos_down
    if(not pos_up):
        logging.info("Opening the blinds")
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
        logging.info("Closing the blinds")
        GPIO.output(21, GPIO.LOW)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(time_blinds_down)
        GPIO.output(26, GPIO.LOW)
        pos_up = False
        pos_down = True

while(True):
    try:
        owm = pyowm.OWM(owm_token)
        wea = json.loads(owm.weather_at_id(city).get_weather().to_JSON())
        date = datetime.datetime.now()
        sun_altitude = get_altitude(lat, lon, date)
        sun_azimuth = get_azimuth(lat, lon, date)
        #is_sun_at_window = (sun_azimuth_min < sun_azimuth <= sun_azimuth_max)
        is_sunup = (sun_altitude > sun_altitude_threshold)
        is_sunny = wea["clouds"] < clouds_threshold
        is_hot = wea["temperature"]["temp"] > 273.15 + temperature_threshold
        is_windy = wea["wind"]["speed"] > wind_threshold or wea["wind"]["gust"] > wind_gust_threshold
        len_rain = len(wea["rain"])
        is_rain = False
        if len_rain > 0 and "1h" in wea["rain"]:
            if wea["rain"]["1h"] > rain_threshold:
                is_rain = True
        is_workday = date.weekday() < work_end_d
        is_worktime = date.hour >= work_start_h and date.hour < work_end_h
        is_working = is_workday and is_worktime

        # if the blinds need to be up
        is_blinds_need_up = \
                is_windy or \
                is_rain or \
                (not is_sunup) or \
                (is_working)
        
        # if we want the blinds to be down
        is_blinds_want_down = \
                (is_sunny or is_hot) \
                and \
                (is_sunup)
                #(is_sunup and is_sun_at_window)

        logging.info("================================================================================")
        logging.info("= %s" % date.strftime("%d/%m/%Y %H:%M:%S"))
        logging.info("================================================================================")
        logging.info("Current weather report:")
        logging.info(json.dumps(wea, indent=2))
        logging.info("Sun altitude: %f" % sun_altitude)
        logging.info("Sun azimuth: %f" % sun_azimuth)
        logging.info("is_working: %s" % is_working)
        #logging.info("is_sun_at_window: %s" % is_sun_at_window)
        logging.info("is_sunup: %s" % is_sunup)
        logging.info("is_sunny: %s" % is_sunny)
        logging.info("is_hot: %s" % is_hot)
        logging.info("is_windy: %s" % is_windy)
        logging.info("len_rain: %s" % len_rain)
        logging.info("is_rain: %s" % is_rain)
        logging.info("is_blinds_need_up: %s" % is_blinds_need_up)
        logging.info("is_blinds_want_down: %s" % is_blinds_want_down)


        if (is_blinds_want_down and not is_blinds_need_up):
            go_down()
        else:
            go_up()

    except Exception as e:
        logging.info("GOT AN ERROR!", exc_info=True)
        go_up()

    logging.info("Sleeping for %d seconds" % delay)
    time.sleep(delay)
