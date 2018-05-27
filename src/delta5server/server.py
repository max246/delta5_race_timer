'''Delta5 race timer server script'''

import os
import sys
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, Response
from flask_socketio import  emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base


import gevent
import gevent.monkey
gevent.monkey.patch_all()


from lib.RX5808 import *
from lib.SPI import *
from lib.Delta5Hardware import  *

from Delta5Race import get_race_state


APP = Flask(__name__, static_url_path='/static')
APP.config['SECRET_KEY'] = 'secret!'

HEARTBEAT_THREAD = None

from util.socket_util import *
from util.socket_util import SOCKET_IO

SOCKET_IO.init_app(APP)


manager_hardware = Delta5Hardware()


RACE = get_race_state() # For storing race management variables

PROGRAM_START = datetime.now()
RACE_START = datetime.now() # Updated on race start commands

#
# Database Models
#

BASEDIR = os.path.abspath(os.path.dirname(__file__))
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASEDIR, 'database.db')
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#DB = SQLAlchemy(APP)

from model.db_models import DB
from model.db_models import Profiles, FixTimeRace, LastProfile, SavedRace, Pilot, Heat, Frequency, CurrentLap
from util.db_util import *

#This must be like that for some silly reason that SQL library doesnt add the reference
DB.init_app(APP)
DB.app = APP


#
# Authentication
#

def check_auth(username, password):
    '''Check if a username password combination is valid.'''
    return username == 'admin' and password == 'delta5'

def authenticate():
    '''Sends a 401 response that enables basic auth.'''
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

#
# Routes
#

@APP.route('/')
def index():
    '''Route to round summary page.'''
    # A more generic and flexible way of viewing saved race data is needed
    # - Individual round/race summaries
    # - Heat summaries
    # - Pilot summaries
    # Make a new dynamic route for each? /pilotname /heatnumber /
    # Three different summary pages?
    # - One for all rounds, grouped by heats
    # - One for all pilots, sorted by fastest lap and shows average and other stats
    # - One for individual heats
    #
    # Calculate heat summaries
    # heat_max_laps = []
    # heat_fast_laps = []
    # for heat in SavedRace.query.with_entities(SavedRace.heat_id).distinct() \
    #     .order_by(SavedRace.heat_id):
    #     max_laps = []
    #     fast_laps = []
    #     for node in range(RACE.num_nodes):
    #         node_max_laps = 0
    #         node_fast_lap = 0
    #         for race_round in SavedRace.query.with_entities(SavedRace.round_id).distinct() \
    #             .filter_by(heat_id=heat.heat_id).order_by(SavedRace.round_id):
    #             round_max_lap = DB.session.query(DB.func.max(SavedRace.lap_id)) \
    #                 .filter_by(heat_id=heat.heat_id, round_id=race_round.round_id, \
    #                 node_index=node).scalar()
    #             if round_max_lap is None:
    #                 round_max_lap = 0
    #             else:
    #                 round_fast_lap = DB.session.query(DB.func.min(SavedRace.lap_time)) \
    #                 .filter(SavedRace.node_index == node, SavedRace.lap_id != 0).scalar()
    #                 if node_fast_lap == 0:
    #                     node_fast_lap = round_fast_lap
    #                 if node_fast_lap != 0 and round_fast_lap < node_fast_lap:
    #                     node_fast_lap = round_fast_lap
    #             node_max_laps = node_max_laps + round_max_lap
    #         max_laps.append(node_max_laps)
    #         fast_laps.append(time_format(node_fast_lap))
    #     heat_max_laps.append(max_laps)
    #     heat_fast_laps.append(fast_laps)
    # print heat_max_laps
    # print heat_fast_laps
    return render_template('rounds.html', num_nodes=RACE.num_nodes, rounds=SavedRace, \
        pilots=Pilot, heats=Heat)
        #, heat_max_laps=heat_max_laps, heat_fast_laps=heat_fast_laps

@APP.route('/heats')
def heats():
    '''Route to heat summary page.'''
    return render_template('heats.html', num_nodes=RACE.num_nodes, heats=Heat, pilots=Pilot, \
        frequencies=[node.frequency for node in manager_hardware.get_nodes()], \
        channels=[Frequency.query.filter_by(frequency=node.frequency).first().channel \
            for node in manager_hardware.get_nodes()])

