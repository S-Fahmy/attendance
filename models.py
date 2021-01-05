import os
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, Date, Boolean, Time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_migrate import Migrate
from flask import abort

import json
from datetime import datetime
from controllers.timeUtils import get_hms_from_minutes

db = SQLAlchemy()


def setup_db(app):
    db.app = app
    db.init_app(app)
    Migrate(app, db, compare_type=True)


#assign the test db uri
def setup_test_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://{}:{}@{}/{}".format(
        'postgres', 'root', 'localhost: 5432', 'attendance_test')
   


'''
Employees

'''


class Employee(db.Model):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    name = Column(String,  nullable=False)

    attendances = relationship(
        "Attendance", backref="employees", lazy=True, cascade="all, delete-orphan")
    schedule_id = Column(Integer, ForeignKey(
        'schedules.id',  ondelete='SET NULL'), nullable=True)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
        }


'''
Attendances

'''


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = Column(Integer, primary_key=True)
    day = Column(Date,  nullable=False)
    checkin = Column(String,  nullable=True)
    checkout = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey(
        'employees.id',  ondelete='SET NULL'), nullable=False)

    def __init__(self, day, checkin, checkout, user_id):
        self.day = day
        self.checkin = checkin
        self.checkout = checkout
        self.user_id = user_id

    def format(self):
        return {
            'id': self.id,
            # converting it to a string here because the jsonify will convert it anyway but add extra unasked for items to the date str!!!
            'day': str(self.day),
            'checkin': self.checkin,
            'checkout': self.checkout,
            'user_id': self.user_id,
            "attendances": None,
        }



class Schedule(db.Model):
    #TODO: update this with the needed rules columns.
    
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    shift_begins = Column(Time(timezone=False), nullable=False)
    shift_ends = Column(Time(timezone=False), nullable=False)
    
    # #rules
    clock_in_start = Column(Time(timezone=False), nullable=True, default= '07:30:00')
    clock_in_end = Column(Time(timezone=False), nullable=True, default= '12:30:00')
    
    clock_out_start = Column(Time(timezone=False), nullable=True, default= '13:00:00')
    clock_out_end = Column(Time(timezone=False), nullable=True, default= '23:00:00')
    
    allowed_late_arrival = Column(Integer, nullable=True, default= 0)
    allowed_early_leave = Column(Integer, nullable=True, default= 0)
    missing_check_penalty = Column(String, nullable=True, default= "0") 
    
    active = Column(Boolean, default=False)
    
    employees = relationship("Employee", backref="schedule", lazy=True)

#title, shift_begins, shift_ends, assigned_employees, active, clock_in_start, clock_in_end, clock_out_start, clock_out_end
    def __init__(self, json_schedule):
        self.title = json_schedule['title']
        self.shift_begins = json_schedule['shift_begins']
        self.shift_ends = json_schedule['shift_ends']
        self.clock_in_start= json_schedule.get('clock_in_start', None)
        self.clock_in_end= json_schedule.get('clock_in_end', None)
        self.clock_out_end= json_schedule.get('clock_out_end', None)
        self.clock_out_start= json_schedule.get('clock_out_start', None)
        self.allowed_late_arrival = json_schedule.get('allowed_late_arrival', None)
        self.allowed_early_leave = json_schedule.get('allowed_early_leave', None)
        self.missing_check_penalty = json_schedule.get('missing_check_penalty', None)
        self.active = json_schedule.get('active', True)

        self.employees = Employee.query.filter(Employee.id.in_(json_schedule['assigned_employees'])).all()

    def format(self):
        return{
            'id': self.id,
            'shift_begins': str(self.shift_begins),
            'shift_ends': str(self.shift_ends),
            'title': self.title,
            
            
            'clock_in_start': str(self.clock_in_start),
            'clock_in_end': str(self.clock_in_end),
            'clock_out_start': str(self.clock_out_start),
            'clock_out_end': str(self.clock_out_end),
            'allowed_late_arrival': self.allowed_late_arrival,
            'allowed_early_leave': self.allowed_early_leave,
            'missing_check_penalty': self.missing_check_penalty,
            
            
            'assigned_employees': [emp.format() for emp in self.employees] #if this ever gets big i will make this a join query.
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

        return self

    def update(self, json_schedule):
        self.title = json_schedule['title']
        self.shift_begins = json_schedule['shift_begins']
        self.shift_ends = json_schedule['shift_ends']
        self.employees = Employee.query.filter(Employee.id.in_(json_schedule['assigned_employees'])).all()
        #rules
        
        self.clock_in_start = json_schedule['clock_in_start']
        self.clock_in_end = json_schedule['clock_in_end']
        self.clock_out_start = json_schedule['clock_out_start']
        self.clock_out_end = json_schedule['clock_out_end']
        self.allowed_late_arrival = json_schedule['allowed_late_arrival']
        self.allowed_early_leave = json_schedule['allowed_early_leave']
        self.missing_check_penalty = json_schedule['missing_check_penalty']
        
        try:
            db.session.commit()
            return self.format()
        except:
            abort(400)
            
        finally:
            db.session.close()     
            
               
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except:
            abort(400)
        finally:
            db.session.close()


class Holiday(db.Model):
    __tablename__ = 'holidays'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)

    def __init__(self, name, date):
        self.name = name
        self.date = date

    def insert(self):
        db.session.add(self)
        db.session.commit()

        return self

    def update(self):
        try:
            db.session.commit()
            
        except:
            abort(400)
        finally:
            db.session.close()
        
            
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except:
            abort(400)
        finally:
            db.session.close()

    def format(self):
        return{
            'id': self.id,
            'date': str(self.date),
            'name': self.name
        }


def insert_bulk(list):
    try:
        db.session.bulk_save_objects(list)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
    finally:
        db.session.close

    return {"success": True}


def delete_bulk(list):
    try:
        db.session.bulk_delete_objects(list)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
    finally:
        db.session.close

    return {"success": True}
