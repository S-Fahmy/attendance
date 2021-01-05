import sys
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from flaskr import create_app


from models import setup_test_db, db, Employee, Attendance, Schedule
from controllers.mdbcontroller import connect_to_machine_access_db


class mdbTestCase(unittest.TestCase):
    """This class represents the mdb data test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.db = setup_test_db(self.app)



    def tearDown(self):
       pass

    def test_reports_selected_dates_scenarios(self):
        res = self.client().get('/employees/5/attendances?schedule=true&start_date=7-2-2019&end_date=8-28-2019')
        data = load_response_data(res)
        self.assertEqual(data['report']["attendances"][0]['day'], "2019-07-02")
        self.assertEqual(data['report']["attendances"][-1]['day'], "2019-08-28")
        
        res = self.client().get('/employees/5/attendances?schedule=true&start_date=7-1-2019')
        data = load_response_data(res)
        self.assertEqual(data['report']["attendances"][0]['day'], "2019-07-01")
        self.assertEqual(data['report']["attendances"][-1]['day'], "2020-02-12")
        
        res = self.client().get('/employees/5/attendances?schedule=true&end_date=8-28-2019')
        data = load_response_data(res)
        self.assertEqual(data['report']["attendances"][0]['day'], "2016-08-10")
        self.assertEqual(data['report']["attendances"][-1]['day'], "2019-08-28")
    
        res = self.client().get('/employees/5/attendances?schedule=true')
        data = load_response_data(res)
        self.assertEqual(data['report']["attendances"][0]['day'], "2016-08-10")
        self.assertEqual(data['report']["attendances"][-1]['day'], "2020-02-12")
        

    def test_employee_each_attendance_day_record_caluclated_correctly(self):
        
        #schedule is created and assigned to an employee
        #getting schedule from test_db, if in future that test gets deleted then we need to create a new schedule record
        schedule = Schedule.query.filter(Schedule.title == 'main').first()
        self.assertIsNotNone(schedule)

        #get employee with that assigned schedule attendances, default are id 5 and 2
        #manually calculated values.
        res = self.client().get('/employees/5/attendances?schedule=true&start_date=7-1-2017&end_date=8-1-2017')
        data = load_response_data(res)
        
        self.assertTrue(data['success'])
        #assert that that each attendance day correctly has checkin and checkout status and
        #overtime status calculated correctly.
        self.assertIsNotNone(data['report']["attendances"][1]["checkin_status"])
        self.assertIsNotNone(data['report']["attendances"][1]['check_in_calculation'])
        self.assertEqual(data['report']['total_absent_days'], 2)

        #130 minutes of over for this duration is done by manual calculation by me.
        self.assertEqual(data['report']['overtime'], 90)
        self.assertEqual(data['report']['overtime'], data['report']['arrival_total']+data['report']['leave_total'])


        #this time period is good because it has both ot ut late early and forgetting to clock-in or to clockout and absence
        res = self.client().get('/employees/5/attendances?schedule=true&start_date=7-1-2018&end_date=8-1-2018')
        data = load_response_data(res)

        self.assertEqual(data['report']['overtime'], 0)
        self.assertEqual(data['report']['undertime'], -3431)
        self.assertEqual(data['report']['days_without_checks'], 12)
        self.assertEqual(data['report']['total_absent_days'], 3)
        
        
    def test_holidays_not_counted_as_absence(self):
        #~1.5 months, 4 days holidays, and 4 day absences.
        res = self.client().get('/employees/5/attendances?schedule=true&start_date=7-1-2019&end_date=8-13-2019')
        data = load_response_data(res)
        
        self.assertEqual(data['report']['total_absent_days'], 4)
        
    
        
        

def load_response_data(res):
    return json.loads(res.data)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