@APP.route('/race')
@requires_auth
def race():
    '''Route to race management page.'''
    return render_template('race.html', num_nodes=RACE.num_nodes,
                           current_heat=RACE.current_heat,
                           heats=Heat, pilots=Pilot,
                           fix_race_time=FixTimeRace.query.get(1).race_time_sec,
						   lang_id=RACE.lang_id,
        frequencies=[node.frequency for node in manager_hardware.get_nodes()],
        channels=[Frequency.query.filter_by(frequency=node.frequency).first().channel
            for node in manager_hardware.get_nodes()])

@APP.route('/settings')
@requires_auth
def settings():
    '''Route to settings page.'''

    return render_template('settings.html', num_nodes=RACE.num_nodes,
                           pilots=Pilot,
                           frequencies=Frequency,
                           heats=Heat,
                           last_profile =  LastProfile,
                           profiles = Profiles,
                           current_fix_race_time=FixTimeRace.query.get(1).race_time_sec,
						   lang_id=RACE.lang_id)

# Debug Routes

@APP.route('/hardwarelog')
@requires_auth
def hardwarelog():
    '''Route to hardware log page.'''
    return render_template('hardwarelog.html')

@APP.route('/database')
@requires_auth
def database():
    '''Route to database page.'''
    return render_template('database.html', pilots=Pilot, heats=Heat, currentlaps=CurrentLap, \
        savedraces=SavedRace, frequencies=Frequency, )

#
# Socket IO Events
#

@SOCKET_IO.on('connect')
def connect_handler():
    '''Starts the delta 5 interface and a heartbeat thread for rssi.'''
    server_log('Client connected')
    INTERFACE.start()
    #global HEARTBEAT_THREAD
    #if HEARTBEAT_THREAD is None:
    #    HEARTBEAT_THREAD = gevent.spawn(heartbeat_thread_function)
    #    server_log('Heartbeat thread started')
    emit_node_data() # Settings page, node channel and triggers
    emit_node_tuning() # Settings page, node tuning values
    emit_race_status() # Race page, to set race button states
    emit_current_laps() # Race page, load and current laps
    emit_leaderboard() # Race page, load leaderboard for current laps

@SOCKET_IO.on('disconnect')
def disconnect_handler():
    '''Emit disconnect event.'''
    server_log('Client disconnected')

# Settings socket io events

@SOCKET_IO.on('set_frequency')
def on_set_frequency(data):
    '''Set node frequency.'''
    node_index = data['node']
    frequency = data['frequency']
    manager_hardware.set_frequency(node_index, frequency)
    server_log('Frequency set: Node {0} Frequency {1}'.format(node_index+1, frequency))
    emit_node_data() # Settings page, new node channel

@SOCKET_IO.on('set_language')
def on_set_language(data):
    '''Set language.'''
    RACE.lang_id = data['language']
    emit_language_data()


@SOCKET_IO.on('add_heat')
def on_add_heat():
    '''Adds the next available heat number to the database.'''
    max_heat_id = DB.session.query(DB.func.max(Heat.heat_id)).scalar()
    for node in range(RACE.num_nodes): # Add next heat with pilots 1 thru 5
        DB.session.add(Heat(heat_id=max_heat_id+1, node_index=node, pilot_id=node+1))
    DB.session.commit()
    server_log('Heat added: Heat {0}'.format(max_heat_id+1))

@SOCKET_IO.on('set_pilot_position')
def on_set_pilot_position(data):
    '''Sets a new pilot in a heat.'''
    heat = data['heat']
    node_index = data['node']
    pilot = data['pilot']
    db_update = Heat.query.filter_by(heat_id=heat, node_index=node_index).first()
    db_update.pilot_id = pilot
    DB.session.commit()
    server_log('Pilot position set: Heat {0} Node {1} Pilot {2}'.format(heat, node_index+1, pilot))
    emit_heat_data() # Settings page, new pilot position in heats

@SOCKET_IO.on('add_pilot')
def on_add_pilot():
    '''Adds the next available pilot id number in the database.'''
    max_pilot_id = DB.session.query(DB.func.max(Pilot.pilot_id)).scalar()
    DB.session.add(Pilot(pilot_id=max_pilot_id+1, callsign='callsign{0}'.format(max_pilot_id+1), \
        phonetic='callsign{0}'.format(max_pilot_id+1), name='Pilot Name'))
    DB.session.commit()
    server_log('Pilot added: Pilot {0}'.format(max_pilot_id+1))

