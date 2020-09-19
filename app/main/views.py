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
        return redirect(url_for('main.my_words', lang='eng'))
    
    else:
        return render_template('user.html', name=name)


# Return the user's examples and translated words
@main.route('/my_words/<lang>', methods=['GET'])
# Options for languages: 'eng', 'spa', 'por', 'ger'
def my_words(lang):
    user_id = current_user.id

    if (lang == 'eng'):
        language = 0
    else:
        language = lang

    if language == 0:
        # Read all the entries for that user
        words = UserExample.query.filter_by(user_id=user_id).all()
    else:
        # Read all the entries for that user
        # Filter on the language as well
        words = UserTranslation.query.filter_by(user_id=user_id).all()

    return render_template('user_words.html', words=words, language=language)


@main.route('/delete<id>', methods=['GET'])
def delete(id):
    if request.method == 'GET':
        # TODO => Include a last modified field in the User Example model
        # last_modified = datetime.utcnow()
    
        # Get the id for the example sentence from the form
        # id = request.form.get('delete-example')
        
        # Hard delete data
        UserExample.query.filter_by(id=id).delete()
        db.session.commit()
 
        # Return to same page
        return redirect(url_for('main.my_words', lang='eng'))


# TODO => think about what the best dynamic route would look like
@main.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        # Get value from form
        updated_example = request.form.get('edited-example') 
        last_modified = datetime.utcnow()

        # Update by ID
        UserExample.query.filter_by(id=id).update({'example': updated_example})
        db.session.commit()

        # Redirect to User List
        return redirect(url_for('main.my_words', lang='eng'))

    else: # GET    
        # Lookup the value from the db
        word = UserExample.query.filter_by(id=id).first()

        return render_template('edit.html', word=word)


# Create route with a dynamic component
@main.route('/definition/<word>')
def define(word):
    # Use helper function (found in helpers.py) to look up word in database dictionary    
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
            # TODO => change logic to render a "did you mean X" page (Nice to Have Version2 Feature)
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


@main.route('/definition', methods=['POST'])
def lookup():
    if request.method == 'POST':
        # TODO => parse the word
        word_to_lookup = request.form.get('word-to-lookup')
        return redirect(url_for('main.define', word=word_to_lookup))


@main.route('/profile', methods=['GET'])
def profile():
    return render_template('user_profile.html', user=current_user)


@main.route('/challenge', methods=['GET', 'POST'])
def challenge():
    user_id = current_user.id
    if request.method == 'POST':
        # Convert Immutable Dict into list
        word_ids = request.form.getlist('word_id')
        target_words = request.form.getlist('target_word')
        stars = request.form.getlist('star_boolean')
        skips = request.form.getlist('eye_boolean')
        guesses = request.form.getlist('user_guess')

        size = len(word_ids)

        # Declare empty list to store results
        results = []

        for i in range(size):
            result_bool = 1 if target_words[i].lower() == guesses[i].lower() else 0

            # Create dictionary
            result_dict = {
                'id': word_ids[i], 
                'target_word': target_words[i],
                'starred': stars[i],
                'skipped': skips[i],
                'user_guess': guesses[i],
                'result': result_bool
            }
            results.append(result_dict)

            # Query database
            metadata = UserExample.query.filter_by(user_id=user_id, word=target_words[i]).first()

            # Update database
            # TODO
            if (result_bool):
                metadata.success = UserExample.success + 1
            else:
                metadata.fail = UserExample.fail + 1

            if (skips[i]):
                metadata.skip = 1

            if (stars[i]):
                metadata.starred = 1

            db.session.commit()

        return render_template('results.html', list_of_results=results)

    # GET
    else:
        # Read all the entries for that user
        words = UserExample.query.filter_by(user_id=user_id).all()
        # TODO => Check if you should db.commit or not

        # Declare variable to hold maximum number of questions for Challenge page
        max = 0

        if (len(words) == 0):
            flash('You have no words in your dictionary')
            return render_template('404.html', dev_text=dev_text)
        elif (len(words) > 4):
            # Create a list of dictionaries
            max = 5
        else:
            max = len(words)

        # Declare list which will hold dictionaries of each word
        list_of_words = []

        # Start loop and add words until the list is at the maximum size
        while len(list_of_words) < max:
            word = random.choice(words)
            # TODO => check if this word is already in the list chosen

            # Now that they have a random word, retrieve the example sentence
            target_word = word.word
            user_sentence = word.example
            word_id = word.id

            # Check if the sentence contains the word (there is a chance that the example sentence contains the word in a different word, i.e. an adjective instead of a noun)
            if target_word in user_sentence:
                # Find position of target word in sentence
                pos = user_sentence.find(target_word)
                word_length = len(target_word)
                sentence_length = len(user_sentence)

                first_half_sentence = user_sentence[0:pos]
                second_half_sentence = user_sentence[(pos+word_length):sentence_length]

                word_dict = {
                    'id': word_id,
                    'target_word': target_word,
                    'first_half_sentence': first_half_sentence,
                    'second_half_sentence': second_half_sentence
                }

                # Remove word from list 1 (bucket) to avoid duplicates
                words.remove(word)

                # Append to list of words
                list_of_words.append(word_dict)

            else:
                # TODO: Create logic if the word does not appear in the target sentence
                pass

        return render_template('challenge.html', list_of_words=list_of_words)


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
            # Save to database

            # hardcode while test database
            destination_language = 'pt'
            input = request.form.get('src_hidden_input')
            output = request.form.get('translation_result')
            
            # temp hardcoding id
            user_id = current_user.id
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

        # If it's the edit to the translation page, this is done on the front-end through a JavaScript event handler

        # If it's the add to dictionary form, add the translation to the databse

        # Then redirect to trans translate page

    # GET request
    else:
        return render_template('translate.html')


# -------- start of temp routes ---------- #
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
# -------- end of temp routes ---------- #
