# Wiring

## RX
CH1 => GPIO10 ( MOSI )
CH2 => GPIO25 ( CS )
CH3 => GPIO11 ( SCLK )
5V => 5V
GND => GND



## MCP3008
0 => RSSI
16 => 3.3V
15 => 3.3V
14 => GND
13 => GPIO11 ( SCLK )
12 => GPIO9 ( MISO )
11 => GPIO10 ( MOSI )
10 => GPIO8 ( CS )
9 => GND


# Code

Setup the SPI with the following if you followed the schematic above, remember to populate he array CS if you add more RXs
    spi = SPI(11,10,8,9,[25]) #CLK, MOSI, CS, MISO, ARRAY CS RX

Setup the RX by telling which GPIO is going to be CS ( each RX need to have an individual one! ) and the index on the MCP3008
    rx1 = RX5808(25,0) #CS , INDEX
    rx1.set_spi(spi)
    print rx1.set_frequency(5725)


RSSI is 150  ( around this value ) when nothing
RSSI is 350 ( around this value ) when high / close vtx
    rx1.get_rssi()