@SOCKET_IO.on('set_pilot_callsign')
def on_set_pilot_callsign(data):
    '''Gets pilot callsign to update database.'''
    pilot_id = data['pilot_id']
    callsign = data['callsign']
    db_update = Pilot.query.filter_by(pilot_id=pilot_id).first()
    db_update.callsign = callsign
    DB.session.commit()
    server_log('Pilot callsign set: Pilot {0} Callsign {1}'.format(pilot_id, callsign))
    emit_pilot_data() # Settings page, new pilot callsign
    emit_heat_data() # Settings page, new pilot callsign in heats

@SOCKET_IO.on('set_pilot_phonetic')
def on_set_pilot_phonetic(data):
    '''Gets pilot phonetic to update database.'''
    pilot_id = data['pilot_id']
    phonetic = data['phonetic']
    db_update = Pilot.query.filter_by(pilot_id=pilot_id).first()
    db_update.phonetic = phonetic
    DB.session.commit()
    server_log('Pilot phonetic set: Pilot {0} Phonetic {1}'.format(pilot_id, phonetic))
    emit_pilot_data() # Settings page, new pilot phonetic
    emit_heat_data() # Settings page, new pilot phonetic in heats. Needed?

@SOCKET_IO.on('set_pilot_name')
def on_set_pilot_name(data):
    '''Gets pilot name to update database.'''
    pilot_id = data['pilot_id']
    name = data['name']
    db_update = Pilot.query.filter_by(pilot_id=pilot_id).first()
    db_update.name = name
    DB.session.commit()
    server_log('Pilot name set: Pilot {0} Name {1}'.format(pilot_id, name))
    emit_pilot_data() # Settings page, new pilot name

@SOCKET_IO.on('speak_pilot')
def on_speak_pilot(data):
    '''Speaks the phonetic name of the pilot.'''
    pilot_id = data['pilot_id']
    phtext = Pilot.query.filter_by(pilot_id=pilot_id).first().phonetic
    emit_phonetic_text(phtext)
    server_log('Speak pilot: {0}'.format(phtext))

@SOCKET_IO.on('add_profile')
def on_add_profile():
    '''Adds new profile in the database.'''
    max_profile_id = DB.session.query(Profiles).count()+1
    DB.session.add(Profiles(name='New Profile %s' % max_profile_id,
                           description = 'New Profile %s' % max_profile_id,
                           c_offset=8,
                           c_threshold=90,
                           t_threshold=40))
    DB.session.commit()
    on_set_profile(data={ 'profile': 'New Profile %s' % max_profile_id})

@SOCKET_IO.on('delete_profile')
def on_delete_profile():
    '''Delete profile'''
    if (DB.session.query(Profiles).count() > 1): # keep one profile
     last_profile = LastProfile.query.get(1).profile_id
     profile = Profiles.query.get(last_profile)
     DB.session.delete(profile)
     DB.session.commit()
     last_profile =  LastProfile.query.get(1)
     first_profile_id = Profiles.query.first().id
     last_profile.profile_id = first_profile_id
     DB.session.commit()
     profile =Profiles.query.get(first_profile_id)
     manager_hardware.set_calibration_threshold_global(profile.c_threshold)
     manager_hardware.set_calibration_offset_global(profile.c_offset)
     manager_hardware.set_trigger_threshold_global(profile.t_threshold)
     emit_node_tuning()

@SOCKET_IO.on('set_profile_name')
def on_set_profile_name(data):
    ''' update profile name '''
    profile_name = data['profile_name']
    last_profile = LastProfile.query.get(1)
    profile = Profiles.query.filter_by(id=last_profile.profile_id).first()
    profile.name = profile_name
    DB.session.commit()
    server_log('set profile name %s' % (profile_name))
    emit_node_tuning()

@SOCKET_IO.on('set_profile_description')
def on_set_profile_description(data):
    ''' update profile description '''
    profile_description = data['profile_description']
    last_profile = LastProfile.query.get(1)
    profile = Profiles.query.filter_by(id=last_profile.profile_id).first()
    profile.description = profile_description
    DB.session.commit()
    server_log('set profile description %s for profile %s' %
               (profile_name, profile.name))
    emit_node_tuning()

