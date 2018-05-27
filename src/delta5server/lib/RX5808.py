import time
try:
    import RPi.GPIO as GPIO
except:
    import RPiDummy as GPIO



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

    MODE_NORMAL = 0
    MODE_CALIBRATION = 1



    def __init__(self,ss,index):
        self._ss = ss
        self._index = index
        self._calibration_threshold = 95
        self._trigger_rssi = 40
        self._calibration_offset = 0
        self._filter_ratio = 0

        self._ms_since_lap = 0
        self._peak_rssi = 0
        self._peak_rssi_raw = 0
        self._frequency = 0
        self._currrent_rssi = 0


        self._MODE = MODE_NORMAL

        GPIO.setup(ss, GPIO.OUT)

    def set_spi(self,spi):
        self._spi = spi


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

        self._frequency = freq
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


    def set_trigger_threshold(self, rssi):
        self._trigger_rssi = rssi

    def get_trigger_threashold(self):
        return self._trigger_rssi

    def get_peak_rssi(self):
        return self._peak_rssi

    def get_rssi(self):
        if ((self._index > 7) or (self._index < 0)):
                return -1

        self._currrent_rssi = self._spi.read_adc(self._index)
        if self._currrent_rssi > self._peak_rssi: #Update the peak rssi
            self._peak_rssi = self._currrent_rssi
        return self._currrent_rssi


    def set_filter_ratio(self, ratio):
        self._filter_ratio = ratio

    def get_filter_ratio(self):
        return self._filter_ratio

    def set_calibration_offset(self, offset):
        self._calibration_offset = offset

    def get_calibration_offset(self):
        return self._calibration_offset

    def set_calibration_mode(self, active):
        if active:
            self._MODE = self.MODE_CALIBRATION
        else:
            self._MODE = self.MODE_NORMAL

    def set_calibration_threshold(self, threshold):
        self._calibration_threshold = threshold

    def get_settings_json(self):
        return {
            'frequency': self._frequency,
            'current_rssi': self._currrent_rssi,
            'trigger_rssi': self._trigger_rssi,
        }

    def get_heartbeat_json(self):
        return {
            'current_rssi': self._currrent_rssi,
            'trigger_rssi': self._trigger_rssi,
            'peak_rssi': self._peak_rssi
        }


    def get_current_rssi(self):
        return self._currrent_rssi