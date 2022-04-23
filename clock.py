#!/usr/bin/python3
#---------------------------------------------------------------------#
# File: /home/will/OneDrive/PiSpace/ByProject/Octoprint Clock/clock.py
# Project: OctoPrint Clock
# Created Date: Wednesday, December 1st 2021, 9:03:51 pm
# Description: The main python file for my OctoPrint information clock project
# Author: Will Hall
# Copyright (c) 2021 Lime Parallelogram
# -----
# Last Modified: Sat Apr 23 2022
# Modified By: Will Hall
# -----
# HISTORY:
# Date      	By	Comments
# ----------	---	---------------------------------------------------------
# 2022-04-23	WH	Added simple checks before loading config file
# 2022-04-23	WH	Moved to use standard configparser
# 2022-04-23	WH	Code now ignores template file
# 2021-12-01	WH	Created request for server data
# 2021-12-01	WH	Created parser to load config from file
# 2021-12-01	WH	Raspberry Pi Password: OctoClock
#---------------------------------------------------------------------#
# ------------------------------ Imports modules ----------------------------- #
import board
import neopixel
import os
import math
import requests
import json
from string import Template
import RPi.GPIO as GPIO
import time
import threading
import configparser

# ---------------------------- Program Parameters ---------------------------- #
# CONFIG File Settings
CONFIG_DIR = "config/"
PRINTER_CONFIG = CONFIG_DIR + "printers.conf"
LED_CONFIG = CONFIG_DIR + "led_ring.conf"

# LED Settings
BRIGHTNESS_REDUCTION_FACTOR = 0.3

# Colour / Image
DEFAULT_COLOUR = (0,0,2) 
DEFAULT_YELLOW = (3,2,1)
BLANK = (0, 0, 0)
LED_DEFAULT = [DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, BLANK, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, DEFAULT_COLOUR, BLANK, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW, DEFAULT_YELLOW]

# ----------------------------- Program Variables ---------------------------- #

# --------------- Class that governs interactions with the API --------------- #
class OctoAPI:
    def __init__(self,printer):
        try:
            # Set instance attributes from printer dictionary
            self.API_KEY = printer["API_KEY"]
            self.IP = printer["IP"]
            self.PORT = printer["PORT"]
            self.address = Template(f"http://{self.IP}:{self.PORT}/api/$request?apikey={self.API_KEY}")
            self.ID = int(printer["ID"])
            self.colour = printer["COLOUR"]
            # Convert string colour (###,###,###) to tuple
            self.colour = self.colour.replace("(","")
            self.colour = self.colour.replace(")","")
            self.colour = tuple(map(int,self.colour.split(",")))
            self.colour = [c * BRIGHTNESS_REDUCTION_FACTOR for c in self.colour]
        except:
            raise self.InvalidConfigError

        # ----------------- #
        # Simple config checks
        if len(self.colour) != 3: # Check colour is in a valid format
            raise self.InvalidConfigError
        if not self.PORT.isdigit(): # Check that specified port is a digit
            raise self.InvalidConfigError
        if len(self.API_KEY) != 32: # Check API key is correct length
            raise self.InvalidConfigError

        self.remainingTime = 6
        self.displayedTime = -1

    # ----------------- #
    # Make a HTTP request to the server
    def makeRequest(self,request):
        apiRequest = requests.get(self.address.substitute(request=request))
        data = apiRequest.text
        jsonData = json.loads(data)
        return jsonData
    
    # ----------------- #
    # Check if printer is operational
    def isOperational(self):
        response = self.makeRequest("connection")
        if response["current"]["state"] == "Operational":
            return True

        return False

    # ----------------- #
    # Get the remaining time [in mins]
    def getRemainingTime(self):
        job = self.makeRequest("job")
        progress = job["progress"]
        seconds = int(progress["printTimeLeft"]) if progress["printTimeLeft"] != None else 0
        
        if job["state"] != "Printing":
            self.remainingTime = -1

        elif seconds == 0 and job["state"] == "Printing": # If time estimate not provided, assume > 11.5 hours
            self.remainingTime = 11.5*60

        else:
            mins = seconds // 60
            self.remainingTime = mins

        return self.remainingTime
    
    # ----------------- #
    # Get update the displayed time on the return
    def updateDisplayedTime(self):
        self.displayedTime = self.remainingTime

    # ----------------- #
    # Update the remaining time in this class
    def updateRemainingTime(self):
        self.remainingTime = self.getRemainingTime()

    # ----------------- #
    # Invalid config error - raised when the config is invalid or incomplete
    class InvalidConfigError(Exception):
        pass 

