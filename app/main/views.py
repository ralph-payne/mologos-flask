from datetime import datetime
import random

import os # For env variables for test user ID

from flask import flash, redirect, render_template, request, session, url_for
from . import main
from .forms import NameForm
from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, Word

from flask_login import current_user

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary

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
        # Use the function url for to avoid hardcoding of URLs
        return redirect(url_for('main.index'))
    return render_template('index.html', form=form, name=session.get('name'), current_time=datetime.utcnow())


@main.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Get word from URL query parameters with request.args.get
        word = request.args.get('word')

        # Get posted form input with use request.form.get
        user_example = request.form.get('user-example')
        
        # Temp hardcode of User Id until Auth Routes are set up
        # It's easier to test when you don't have to keep on logging in after restarting the server
        # user_id = os.environ.get('TEST_USER_ID')
        user_id = current_user.id
    
        # Insert User's Example sentence into the database
        record = UserExample(word, user_example, user_id)
        db.session.add(record)
        # https://docs.sqlalchemy.org/en/13/orm/session_basics.html
        db.session.commit()

        # Redirect to find another word? / homepage
        # Temp redirect to homepage after saving word in database
        return redirect(url_for('main.read'))
    
    else:
        return render_template('user.html', name=name)


# Return the user's example
@main.route('/my_words', methods=['GET'])
def read():
    # TODO: Get the user id from sessions (dependency on setting up Auth routes)
    # user_id = os.environ.get('TEST_USER_ID')
    user_id = current_user.id

    # Read all the entries for that user
    words = UserExample.query.filter_by(user_id=user_id).all()
    # TODO => Check if this is necessary or should I use engine.dispose or does it close automatically?
    # https://stackoverflow.com/questions/21738944/how-to-close-a-sqlalchemy-session
    db.session.close()

    return render_template('user_words.html', words=words)


@main.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        # TODO => Include a last modified field in the User Example model
        last_modified = datetime.utcnow()
    
        # Get the id for the example sentence from the form
        id = request.form.get('delete-example')
        
        # Hard delete data as opposed to soft deleting by toggling boolean
        UserExample.query.filter_by(id=id).delete()
        db.session.commit()      
 
        # Return to same page
        return redirect(url_for('main.read'))
    
    # TODO => Check if this is necessary or whether the delete route should only be a POST route and the GET method should be removed
    else:
        return redirect(url_for('main.read'))


# TODO => think about what the best dynamic route would look like
@main.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        # Get value from form
        updated_example = request.form.get('edited-example') 

        last_modified = datetime.utcnow()

        # Update by ID
        UserExample.query.filter_by(id=id).update({'example': updated_example})
        db.session.close()

        # redirect to read
        return redirect(url_for('main.read'))

    # Get request (Select from db)
    else:      
        # Get the user id from sessions (TODO)

        # Lookup the value from the db
        # SELECT / READ word from db
        # This is sloppy & could be improved with a unique search
        word = UserExample.query.filter_by(id=id).all()
        db.session.close()

        # Returning index 0 but actually this should be a unique search
        return render_template('edit.html', word=word[0])


# Create route with a dynamic component
@main.route('/definition/<word>')
def define(word):
    # Use helper function (helpers.py) to look up word in database dictionary    
    local_dictionary_res = lookup_db_dictionary(word)

    if local_dictionary_res is not None:
        return render_template('definition.html', word=local_dictionary_res, source='local')

    # If not found in local dictionary, use the API
    else:
        # Lookup the word in the API (helper function returns a dict)
        api_return_val = lookup_api(word)

        # Return a cannot find if it couldn't be found
        if api_return_val is None:
            flash(f'{word} was not found')
            # TODO => change logic to render a "did you mean X" page 
            # TODO => get rid of the word in the url parameters as well

        else:
            word = api_return_val['word']
            pronunciation = api_return_val['pronunciation']
            etymology = api_return_val['etymology']
            definitions = api_return_val['definitions']
            examples = api_return_val['examples']
            
            # Temp hardcoding; this should come from a helper function eventually
            source = 'oxford'

            # Add to local dictionary database
            new_word = Word(word, etymology, pronunciation)
            db.session.add(new_word)

            # Add each of the examples to the database
            for definition in definitions:
                record = Definition(word, definition, source)
                db.session.add(record)

            # Add each of the examples to the database
            for example in examples:
                record = DictionaryExample(word, example, source)
                db.session.add(record)

            db.session.commit()
    
        return render_template('definition.html', word=api_return_val, source='API')


