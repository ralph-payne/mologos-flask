import re
import unittest
from app import create_app, db
from app.models import User, Role, Word

from flask_login import current_user, login_required

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles() # Just for Grinberg as I don't use roles
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page22(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # self.assertTrue('Stranger' in response.get_data(as_text=True))

    def test_register_and_login(self):
        # register a new account
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password1': 'catcatcat',
            'password2': 'catcatcat'
        })
        # print(response)
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        user = User.query.filter_by(email='john@example.com').first()
        print('looking up user')
        print(user)


    def save_a_word(self):
        print('save a WORD')
        response = self.client.post('/add', data={
            'user-example': 'mouse'
        })
        print(response)
        print(234234234)
        self.assertEqual(response.status_code, 302)


    def translate_a_word(self):
        print('traasdfasdfsdafasdflated a word')
        response = self.client.post('/auth/register', data={
            'email': 'john4@example.com',
            'username': 'john4',
            'password1': 'catcatcat2',
            'password2': 'catcatcat2'
        })
        # print(response)
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        user_all = User.query.all()
        print('translated a word')
        response = self.client.post('/add', data={
            'src_tra_1': 'house',
            'dst_lng_1': 'es'
        })
        print(response)
        print(234234234)
        self.assertEqual(response.status_code, 302)


    def test_register_and_login_2(self):
        # register a 2nd new account
        response = self.client.post('/auth/register', data={
            'email': 'john2@example.com',
            'username': 'john2',
            'password1': 'catcatcat2',
            'password2': 'catcatcat2'
        })
        # print(response)
        # self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        user_all = User.query.all()
        print(type(user_all))
        print(len(user_all))

        # login with the new account
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'catcatcat'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        print('yay')
        # self.assertTrue(re.search('Hello,\s+john!',
        #                           response.get_data(as_text=True)))
        # self.assertTrue(
        #     'You have not confirmed your account yet' in response.get_data(
        #         as_text=True))

        # send a confirmation token
        user = User.query.filter_by(email='john2@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),
                                   follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        # self.assertTrue(
        #     'You have confirmed your account' in response.get_data(
        #         as_text=True))
        print('You have confirmed your account')
        print(f'Below is the User ID {user.id} and user Email {user.email}')
        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        print('log out has worked')
        # self.assertTrue('You have been logged out' in response.get_data(
        #     as_text=True))


    # class Word(db.Model):
    #     __tablename__ = 'word'
    #     id = db.Column(db.Integer, primary_key=True)
    #     word = db.Column(db.String(64), unique=True, index=True)
    #     etymology = db.Column(db.Text())
    #     pronunciation = db.Column(db.String(64))
    #     created = db.Column(db.DateTime, default=datetime.utcnow)

    #     def __init__(self, word, etymology, pronunciation):
    #         self.word = word
    #         self.etymology = etymology
    #         self.pronunciation = pronunciation

    def define_a_word(self):
        # @main.route('/definition/<word>')
        response = self.client.get('/definition/horse')
        self.assertEqual(response.status_code, 200)

        # # register a new account
        # response = self.client.post('/auth/register', data={
        #     'email': 'john@example.com',
        #     'username': 'john',
        #     'password1': 'catcatcat',
        #     'password2': 'catcatcat'
        # })
        # # print(response)
        # # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.status_code, 302)
        # user = User.query.filter_by(email='john@example.com').first()
        # print('looking up user')
        # print(user)