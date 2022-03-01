#---------------------------------------------------------------------#
# File: /home/will/OneDrive/PiSpace/ByProject/Octoprint Clock/clock.py
# Project: OctoPrint Clock
# Created Date: Wednesday, December 1st 2021, 9:03:51 pm
# Description: The main python file for my OctoPrint information clock project
# Author: Will Hall
# Copyright (c) 2021 Lime Parallelogram
# -----
# Last Modified: Thu Dec 16 2021
# Modified By: Will Hall
# -----
# HISTORY:
# Date      	By	Comments
# ----------	---	---------------------------------------------------------
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

# ---------------------------- Program Parameters ---------------------------- #
CONFIG_DIR = "/mnt/config"
PRINTER_CONFIG = "/mnt/config/printers/"
NUM_LEDS = 24
MINS_PER_LED = (12*60)/NUM_LEDS
LED_PIN = board.D18
TAKEOVER_PIN = 15
TWELVE_LED = 20 #The ID of the LED that represents 12 o-clock
DEFAULT_COLOUR = (0,0,2)
BLANK = (0, 0, 0)
LED_DEFAULT = [DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK, DEFAULT_COLOUR, BLANK]
BRIGHTNESS_REDUCTION_FACTOR = 0.3

# ----------------------------- Program Variables ---------------------------- #
m
# ---------------------------------- Parsers --------------------------------- #
class Parsers:
    def parsePrinterConfig(file):
        with open(file,'r') as f:
            lines = f.readlines()

        printer = {}
        for line in lines:
            if not line[0] == "#" and len(line) > 3: #Ignore commented lines and empty lines
                if line.count("=") == 1: #Check there is exactly one equals sign
                    line = line.replace(" ","") #Remove spaces
                    line = line.strip() #Remove endline and erroneous characters
                    keyValue = line.split("=")
                    printer[keyValue[0]] = keyValue[1]
        
        return printer

# --------------- Class that governs interactions with the API --------------- #
class OctoAPI:
    def __init__(self,printer):
        self.API_KEY = printer["API_KEY"]
        self.IP = printer["IP"]
        self.PORT = printer["PORT"]
        self.address = Template(f"http://{self.IP}:{self.PORT}/api/$request?apikey={self.API_KEY}")
        self.ID = int(printer["ID"])
        self.colour = printer["COLOUR"]
        self.colour = self.colour.replace("(","")
        self.colour = self.colour.replace(")","")
        self.colour = tuple(map(int,self.colour.split(",")))
        self.colour = [c * BRIGHTNESS_REDUCTION_FACTOR for c in self.colour]
        self.remainingTime = 6
        self.displayedTime = -1

    def makeRequest(self,request):
        apiRequest = requests.get(self.address.substitute(request=request))
        data = apiRequest.text
        jsonData = json.loads(data)
        return jsonData
    
    def isOperational(self):
        response = self.makeRequest("connection")
        if response["current"]["state"] == "Operational":
            return True

        return False

    def getRemainingTime(self):
        job = self.makeRequest("job")
        progress = job["progress"]
        seconds = int(progress["printTimeLeft"]) if progress["printTimeLeft"] != None else 0
        if job["state"] != "Printing":
            return -1
        if seconds == 0 and job["state"] == "Printing":
            self.remainingTime = 11
            return 11
        mins = seconds // 60
        segments = round(mins / 30)
        if segments > NUM_LEDS - 1:
            segments = NUM_LEDS -1
            
        self.remainingTime = segments
        return segments
    
    def updateDisplayedTime(self):
        self.displayedTime = self.remainingTime

