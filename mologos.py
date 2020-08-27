import os
from flask_migrate import Migrate, upgrade
from app import create_app, db
# from app.models import Word, Definition, User, Sentence
from app.models import Definition, DictionaryExample, UserExample, User, Word

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Sentence=Sentence)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)