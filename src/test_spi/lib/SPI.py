#import RPi.GPIO as GPIO
try:
    import RPi.GPIO as GPIO
except:
    import RPiDummy as GPIO

import time

class SPI:


   def __init__(self, sck, mosi, miso, cs):
       self._sck = sck
       self._mosi = mosi
       self._miso = miso
       self._cs = cs

       GPIO.setup(self._sck,GPIO.OUT)
       GPIO.setup(self._mosi,GPIO.OUT)
       GPIO.setup(self._miso,GPIO.IN)
       GPIO.setup(self._cs,GPIO.OUT)

   def send_bit_zero(self):
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.3)
       GPIO.output(self._mosi, GPIO.HIGH)
       time.sleep(0.3)
       GPIO.output(self._sck, GPIO.HIGH)
       time.sleep(0.3)
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.3)


   def send_bit_one(self):
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.3)
       GPIO.output(self._mosi, GPIO.LOW)
       time.sleep(0.3)
       GPIO.output(self._sck, GPIO.HIGH)
       time.sleep(0.3)
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.3)

   def set_low(self, ss):
       time.sleep(0.1)
       GPIO.output(ss, GPIO.LOW)
       time.sleep(0.1)

   def set_high(self, ss):
       time.sleep(0.1)
       GPIO.output(ss, GPIO.HIGH)
       time.sleep(0.1)


   def read_adc(self, adcnum): #Thanks to ADAFRUIT for the code
       GPIO.output(self._cs, True)

       GPIO.output(self._sck, False)  # start clock low
       GPIO.output(self._cs, False)     # bring CS low

       commandout = adcnum
       commandout |= 0x18  # start bit + single-ended bit
       commandout <<= 3    # we only need to send 5 bits here
       for i in range(5):
            if (commandout & 0x80):
                GPIO.output(self._mosi, True)
            else:
                GPIO.output(self._mosi, False)
            commandout <<= 1
            GPIO.output(self._sck, True)
            GPIO.output(self._sck, False)

       adcout = 0

       # read in one empty bit, one null bit and 10 ADC bits
       for i in range(12):
           GPIO.output(self._sck, True)
           GPIO.output(self._sck, False)
           adcout <<= 1
           if (GPIO.input(self._miso)):
               adcout |= 0x1

       GPIO.output(self._cs, True)

       adcout >>= 1       # first bit is 'null' so drop it

       return adcout
