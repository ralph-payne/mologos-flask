import os # for environment variables

from flask import Flask, render_template

from flask_mail import Mail
from flask_moment import Moment 
from flask_sqlalchemy import SQLAlchemy
from config import config

from flask_login import LoginManager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

mail = Mail()
moment = Moment()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

config_name = os.getenv('FLASK_CONFIG') or 'default'

def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # Main blueprint registration
    from.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Authentication blueprint registration (p106 Grinberg)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app