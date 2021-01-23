#!/usr/bin/env python3
#
# Glen's drink warmer
#
# Best temperature (for coffee) info:
#   https://driftaway.coffee/temperature/
# GPIO Info:
#   https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
#     GPIO.setmode(GPIO.BCM) # or GPIO.BOARD
#     GPIO.setwarnings(False)
#     GPIO.setup(PIN, GPIO.OUT, initial=GPIO.HIGH) # or GPIO.DOWN
#     GPIO.setup(PIN, GPIO.IN,  pull_up_down=GPIO.PUD_UP) # or GPIO.PUD_DOWN
#     GPIO.add_event_detect(PIN, GPIO.FALLING, bouncetime=200) # or GPIO.RISING
#     if GPIO.event_detected(PIN): ...
#     while GPIO.input(PIN) == GPIO.LOW: ...
#     GPIO.output(PIN, GPIO.LOW) # GPIO.HIGH
# ADC (MCP3008) info:
#   https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/mcp3008
#   https://bitbucket.org/pschow/rpiadctherm/src/d410733214027d58c35c944e75eebf71e56ea5a2/basiclogmcp.py?at=master&fileviewer=file-view-default
#   Hardware SPI:
#     mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))
#     n = mcp.read_adc(i) # Read raw value from ADC channel 'i'
# Thermisor usage info:
#   https://bitbucket.org/pschow/rpiadctherm/src/
# NeoPixel info:
#   https://learn.adafruit.com/neopixels-on-raspberry-pi/software
#   https://github.com/jgarff/rpi_ws281x
#     color is int32:  (white << 24) | (red << 16)| (green << 8) | blue
#     LED_FREQ_HZ    = 800000 # LED signal frequency in hertz (usually 800khz)
#     LED_DMA        = 10     # DMA channel for generating signal (try 10)
#     LED_BRIGHTNESS = 255    # Set '0' for darkest and 255 for brightest
#     LED_INVERT     = False  # Set 'True' when using NPN transistor level shift
#     LED_CHANNEL    = 0      # set '1' for GPIOs 13, 19, 41, 45 or 53
#     LED_STRIP      = ws.WS2811_STRIP_GRB (or ws.WS2811_STRIP_RGB, or others)
#     neopixels = Adafruit_NeoPixel(LED_COUNT, PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
#     neopixels.begin()
#     neopixels.setPixelColor(pixel_num, color)
#     neopixels.show()
#

# How much time (in minutes) to add/subtract for each button press
TIME_QUANTUM_IN_MINUTES = 10.0

# Maximum time (in minutes) that the timer can be set for
TIME_MAX_IN_MINUTES = 50.0

# How long in seconds after it is off, and cools, before dimming the neopixels
COOLDOWN_PAUSE_IN_SECONDS = (60.0 * 15)

from functools import *
import math
import os
import time
import threading

# Create the web server
from flask import Flask
from flask import send_file
app = Flask(__name__)

# Import the Adafruit NeoPixel library
from neopixel import *

# Import Adafruit SPI library (for hardware SPI)
import Adafruit_GPIO.SPI as SPI

# Import the Adafruit MCP3008 support library
import Adafruit_MCP3008

# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO

# Setup the NeoPixels
NEOPIXEL_PIN   = 18
NEOPIXEL_COUNT = 5
NEOPIXEL_TYPE  = ws.WS2811_STRIP_GRB
neopixels = Adafruit_NeoPixel(NEOPIXEL_COUNT, NEOPIXEL_PIN, 800000, 10, False, 255, 0, NEOPIXEL_TYPE)
neopixels.begin()
neopixels.setBrightness(255);

# Setup hardware SPI for the MCP3008
SPI_PORT   = 0
SPI_DEVICE = 0
mcp3008 = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# Define a name for the MCP3008 channel where the thermistor is wired
THERMISTOR_CHANNEL = 0

# Configure GPIO library
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define names for the GPIO pins being used
READY_LED    = 26 # Use only BCM pins #9 or higher (they are low at startup)
BUTTON_RED   = 22
BUTTON_GREEN = 27
WARMER_RELAY = 17

