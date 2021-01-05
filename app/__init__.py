from flask import Flask, abort, jsonify, request
from models import setup_db, Employee, Attendance, Schedule, Holiday, insert_bulk, db
from controllers.mdbcontroller import import_employees_from_access_db, import_attendances_from_access_db
from controllers.timeUtils import *
from controllers.Reports import *
from datetime import datetime
from controllers.holidaysSync import syncHolidaysDb
from flask_cors import CORS
import sys


# def create_app(test_config=None):

app = Flask(__name__)
app.config.from_object('config')
setup_db(app)
CORS(app)


    # CORS Headers

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                            'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                            'GET,PUT,POST,PATCH,DELETE,OPTIONS')
    return response

default_start_date = "2000-01-01"
default_end_date = "2200-01-01"

@app.route('/')
def index():
    # get_employees_from_access_db()
    # get_attendances_from_access_db()
    # get_egypt_public_holidays()
    # get_days_between_two_dates("2019-08-01", "2019-08-15")
    return 'hello '

@app.route('/employees-importer')
def import_employees():
    try:
        imported_emps_count = import_employees_from_access_db()
    except:
        abort(501)

    return jsonify({
        "success": True,
        "count": imported_emps_count
    }), 200

@app.route('/employees')
def get_employees():
    try:
        employees = Employee.query.all()

    except:
        abort(404)

    return jsonify({
        "success": True,
        "employees": [employee.format() for employee in employees],
        "count": len(employees)
    })

@app.route('/employees/<int:id>')
def get_employee_by_id(id):
    try:
        employee = Employee.query.get(id)
        abort_if_none(employee)

    except:
        abort(404)

    return jsonify({
        "success": True,
        "employee": employee.format(),
    })

@app.route('/attendances-importer')
def import_attendances():
    try:
        imported_attens_count = import_attendances_from_access_db()
    except Exception as e:
        print(sys.exc_info)
        print(e)
        abort(501)

    return jsonify({
        "success": True,
        "count": imported_attens_count
    }), 200

'''
    get all attendances or get all attendaces between 2 dates if asked for
    the json data structure returned is an array of objects that contain each employee and an array of his attendances.

'''
@app.route('/attendances')
def get_attendances():
    try:

        data = []
        all_attendances_count = 0
        # get all id and name of all emps
        employees = Employee.query.order_by(Employee.id).all()
        abort_if_none(employees)

        start_date = request.args.get(
            'start_date', default=default_start_date, type=str)
        end_date = request.args.get(
            'end_date', default=default_end_date, type=str)

        dates_are_being_provided = start_date != default_start_date or end_date != default_end_date

        for employee in employees:
            # the reason i check for this instead of just getting records between the default dates is because i believe it costs more for the db to do that when we dont need to
            if dates_are_being_provided:
                attendances = Attendance.query.filter(
                    Attendance.user_id == employee.id, Attendance.day >= start_date, Attendance.day <= end_date).all()
            else:
                attendances = employee.attendances

            if attendances != None:
                all_attendances_count += len(attendances)

                data.append({
                    "employee_id": employee.id,
                    "name": employee.name,
                    "attendances": [attendance.format() for attendance in attendances],
                    "total": len(attendances)
                })

            else:
                data.append({
                    "employee_id": employee.id,
                    "employee": employee.name,
                    "attendances": []
                })

        # attens = Attendance.query.all()
        abort_if_none(data)

    except:
        print(sys.exc_info)
        abort(404)

    return jsonify({
        "success": True,
        "employees_attendances": data,
        "count": all_attendances_count,
        'start_date': start_date,
        'end_date': end_date
    })

