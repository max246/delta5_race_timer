from lib.RX5808 import *
from lib.SPI import *
import time

spi = SPI(11,10,8,9,[25]) #CLK, MOSI, CS, MISO, ARRAY CS RX


rx1 = RX5808(25,0) #CS , INDEX
rx1.set_spi(spi)
print rx1.set_frequency(5725)

#RSSI is 150  ( around this value ) when nothing
#RSSI is 350 ( around this value ) when high / close vtx
while True:
    print rx1.get_rssi()
    time.sleep(0.1)
