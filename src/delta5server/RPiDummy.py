HIGH = 1
LOW = 0
BOARD = 2
BCM = 3
IN = 4
OUT = 5
PUD_UP = 6
PUD_DOWN = 7

channels = {}

def setmode(mode):
    pass

def setup(channel, type, initial=LOW, pull_up_down=PUD_DOWN):
    channels[channel] = initial

def output(channel, value):
    channels[channel] = value

def input(channel):
    return channels[channel]

def cleanup():
    channels = {}

def RPI_INFO():
    return "Dummy"

def VERSION():
    return "Dummy"
