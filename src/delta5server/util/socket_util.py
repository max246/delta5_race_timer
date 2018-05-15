from flask_socketio import SocketIO, emit
import gevent


SOCKET_IO = SocketIO(async_mode='gevent')



def server_log(message):
    '''Messages emitted from the server script.'''
    print message
    SOCKET_IO.emit('hardware_log', message)

def hardware_log_callback(message):
    '''Message emitted from the delta 5 interface class.'''
    print message
    SOCKET_IO.emit('hardware_log', message)