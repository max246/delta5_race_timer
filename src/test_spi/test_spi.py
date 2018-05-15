from lib.SPI import *
import time

spi = SPI(11,10,8,9,[25]) #CLK, MOSI, CS, MISO, ARRAY CS RX


while True:
    print spi.read_adc(0)
    time.sleep(0.1)
