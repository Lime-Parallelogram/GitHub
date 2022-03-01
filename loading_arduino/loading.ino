/*
 * File: /home/will/OneDrive/PiSpace/ByProject/Octoprint Clock/loading.ino
 * Project: Octoprint Clock
 * Created Date: Saturday, December 11th 2021, 8:09:32 am
 * Description: An arduino project to handle the loading animation of the LED strip
 * Author: Will Hall
 * Copyright (c) 2021 Lime Parallelogram
 * -----
 * Last Modified: Sat Dec 11 2021
 * Modified By: Will Hall
 * -----
 * HISTORY:
 * Date      	By	Comments
 * ----------	---	---------------------------------------------------------
 */
#include <FastLED.h>

#define LEDPIN     11
#define NUMOFLEDS    24
#define INTERRUPT_PIN 2

CRGB leds[NUMOFLEDS];

void setup() {

  FastLED.addLeds<WS2812, LEDPIN, GRB>(leds, NUMOFLEDS);
  pinMode(INTERRUPT_PIN, INPUT);

}

void loop()
{
  if (digitalRead(INTERRUPT_PIN) == LOW) {

    leds[NUMOFLEDS-1] = CRGB( 0, 0, 0);
    for (int i = 0; i < NUMOFLEDS; i++) {
      leds[i-1] = CRGB ( 0, 0, 0);
      leds[i] = CRGB ( 255, 0, 0);
      FastLED.show();
      delay(100);
    }
  }
}