'''
    this can return attendances between 2 dates or all of them for an employee
    date format is month-day-year
'''
@app.route('/employees/<int:employee_id>/attendances')
def get_employee_attendances(employee_id):
    # try:

    employee = Employee.query.get(employee_id)
    abort_if_none(employee)
    employee_attendances = []
    # checking if the user specified any datess
    start_date = request.args.get('start_date', default=False, type=str)
    end_date = request.args.get('end_date', default=False, type=str)

    #if user defined both dates
    if start_date != False and end_date != False:
        employee_attendances = Attendance.query.filter(Attendance.user_id == employee_id, Attendance.day >= start_date, Attendance.day <= end_date).order_by(Attendance.day).all()

    elif start_date == False and end_date != False:

        employee_attendances = Attendance.query.filter(Attendance.user_id == employee_id, Attendance.day <= end_date).order_by(Attendance.day).all()
        abort_if_none(employee_attendances)
        start_date = str(employee_attendances[0].day)
            
    elif end_date == False and start_date != False:
        employee_attendances =  Attendance.query.filter(Attendance.user_id == employee_id, Attendance.day >= start_date).order_by(Attendance.day).all()
        abort_if_none(employee_attendances)
        end_date = str(employee_attendances[-1].day)
            
    elif start_date == False and end_date == False:
        employee_attendances = employee.attendances
        abort_if_none(employee_attendances)
        
        #need to set this according to the employee start and end records to avoid counting extra days in the report.
        start_date = str(employee_attendances[0].day)
        end_date = str(employee_attendances[len(employee_attendances)-1].day)
            
        #TODO: IMPORTANT for report generating: handle if no dates were selected then set them according to first and last attendances dates
    '''
    generating the report
        '''
    if request.args.get('schedule', default='false') == 'true' and employee.schedule_id != None:            
        holidays = Holiday.query.filter(Holiday.date >= start_date, Holiday.date <= end_date).all()
        report = reportsBuilder().build_report(employee_active_schedule=employee.schedule,attendances_list=employee_attendances, holidays=holidays, start_date=start_date, end_date=end_date)

    else:
        report = [attendance.format()
                    for attendance in employee_attendances]

    # except:
    #     abort(404)

    return jsonify({
        'success': True,
        'employee': employee.format(),
        'report': report,
        'attended_days_count': len(employee_attendances),
        'start_date': start_date,
        'end_date': end_date
    }), 200

@app.route('/attendances/count')
def get_attendances_count():

    try:

        attens_count = Attendance.query.count()
    except:
        abort(404)

    return jsonify({
        "success": True,
        # "attendances": [attens.format() for employee in attens],
        "count": attens_count
    })

def abort_if_none(result):
    if result is None:
        abort(404)
        
    #if its a list not an object, abort if list is empty but not none
    if type(result) == list or type(result) == dict:
        if len(result) == 0:
            abort(404)

        

@app.route('/schedules', methods=["POST"])
def add_schedule():
    schedule_form = request.get_json()
    
    # validate data
    validate_schedule_form(schedule_form)

    new_schedule = Schedule(schedule_form)

    added_schedule = new_schedule.insert()

    return jsonify({
        "success": True,
        "schedule": added_schedule.format()
    })

@app.route('/schedules/<int:id>', methods=['DELETE'])
def delete_schedule(id):
    schedule = Schedule.query.get(id)
    if schedule == None:
        abort(404)

    schedule.delete()

    return jsonify({"success": True})

@app.route('/schedules', methods=['PATCH'])
def edit_schedule():
    schedule_form = request.get_json()['data']
    validate_schedule_form(schedule_form)

    schedule = Schedule.query.get(schedule_form['id'])
    abort_if_none(schedule)

    #update the existing schedule with the new data in the json form and return the updated version.
    formatted_edited_schedule= schedule.update(schedule_form)

    return jsonify({
        "success": True,
        "schedule": formatted_edited_schedule
    })

@app.route('/schedules', methods=['GET'])
def get_schedules():
    #TODO: create an schedules and employees join query later if this ever gets big.
    schedules = Schedule.query.all()
    abort_if_none(schedules)

    return jsonify({
        "success": True,
        "schedules": [sch.format() for sch in schedules]
    })

@app.route('/schedule/<int:id>', methods=['GET'])
def get_schedule(id):
    schedule = Schedule.query.get(id)
    abort_if_none(schedule)

    return jsonify({
        "success": True,
        "schedule": schedule.format()
    })

