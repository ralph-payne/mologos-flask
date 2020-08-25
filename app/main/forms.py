# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class NameForm(FlaskForm):
    # Data required ensures that form is not submitted empty
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')