@main.route('/definition', methods=['GET', 'POST'])
def lookup():
    if request.method == 'POST':
        # TODO => parse the word
        word_to_lookup = request.form.get('word-to-lookup')

        return redirect(url_for('main.define', word=word_to_lookup))

    # TODO => Check if I actually need this route??
    else:
        return render_template('definition.html')


@main.route('/profile', methods=['GET'])
def profile():
    # current_user is imported from flask_login
    return render_template('user_profile.html', user=current_user)


@main.route('/challenge', methods=['GET', 'POST'])
def challenge():
    user_id = current_user.id
    # user_id = os.environ.get('TEST_USER_ID')
    if request.method == 'POST':
        # If the request.form contains user_guess, it means that the user has clicked on the submit button.
        if ('user_guess' in request.form):          
            # Retrieve the target word (hidden input) and user_guess from the form
            user_guess = request.form.get('user_guess')
            target_word = request.form.get('target_word')
            attempts = int(request.form.get('attempts'))
            star_boolean = int(request.form.get('star_boolean'))

            # Compare with hidden input
            if user_guess == target_word:
                flash('Correct')
                metadata = UserExample.query.filter_by(user_id=user_id, word=target_word).first()
                # Add to the skip column in the database
                metadata.success = UserExample.success + 1

                # If the user has pressed star, toggle the boolean to True in the db
                if (star_boolean):
                    metadata.starred = 1
                if (attempts):
                    metadata.fail = UserExample.fail + attempts
                db.session.commit()
                
            else:
                # The checking is done on the browser side (with JavaScript) so this should never get to this stage
                flash('Error')

        # If the request.form does not contain user_guess, it means that the user has clicked on the skip button
        else:
            # Retrieve data from hidden input
            target_word = request.form.get('target_word_skipped')
            # Update by ID and word
            metadata = UserExample.query.filter_by(user_id=user_id, word=target_word).first()
            # Add to the skip column in the database
            metadata.skip = UserExample.skip + 1
            db.session.commit()

        # Regardless of what button the user pressed, the next page should be another challenge
        return redirect(url_for('main.challenge'))

    # GET
    else:
        # Read all the entries for that user
        words = UserExample.query.filter_by(user_id=user_id).all()
        # TODO => Check if you should db.commit or not
        db.session.close()

        if (len(words) == 0):
            dev_text = 'user has no words in database - TODO make a warning'
            return render_template('404.html', dev_text=dev_text)

        word = random.choice(words)

        # Now that they have a random word, retrieve the example sentence
        target_word = word.word
        user_sentence = word.example
        blank = '____________'

        # TODO => Perform a check to see if the sentence contains the word (there is a chance that the example sentence contains the word in a different word, i.e. an adjective instead of a noun)
        if target_word in user_sentence:
            # The string method replace() returns a copy of the string in which the occurrences of old have been replaced with new
            sentence_with_removed_word = user_sentence.replace(target_word, blank)
            return render_template('challenge.html', target_word=target_word, sentence_with_removed_word=sentence_with_removed_word)

        else:
            pass
            # TODO => There is a problem here that can be sorted with a recursive helper function
            # Temp returning 404 until this has been fixed
            return render_template('404.html')


# Define temp routes to see how the local dictionary is storing words
@main.route('/admin_words', methods=['GET'])
def admin_words():
    words = Word.query.all()
    return render_template('user_words.html', words=words)

@main.route('/admin_dictionary_examples', methods=['GET'])
def admin_dictionary_examples():
    examples = DictionaryExample.query.all()
    return render_template('user_words.html', words=examples)

@main.route('/admin_user_examples', methods=['GET'])
def admin_user_examples():
    examples = UserExample.query.all()
    return render_template('user_words.html', words=examples)

@main.route('/admin_definitions', methods=['GET'])
def admin_definitions():
    definitions = Definition.query.all()
    return render_template('user_words.html', words=definitions)
# -------- end of temp routes ---
