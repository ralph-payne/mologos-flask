import os

from flask import Flask, render_template
# from flask_mail import Mail
from flask_moment import Moment 
from flask_sqlalchemy import SQLAlchemy
from config import config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# mail = Mail()
moment = Moment()
db = SQLAlchemy()

config_name = os.getenv('FLASK_CONFIG') or 'default'
print(f'creating app w config name: {config_name}')
# print(os.getenv('FLASK_APP'))

def create_app(config_name):
    app = Flask(__name__)
    
    try:
        # Results in an error. TODO => debug
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        print(f'Successfully created app w config name: {config_name}')
        print(app.config['TEMPLATES_AUTO_RELOAD'])
    
    except:

        print(f'Caught error with creating app w config name: {config_name}')
        app.config['TEMPLATES_AUTO_RELOAD']
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'data.sqlite')
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'hard to guess string'
    
    # Don't initialize mail until later
    # mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    # Attach routes and custom error pages here

    # Main blueprint registration
    from.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app


