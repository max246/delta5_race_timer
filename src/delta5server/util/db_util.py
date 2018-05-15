from model.db_models import DB
from util.socket_util import *

def db_init():
    '''Initialize database.'''
    DB.create_all() # Creates tables from database classes/models
    #Profiles.__table__.create(DB)
    #Base.metadata.create_all(DB)
    db_reset_pilots()
    db_reset_heats()
    db_reset_frequencies()
    db_reset_current_laps()
    db_reset_saved_races()
    db_reset_profile()
    db_reset_default_profile()
    db_reset_fix_race_time()
    server_log('Database initialized')

def db_reset():
    '''Resets database.'''
    db_reset_pilots()
    db_reset_heats()
    db_reset_frequencies()
    db_reset_current_laps()
    db_reset_saved_races()
    db_reset_profile()
    db_reset_default_profile()
    db_reset_fix_race_time()
    server_log('Database reset')

def db_reset_keep_pilots():
    '''Resets database, keeps pilots.'''
    db_reset_heats()
    db_reset_frequencies()
    db_reset_current_laps()
    db_reset_saved_races()
    db_reset_fix_race_time()
    server_log('Database reset, pilots kept')

def db_reset_pilots():
    '''Resets database pilots to default.'''
    try:
        DB.session.query(Pilot).delete()
    except:
        print "No tablet pilot present"
    DB.session.add(Pilot(pilot_id='0', callsign='-', name='-', phonetic="-"))
    for node in range(RACE.num_nodes):
        DB.session.add(Pilot(pilot_id=node+1, callsign='callsign{0}'.format(node+1), \
            name='Pilot Name', phonetic='callsign{0}'.format(node+1)))
    DB.session.commit()
    server_log('Database pilots reset')
def db_reset_heats():
    '''Resets database heats to default.'''
    DB.session.query(Heat).delete()
    for node in range(RACE.num_nodes):
        DB.session.add(Heat(heat_id=1, node_index=node, pilot_id=node+1))
    DB.session.commit()
    server_log('Database heats reset')