@SOCKET_IO.on('set_calibration_threshold')
def on_set_calibration_threshold(data):
    '''Set Calibration Threshold.'''
    calibration_threshold = data['calibration_threshold']
    manager_hardware.set_calibration_threshold_global(calibration_threshold)
    last_profile = LastProfile.query.get(1)
    profile = Profiles.query.filter_by(id=last_profile.profile_id).first()
    profile.c_threshold = calibration_threshold
    DB.session.commit()
    server_log('Calibration threshold set: {0}'.format(calibration_threshold))
    emit_node_tuning()


@SOCKET_IO.on('set_calibration_offset')
def on_set_calibration_offset(data):
    '''Set Calibration Offset.'''
    calibration_offset = data['calibration_offset']
    manager_hardware.set_calibration_offset_global(calibration_offset)
    last_profile = LastProfile.query.get(1)
    profile = Profiles.query.filter_by(id=last_profile.profile_id).first()
    profile.c_offset = calibration_offset
    DB.session.commit()
    server_log('Calibration offset set: {0}'.format(calibration_offset))
    emit_node_tuning()


@SOCKET_IO.on('set_trigger_threshold')
def on_set_trigger_threshold(data):
    '''Set Trigger Threshold.'''
    trigger_threshold = data['trigger_threshold']
    manager_hardware.set_trigger_threshold_global(trigger_threshold)
    last_profile = LastProfile.query.get(1)
    profile = Profiles.query.filter_by(id=last_profile.profile_id).first()
    profile.t_threshold = trigger_threshold
    DB.session.commit()
    server_log('Trigger threshold set: {0}'.format(trigger_threshold))
    emit_node_tuning()

@SOCKET_IO.on('reset_database')
def on_reset_database():
    '''Reset database.'''
    db_reset()

@SOCKET_IO.on('reset_database_keep_pilots')
def on_reset_database_keep_pilots():
    '''Reset database but keep pilots list.'''
    db_reset_keep_pilots()

@SOCKET_IO.on('shutdown_pi')
def on_shutdown_pi():
    '''Shutdown the raspberry pi.'''
    server_log('Shutdown pi')
    os.system("sudo shutdown now")


@SOCKET_IO.on("set_profile")
def on_set_profile(data):
    ''' set current profile '''
    profile_val = data['profile']
    profile =Profiles.query.filter_by(name=profile_val).first()
    DB.session.flush()
    last_profile = LastProfile.query.get(1)
    last_profile.profile_id = profile.id
    DB.session.commit()
    manager_hardware.set_calibration_threshold_global(profile.c_threshold)
    manager_hardware.set_calibration_offset_global(profile.c_offset)
    manager_hardware.set_trigger_threshold_global(profile.t_threshold)
    emit_node_tuning()
    server_log("set tune paramas for profile '%s'" % profile_val)

@SOCKET_IO.on("set_fix_race_time")
def on_set_fix_race_time(data):
    race_time = data['race_time']
    fix_race_time = FixTimeRace.query.get(1)
    fix_race_time.race_time_sec = race_time
    DB.session.commit()
    server_log("set fixed time race to %s seconds" % race_time)

    # @SOCKET_IO.on('clear_rounds')
# def on_reset_heats():
#     '''Clear all saved races.'''
#     DB.session.query(SavedRace).delete() # Remove all races
#     DB.session.commit()
#     server_log('Saved rounds cleared')

# @SOCKET_IO.on('reset_heats')
# def on_reset_heats():
#     '''Resets to one heat with default pilots.'''
#     DB.session.query(Heat).delete() # Remove all heats
#     DB.session.commit()
#     for node in range(RACE.num_nodes): # Add back heat 1 with pilots 1 thru 5
#         DB.session.add(Heat(heat_id=1, node_index=node, pilot_id=node+1))
#     DB.session.commit()
#     server_log('Heats reset to default')

# @SOCKET_IO.on('reset_pilots')
# def on_reset_heats():
#     '''Resets default pilots for nodes detected.'''

#     DB.session.query(Pilot).delete() # Remove all pilots
#     DB.session.commit()
#     DB.session.add(Pilot(pilot_id='0', callsign='-', name='-'))
#     for node in range(RACE.num_nodes): # Add back heat 1 with pilots 1 thru 5
#         DB.session.add(Pilot(pilot_id=node+1, callsign='callsign{0}'.format(node+1), \
#             name='Pilot Name'))
#     DB.session.commit()
#     server_log('Pilots reset to default')

# Race management socket io events

