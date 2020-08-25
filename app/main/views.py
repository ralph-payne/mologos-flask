from datetime import datetime
from flask import flash, redirect, render_template, request, session, url_for
from . import main
from .forms import NameForm
from .. import db
from ..models import User, Sentence

# My helpers
from .helpers import lookup_api

@main.route('/', methods=['GET', 'POST'])
def index():
    name = None
    # Create instance of name form class
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        # Store user name in session
        session['name'] = form.name.data
        # Use url for to avoid hardcording of URLs
        return redirect(url_for('main.index'))
    return render_template('index.html', form=form, name=session.get('name'), current_time=datetime.utcnow())


@main.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Get example sentence and word from form
        word = request.form.get('defined-word')
        user_example = request.form.get('user-example')
        user_id = 3238 # Temp hardcode of User Id
        created = datetime.utcnow()
    
        # Original SQL Code (Temp Leave in for Reference)
        # db.execute('INSERT INTO examples (user_id, word, example) VALUES (:user_id, :word, :example)', user_id=user_id, word=word, example=user_example)
        # Use SQL Alchemy to insert into the database
        record = Sentence(user_id, word, user_example, created)
        db.session.add(record)
        db.session.commit()

        # Redirect to find another word? / homepage
        # Temp redirect to homepage after saving word in database
        return redirect(url_for('main.read'))
    
    else:
        return render_template('user.html', name=name)


@main.route('/read', methods=['GET'])
def read():
    # Get the user id from sessions
    # TODO

    # Read all the entries for that user
    words = Sentence.query.all()

    return render_template('user_words.html', words=words)


@main.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        last_modified = datetime.utcnow()
    
        # Edit
        # db.session.add(record)

        # get the id from the form
        id = request.form.get('delete-example')
        
        Sentence.query.filter_by(id=id).delete()
        db.session.commit()      
 
        # Return to same page
        return redirect(url_for('main.read'))
    
    else:      
        # Get the user id from sessions (TODO)

        # Read all the entries for that user
        words = Sentence.query.all()
        db.session.commit()     

        return render_template('user_words.html', words=words)


# TODO => think about what the best dynamic route would look like
@main.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':

        print(id)
        print('posting EDIT')

        # Get value from form
        updated_example = request.form.get('edited-example') 

        last_modified = datetime.utcnow()

        # Update by ID
        Sentence.query.filter_by(id=id).update({'example': updated_example})

        db.session.commit()

        # redirect to read
        return redirect(url_for('main.read'))

    # Get request (Select from db)
    else:      
        # Get the user id from sessions (TODO)

        # Lookup the value from the db
        # SELECT / READ word from db
        # This is sloppy & could be improved with a unique search
        word = Sentence.query.filter_by(id=id).all()
        db.session.commit()

        # Returning index 0 but actually this should be a unique search
        return render_template('edit.html', word=word[0])


# Create route with a dynamic component
@main.route('/definition/<word>')
def define(word):

    # Lookup the word in the API
    api_return_val = lookup_api(word)

    # Return a cannot find if it couldn't be found
    if api_return_val is None:
        flash(f'{word} was not found')
        # TODO => change logic to a different page (maybe a did you mean page?) - 
        # get rid of the word in the url params as well

    return render_template('definition.html', word=api_return_val)


@main.route('/definition', methods=['GET', 'POST'])
def lookup():
    if request.method == 'POST':
        # TODO => parse the word
        word_to_lookup = request.form.get('word-to-lookup')

        return redirect(url_for('main.define', word=word_to_lookup))

    # TODO => Check if I actually need this route??
    else:
        return render_template('definition.html')


@main.route('/account', methods=['GET'])
def account():
    # Get the user id from sessions
    # TODO

    # Query database for user info

    user = 'temp placeholder str'

    return render_template('user_profile.html', user=user, current_time=datetime.utcnow())