@app.route('/holidays', methods=['POST'])
def resync_holidays_by_year():
    year = request.get_json()['year']

    holidays = syncHolidaysDb(year)

    if len(holidays) == 0:

        return jsonify({
            "success": False,
        })

    return jsonify({
        "success": True,
        "holidays": [holiday.format() for holiday in holidays]
    })
    
    
@app.route('/holidays', methods=['GET'])
def get_holidays():
    holidays = Holiday.query.all()
    abort_if_none(holidays)
    
    return jsonify({
        "holidays": [holiday.format() for holiday in holidays]
    })
    
@app.route('/holidays/<int:id>', methods=['PATCH'])
def edit_holiday(id):
    holiday = Holiday.query.get(id)
    abort_if_none(holiday)
    
    holiday_form = request.get_json()
    if holiday_form['name'] != None and holiday_form['date'] != None:
        holiday.name = holiday_form['name']
        holiday.date = holiday_form['date']
        holiday.update()
        
    return jsonify({
        "success": True,
        "holiday": [holiday_form['name'], holiday_form['date']]
    })



'''
    validates the schedule form data
    TODO:SO far im only checking fo nulls, but i need to check for data types too!!
'''


def validate_schedule_form(schedule_form):
    if schedule_form == None or schedule_form['shift_begins'] == None or schedule_form['shift_ends'] == None or schedule_form['title'] == None or get_time_from_string(schedule_form["shift_begins"]) >= get_time_from_string(schedule_form["shift_ends"]):
        abort(500)
        
        
    
    #validate the clock in&out start and end data constraints
    #clock ins should start before or equal to the schedule on duty time, and ends earlier then the off-duty time and the clock out time
    on_duty = get_time_from_string(schedule_form["shift_begins"])
    off_duty = get_time_from_string(schedule_form["shift_ends"])
    
    clock_in_start = schedule_form.get('clock_in_start', None)
    clock_in_end = schedule_form.get('clock_in_end',None)
    clock_out_start = schedule_form.get('clock_out_start',None)
    clock_out_end = schedule_form.get('clock_out_end',None)
    
    if clock_in_start != None and clock_out_start != None:
        if get_time_from_string(clock_in_start) > on_duty or get_time_from_string(clock_in_start) >= get_time_from_string(clock_out_start) or  get_time_from_string(clock_in_start) >= get_time_from_string(clock_in_end):
            abort(400)
            
        if get_time_from_string(clock_in_end) <= get_time_from_string(clock_in_start) or get_time_from_string(clock_in_end) >= get_time_from_string(clock_out_start):
            abort(400)
            
        
        #clockouts start before or equal to the schedule clock out time but after the clock in time, and ends earlier then the clockin accepting time
        if get_time_from_string(clock_out_start) > off_duty or get_time_from_string(clock_out_start) <= get_time_from_string(clock_in_end) or  get_time_from_string(clock_out_start) >= get_time_from_string(clock_out_end):
            abort(400)

        if get_time_from_string(clock_out_end) <= get_time_from_string(clock_out_start) or get_time_from_string(clock_out_end) > datetime(2000,1,1, 23, 59).time():
            abort(400)
    
        if schedule_form.get('allowed_early_leave', 0) > 60 or schedule_form.get('allowed_late_arrival', 0) > 60:
            abort (400)
        
        if on_duty > get_time_from_string(clock_in_end) or on_duty < get_time_from_string(clock_in_start):
            abort(400);
            
        if off_duty > get_time_from_string(clock_out_end):
            abort(400);
        #{'a'} for absence, {'N'} for number of penalty minutes, 0 do nothing
        #checking if its 'A' then it must be a number, that is less than 5 hours
        if schedule_form.get('missing_check_penalty', None) != None and schedule_form['missing_check_penalty'] != 'A':
            if schedule_form['missing_check_penalty'].isnumeric() == False or int(schedule_form['missing_check_penalty']) > 360:
                abort(400)
    
                
    # no need to check if employees exist, even if they don't i want to be able to create the schedule still
    
    
if __name__ == "__main__":
    app.run()