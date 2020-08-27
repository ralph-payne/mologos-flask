from app import db
from datetime import datetime


# TODO: Make sure that this is standard practice. 
# It's currently just a quick fix
db.metadata.clear()

# SQL Naming Conventions
# https://launchbylunch.com/posts/2014/Feb/16/sql-naming-conventions/

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


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Keep last visit date for users updated with ping method
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()