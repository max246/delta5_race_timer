

class ManagerRX:


    def __init__(self,spi):
        self._spi = spi
        self._rxs = []
        self._calibration_threshold = 65

    def add_node(self,freq,cs, index):
        rx =  RX5808(cs, index) #CS , INDEX
        rx.set_spi(self._spi)
        rx.set_frequency(5725)
        self._rxs.append(rx)

    def remove_node(self,index):
        self._rxs.remove(index)

    def set_trigger_threshold_global(self,threshold):
        self._calibration_threshold = threshold
        for rx in self._rxs:
            rx.set_calibration_threadshold(threshold)
        return threshold


    def enable_calibration_mode(self):
        for rx in self._rxs:
            rx.enable_calibration_mode()

    def get_nodes(self):
        return self._rxs


    def get_calibration_threshold_json(self):

    def get_calibration_offset_json(self):

    def get_trigger_threshold_json(self):

    def get_heartbeat_json(sefl):

    
    
