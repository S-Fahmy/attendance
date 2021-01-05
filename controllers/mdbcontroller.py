from sqlalchemy import create_engine, text
import urllib, sys
from models import Employee, Attendance, insert_bulk, db
from datetime import datetime
from flask import abort
import os

'''
A reminder not to be confused in the future:
To be noted, the access db, user table has 2 columns, one called userid and the other is badge number
the ztecko app use the badge number as the id when showing emps in reports but behind the scenes it uses the userid for all foreignkeys

'''

def connect_to_machine_access_db():
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    importedDbname = 'att2000.mdb' #when its imported manually from the ztecko app.
    dbPath =  os.path.join(root_path, importedDbname)

    try:
        connection_string = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ='+ dbPath +';'
            r'ExtendedAnsiSQL=1;'
        )

        

        connection_uri = f"access+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
        engine = create_engine(connection_uri)
        return engine.connect()
    
    except Exception as e:
        print(e)
        abort(500)


# TODO: write code to only check for and add new entries
def import_employees_from_access_db():

    try:
        conn = connect_to_machine_access_db()

        # with engine.connect() as conn:
        employees = conn.execute("SELECT USERID, Name FROM [USERINFO]")
        
        employees_list = []

        for employee in employees:

            employees_list.append(
                Employee(id=employee['USERID'], name=employee['Name']))

        insert_bulk(employees_list)

    except Exception as e:
        print(e)

    finally:
        conn.close()

    return len(employees_list)

# TODO: write code to only check for and add new entries, this imports a fresh records
def import_attendances_from_access_db():
    reset_db()
    import_employees_from_access_db()
    # the goal is to grp all users ins and outs in 1 day row


    try:
        conn = connect_to_machine_access_db()

        #get all values from mdb, TODO: check for the latest value date in the app db then structure the query to only fetch records with newer dates
        attendances = conn.execute(
            "SELECT userid, checktime, checktype FROM [CHECKINOUT] ORDER BY userid, checktime")

        #initialzing the needed values with default data.
        attendances_list = []
        current_day = datetime(1500, 1, 1).date()
        check_ins = check_outs = ""
        user_id = 0

        #looping through the attendances records list returned from machine access db
        #each record is a date and the clock in or out type.
        #GOAL: group clock ins and outs per user by the day they belong to.
        for attendance in attendances:

            check_time = attendance['checktime']
            # new record is when the date is newer then current_day value. or user id is different
            #note: comparing only the date without the time, or else every record will be counted as a new day
            if check_time.date() > current_day or user_id != attendance['userid']:
                
                # before doing anything we need to save the previous day as an Attendance object in the attendances list if there is
                #if user_id isn't the default value then we definitely have some new data to save, else this is the first new record ever
                if user_id > 0:
                    attendances_list.append(Attendance(
                        current_day, check_ins, check_outs, user_id))
                    check_ins = check_outs = ""

                current_day = check_time.date()
                user_id = attendance['userid']

                if attendance['checktype'] == 'I':
                    check_ins = str(check_time.time()) + ','
                elif attendance['checktype'] == 'O':
                    check_outs = str(check_time.time()) + ','

            elif check_time.date() == current_day:

                if attendance['checktype'] == 'I':
                    check_ins = check_ins + str(check_time.time()) + ','
                elif attendance['checktype'] == 'O':
                    check_outs = check_outs + str(check_time.time()) + ','

        insert_bulk(attendances_list)

    finally:
        conn.close()
    
    return len(attendances_list)


def reset_db():
    try:
        db.session.query(Attendance).delete()
        db.session.query(Employee).delete()
        db.session.commit()
    except:
        print(sys.exc_info)
    finally:
        db.session.close()