# -------------- Class that governes interactions with the LEDS -------------- #
class LEDRing:
    def __init__(self,pin,numLEDs):
        self.NUM_LEDS = numLEDs
        self.PIXELS = neopixel.NeoPixel(pin,numLEDs)
    
    def clear(self):
        for pixel in range(NUM_LEDS):
            self.PIXELS[pixel] = LED_DEFAULT[pixel]
            time.sleep(0.03)
    
    def errorDisplay(self):
        for i in range(7):
            self.PIXELS.fill((255,0,0))
            time.sleep(0.1)
            self.PIXELS.fill((0,0,0))
            time.sleep(0.1)
        
    def shadeNumber(self,number,colour):
        secondLED = TWELVE_LED-number*2
        secondLED = secondLED + (NUM_LEDS) if secondLED < 0 else secondLED
        self.PIXELS[secondLED] = colour
        self.PIXELS[secondLED-1] = colour
    
    def setPixel(self,pixel,colour):
        self.PIXELS[pixel] = colour
    
    def showTime(self,displayedTime,remainingTime,colour):
        oldLEDNum = getLEDNum(displayedTime)
        LEDNum = getLEDNum(remainingTime)
        if remainingTime != -1:
            originalColour = self.PIXELS[LEDNum]
            if originalColour != list(colour):
                if originalColour != (0,0,0):
                    if displayedTime != -1:
                        for intensity in range(50,-1,-1):
                            newColour = tuple([i * (0.01*intensity) for i in originalColour])
                            self.PIXELS[oldLEDNum] = newColour
                            time.sleep(0.01)
                        self.PIXELS[oldLEDNum] = LED_DEFAULT[oldLEDNum]
                    for intensity in range(0,51):
                        newColour = tuple([i * (0.01*intensity) for i in colour])
                        self.PIXELS[LEDNum] = newColour
                        time.sleep(0.01)

                    time.sleep(4)
                    self.PIXELS[LEDNum] = colour
        else:
            if displayedTime != -1:
                printerFinnish(colour)
                self.PIXELS[oldLEDNum] = LED_DEFAULT[oldLEDNum]        
        

# ----------------------------- Display functions ---------------------------- #
def showOperationStatus():
    for printer in PRINTERS:
        if printer.isOperational():
            ring.shadeNumber(printer.ID,(0,255,0))
        else:
            ring.shadeNumber(printer.ID,(255,0,0))
    
def showColourTest():
    for printer in PRINTERS:
        ring.shadeNumber(printer.ID,printer.colour)
    
def printerFinnish(colour):
    ring.clear()

    for p in range(NUM_LEDS):
        ring.setPixel(getLEDNum(p),colour)
        time.sleep(0.1)

    time.sleep(5)
    
    for p in range(NUM_LEDS,-1,-1):
        ledNum = getLEDNum(p)
        ring.setPixel(ledNum,LED_DEFAULT[ledNum])
        time.sleep(0.1)
    
    time.sleep(3)

# ------------- Function to convert clock segment to pixel number ------------ #
def getLEDNum(segment):
    LEDNum = TWELVE_LED - segment
    LEDNum = LEDNum + 24 if LEDNum < 0 else LEDNum
    return LEDNum

# ------------------------------- Loads Config ------------------------------- #
printerFiles = [PRINTER_CONFIG+file for file in os.listdir(PRINTER_CONFIG) if not os.path.isdir(PRINTER_CONFIG+file) and file.endswith(".txt")]
PRINTERS = [OctoAPI(printer) for printer in [Parsers.parsePrinterConfig(printer) for printer in printerFiles]]

# ------------------------ Setup Instance of LED ring ------------------------ #
ring = LEDRing(LED_PIN,NUM_LEDS)

# ----------------------- Assumes control from Arduino ----------------------- #
GPIO.setup(TAKEOVER_PIN,GPIO.OUT)
GPIO.output(TAKEOVER_PIN,True)
time.sleep(3)
ring.clear()


# ------------------------------ Main Execution ------------------------------ #
def monitorTime():
    while True:
        try:
            for printer in PRINTERS:
                printer.remainingTime = printer.getRemainingTime()
            time.sleep(30)
        except Exception as e:
            ring.errorDisplay()
            time.sleep(600)
            #//raise e

try:
    showColourTest()
    time.sleep(5)
    ring.clear()

    threading.Thread(target=monitorTime).start()

    while True:
        for printer in PRINTERS:
            #Update the displayed time on the clock face
            oldDisplayedTime = printer.displayedTime
            printer.updateDisplayedTime()
            ring.showTime(oldDisplayedTime,printer.remainingTime,printer.colour)

except Exception as e:
    ring.errorDisplay()
    raise e