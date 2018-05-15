#Part of code has been taken from https://github.com/xythobuz/ due to issues by converting Arduino code to Python

try:
    import RPi.GPIO as GPIO
except:
    import RPiDummy as GPIO

import time

class SPI:


   def __init__(self, sck, mosi, cs, miso, csRX):
       self._sck = sck
       self._mosi = mosi
       self._cs = cs
       self._miso = miso
       self._csRX = csRX
       GPIO.setmode(GPIO.BCM)
       GPIO.setup(self._sck,GPIO.OUT)
       GPIO.setup(self._mosi,GPIO.OUT)
       GPIO.setup(self._cs,GPIO.OUT)
       GPIO.setup(self._miso,GPIO.IN)
       self.set_output_csrx()
     

   def set_output_csrx(self):
       for cs in self._csRX:
           GPIO.setup(cs,GPIO.OUT)

   def spi_readbit(self):
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)

       GPIO.output(self._sck, GPIO.HIGH)
       time.sleep(0.000001)

       if GPIO.input(self._mosi) == GPIO.HIGH:
           return True
       else:
           return False

       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)

   def get_register(self,reg,ss):
       self.set_low(ss)
       time.sleep(0.000001)
       self.set_high(ss)

       for i in range(4):
           if reg & (1 << i):
               self.send_bit_one()
           else:
               self.send_bit_zero()

       # Read from register
       self.send_bit_zero()

       GPIO.setup(self._mosi, GPIO.IN)

       data = 0
       for i in range(20):
           # Is bit high or low?
           val = self.spi_readbit()
           if val:
               data |= (1 << i)

       # Finished clocking data in
       self.set_high(ss)
       time.sleep(0.000001)

       GPIO.setup(self._mosi, GPIO.OUT)

       GPIO.output(ss, GPIO.LOW)
       GPIO.output(self._sck, GPIO.LOW)
       GPIO.output(self._mosi, GPIO.LOW)

       return data
    
   def set_register(self, reg, val, ss):
       self.set_high(ss)
       time.sleep(0.000001)
       self.set_low(ss)

       for i in range(4):
           if reg & (1 << i):
               self.send_bit_one()
           else:
               self.send_bit_zero()

       # Write to register
       self.send_bit_one();

       # D0-D15
       for i in range(20):
           # Is bit high or low?
           if val & 0x1:
               self.send_bit_one()
           else:
               self.send_bit_zero()
           # Shift bits along to check the next one
           val >>= 1

       # Finished clocking data in
       self.set_high(ss)
       time.sleep(0.000001)
       self.set_low(ss)

   def set_all_low(self, ss):
       GPIO.output(self._sck, GPIO.LOW)
       GPIO.output(self._mosi, GPIO.LOW)
       GPIO.output(ss, GPIO.LOW)

   def send_bit_zero(self):
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)

       GPIO.output(self._mosi, GPIO.LOW)
       time.sleep(0.000001)
       GPIO.output(self._sck, GPIO.HIGH)
       time.sleep(0.000001)
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)


   def send_bit_one(self):
       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)

       GPIO.output(self._mosi, GPIO.HIGH)
       time.sleep(0.000001)
       GPIO.output(self._sck, GPIO.HIGH)
       time.sleep(0.000001)

       GPIO.output(self._sck, GPIO.LOW)
       time.sleep(0.000001)

   def set_low(self, ss):
       time.sleep(0.000001)
       GPIO.output(ss, GPIO.LOW)
       time.sleep(0.000001)

   def set_high(self, ss):
       time.sleep(0.000001)
       GPIO.output(ss, GPIO.HIGH)
       time.sleep(0.000001)


   def set_all_cs_high(self):
       for cs in self._csRX:
           GPIO.output(cs, GPIO.HIGH)

   def read_adc(self, adcnum): #Thanks to ADAFRUIT for the code
       self.set_all_cs_high()
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
