from app import db
from datetime import datetime

# Note: I should look to see if this is standard practice. It's currently just a quick fix
db.metadata.clear()

# db.Model is required - don't change it
# identify all columns by name and data type
class Sentence(db.Model):
    __tablename__ = 'sentences'
    id = db.Column(db.Integer, primary_key=True)
    # Todo: find a way to link the user ID with the User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    word = db.Column(db.String)
    example = db.Column(db.String)
    created = db.Column(db.String)

    def __init__(self, user_id, word, example, created):
        self.user_id = user_id
        self.word = word
        self.example = example
        self.created = created


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username