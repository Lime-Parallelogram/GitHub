/*
 * File: /home/will22/OneDrive/PiSpace/ByProject/Octoprint Clock/GitHub/loading_arduino/loading/loading.ino
 * Project: /home/will22/OneDrive/PiSpace/ByProject/Octoprint Clock/GitHub/loading_arduino/loading
 * Created Date: Friday, April 22nd 2022, 7:58:37 pm
 * Description: 
 * Author: Will Hall
 * Copyright (c) 2022 Lime Parallelogram
 * -----
 * Last Modified: Sat Apr 23 2022
 * Modified By: Will Hall
 * -----
 * HISTORY:
 * Date      	By	Comments
 * ----------	---	---------------------------------------------------------
 * 2022-04-23	WH	Added descriptive comments
 */
#include <FastLED.h>

// UPDATE TO MATCH YOUR CONFIGURTION
#define LEDPIN     1
#define NUMOFLEDS    24
#define INTERRUPT_PIN 2

// -- //
CRGB leds[NUMOFLEDS];

void setup() {
  // Setup LED ring and Pi takeover pin
  FastLED.addLeds<WS2812, LEDPIN, GRB>(leds, NUMOFLEDS);
  pinMode(INTERRUPT_PIN, INPUT);

}

void loop()
{
  if (digitalRead(INTERRUPT_PIN) == LOW) { // Cease sending commands when pi input is detected
    leds[NUMOFLEDS-1] = CRGB(0, 0, 0); // Turn off final LED
    
    for (int i = 0; i < NUMOFLEDS; i++) {
      leds[i-1] = CRGB ( 0, 0, 0); // Deactivate previous LED
      leds[i] = CRGB (255, 0, 0); // Illuminate single LED
      FastLED.show(); // Update LEDs
      
      delay(100);
    }
  }
}
