
from lib.RX5808 import *
from lib.SPI import *

spi = SPI(18,24)


rx1 = RX5808(1,1)
rx1.set_spi(spi)
rx1.change_frequency(5865)
rx1.read_rssi()
