
from lib.RX5808 import *
from lib.SPI import *

spi = SPI(11,10,25,9) #CLK, MOSI, CS, MISO


rx1 = RX5808(25,1) #CS , INDEX
rx1.set_spi(spi)
#print rx1.get_rssi()
print rx1.set_frequency(5740)

