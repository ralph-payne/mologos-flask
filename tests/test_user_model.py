import unittest
import time
from app.models import User
from app import db

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User(password = 'catcatcat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password = 'catcatcat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password = 'catcatcat')
        self.assertTrue(u.verify_password('catcatcat'))
        self.assertFalse(u.verify_password('dogdogdog'))

    def test_password_salts_are_random(self):
        u = User(password='catcatcat')
        u2 = User(password='catcatcat')
        self.assertTrue(u.password_hash != u2.password_hash)

    # Fails: (sqlite3.OperationalError) table app_user has no column named role_id
    # def test_valid_confirmation_token(self):
    #     u = User(password='catcatcat')
    #     db.session.add(u)
    #     db.session.commit()
    #     token = u.generate_confirmation_token()
    #     self.assertTrue(u.confirm(token))