from sqlalchemy import Column, Integer, String
from flask_sqlalchemy import SQLAlchemy


DB = SQLAlchemy()


class SavedRace(DB.Model):
    __tablename__ = "saved_race"
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, nullable=False)
    heat_id = Column(Integer, nullable=False)
    node_index = Column(Integer, nullable=False)
    pilot_id = Column(Integer, nullable=False)
    lap_id = Column(Integer, nullable=False)
    lap_time_stamp = Column(Integer, nullable=False)
    lap_time = Column(Integer, nullable=False)
    lap_time_formatted = Column(Integer, nullable=False)

    def __repr__(self):
        return '<SavedRace %r>' % self.round_id



class Pilot(DB.Model):
    __tablename__ = "pilot"
    id = Column(Integer, primary_key=True)
    pilot_id = Column(Integer, unique=True, nullable=False)
    callsign = Column(String(80), unique=True, nullable=False)
    phonetic = Column(String(80), unique=True, nullable=False)
    name = Column(String(120), nullable=False)

    def __repr__(self):
        return '<Pilot %r>' % self.pilot_id



class Heat(DB.Model):
    __tablename__ = "heat"
    id = Column(Integer, primary_key=True)
    heat_id = Column(Integer, nullable=False)
    node_index = Column(Integer, nullable=False)
    pilot_id = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Heat %r>' % self.heat_id


class Frequency(DB.Model):
    __tablename__ = "frequency"
    id = Column(Integer, primary_key=True)
    band = Column(Integer, nullable=False)
    channel = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Frequency %r>' % self.frequency


class CurrentLap(DB.Model):
    __tablename__ = "current_lap"
    id = Column(Integer, primary_key=True)
    node_index = Column(Integer, nullable=False)
    pilot_id = Column(Integer, nullable=False)
    lap_id = Column(Integer, nullable=False)
    lap_time_stamp = Column(Integer, nullable=False)
    lap_time = Column(Integer, nullable=False)
    lap_time_formatted = Column(Integer, nullable=False)

    def __repr__(self):
        return '<CurrentLap %r>' % self.pilot_id




class Profiles(DB.Model):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(256), nullable=True)
    c_offset = Column(Integer, nullable=True)
    c_threshold = Column(Integer, nullable=True)
    t_threshold = Column(Integer, nullable=True)

class LastProfile(DB.Model):
    __tablename__ = "last_profile"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)


class FixTimeRace(DB.Model):
    __tablename__ = "fix_time_race"
    id = Column(Integer, primary_key=True)
    race_time_sec = Column(Integer, nullable=False)