@SOCKET_IO.on('start_race')
def on_start_race():
    '''Starts the race and the timer counting up, no defined finish.'''
    start_race()
    SOCKET_IO.emit('start_timer') # Loop back to race page to start the timer counting up

@SOCKET_IO.on('start_race_2min')
def on_start_race_2min():
    '''Starts the race with a two minute countdown clock.'''
    start_race()
    SOCKET_IO.emit('start_timer_2min') # Loop back to race page to start a 2 min countdown

def start_race():
    '''Common race start events.'''
    on_clear_laps() # Ensure laps are cleared before race start, shouldn't be needed
    emit_current_laps() # Race page, blank laps to the web client
    emit_leaderboard() # Race page, blank leaderboard to the web client
    manager_hardware.enable_calibration_mode() # Nodes reset triggers on next pass
    gevent.sleep(0.500) # Make this random 2 to 5 seconds
    RACE.race_status = 1 # To enable registering passed laps
    global RACE_START # To redefine main program variable
    RACE_START = datetime.now() # Update the race start time stamp
    server_log('Race started at {0}'.format(RACE_START))
    emit_node_data() # Settings page, node channel and triggers on the launch pads
    emit_race_status() # Race page, to set race button states

@SOCKET_IO.on('stop_race')
def on_race_status():
    '''Stops the race and stops registering laps.'''
    RACE.race_status = 2 # To stop registering passed laps, waiting for laps to be cleared
    SOCKET_IO.emit('stop_timer') # Loop back to race page to start the timer counting up
    server_log('Race stopped')
    emit_race_status() # Race page, to set race button states

@SOCKET_IO.on('save_laps')
def on_save_laps():
    '''Save current laps data to the database.'''
    # Get the last saved round for the current heat
    max_round = DB.session.query(DB.func.max(SavedRace.round_id)) \
            .filter_by(heat_id=RACE.current_heat).scalar()
    if max_round is None:
        max_round = 0
    # Loop through laps to copy to saved races
    for node in range(RACE.num_nodes):
        for lap in CurrentLap.query.filter_by(node_index=node).all():
            DB.session.add(SavedRace(round_id=max_round+1, heat_id=RACE.current_heat, \
                node_index=node, pilot_id=lap.pilot_id, lap_id=lap.lap_id, \
                lap_time_stamp=lap.lap_time_stamp, lap_time=lap.lap_time, \
                lap_time_formatted=lap.lap_time_formatted))
    DB.session.commit()
    server_log('Current laps saved: Heat {0} Round {1}'.format(RACE.current_heat, max_round+1))
    on_clear_laps() # Also clear the current laps

@SOCKET_IO.on('clear_laps')
def on_clear_laps():
    '''Clear the current laps due to false start or practice.'''
    RACE.race_status = 0 # Laps cleared, ready to start next race
    DB.session.query(CurrentLap).delete() # Clear out the current laps table
    DB.session.commit()
    server_log('Current laps cleared')
    emit_current_laps() # Race page, blank laps to the web client
    emit_leaderboard() # Race page, blank leaderboard to the web client
    emit_race_status() # Race page, to set race button states

@SOCKET_IO.on('set_current_heat')
def on_set_current_heat(data):
    '''Update the current heat variable.'''
    new_heat_id = data['heat']
    RACE.current_heat = new_heat_id
    server_log('Current heat set: Heat {0}'.format(new_heat_id))
    emit_current_heat() # Race page, to update heat selection button
    emit_leaderboard() # Race page, to update callsigns in leaderboard

@SOCKET_IO.on('delete_lap')
def on_delete_lap(data):
    '''Delete a false lap.'''
    node_index = data['node']
    lap_id = data['lapid']
    max_lap = DB.session.query(DB.func.max(CurrentLap.lap_id)) \
        .filter_by(node_index=node_index).scalar()
    if lap_id is not max_lap:
        # Update the lap_time for the next lap
        previous_lap = CurrentLap.query.filter_by(node_index=node_index, lap_id=lap_id-1).first()
        next_lap = CurrentLap.query.filter_by(node_index=node_index, lap_id=lap_id+1).first()
        next_lap.lap_time = next_lap.lap_time_stamp - previous_lap.lap_time_stamp
        next_lap.lap_time_formatted = time_format(next_lap.lap_time)
        # Delete the false lap
        CurrentLap.query.filter_by(node_index=node_index, lap_id=lap_id).delete()
        # Update lap numbers
        for lap in CurrentLap.query.filter_by(node_index=node_index).all():
            if lap.lap_id > lap_id:
                lap.lap_id = lap.lap_id - 1
    else:
        # Delete the false lap
        CurrentLap.query.filter_by(node_index=node_index, lap_id=lap_id).delete()
    DB.session.commit()
    server_log('Lap deleted: Node {0} Lap {1}'.format(node_index, lap_id))
    emit_current_laps() # Race page, update web client
    emit_leaderboard() # Race page, update web client