# Configure GPIO pins for input or output
GPIO.setup(READY_LED,    GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(BUTTON_RED,   GPIO.IN,  pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_GREEN, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
GPIO.setup(WARMER_RELAY, GPIO.OUT, initial=GPIO.LOW)

# Configure edge detection on the two buttons
DEBOUNCE_MSEC = 200
GPIO.add_event_detect(BUTTON_RED,   GPIO.FALLING, bouncetime=DEBOUNCE_MSEC)
GPIO.add_event_detect(BUTTON_GREEN, GPIO.FALLING, bouncetime=DEBOUNCE_MSEC)

# Spectrum of 100 colors from red (hot) through yellow to blue (cold)
colors = [
  0xff0000, 0xfa0500, 0xf50a00, 0xf00f00, 0xeb1400, 0xe61900, 0xe11e00,
  0xdc2300, 0xd72800, 0xd22d00, 0xcd3200, 0xc83700, 0xc33c00, 0xbe4100,
  0xb94600, 0xb44b00, 0xaf5000, 0xaa5500, 0xa55a00, 0xa05f00, 0x9b6400,
  0x966900, 0x916e00, 0x8c7300, 0x877800, 0x827d00, 0x788700, 0x738c00,
  0x6e9100, 0x699600, 0x649b00, 0x5fa000, 0x5aa500, 0x55aa00, 0x50af00,
  0x4bb400, 0x46b900, 0x41be00, 0x3cc300, 0x37c800, 0x32cd00, 0x2dd200,
  0x28d700, 0x23dc00, 0x1ee100, 0x19e600, 0x14eb00, 0x0ff000, 0x0af500,
  0x05fa00, 0x00ff00, 0x00fa05, 0x00f00f, 0x00eb14, 0x00e619, 0x00e11e,
  0x00dc23, 0x00d728, 0x00d22d, 0x00cd32, 0x00c837, 0x00c33c, 0x00be41,
  0x00b946, 0x00b44b, 0x00af50, 0x00aa55, 0x00a55a, 0x00a05f, 0x009b64,
  0x009669, 0x00916e, 0x008c73, 0x008778, 0x00827d, 0x007d82, 0x007887,
  0x00738c, 0x006996, 0x00649b, 0x005fa0, 0x005aa5, 0x0055aa, 0x0050af,
  0x004bb4, 0x0046b9, 0x0041be, 0x003cc3, 0x0037c8, 0x0032cd, 0x002dd2,
  0x0028d7, 0x0023dc, 0x001ee1, 0x0019e6, 0x0014eb, 0x000ff0, 0x000af5,
  0x0005fa, 0x0000ff
]

# This is slightly edited from https://bitbucket.org/pschow/rpiadctherm/src/
def get_temp_celsius(mcp3008, channel):

  value = mcp3008.read_adc(channel)

  volts = (value * 3.3) / 1024 #calculate the voltage
  ohms = ((1/volts)*3300)-1000 #calculate the ohms of the thermististor

  #a, b, & c values from http://www.thermistor.com/calculators.php
  #using curve R (-6.2%/C @ 25C) Mil Ratio X
  a =  0.002197222470870
  b =  0.000161097632222
  c =  0.000000125008328

  #Steinhart Hart Equation
  # T = 1/(a + b[ln(ohm)] + c[ln(ohm)]^3)
  lnohm = math.log1p(ohms) #take ln(ohms)
  t1 = (b*lnohm) # b[ln(ohm)]
  c2 = c*lnohm # c[ln(ohm)]
  t2 = math.pow(c2,3) # c[ln(ohm)]^3
  temp = 1/(a + t1 + t2) #calcualte temperature
  tempc = temp - 273.15 - 4 #K to C
  # the -4 is error correction for bad python math

  #print out debug info
  # print("%4d/1023 => %5.3f V => %4.1f Ω => %4.1f °K => %4.1f °C from adc %d at %s" % (value, volts, ohms, temp, tempc, adc,strftime("%H:%M")))
  return tempc

# Compute running average of temperature over last MEAN_COUNT samples
MEAN_COUNT = 8
# Fill the storage buffer array with this temperature as a start temp
START_TEMP = 25
# Cool python trick to do that initialization
samples = [START_TEMP] * MEAN_COUNT
current_sample = 0
def get_smoothed_temp(mcp3008, channel):
  global current_sample
  samples[current_sample] = get_temp_celsius(mcp3008, THERMISTOR_CHANNEL)
  current_sample = (current_sample + 1) % MEAN_COUNT
  smoothed = reduce(lambda x, y: x + y, samples) / len(samples)
  return smoothed

# Return a dimmed color
DIMMING_MULTIPLIER = 0.10
COOLDOWN_TEMP      = 35.0
FADE_RATE_SEC      = 0.025
FADE_TIME_SEC      = (1 / FADE_RATE_SEC)
# For development
# COOLDOWN_PAUSE_IN_SECONDS = 15.0
def dim_color(color):
  # print("dim color=" + hex(color))
  global just_started
  out_n = 0
  cooldown_multiplier = 1.0
  # print("--> hs=%d, cd_s=%d, c_t=%f" % (heater_state, cooldown_start, current_temp))
  if heater_state == 0 and cooldown_start != 0 and current_temp <= COOLDOWN_TEMP:
    how_long = time.time() - cooldown_start
    # print("--> in cooldown for %d seconds" % (how_long))
    if how_long > COOLDOWN_PAUSE_IN_SECONDS:
      # print("--> after pause of %d seconds" % (COOLDOWN_PAUSE_IN_SECONDS))
      how_long -= COOLDOWN_PAUSE_IN_SECONDS
      cooldown_multiplier = (1.0 - how_long * FADE_RATE_SEC)
      if cooldown_multiplier < 0.0001: cooldown_multiplier = 0.0
      # print("--> cdm=%0.1f" % (cooldown_multiplier))
  for o in (0, 8, 16, 24):
    # print("dim o=" + str(o))
    in_color = (color >> o & 0xff)
    # print("dim in_color=" + hex(in_color))
    out_n += (int(in_color * DIMMING_MULTIPLIER * cooldown_multiplier) << o)
  # print("dim out_n=" + hex(out_n))
  return out_n

# Create a color to match the passed temperature (red => hot, blue => cold)
COLD_BOTTOM     = 25.0
HOT_TOP         = 60.0
def get_color_for_temperature(temp):
  # print("get_color_for_temperature --> %0.2f degrees." % (temp))
  # Note: the drink warmer hardware maxes out around 85C - 90C
  # Anything cooler than COLD_BOTTOM is treated the same as COLD_BOTTOM
  if temp < COLD_BOTTOM: temp = COLD_BOTTOM
  # Anything hotter than HOT_TOP is treated the same as HOT_TOP
  if temp > HOT_TOP: temp = HOT_TOP
  # Normalize the temperature to range 0..99
  n = int(99 * (temp - COLD_BOTTOM) / (HOT_TOP - COLD_BOTTOM))
  # Get color from the 100-color spectrum array
  c = colors[99 - n]
  global temp_color
  temp_color = c
  r = (c & 0xff0000) >> 16
  g = (c & 0x00ff00) >> 8
  b = (c & 0x0000ff)
  #print("--> c=0x%06x, r=0x%02x, g=0x%02x, b=0x%02x" % (c, r, g, b))
  out_color = Color(r, g, b)
  # print("get_color_for_temperature <-- " + hex(out_color))
  return out_color

# Update the NeoPixels with color for temp, and brightnes for time remaining
SECONDS_PER_PIXEL = (60 * TIME_QUANTUM_IN_MINUTES)
def update_neopixels(temp, time_remaining_sec):
  # print("update_neopixels(temp=%0.1fC/%0.1fF, sec=%0.2f)" % (temp, temp * 9.0 / 5.0 + 32, time_remaining_sec))
  if time_remaining_sec < 0:
    time_remaining_sec = 0
  pixels_remaining = int(0.5 + time_remaining_sec / SECONDS_PER_PIXEL)
  # print(" -- pixels_remaining = %d" % (pixels_remaining))
  color = get_color_for_temperature(temp)
  num = neopixels.numPixels()
  for i in range(num):
    # Make sure one pixel stays bright if any more than a millisecond remains
    if i < pixels_remaining or (i == 0 and time_remaining_sec > 0.001):
      # print("(T) --> setPixelColor(%d, 0x%x)" % (i, color))
      # Oops! I foolishly glued pixel strip backwards, so must invert 'i' here!
      neopixels.setPixelColor(NEOPIXEL_COUNT - i - 1, color)
    else:
      # print("(F) --> setPixelColor(%d, 0x%x (dim))" % (i, dim_color(color)))
      # Oops! I foolishly glued pixel strip backwards, so must invert 'i' here!
      neopixels.setPixelColor(NEOPIXEL_COUNT - i - 1, dim_color(color))
    time.sleep(0.01) # Need to pause briefly between settings
    neopixels.show()

# Control the modifications to the off_time variable
def change_off_time(delta):
  global off_time
  # print("--> change_off_time(%0.2f)  [%0.2f]" % (delta, off_time - time.time()))
  if off_time < time.time():
    if delta > 0:
      off_time = time.time() + delta
  else:
    if delta > 0:
      off_time += delta
    elif delta < 0 and off_time + delta <= time.time():
      off_time = time.time() - 1
    else:
      off_time += delta
  # Enforce the timer maximum
  now = time.time()
  max = now + (TIME_MAX_IN_MINUTES * 60.0)
  if off_time > max:
    off_time = max
  # print("<-- change_off_time(%0.2f)  [%0.2f]" % (delta, off_time - time.time()))

# Handle button presses
def press_button(which):
  if (which == "red"):
    #print("RED Button")
    change_off_time(TIME_QUANTUM_IN_MINUTES * 60.0)
  elif (which == "green"):
    #print("GREEN Button")
    change_off_time(- TIME_QUANTUM_IN_MINUTES * 60.0)

# Shutdown the Heater, the NeoPixels, etc.
def cleanup():
  # Reset the off timer
  global off_time
  off_time = time.time() - 1
  # Turn off the warmer relay
  GPIO.output(WARMER_RELAY, GPIO.LOW)
  # Turn off the "ready" LED
  GPIO.output(READY_LED, GPIO.LOW)
  # Turn off all of the NeoPixels
  for i in range(neopixels.numPixels()):
    neopixels.setPixelColor(i, Color(0,0,0))
    time.sleep(0.01) # Need to pause briefly between settings
    neopixels.show()
  # For cleanliness, move to a new line in the output after the ^C
  print('')

# Update the global current_state, used by the REST srver
def update_current_state():
  global current_state
  secs = max(0, off_time - time.time())
  c_s = '{'
  c_s += ('"temp_c":%0.1f,' % (current_temp))
  c_s += ('"temp_color":"#%06x",' % (temp_color))
  c_s += ('"time_sec":%0.1f' % (secs))
  c_s += '}'
  current_state = c_s
  # print('current_state = "' + current_state + '"')

# This is all the code that implements the Flask web server
web_server = None
def start_web_server():
  # app.run(debug=False, use_reloader=False, host='0.0.0.0')
  app.run(debug=True, use_reloader=False, host='0.0.0.0')
@app.route('/favicon.ico', methods=['GET'])
def send_favicon():
  return send_file('/usr/src/app/favicon.ico')
@app.route("/images/<filename>", methods=['GET'])
def send_image(filename):
  filename = os.path.basename(filename)
  return send_file('/usr/src/app/images/' + filename)
@app.route("/<filename>", methods=['GET'])
def send_other(filename):
  filename = os.path.basename(filename)
  return send_file('/usr/src/app/html/' + filename)
@app.route("/state", methods=['GET'])
def send_state():
  return '{"state":' + current_state + '}'
@app.route("/", methods=['GET'])
def send_root():
  return send_file('/usr/src/app/html/index.html')
@app.route('/button/red', methods=['POST'])
def press_button_red():
  press_button('red')
  return ''
@app.route('/button/green', methods=['POST'])
def press_button_green():
  press_button('green')
  return ''

# Global variables and main program
current_state = None
off_time = time.time() - 1
current_temp = 0
temp_color = 0x000000
heater_state = 0
cooldown_start = 0
def main():

  try:                                                                        

    # Initialize the global current_state, used by the REST srver
    update_current_state()

    # Start the web server in a thread
    global web_server
    web_server = threading.Thread(target=start_web_server)
    # The line below ensures the web server thread exits when main exits
    web_server.setDaemon(True)
    web_server.start()

    # Reduce console noise
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Turn on the "ready" indicator
    GPIO.output(READY_LED, GPIO.HIGH)

    global heater_state
    heater_state = 0
    just_started = True
    while True:                                                             

      # Get the smoothed temperature reading
      temp_smoothed = get_smoothed_temp(mcp3008, THERMISTOR_CHANNEL)
      # print("The temperature is %0.2f degrees celsius." % (temp_smoothed))

      # Adjust the temperature if appropriate
      global current_temp
      if math.fabs(current_temp - temp_smoothed) > 0.5:
        current_temp = temp_smoothed

      if GPIO.event_detected(BUTTON_RED):
        press_button("red")

      if GPIO.event_detected(BUTTON_GREEN):
        press_button("green")

      # Operate the relay
      now = time.time()
      if off_time > now:
        #if heater_state == 0: print("--> ON (off in %0.2fs)" % (off_time - now))
        GPIO.output(WARMER_RELAY, GPIO.HIGH)
        heater_state = 1
      else:
        global cooldown_start
        if just_started:
          just_started = False
          cooldown_start = time.time() - (COOLDOWN_PAUSE_IN_SECONDS + FADE_TIME_SEC + 1)
          # print("--> OFF (at startup)")
        elif heater_state != 0:
          cooldown_start = time.time()
          # print("--> OFF")
        GPIO.output(WARMER_RELAY, GPIO.LOW)
        heater_state = 0

      # Update state every loop even if user does nothing, because time flies!
      update_current_state()

      # Update neopixels ever loop too
      update_neopixels(temp_smoothed, max(0, off_time - time.time()))

      # Brief pause before repeating
      # time.sleep(LOOP_SLEEP_MSEC / 1000.0)
                                                                                
  except KeyboardInterrupt:
    cleanup()

  # For any failure at all, shutdown everything (especially the warmer relay!
  except:                                                   
    import traceback
    traceback.print_exc()
    cleanup()

  # Exit cleanly (need this to close the web server thread
  exit(0)

if __name__ == '__main__':
  main()
