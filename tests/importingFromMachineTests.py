import sys
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from app import app


from models import setup_test_db, Employee, Attendance
from controllers.mdbcontroller import connect_to_machine_access_db


class mdbTestCase(unittest.TestCase):
    """This class represents the mdb data test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        self.client = self.app.test_client
        self.db = setup_test_db(self.app)

        # binds the app to the current context
        # with self.app.app_context():
        #     self.db = SQLAlchemy()
        #     self.db.init_app(self.app)

    def tearDown(self):
       pass


    # def test_can_import_employees_from_mdb(self):
    #     # self.db.session.query(Employee).delete()
    #     # self.db.session.commit()

    #     res = self.client().get('/employees-importer')

    #     data1 = load_response_data(res)

    #     self.assertEqual(res.status_code, 200)
    #     self.assertTrue(data1['count'] > 1)

    #     # check if the employees in our database is equal to the number imported from access
    #     res2 = self.client().get('/employees')
    #     data2 = load_response_data(res2)
    # #     self.assertEqual(data1['count'], data2['count'])


    def test_can_import_employees_records_from_db(self):

        res1 = self.client().get('/attendances-importer')
        data1 = load_response_data(res1)
        
        self.assertTrue(data1['count'] > 1)

        count = len(Attendance.query.all())

        self.assertEqual(data1['count'], count)
    

def load_response_data(res):
    return json.loads(res.data)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
