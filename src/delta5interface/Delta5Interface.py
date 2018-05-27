'''Delta 5 hardware interface layer.'''

import gevent # For threads and timing
from gevent.lock import BoundedSemaphore # To limit i2c calls

from BaseHardwareInterface import BaseHardwareInterface
from delta5server.lib.ManagerRX import *

UPDATE_SLEEP = 0.1 # Main update loop delay



class Delta5Interface(BaseHardwareInterface):
    def __init__(self):
        BaseHardwareInterface.__init__(self)
        self.update_thread = None # Thread for running the main update loop
        self.pass_record_callback = None # Function added in server.py
        self.hardware_log_callback = None # Function added in server.py

        #Setup reader
        cs_rx = [25,2,2,2,2,2]
        spi = SPI(11, 10, 8, 9, cs_rx)  # CLK, MOSI, CS, MISO, ARRAY CS RX
        self._manager_rx = ManagerRX(spi)
        for i in range(0,5):
            if spi.read_adc(i) > 0:
                self._manager_rx.add_node(5865, cs_rx[i], i)


        '''
        # Scans all i2c_addrs to populate nodes array
        self.nodes = [] # Array to hold each node object
        i2c_addrs = [8, 10, 12, 14, 16, 18, 20, 22] # Software limited to 8 nodes
        for index, addr in enumerate(i2c_addrs):
            try:
                self.i2c.read_i2c_block_data(addr, READ_ADDRESS, 1)
                print "Node FOUND at address {0}".format(addr)
                gevent.sleep(I2C_CHILL_TIME)
                node = Node() # New node instance
                node.i2c_addr = addr # Set current loop i2c_addr
                node.index = index
                self.nodes.append(node) # Add new node to Delta5Interface
            except IOError as err:
                print "No node at address {0}".format(addr)
            gevent.sleep(I2C_CHILL_TIME)

        '''

        '''
        for node in self.nodes:
            node.frequency = self.get_value_16(node, READ_FREQUENCY)
            if node.index == 0:
                self.calibration_threshold = self.get_value_16(node,
                    READ_CALIBRATION_THRESHOLD)
                self.calibration_offset = self.get_value_16(node,
                    READ_CALIBRATION_OFFSET)
                self.trigger_threshold = self.get_value_16(node,
                    READ_TRIGGER_THRESHOLD)
                self.filter_ratio = self.get_value_8(node,
                    READ_FILTER_RATIO)
            else:
                self.set_calibration_threshold(node.index, self.calibration_threshold)
                self.set_calibration_offset(node.index, self.calibration_offset)
                self.set_trigger_threshold(node.index, self.trigger_threshold)
        '''

    #
    # Class Functions
    #

    def log(self, message):
        '''Hardware log of messages.'''
        if callable(self.hardware_log_callback):
            string = 'Delta 5 Log: {0}'.format(message)
            self.hardware_log_callback(string)

    #
    # Update Loop
    #

    def start(self):
        if self.update_thread is None:
            self.log('Starting background thread.')
            self.update_thread = gevent.spawn(self.update_loop)

    def update_loop(self):
        while True:
            self.update()
            gevent.sleep(UPDATE_SLEEP)

    def update(self):
        self._manager_rx.read_all()
        for rx in self._manager_rx.get_nodes():
            ms_since_lap = rx.get_last_ms()
            self.pass_record_callback(rx, ms_since_lap)

        '''
        for node in self.nodes:
            data = self.read_block(node.i2c_addr, READ_LAP_STATS, 17)
            if data != None:
                lap_id = data[0]
                ms_since_lap = unpack_32(data[1:])
                node.current_rssi = unpack_16(data[5:])
                node.trigger_rssi = unpack_16(data[7:])
                node.peak_rssi_raw = unpack_16(data[9:])
                node.peak_rssi = unpack_16(data[11:])
                node.loop_time = unpack_32(data[13:])

                if lap_id != node.last_lap_id:
                    if node.last_lap_id != -1 and callable(self.pass_record_callback):
                        self.pass_record_callback(node, ms_since_lap)
                    node.last_lap_id = lap_id
        '''

    #
    # External functions for setting data
    #

    #done
    def set_frequency(self, node_index, frequency):
        self._manager_rx.set_frequency(node_index, frequency)
    #done
    def set_calibration_threshold(self, node_index, threshold):
        self._manager_rx.set_calibration_threshold(node_index, threshold)

    #done
    def set_calibration_threshold_global(self, threshold):
        self.calibration_threshold = threshold
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_threshold(i, threshold)
        return self.calibration_threshold

    #done
    def set_calibration_mode(self, node_index, calibration_mode):
        self._manager_rx.set_calibration_mode(node_index, calibration_mode);

    #done
    def enable_calibration_mode(self):
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_mode(i, True);
    #done
    def set_calibration_offset(self, node_index, offset):
        self._manager_rx.set_calibration_offset(node_index, offset)
    #done
    def set_calibration_offset(self, offset):
        self.calibration_offset = offset
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_calibration_offset(i, offset)
        return self.calibration_offset
    #done
    def set_trigger_threshold(self, node_index, threshold):
        self._manager_rx.set_trigger_threshold(node_index, threshold)

    #done
    def set_trigger_threshold_global(self, threshold):
        self.trigger_threshold = threshold
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_trigger_threshold(i, threshold)
        return self.trigger_threshold

    #done
    def set_filter_ratio(self, node_index, filter_ration):
        self._manager_rx(node_index, filter_ration)

    #done
    def set_filter_ratio_global(self, filter_ratio):
        self.filter_ratio = filter_ratio
        amount = self._manager_rx.get_amount()
        for i in range(0, amount):
            self._manager_rx.set_filter_ratio(i, filter_ratio)
        return self.filter_ratio

    def intf_simulate_lap(self, node_index):
        node = self.nodes[node_index]
        node.current_rssi = 11
        node.trigger_rssi = 22
        node.peak_rssi_raw = 33
        node.peak_rssi = 44
        node.loop_time = 55
        self.pass_record_callback(node, 100)

def get_hardware_interface():
    '''Returns the delta 5 interface object.'''
    return Delta5Interface()