@SOCKET_IO.on('simulate_lap')
def on_simulate_lap(data):
    '''Simulates a lap (for debug testing).'''
    node_index = data['node']
    server_log('Simulated lap: Node {0}'.format(node_index))
    INTERFACE.intf_simulate_lap(node_index)

# Socket io emit functions

def emit_race_status():
    '''Emits race status.'''
    SOCKET_IO.emit('race_status', {'race_status': RACE.race_status})

def emit_node_data():
    '''Emits node data.'''
    frequency = []
    channel = []
    trigger_rssi = []
    peak_rssi = []
    for node in manager_hardware.get_nodes():
        frequency.append(node.get_frequency())
        channel.append(Frequency.query.filter_by(frequency=node.get_frequency()).first().channel)
        trigger_rssi.append(node.get_trigger_threashold())
        peak_rssi.append(node.get_peak_rssi())

    SOCKET_IO.emit('node_data', {
        'frequency': frequency,
        'channel': channel,
        'trigger_rssi': trigger_rssi,
        'peak_rssi': peak_rssi
    })
def emit_node_tuning():
    '''Emits node tuning values.'''
    last_profile = LastProfile.query.get(1)
    tune_val = Profiles.query.get(last_profile.profile_id)
    SOCKET_IO.emit('node_tuning', {
        'calibration_threshold': \
            tune_val.c_threshold,
        'calibration_offset': \
            tune_val.c_offset,
        'trigger_threshold': \
            tune_val.t_threshold,
        'profile_name':
            tune_val.name,
        'profile_description':
            tune_val.description
    })


def emit_current_laps():
    '''Emits current laps.'''
    current_laps = []
    # for node in DB.session.query(CurrentLap.node_index).distinct():
    for node in range(RACE.num_nodes):
        node_laps = []
        node_lap_times = []
        for lap in CurrentLap.query.filter_by(node_index=node).all():
            node_laps.append(lap.lap_id)
            node_lap_times.append(lap.lap_time_formatted)
        current_laps.append({'lap_id': node_laps, 'lap_time': node_lap_times})
    current_laps = {'node_index': current_laps}
    SOCKET_IO.emit('current_laps', current_laps)

def emit_leaderboard():
    '''Emits leaderboard.'''
    # Get the max laps for each pilot
    max_laps = []
    for node in range(RACE.num_nodes):
        max_lap = DB.session.query(DB.func.max(CurrentLap.lap_id)) \
            .filter_by(node_index=node).scalar()
        if max_lap is None:
            max_lap = 0
        max_laps.append(max_lap)
    # Get the total race time for each pilot
    total_time = []
    for node in range(RACE.num_nodes):
        if max_laps[node] is 0:
            total_time.append(0) # Add zero if no laps completed
        else:
            total_time.append(CurrentLap.query.filter_by(node_index=node, \
                lap_id=max_laps[node]).first().lap_time_stamp)
    # Get the last lap for each pilot
    last_lap = []
    for node in range(RACE.num_nodes):
        if max_laps[node] is 0:
            last_lap.append(0) # Add zero if no laps completed
        else:
            last_lap.append(CurrentLap.query.filter_by(node_index=node, \
                lap_id=max_laps[node]).first().lap_time)
    # Get the average lap time for each pilot
    average_lap = []
    for node in range(RACE.num_nodes):
        if max_laps[node] is 0:
            average_lap.append(0) # Add zero if no laps completed
        else:
            avg_lap = DB.session.query(DB.func.avg(CurrentLap.lap_time)) \
                .filter(CurrentLap.node_index == node, CurrentLap.lap_id != 0).scalar()
            average_lap.append(avg_lap)
    # Get the fastest lap time for each pilot
    fastest_lap = []
    for node in range(RACE.num_nodes):
        if max_laps[node] is 0:
            fastest_lap.append(0) # Add zero if no laps completed
        else:
            fast_lap = DB.session.query(DB.func.min(CurrentLap.lap_time)) \
                .filter(CurrentLap.node_index == node, CurrentLap.lap_id != 0).scalar()
            fastest_lap.append(fast_lap)
    # Get the pilot callsigns to add to sort
    callsigns = []
    for node in range(RACE.num_nodes):
        pilot_id = Heat.query.filter_by( \
            heat_id=RACE.current_heat, node_index=node).first().pilot_id
        callsigns.append(Pilot.query.filter_by(pilot_id=pilot_id).first().callsign)
    # Combine for sorting
    leaderboard = zip(callsigns, max_laps, total_time, last_lap, average_lap, fastest_lap)
    # Reverse sort max_laps x[1], then sort on total time x[2]
    leaderboard_sorted = sorted(leaderboard, key = lambda x: (-x[1], x[2]))

    SOCKET_IO.emit('leaderboard', {
        'position': [i+1 for i in range(RACE.num_nodes)],
        'callsign': [leaderboard_sorted[i][0] for i in range(RACE.num_nodes)],
        'laps': [leaderboard_sorted[i][1] for i in range(RACE.num_nodes)],
        'total_time': [time_format(leaderboard_sorted[i][2]) for i in range(RACE.num_nodes)],
        'last_lap': [time_format(leaderboard_sorted[i][3]) for i in range(RACE.num_nodes)],
        'behind': [(leaderboard_sorted[0][1] - leaderboard_sorted[i][1]) \
            for i in range(RACE.num_nodes)],
        'average_lap': [time_format(leaderboard_sorted[i][4]) for i in range(RACE.num_nodes)],
        'fastest_lap': [time_format(leaderboard_sorted[i][5]) for i in range(RACE.num_nodes)]
    })
	