def db_reset_frequencies():
    '''Resets database frequencies to default.'''
    DB.session.query(Frequency).delete()
    # IMD Channels
    DB.session.add(Frequency(band='IMD', channel='E2', frequency='5685'))
    DB.session.add(Frequency(band='IMD', channel='F2', frequency='5760'))
    DB.session.add(Frequency(band='IMD', channel='F4', frequency='5800'))
    DB.session.add(Frequency(band='IMD', channel='F7', frequency='5860'))
    DB.session.add(Frequency(band='IMD', channel='E6', frequency='5905'))
    DB.session.add(Frequency(band='IMD', channel='E4', frequency='5645'))
    # Band R - Raceband
    DB.session.add(Frequency(band='R', channel='R1', frequency='5658'))
    DB.session.add(Frequency(band='R', channel='R2', frequency='5695'))
    DB.session.add(Frequency(band='R', channel='R3', frequency='5732'))
    DB.session.add(Frequency(band='R', channel='R4', frequency='5769'))
    DB.session.add(Frequency(band='R', channel='R5', frequency='5806'))
    DB.session.add(Frequency(band='R', channel='R6', frequency='5843'))
    DB.session.add(Frequency(band='R', channel='R7', frequency='5880'))
    DB.session.add(Frequency(band='R', channel='R8', frequency='5917'))
    # Band F - ImmersionRC, Iftron
    DB.session.add(Frequency(band='F', channel='F1', frequency='5740'))
    DB.session.add(Frequency(band='F', channel='F2', frequency='5760'))
    DB.session.add(Frequency(band='F', channel='F3', frequency='5780'))
    DB.session.add(Frequency(band='F', channel='F4', frequency='5800'))
    DB.session.add(Frequency(band='F', channel='F5', frequency='5820'))
    DB.session.add(Frequency(band='F', channel='F6', frequency='5840'))
    DB.session.add(Frequency(band='F', channel='F7', frequency='5860'))
    DB.session.add(Frequency(band='F', channel='F8', frequency='5880'))
    # Band E - HobbyKing, Foxtech
    DB.session.add(Frequency(band='E', channel='E1', frequency='5705'))
    DB.session.add(Frequency(band='E', channel='E2', frequency='5685'))
    DB.session.add(Frequency(band='E', channel='E3', frequency='5665'))
    DB.session.add(Frequency(band='E', channel='E4', frequency='5645'))
    DB.session.add(Frequency(band='E', channel='E5', frequency='5885'))
    DB.session.add(Frequency(band='E', channel='E6', frequency='5905'))
    DB.session.add(Frequency(band='E', channel='E7', frequency='5925'))
    DB.session.add(Frequency(band='E', channel='E8', frequency='5945'))
    # Band B - FlyCamOne Europe
    DB.session.add(Frequency(band='B', channel='B1', frequency='5733'))
    DB.session.add(Frequency(band='B', channel='B2', frequency='5752'))
    DB.session.add(Frequency(band='B', channel='B3', frequency='5771'))
    DB.session.add(Frequency(band='B', channel='B4', frequency='5790'))
    DB.session.add(Frequency(band='B', channel='B5', frequency='5809'))
    DB.session.add(Frequency(band='B', channel='B6', frequency='5828'))
    DB.session.add(Frequency(band='B', channel='B7', frequency='5847'))
    DB.session.add(Frequency(band='B', channel='B8', frequency='5866'))
    # Band A - Team BlackSheep, RangeVideo, SpyHawk, FlyCamOne USA
    DB.session.add(Frequency(band='A', channel='A1', frequency='5865'))
    DB.session.add(Frequency(band='A', channel='A2', frequency='5845'))
    DB.session.add(Frequency(band='A', channel='A3', frequency='5825'))
    DB.session.add(Frequency(band='A', channel='A4', frequency='5805'))
    DB.session.add(Frequency(band='A', channel='A5', frequency='5785'))
    DB.session.add(Frequency(band='A', channel='A6', frequency='5765'))
    DB.session.add(Frequency(band='A', channel='A7', frequency='5745'))
    DB.session.add(Frequency(band='A', channel='A8', frequency='5725'))
    # Band L - Lowband
    DB.session.add(Frequency(band='L', channel='L1', frequency='5362'))
    DB.session.add(Frequency(band='L', channel='L2', frequency='5399'))
    DB.session.add(Frequency(band='L', channel='L3', frequency='5436'))
    DB.session.add(Frequency(band='L', channel='L4', frequency='5473'))
    DB.session.add(Frequency(band='L', channel='L5', frequency='5510'))
    DB.session.add(Frequency(band='L', channel='L6', frequency='5547'))
    DB.session.add(Frequency(band='L', channel='L7', frequency='5584'))
    DB.session.add(Frequency(band='L', channel='L8', frequency='5621'))
    DB.session.commit()
    server_log('Database frequencies reset')

def db_reset_current_laps():
    '''Resets database current laps to default.'''
    try:
        DB.session.query(CurrentLap).delete()
    except:
        print "oppsss doesnt exists"
    DB.session.commit()
    server_log('Database current laps reset')

def db_reset_saved_races():
    '''Resets database saved races to default.'''
    DB.session.query(SavedRace).delete()
    DB.session.commit()
    server_log('Database saved races reset')

def db_reset_profile():
    '''Set default profile'''
    try:
        DB.session.query(Profiles).delete()
    except:
        print "oppsss"
    DB.session.add(Profiles(name="default 25mW",
                             description ="default tune params for 25mW race",
                             c_offset=8,
                             c_threshold=65,
                             t_threshold=40))
    DB.session.add(Profiles(name="default 200mW",
                             description ="default tune params for 200mW race",
                             c_offset=8,
                             c_threshold=90,
                             t_threshold=40))
    DB.session.add(Profiles(name="default 600mW",
                             description ="default tune params for 600mW race",
                             c_offset=8,
                             c_threshold=100,
                             t_threshold=40))
    DB.session.commit()
    server_log("Database set default profiles for 25,200,600 mW races")

def db_reset_default_profile():
    DB.session.query(LastProfile).delete()
    DB.session.add(LastProfile(profile_id=1))
    DB.session.commit()
    server_log("Database set default profile on default 25mW race")


def db_reset_fix_race_time():
    DB.session.query(FixTimeRace).delete()
    DB.session.add(FixTimeRace(race_time_sec=120))
    DB.session.commit()
    server_log("Database set fixed time race to 120 sec (2 minutes)")