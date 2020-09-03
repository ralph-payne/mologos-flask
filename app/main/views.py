from datetime import datetime
import random

# TODO => Check if this is still required
import os # For env variables for test user ID

from flask import flash, redirect, render_template, request, session, url_for
from . import main
from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, UserTranslation, Word

from flask_login import current_user

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary, translate_api

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Get word from URL query parameters
        word = request.args.get('word')

        # Get posted form input with request.form.get
        user_example = request.form.get('user-example')
        user_id = current_user.id
    
        # Insert User's Example sentence into the database
        record = UserExample(word, user_example, user_id)
        db.session.add(record)
        # https://docs.sqlalchemy.org/en/13/orm/session_basics.html
        db.session.commit()

        # Temp redirect to homepage after saving word in database
        return redirect(url_for('main.my_words'))
    
    else:
        return render_template('user.html', name=name)


# Return the user's example
@main.route('/my_words', methods=['GET'])
def my_words():
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
        
        # Hard delete data
        UserExample.query.filter_by(id=id).delete()
        db.session.commit()      
 
        # Return to same page
        return redirect(url_for('main.my_words'))
    
    # TODO => Check if this is necessary or whether the delete route should only be a POST route and the GET method should be removed
    else:
        return redirect(url_for('main.my_words'))


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
        return redirect(url_for('main.my_words'))

    # Get request (Select from db)
    else:      
        # Lookup the value from the db
        word = UserExample.query.filter_by(id=id).first()
        db.session.close()

        return render_template('edit.html', word=word)


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
            # TODO => change logic to render a "did you mean X" page (Nice to Have Feature)
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

            # Add each of the definitions to the database
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
                # The checking is done on the client side (with JavaScript event listener) so this should never get to this stage
                return render_template('500.html', dev_text='error')

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
            flash('You have no words in your dictionary')
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


@main.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':
        # Check which form has been submitted
        if ('text_to_translate' in request.form): 
            # Translate the word with function from helpers.py
            text_to_translate = request.form.get('text_to_translate')
            dest_language = request.form.get('select_language')

            output = translate_api(text_to_translate, dest_language)

            if output is None:
                # return error
                return render_template('404.html', dev_text='error with translation helper')
            else:
                # Redirect to the same page and include the text_to_translate and the translation
                # Note: this would be better with Ajax but for the moment leave it as is

                # Save to database with user's id etc.
                return render_template('translate.html', input=text_to_translate, output=output)

        # User is trying to save phrase
        else:
            output = request.form.get('translation-result')
            print(request.form)
            # Save to database

            # hardcode while test database
            destination_language = 'pt'
            input = request.form.get('src_hidden_input')
            output = request.form.get('translation_result')
            
            # temp hardcoding id
            user_id = 325458
            # user_id = current_user.id
            if request.form.get('comment'):
                comment = request.form.get('comment')
                # TODO: work out best practice for adding comment in this model
                record = UserTranslation(destination_language, input, output, user_id)
            else:
                record = UserTranslation(destination_language, input, output, user_id)
                      
            db.session.add(record)
            db.session.commit()

            return redirect(url_for('main.translate'))

        # temp option
        return render_template('translate.html')
        # If it's the translation form, call the translate helper

        # If it's the edit the translation page, this is done on the front-end through a JavaScript event handler

        # If it's the add to dictionary form, add the translation to the databse

        # Then redirect to trans translate page

    # GET request
    else:
        return render_template('translate.html')

# TEMP REF User Translation Model
# class UserTranslation(db.Model):
#     __tablename__ = 'user_translation'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#     source_language = db.Column(db.String(2))
#     destination_language = db.Column(db.String(2))
#     input = db.Column(db.Text())
#     output = db.Column(db.Text())
#     comment = db.Column(db.Text())

#     created = db.Column(db.DateTime, default=datetime.utcnow)
#     success = db.Column(db.Integer, default=0)
#     fail = db.Column(db.Integer, default=0)
#     skip = db.Column(db.Integer, default=0)
#     # Level is used to determine the probablity of the user seeing the word on the Challenge
#     level = db.Column(db.Integer, default=0)
#     deleted = db.Column(db.Boolean, default=0)
#     ignored = db.Column(db.Boolean, default=0)
#     starred = db.Column(db.Boolean, default=0)

#     def __init__(self, word, example, user_id):
#         self.word = word
#         self.example = example
#         self.user_id = user_id
