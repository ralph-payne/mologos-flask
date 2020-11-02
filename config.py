import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
    ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MOLOGOS_MAIL_SUBJECT_PREFIX = '[Mologos]'
    FLASKY_MAIL_SENDER = 'Mologos Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SSL_REDIRECT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    # TEMPLATES_AUTO_RELOAD = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    'sqlite:///' + os.path.join(BASE_DIR, 'data-dev.sqlite')

'''
Right now the issue with testing is that the tables are not being created with create_all
One work around is using the Prod database (obviously a terrible idea in practice but it works for the moment)
The next step is to create a test database manually on the local machine
Then enter the flask shell and create all the tables within the test databsae

1. No such table: user in data-dev.sqlite
2. Go into flask shell, from mologos import db, db.create_all(), quit()
3. Go into data-dev.sqlite and check that the table has been created
4. Change the config within config.py so that the test script uses the data-dev.sqlite database
5. Run Flask Test
6. All tests are passed

'''
# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
#     'sqlite:///' + os.path.join(BASE_DIR, 'data-test.sqlite')
#     WTF_CSRF_ENABLED = False

# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'data-test-2020-09-28.sqlite')
#     # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'data-dev.sqlite')
#     WTF_CSRF_ENABLED = False

class TestingConfig(Config):
    TESTING = True
    print(BASE_DIR)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
    #     'sqlite://'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI_V1') or \
    # 'sqlite:///' + os.path.join(BASE_DIR, 'data2.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL_NOOOO') or \
    'sqlite:///' + os.path.join(BASE_DIR, 'data-dev.sqlite')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(BASE_DIR, 'data.sqlite')


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}
