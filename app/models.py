from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app
from flask_login import UserMixin

from . import db, login_manager

# TODO: Make sure that this is standard practice; It's currently just a quick fix
db.metadata.clear()


class Word(db.Model):
    __tablename__ = 'word'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), unique=True, index=True)
    etymology = db.Column(db.Text())
    pronunciation = db.Column(db.String(64))

    def __init__(self, word, etymology, pronunciation):
        self.word = word
        self.etymology = etymology
        self.pronunciation = pronunciation


class Definition(db.Model):
    __tablename__ = 'definition'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), db.ForeignKey('word.id'))
    definition = db.Column(db.Text())
    source = db.String(32)

    def __init__(self, word, definition, source):
        self.word = word
        self.definition = definition
        self.source = source


class DictionaryExample(db.Model):
    __tablename__ = 'dictionary_example'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String, db.ForeignKey('word.id'))
    example = db.Column(db.String)
    # source can be oxford_dict or merriam_webster
    # TODO => See if it makes more sense to use an enum instead of a string with 32 chars
    source = db.String(32)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word, example, source):
        self.word = word
        self.example = example
        self.source = source


class UserExample(db.Model):
    __tablename__ = 'user_example'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String, db.ForeignKey('word.id'))
    example = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Integer, default=0)
    fail = db.Column(db.Integer, default=0)
    skip = db.Column(db.Integer, default=0)
    # Level is used to determine the probablity of the user seeing the word on the Challenge
    level = db.Column(db.Integer, default=0)
    deleted = db.Column(db.Boolean, default=0)
    ignored = db.Column(db.Boolean, default=0)
    starred = db.Column(db.Boolean, default=0)

    def __init__(self, word, example, user_id):
        self.word = word
        self.example = example
        self.user_id = user_id


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))  
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Keep last visit date for users updated with ping method
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Method which generates a token with default validity time of one hour
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    # Method which checks the id from the token matches the logged-in user
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        # Not using avatars at the moment
        # self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))