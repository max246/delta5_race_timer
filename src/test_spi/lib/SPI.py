


class SPI:


   def __init__(self, sck, mosi)
       self._sck = sck
       self._mosi = mosi

       GPIO.setup(self._sck,GPIO.OUT)
       GPIO.setup(self._mosi,GPIO.OUT)

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
