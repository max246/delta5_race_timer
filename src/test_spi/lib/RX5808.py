import time



class RX5808:


    vtx_frequency = [5865, 5845, 5825, 5805, 5785, 5765, 5745, 5725,  #  Band A
                     5733, 5752, 5771, 5790, 5809, 5828, 5847, 5866,  #  Band B
                     5705, 5685, 5665, 5645, 5885, 5905, 5925, 5945,  #  Band E
                     5740, 5760, 5780, 5800, 5820, 5840, 5860, 5880,  #  Band F
                      5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917 ] # Band C / Raceband
    vtx_hex    = [ 0x2A05, 0x299B, 0x2991, 0x2987, 0x291D, 0x2913, 0x2909, 0x289F,  #  Band A
                   0x2903, 0x290C, 0x2916, 0x291F, 0x2989, 0x2992, 0x299C, 0x2A05,  #  Band B
                   0x2895, 0x288B, 0x2881, 0x2817, 0x2A0F, 0x2A19, 0x2A83, 0x2A8D,  #  Band E
                   0x2906, 0x2910, 0x291A, 0x2984, 0x298E, 0x2998, 0x2A02, 0x2A0C,  #  Band F
                   0x281D, 0x288F, 0x2902, 0x2914, 0x2987, 0x2999, 0x2A0C, 0x2A1E  ] # Band C / Raceband

    def __init__(self,ss,index):
        self._ss = ss
        self._index = index


    def set_spi(self,spi):
        self._spi = spi

    def set_adc(self, adc):
        self._adc = adc

    def get_vtx_hex(self, freq):
        for i in range(len(self.vtx_frequency)):
            if self.vtx_frequency[i] == freq:
                return self.vtx_hex[i]
        return None

    def set_frequency(self,freq):
        channel_data = None
        for i in range(len(self.vtx_frequency)):
            if self.vtx_frequency[i] == freq:
                channel_data = self.vtx_hex[i]
                break

        if channel_data == None:
            s = "Error: unknown frequency {}MHz!".format(freq)
            print(s)
            return s

        print("Selected frequency: {}MHz ({})...".format(freq, channel_data))

        #set_register(0x08, 0x00)
        self._spi.set_register(0x08, 0x03F40, self._ss) # default values

        self._spi.set_register(0x01, channel_data, self._ss)

        self._spi.set_all_low(self._ss)

        return "Success (set freq to {})!".format(hex(channel_data))

    def get_frequency(self):
        channel_data = self._spi.get_register(0x01, self._ss)
        print channel_data, self._ss
        channel_freq = None
        for i in range(len(self.vtx_hex)):
            if self.vtx_hex[i] == channel_data:
                channel_freq = self.vtx_frequency[i]
                break

        if channel_freq == None:
            return "Unknown ({})".format(hex(channel_data))
        else:
            return str(channel_freq) + "MHz"


    def get_rssi(self):
        if ((self._index > 7) or (self._index < 0)):
                return -1

        return self._spi.read_adc(self._index)