# -------------- Class that governes interactions with the LEDS -------------- #
class LEDRing:
    def __init__(self,pin,numLEDs,defaultImage,dataDirection,twelveLED):
        self.NUM_LEDS = int(numLEDs)
        self.PIXELS = neopixel.NeoPixel(board.pin.Pin(int(pin)),int(numLEDs))
        self.defaultDisplay = defaultImage

        self.ledMap = self._generateMap(int(twelveLED),dataDirection)
    
    # ----------------- #
    # Generate map dictionary of clock value to actual LED Number
    def _generateMap(self,twelveLED, dataDirection):
        directionMultiplier = -1 if dataDirection == "ACW" else 1

        map = {-1:-1}
        for led in range(0,self.NUM_LEDS):
            ledLocation = twelveLED + led*directionMultiplier
            if ledLocation < 0:
                ledLocation += self.NUM_LEDS
            
            if ledLocation >= self.NUM_LEDS:
                ledLocation -= self.NUM_LEDS

            map[led] = ledLocation
        return map
    
    # ----------------- #
    # Convert a time in mins to a number of clock segments
    def _timeToSegments(self,mins):
        segments = round(mins / 30)
        if segments >= self.NUM_LEDS: # If the segment requested is more than available, show max
            segments = self.NUM_LEDS -1
            
        return segments

    # ----------------- #
    # Reset the entire display to default image
    def clear(self):
        for pixel in range(self.NUM_LEDS):
            self.PIXELS[pixel] = self.defaultDisplay[pixel]
            time.sleep(0.03)
    
    # ----------------- #
    # Flash entire face quickly red (ERROR)
    def errorDisplay(self):
        for i in range(7):
            self.PIXELS.fill((255,0,0))
            time.sleep(0.1)
            self.PIXELS.fill((0,0,0))
            time.sleep(0.1)
        
    # ----------------- #
    # Shade the two LEDs next to a number on the clock
    def shadeNumber(self,number,colour):
        try:
            self.PIXELS[self.ledMap[number*2]] = colour
            self.PIXELS[self.ledMap[number*2+1]] = colour
        except KeyError:
            print(f"The specified number {number} does not exist on a clock face!")
    
    # ----------------- #
    # Set the colour of an arbitrary pixel
    def setPixel(self,pixel,colour):
        self.PIXELS[pixel] = colour

    # ----------------- #
    # Show the remaining time on the clock
    def showTime(self,displayedTime,remainingTime,colour):
        oldLEDNum = self.ledMap[self._timeToSegments(displayedTime)] # The LED that was previously lit
        LEDNum = self.ledMap[self._timeToSegments(remainingTime)] # The LED that should now be lit
        
        if remainingTime != -1:
            originalColour = self.PIXELS[LEDNum]
            if originalColour != list(colour): # Check if another printer is showing the same time.
                # Fade out previous colour
                if displayedTime != -1:
                    for intensity in range(50,-1,-1):
                        newColour = tuple([i * (0.01*intensity) for i in originalColour])
                        self.PIXELS[oldLEDNum] = newColour
                        time.sleep(0.01)
                    self.PIXELS[oldLEDNum] = self.defaultDisplay[oldLEDNum]
                    
                # Fade up new LED
                for intensity in range(0,51):
                    newColour = tuple([i * (0.01*intensity) for i in colour])
                    self.PIXELS[LEDNum] = newColour
                    time.sleep(0.01)

                self.PIXELS[LEDNum] = colour
                
        else: # If the printer has finished
            if displayedTime != -1: # Display animation if printer has just finished
                self.printerFinnish(colour)
                self.PIXELS[oldLEDNum] = self.defaultDisplay[oldLEDNum]

    # ----------------- #
    # Display a finnishing animation 
    def printerFinnish(self,colour):
        ring.clear()

        for p in range(self.NUM_LEDS):
            ring.setPixel(self.ledMap[p],colour)
            time.sleep(0.1)

        time.sleep(5)
        
        for p in range(self.NUM_LEDS-1,-1,-1):
            ledNum = self.ledMap[p]
            ring.setPixel(ledNum,self.defaultDisplay[ledNum])
            time.sleep(0.1)
        
        time.sleep(3)

