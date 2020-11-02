import unittest
from flask import current_app
from app import create_app
from app.models import db


class BasicsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        oi = db.create_all()
        print(oi)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite:///test.db',
        )
        # self.app.init_db()
        db.create_all()
        # db create all not working right now. so developer has to create the tables himself
        # The tests are failing because I can't seem to properly create the tables


    # def setUp(self):
    #     self.app = create_app('testing 2')
    #     self.app = Flask(__name__)
    #     self.app_context.push()
    #     db.init_app(self.app)
    #     with self.app.app_context():
    #         db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
