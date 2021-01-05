import sys
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from flaskr import create_app


from models import setup_test_db, Employee, Attendance, Schedule, db
from controllers.mdbcontroller import connect_to_machine_access_db
from datetime import datetime
from controllers.timeUtils import *


class mdbTestCase(unittest.TestCase):
    """This class represents the mdb data test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.db = setup_test_db(self.app)

        # binds the app to the current context
        # with self.app.app_context():
        #     self.db = SQLAlchemy()
        #     self.db.init_app(self.app)

    def tearDown(self):
        pass

    def test_fetch_all_employees(self):
        res = self.client().get('/employees')
        data = load_response_data(res)
        self.assertTrue(data['success'])

        self.assertIsNotNone(data['employees'][0]['name'])

    def test_fetch_employee_by_id(self):
        res = self.client().get('/employees/6')

        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['employee']['name'])

    def test_404_if_emp_not_found(self):
        res = self.client().get('/employees/655')

        self.assertEqual(res.status_code, 404)

    ######################################

    def test_fetch_all_attendances(self):
        res = self.client().get('/attendances')
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['count'] > 1)
        self.assertIsNotNone(data['employees_attendances']
                             [1]['attendances'][1]['day'])
        self.assertEqual(data['employees_attendances'][1]['employee_id'],
                         data['employees_attendances'][1]['attendances'][1]['user_id'])

    def test_fetch_attendances_by_employee(self):
        res = self.client().get('/employees/6/attendances')
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)

        # should assert that employee name is joined with the attens data
        self.assertIsNotNone(data['employee']['name'])
        self.assertIsNotNone(data['report'][1]['day'])
        self.assertEqual(data['employee']['id'],
                         data['report'][1]['user_id'])

    def test_404_attendances_by_no_employee(self):
        res = self.client().get('/employees/655/attendances')

        self.assertEqual(res.status_code, 404)

    def test_integrity_of_attendances_data(self):
        res = self.client().get('/employees/11/attendances')
        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)

        # assert day record only occur once
        self.assertTrue(
            days_in_attendances_occur_once_per_user(data['report']))

    def test_fetch_attendances_by_employee_by_date(self):
        res = self.client().get(
            '/employees/10/attendances?start_date=7-1-2017&end_date=8-1-2017')

        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)

        # asserting that the first day is bigger than the start date and the end date is less than the end date
        self.assertTrue(datetime.strptime(data['report'][0]['day'], '%Y-%m-%d').date() >= datetime(2017, 7, 1).date())
        self.assertTrue(datetime.strptime(data['report'][len(data['report'])-1]['day'], '%Y-%m-%d').date() <= datetime(2017, 8, 1).date())

    def test_fetch_attendances_by_date(self):
        res = self.client().get('attendances?start_date=7-1-2017&end_date=8-1-2017')

        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)

        # asserting that the first day is bigger than the start date and the end date is less than the end date
        self.assertTrue(datetime.strptime(
            data['employees_attendances'][1]['attendances'][5]['day'], '%Y-%m-%d').date() >= datetime(2017, 7, 1).date())

    ##############schedule#######

    def test_can_create_new_schedule(self):
        reset_a_table(model=Schedule)

        res = self.client().post('/schedules',
                                 json={"title": "main", "shift_begins": "9:30", "shift_ends": '16:30', "assigned_employees": [5, 6, 7], "active": True, "missing_check_penalty": "230"})

        data = load_response_data(res)
        self.assertEqual(res.status_code, 200)

        # check if record is in db
        schedule = Schedule.query.first()
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.title, "main")
        self.assertEqual(schedule.shift_begins,
                         datetime(2010, 1, 1, 9, 30).time())

        # check employees got assigned
        for i in [5, 6]:
            emp = Employee.query.get(i)
            self.assertTrue(emp.schedule_id == schedule.id)

    def test_can_get_schedules(self):
        res = self.client().get('/schedules')
        data = load_response_data(res)
        self.assertIn("9:30", data['schedules'][0]['shift_begins'])
        self.assertTrue(data['success'])
        self.assertTrue(len(data['schedules']) >= 1)

    def test_can_get_schedule_by_id(self):
        schedule_id = Schedule.query.first().id
        self.assertIsNotNone(schedule_id)

        res = self.client().get('schedule/' + str(schedule_id))
        data = load_response_data(res)

        self.assertTrue(data['success'])
        self.assertIsNotNone(data['schedule']['title'])

    def test_can_edit_schedule(self):
        sch = {"title": "editing", 
            "shift_begins": "9:30", 
            "shift_ends": '17:30',
            "clock_in_start": "07:30",
            "clock_in_end": "13:30",
            "clock_out_start": "14:00",
            "clock_out_end": "22:50",
            "assigned_employees": [14], 
            "active": True}
    
        res = self.client().post('/schedules', json=sch)
        self.assertEqual(res.status_code, 200)
        
        
        # this schedule in the database is created in the previous tasted
        schedule = Schedule.query.filter(Schedule.title == 'editing').first()
        self.assertIsNotNone(schedule)
        self.assertIsNotNone(Employee.query.get(14).schedule_id)

        res = self.client().patch('/schedules',
                                  json={"data":{
                                      "id":schedule.id, 
                                      "title": "edited", 
                                      "shift_begins": "9:40:00", 
                                      "shift_ends": '17:30:00', 
                                      "assigned_employees": [14],
                                      "active": True,
                                      
                                      "clock_in_start":"07:30:00",
                                      "clock_in_end":"13:29:00",
                                      "clock_out_start":"14:00:00",
                                      "clock_out_end":"22:30:00",
                                      "allowed_late_arrival":0,
                                      "allowed_early_leave":0,
                                      "missing_check_penalty":"230"
                                      }})

        #wanna make sure that the patch function returned the edited schedule but also wanna make sure it got persisted in the db
        data = load_response_data(res)
        edited_schedule = Schedule.query.filter(Schedule.title == 'edited').first()
        self.assertEqual(data['schedule']["id"], edited_schedule.id)

        self.assertTrue(edited_schedule.title, "edited")
        # assert that the assigned employee values got changed
        # self.assertIsNone(Employee.query.get(14).schedule_id)
        # self.assertTrue(Employee.query.get(15).schedule_id == edited_schedule.id)

    def test_can_delete_schedule(self):
        # add schedule to the db and then delete it and assert it doesn't exist
        sch_json = {"title": 'del',
                    "shift_begins": get_time_from_string("9:30"), 
                    "shift_ends": get_time_from_string("19:00"), 
                    "active": True,
                    "assigned_employees": [10]}

        schedule = Schedule(sch_json).insert()

        self.assertIsNotNone(Schedule.query.get(schedule.id))
        self.assertIsNotNone(Employee.query.get(10).schedule_id)

        res = self.client().delete('/schedules/' + str(schedule.id))
        data = load_response_data(res)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        self.assertIsNone(Schedule.query.get(schedule.id))
        self.assertIsNone(Employee.query.get(10).schedule_id)


    def test_schedule_rules_times_cant_overlap(self):
        sch = {"title": "overlap", 
               "shift_begins": "9:30", 
               "shift_ends": '14:30',
               "clock_in_start": "07:30",
               "clock_in_end": "13:30",
               "clock_out_start": "14:00",
               "clock_out_end": "13:50",
               "assigned_employees": [3], 
               "active": True}
        
        res = self.client().post('/schedules', json=sch)
        self.assertEqual(res.status_code, 400)

        sch['clock_out_end'] = '23:00'
        sch['clock_in_end'] = '14:10'
        res = self.client().post('/schedules', json=sch)
        self.assertEqual(res.status_code, 400)
        
        sch['clock_in_end'] = '13:30'
        sch['clock_in_start'] = '13:30'      
        res = self.client().post('/schedules', json=sch)
        self.assertEqual(res.status_code, 400)
 
        sch['clock_in_start'] = '08:30'      
        res = self.client().post('/schedules', json=sch)
        self.assertEqual(res.status_code, 200)       
        
        
    ################################


    # @TODO: get all schedule route then the actual report
'''
since all user check in and outs from machine should be grouped under one day
and attendances list here is sorted by date, so if a day exist twice, then the repeated day will be the next value.
'''


def days_in_attendances_occur_once_per_user(attendances):
    i = 0
    while i < len(attendances) - 1:
        # -1 so we dont check for the next day on the last record.

        date = datetime.strptime(attendances[i]['day'], '%Y-%m-%d').date()
        next_date = datetime.strptime(
            attendances[i + 1]['day'], '%Y-%m-%d').date()

        if date == next_date:
            return False

        i += 1

    return True


def load_response_data(res):
    return json.loads(res.data)


def reset_a_table(model):
    db.session.query(model).delete()
    db.session.commit()


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
