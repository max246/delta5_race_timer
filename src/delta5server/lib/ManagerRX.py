class ManagerRX:

    def __init__(self,spi):
        self._spi = spi
        self._rxs = []
        self._calibration_threshold = 65


        

    def add_node(self,freq,cs, index):
        rx =  RX5808(cs, index) #CS , INDEX
        rx.set_spi(self._spi)
        rx.set_frequency(freq)
        self._rxs.append(rx)

    def remove_node(self,index):
        self._rxs.remove(index)


    def set_frequency(self,index, frequency):
        self._rxs[index].set_frequency(frequency)

    def enable_calibration_mode(self):
        for rx in self._rxs:
            rx.enable_calibration_mode()

    def get_nodes(self):
        return self._rxs

    def read_all(self):
        updates = []
        for rx in self._rxs:
            rx.get_rssi()
            if rx.check_pass():
                updates.append(rx)

        return updates


    '''
    def get_calibration_threshold_json(self):

    def get_calibration_offset_json(self):

    def get_trigger_threshold_json(self):

    def get_heartbeat_json(sefl):
'''

    def set_filter_ratio(self, index, ratio):
        self._rxs[index].set_filter_ratio(ratio)

    def set_trigger_threshold(self, index, threshold):
        self._rxs[index].set_trigger_threshold(threshold)

    def set_calibration_offset(self, index, offset):
        self._rxs[index].set_calibration_offset(offset)

    def set_calibration_mode(self, index, active):
        self._rxs[index].set_calibration_mode(active)

    def set_calibration_threshold(self, index, threashold):
        self._rxs[index].set_calibration_threshold(threashold)

    def get_amount(self):
        return len(self._rxs)



    
    
