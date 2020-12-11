from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app
from flask_login import UserMixin

from . import db, login_manager


#### Adding Role and Permission so that db.create_all() works when testing
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


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

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


# WORD MODEL
class Word(db.Model):
    __tablename__ = 'word'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), unique=True, index=True)
    etymology = db.Column(db.Text())
    pronunciation = db.Column(db.String(64))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word, etymology, pronunciation):
        self.word = word
        self.etymology = etymology
        self.pronunciation = pronunciation


# USER EXAMPLE MODEL
class UserExample(db.Model):
    __tablename__ = 'user_example'
    id = db.Column(db.Integer, primary_key=True)
    # Example contains either (1) a sentence in English with the target word in or (2) the translated sentence in the destination language (dst)
    example = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('app_user.id'))
    word = db.Column(db.String(64), index=True)
    # Translation boolean: 0 indicates that it is an English expression | 1 indicates that it is a foreign translation
    translation = db.Column(db.Boolean)
    src = db.Column(db.String(2))
    dst = db.Column(db.String(2))
    # Original is used to store the original English text if the data contains a translation
    comment = db.Column(db.String())
    created = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    last_tested = db.Column(db.DateTime)
    attempt = db.Column(db.Integer, default=0)
    success = db.Column(db.Integer, default=0)
    fail = db.Column(db.Integer, default=0)
    # Level is used to determine the probablity of the user seeing the word on the Challenge
    level = db.Column(db.Integer, default=0)
    ignored = db.Column(db.Boolean, default=0)
    starred = db.Column(db.Boolean, default=0)

    def __init__(self, example, word, user_id, translation, src, dst):
        self.example = example
        self.word = word
        self.user_id = user_id
        self.translation = translation
        self.src = src
        self.dst = dst


# DEFINITION MODEL
class Definition(db.Model):
    __tablename__ = 'definition'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), db.ForeignKey('word.word'), index=True)
    definition = db.Column(db.String(256))
    source = db.String(16)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word, definition, source):
        self.word = word
        self.definition = definition
        self.source = source


# DICTIONARY EXAMPLE MODEL
class DictionaryExample(db.Model):
    __tablename__ = 'dictionary_example'
    id = db.Column(db.Integer, primary_key=True)
    # Legacy; moving to word instead of word id
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    word = db.Column(db.String(64), db.ForeignKey('word.word'), index=True)    
    example = db.Column(db.String(256))
    source = db.String(16)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, word, example, source):
        self.word = word
        self.example = example
        self.source = source


class Translation(db.Model):
    __tablename__ = 'translation'
    id = db.Column(db.Integer, primary_key=True)
    # key word is not in use in Version 1 but it could be added to model if we wanted to set up a connection between the English words and the translations
    created = db.Column(db.DateTime, default=datetime.utcnow)
    source_language = db.Column(db.String(2))
    destination_language = db.Column(db.String(2))
    input = db.Column(db.String(512))
    output = db.Column(db.String(512))

    def __init__(self, word, definition, source):
        self.word = word
        self.definition = definition
        self.source = source


# USER MODEL
class User(UserMixin, db.Model):
    # user is a reserved word in Postgres: https://www.postgresql.org/docs/7.3/sql-keywords-appendix.html so don't use it as a table name or you will encounter issues!
    __tablename__ = 'app_user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    lng_preferred = db.Column(db.String(3))
    lng_recent = db.Column(db.String(3))

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class InternationalAccent(db.Model):
    __tablename__ = 'international_accent'
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(1))
    language = db.Column(db.String(32))
    alt_code = db.Column(db.String(32))
    html_entity = db.Column(db.String(32))
    row_num = db.Column(db.Integer)
    in_use = db.Column(db.Boolean)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# BULK TRANSLATE CLASS
class BulkTranslate(db.Model):
    __tablename__ = 'bulk_translate'
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(128), unique=True, index=True)
    german = db.Column(db.String(128))
    italian = db.Column(db.String(128))
    portuguese = db.Column(db.String(128))
    spanish = db.Column(db.String(128))
    latin = db.Column(db.String(128))
    greek = db.Column(db.String(128))
    french = db.Column(db.String(128))
    polish = db.Column(db.String(128))


# USER LANGUAGE PREFERENCE CLASS
class UserLanguagePreference(db.Model):
    __tablename__ = 'user_language_preference'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('app_user.id'), index=True)
    # The order has to be the same as the order of the language_codes
    english = db.Column(db.Boolean, default=True)
    german = db.Column(db.Boolean, default=True)
    spanish = db.Column(db.Boolean, default=True)    
    italian = db.Column(db.Boolean, default=True)
    portuguese = db.Column(db.Boolean, default=True)
    latin = db.Column(db.Boolean, default=True)
    greek = db.Column(db.Boolean, default=True)
    french = db.Column(db.Boolean, default=True)
    polish = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)