# ----------------------------- Display functions ---------------------------- #
# Display whether or not each printer is operational
def showOperationStatus():
    for printer in PRINTERS:
        if printer.isOperational():
            ring.shadeNumber(printer.ID,(0,255,0))
        else:
            ring.shadeNumber(printer.ID,(255,0,0))
    
# ----------------- #
# Display colours of loaded printer configurations
def showColourTest():
    for printer in PRINTERS:
        ring.shadeNumber(printer.ID,printer.colour)
    

# ------------------------------- Loads Config ------------------------------- #
ledConfig = configparser.ConfigParser()
ledConfig.read(LED_CONFIG)
faceConfig = ledConfig["face"]
pinConfig = ledConfig["pins"]

printerConfig = configparser.ConfigParser()
printerConfig.read(PRINTER_CONFIG)
PRINTERS = []
for printer in printerConfig.sections():
    try:
        PRINTERS.append(OctoAPI(printerConfig[printer]))
    except OctoAPI.InvalidConfigError:
        print(f"The config in {printer} is invalid. It will not be loaded")

# ------------------------ Setup Instance of LED ring ------------------------ #
ring = LEDRing(pin=pinConfig["LED_PIN"],
               numLEDs=faceConfig["NUM_LEDS"],
               defaultImage=LED_DEFAULT,
               dataDirection=faceConfig["DATA_DIRECTION"],
               twelveLED=faceConfig["TWELVE_LED"])

# ----------------------- Assumes control from Arduino ----------------------- #
TAKEOVER_PIN = int(pinConfig["TAKEOVER_PIN"])
if TAKEOVER_PIN != -1: # If the takeover pin is -1, indicates arduino is not installed
    GPIO.setup(TAKEOVER_PIN,GPIO.OUT)
    GPIO.output(TAKEOVER_PIN,True)
    time.sleep(3)
ring.clear()


# ------------------------------ Main Execution ------------------------------ #
# Thread to make requests to update time
def monitorTime():
    print("Starting Monitoring System...")
    thisThread = threading.currentThread()

    while getattr(thisThread,"monitor",True):
        try:
            for printer in PRINTERS:
                printer.updateRemainingTime()
            time.sleep(30) # Wait 30s before next query

        except Exception as e:
            ring.errorDisplay()
            time.sleep(600)

try:
    showColourTest()
    time.sleep(5)
    ring.clear()

    monitor = threading.Thread(target=monitorTime)
    monitor.start()

    print("Starting Display System...")
    while True:
        try:
            for printer in PRINTERS:
                #Update the displayed time on the clock faceremainingTime
                oldDisplayedTime = printer.displayedTime
                printer.updateDisplayedTime()
                ring.showTime(oldDisplayedTime,printer.remainingTime,printer.colour)
                time.sleep(4)
                
        except KeyboardInterrupt:
            print("Stopping System...")
            monitor.monitor = False
            GPIO.cleanup()
            break

except Exception as e:
    ring.errorDisplay()
    raise e