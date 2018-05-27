
from lib.ManagerRX import *

class Delta5Hardware:

    def __init__(self):

        #Setup reader
        cs_rx = [25, 2, 2, 2, 2, 2]
        spi = SPI(11, 10, 8, 9, cs_rx)  # CLK, MOSI, CS, MISO, ARRAY CS RX
        self._manager_rx = ManagerRX(spi)
        for i in range(0, 5):
            if spi.read_adc(i) > 0:
                self._manager_rx.add_node(5865, cs_rx[i], i)

    # done
    def set_frequency(self, node_index, frequency):
        self._manager_rx.set_frequency(node_index, frequency)

    # done
    def set_calibration_threshold(self, node_index, threshold):
        self._manager_rx.set_calibration_threshold(node_index, threshold)

    # done
    def set_calibration_threshold_global(self, threshold):
        self.calibration_threshold = threshold
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_threshold(i, threshold)
        return self.calibration_threshold

    # done
    def set_calibration_mode(self, node_index, calibration_mode):
        self._manager_rx.set_calibration_mode(node_index, calibration_mode);

    # done
    def enable_calibration_mode(self):
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_mode(i, True);

    # done
    def set_calibration_offset(self, node_index, offset):
        self._manager_rx.set_calibration_offset(node_index, offset)

    # done
    def set_calibration_offset(self, offset):
        self.calibration_offset = offset
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_offset(i, offset)
        return self.calibration_offset

    # done
    def set_trigger_threshold(self, node_index, threshold):
        self._manager_rx.set_trigger_threshold(node_index, threshold)

    # done
    def set_trigger_threshold_global(self, threshold):
        self.trigger_threshold = threshold
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_trigger_threshold(i, threshold)
        return self.trigger_threshold

    # done
    def set_filter_ratio(self, node_index, filter_ration):
        self._manager_rx(node_index, filter_ration)

    # done
    def set_filter_ratio_global(self, filter_ratio):
        self.filter_ratio = filter_ratio
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_filter_ratio(i, filter_ratio)
        return self.filter_ratio


    def get_nodes(self):
        return self._manager_rx.get_nodes()

    def get_heartbeat_json(self):
        c_rssi = []
        for node in self._manager_rx.get_nodes():
            c_rssi.append(node.get_current_rssi())

        return {
            'current_rssi': c_rssi,
            'loop_time': [] #need to remove this no needed
        }

    def default_frequencies(self):
        '''Set node frequencies, IMD for 6 or less and race band for 7 or 8.'''
        frequencies_imd_5_6 = [5685, 5760, 5800, 5860, 5905, 5645]
        frequencies_raceband = [5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917]
        for index, node in enumerate(manager_hardware.get_nodes()):
            gevent.sleep(0.100)
            if RACE.num_nodes < 7:
                self.set_frequency(index, frequencies_imd_5_6[index])
            else:
                self.set_frequency(index, frequencies_raceband[index])


class ThreadReadRX(Threading):

    def __init__(self):
        print "thread"
        self._managerRX = None

    def run(self):
        rx_to_update = []
        while True:
            rx_to_update = self._managerRX.read_all()
            #If there are rx updated, do an emit
            if len(rx_to_update) > 0:
                for rx in rx_to_update:
                    self._cb(rx)
            rx_to_update = None
            time.sleep(0.1)


class ThreadHeartbeat(Threading):

    def __init__(self, cb_socket):
        self._cb_socket = cb_socket

    def run(self):
        while True:
            self._cb_socket.emit('heartbeat', manager_hardware.get_heartbeat_json())
            time.sleep(0.5)