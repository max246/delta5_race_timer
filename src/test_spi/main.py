
from lib.RX5808 import *
from lib.SPI import *

spi = SPI(18,24,23,25)


rx1 = RX5808(1,1)
rx1.set_spi(spi)
rx1.change_frequency(5865)
print rx1.get_rssi()