def emit_heat_data():
    '''Emits heat data.'''
    current_heats = []
    for heat in Heat.query.with_entities(Heat.heat_id).distinct():
        pilots = []
        for node in range(RACE.num_nodes):
            pilot_id = Heat.query.filter_by(heat_id=heat.heat_id, node_index=node).first().pilot_id
            pilots.append(Pilot.query.filter_by(pilot_id=pilot_id).first().callsign)
        current_heats.append({'callsign': pilots})
    current_heats = {'heat_id': current_heats}
    SOCKET_IO.emit('heat_data', current_heats)

def emit_pilot_data():
    '''Emits pilot data.'''
    SOCKET_IO.emit('pilot_data', {
        'callsign': [pilot.callsign for pilot in Pilot.query.all()],
        'name': [pilot.name for pilot in Pilot.query.all()]
    })

def emit_current_heat():
    '''Emits the current heat.'''
    callsigns = []
    for node in range(RACE.num_nodes):
        pilot_id = Heat.query.filter_by( \
            heat_id=RACE.current_heat, node_index=node).first().pilot_id
        callsigns.append(Pilot.query.filter_by(pilot_id=pilot_id).first().callsign)

    SOCKET_IO.emit('current_heat', {
        'current_heat': RACE.current_heat,
        'callsign': callsigns
    })

def emit_phonetic_data(pilot_id, lap_id, lap_time):
    '''Emits phonetic data.'''
    phonetic_time = phonetictime_format(lap_time)
    phonetic_name = Pilot.query.filter_by(pilot_id=pilot_id).first().phonetic
    SOCKET_IO.emit('phonetic_data', {'pilot': phonetic_name, 'lap': lap_id, 'phonetic': phonetic_time})

def emit_language_data():
    '''Emits language.'''
    SOCKET_IO.emit('language_data', {'language': RACE.lang_id})

def emit_current_fix_race_time():
    ''' Emit current fixed time race time '''
    race_time_sec = FixTimeRace.query.get(1).race_time_sec
    SOCKET_IO.emit('set_fix_race_time',{ fix_race_time: race_time_sec})

def emit_phonetic_text(phtext):
    '''Emits given phonetic text.'''
    SOCKET_IO.emit('speak_phonetic_text', {'text': phtext})

#
# Program Functions
#



def ms_from_race_start():
    '''Return milliseconds since race start.'''
    delta_time = datetime.now() - RACE_START
    milli_sec = (delta_time.days * 24 * 60 * 60 + delta_time.seconds) \
        * 1000 + delta_time.microseconds / 1000.0
    return milli_sec

def ms_from_program_start():
    '''Returns the elapsed milliseconds since the start of the program.'''
    delta_time = datetime.now() - PROGRAM_START
    milli_sec = (delta_time.days * 24 * 60 * 60 + delta_time.seconds) \
        * 1000 + delta_time.microseconds / 1000.0
    return milli_sec

def time_format(millis):
    '''Convert milliseconds to 00:00.000'''
    millis = int(millis)
    minutes = millis / 60000
    over = millis % 60000
    seconds = over / 1000
    over = over % 1000
    milliseconds = over
    return '{0:02d}:{1:02d}.{2:03d}'.format(minutes, seconds, milliseconds)

def phonetictime_format(millis):
    '''Convert milliseconds to phonetic'''
    millis = int(millis + 50)  # round to nearest tenth of a second
    seconds = millis / 1000
    over = (millis % 60000) % 1000
    tenths = over / 100
    return '{0:01d}.{1:01d}'.format(seconds, tenths)
	
def pass_record_callback(node, ms_since_lap):
    '''Handles pass records from the nodes.'''
    server_log('Raw pass record: Node: {0}, MS Since Lap: {1}'.format(node.index, ms_since_lap))
    emit_node_data() # For updated triggers and peaks

    if RACE.race_status is 1:
        # Get the current pilot id on the node
        pilot_id = Heat.query.filter_by( \
            heat_id=RACE.current_heat, node_index=node.index).first().pilot_id

        # Calculate the lap time stamp, milliseconds since start of race
        lap_time_stamp = ms_from_race_start() - ms_since_lap

        # Get the last completed lap from the database
        last_lap_id = DB.session.query(DB.func.max(CurrentLap.lap_id)) \
            .filter_by(node_index=node.index).scalar()

        if last_lap_id is None: # No previous laps, this is the first pass
            # Lap zero represents the time from the launch pad to flying through the gate
            lap_time = lap_time_stamp
            lap_id = 0
        else: # This is a normal completed lap
            # Find the time stamp of the last lap completed
            last_lap_time_stamp = CurrentLap.query.filter_by( \
                node_index=node.index, lap_id=last_lap_id).first().lap_time_stamp
            # New lap time is the difference between the current time stamp and the last
            lap_time = lap_time_stamp - last_lap_time_stamp
            lap_id = last_lap_id + 1

        # Add the new lap to the database
        DB.session.add(CurrentLap(node_index=node.index, pilot_id=pilot_id, lap_id=lap_id, \
            lap_time_stamp=lap_time_stamp, lap_time=lap_time, \
            lap_time_formatted=time_format(lap_time)))
        DB.session.commit()

        server_log('Pass record: Node: {0}, Lap: {1}, Lap time: {2}' \
            .format(node.index, lap_id, time_format(lap_time)))
        emit_current_laps() # Updates all laps on the race page
        emit_leaderboard() # Updates leaderboard
        if lap_id > 0: 
            emit_phonetic_data(pilot_id, lap_id, lap_time) # Sends phonetic data to be spoken

INTERFACE.pass_record_callback = pass_record_callback



INTERFACE.hardware_log_callback = hardware_log_callback




#
# Program Initialize
#

# Save number of nodes found
RACE.num_nodes = len(manager_hardware.get_nodes())
print 'Number of nodes found: {0}'.format(RACE.num_nodes)

# Delay to get I2C addresses through interface class initialization
gevent.sleep(0.500)
# Set default frequencies based on number of nodes

manager_hardware.default_frequencies()
server_log('Default frequencies set')

# Create database if it doesn't exist
if not os.path.exists('database.db'):
    db_init()

# Clear any current laps from the database on each program start
# DB session commit needed to prevent 'application context' errors
db_reset_current_laps()

# Send initial profile values to nodes
last_profile = LastProfile.query.get(1)
tune_val = Profiles.query.get(last_profile.profile_id)
manager_hardware.set_calibration_threshold_global(tune_val.c_threshold)
manager_hardware.set_calibration_offset_global(tune_val.c_offset)
manager_hardware.set_trigger_threshold_global(tune_val.t_threshold)

thread_rxs =  ThreadReadRX(manager_hardware)
thread_heartbeat = ThreadHeartbeat(SOCKET_IO)

if __name__ == '__main__':
    thread_rxs.set_deamon(True)
    thread_rxs.start()
    thread_heartbeat.start()
    SOCKET_IO.run(APP, host='0.0.0.0', port=5000, debug=True)
