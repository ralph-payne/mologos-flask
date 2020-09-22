from datetime import datetime
import random

from flask import flash, redirect, render_template, request, session, url_for
from . import main
from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, UserTranslation, Word

from flask_login import current_user

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary, translate_api

# Homepage
@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        # Get word from URL query parameters
        word = request.args.get('word')

        # Get posted form input with request.form.get
        user_example = request.form.get('user-example')
        user_id = current_user.id
    
        # Insert User's Example sentence into database
        record = UserExample(word, user_example, user_id)
        db.session.add(record)
        db.session.commit()

        return redirect(url_for('main.my_words', lng='en'))


@main.route('/my_words/<lng>', methods=['GET'])
# Options for languages: 'en', 'es', 'pt', 'de', 'it'
def my_words(lng):
    user_id = current_user.id
    english_view = False

    # English view differs
    if (lng == 'en'):
        english_view = True
        words = UserExample.query.filter_by(user_id=user_id).all()
    else:
        # Filter on the language and read all the entries for the user
        words = UserTranslation.query.filter_by(user_id=user_id, destination_language=lng).all()

    return render_template('user_words.html', words=words, english_view=english_view, lng=lng)


# Only GET requests with delete
@main.route('/delete/<lng>/<id>')
def delete(lng, id):
    if lng == 'en':
        # TODO => Include a last modified field in the User Example model
        # last_modified = datetime.utcnow()
    
        # Get the id for the example sentence from the form
        # id = request.form.get('delete-example')
        print('--req--')
        print(request.args)
        for key, value in request.args.items():
            print(key, ' : ', value)
        print('--^^req^^--')
        # Hard delete data
        UserExample.query.filter_by(id=id).delete()
        db.session.commit()
 
        # Return to same page
        return redirect(url_for('main.my_words', lng='en'))
    # Foreign language
    else:
        UserTranslation.query.filter_by(id=id).delete()
        db.session.commit()
 
        # Return to same page
        return redirect(url_for('main.my_words', lng=lng))

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
        return redirect(url_for('main.my_words', lng='en'))

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

    # If not found in local dictionary, use the APIG
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


@main.route('/challenge/<lng>', methods=['GET', 'POST'])
def challenge(lng):
    user_id = current_user.id
    english_view = False
    # POST request so check results
    if request.method == 'POST':
        # Convert Immutable Dict into list

        print('2123')

        # Declare arrays to store data from forms
        word_ids = request.form.getlist('word_id')
        target_words = request.form.getlist('target_word')
        stars = request.form.getlist('star_boolean')
        skips = request.form.getlist('eye_boolean')
        guesses = request.form.getlist('user_guess')

        # Declare empty list to store results and get length of words submitted
        results = []
        size = len(word_ids)

        # if 'en'
        
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

            if (lng == 'en'):
                # Query database
                metadata = UserExample.query.filter_by(user_id=user_id, id=word_ids[i]).first()
                english_view = True
                # Update database
                if (result_bool):
                    metadata.success = UserExample.success + 1
                else:
                    metadata.fail = UserExample.fail + 1
            else: # Non English lng
                metadata = UserTranslation.query.filter_by(user_id=user_id, id=word_ids[i]).first()
                if (result_bool):
                    metadata.success = UserTranslation.success + 1
                else:
                    metadata.fail = UserTranslation.fail + 1

            if (skips[i]):
                metadata.skip = 1

            if (stars[i]):
                metadata.starred = 1

            db.session.commit()
        print('---res below --')
        print(results)

        return render_template('results.html', list_of_results=results, lng=lng, english_view=english_view)

    # GET
    else:
        # Look at lang
        english_view = False

        # English view differs
        if (lng == 'en'):
            english_view = True
            words_from_db = UserExample.query.filter_by(user_id=user_id).all()
            # Read all the entries for that user
            words_from_db = UserExample.query.filter_by(user_id=user_id).all()
            # TODO => Check if you should db.commit or not

            # Declare variable to hold maximum number of questions for Challenge page
            max = 0

            if (len(words_from_db) == 0):
                flash('You have no words_from_db in your dictionary')
                return render_template('404.html', dev_text=dev_text)
            elif (len(words_from_db) > 4):
                # Create a list of dictionaries
                max = 5
            else:
                max = len(words_from_db)

            # Declare list which will hold dictionaries of each word
            words = []

            # Start loop and add words until the list is at the maximum size
            while len(words) < max:
                word = random.choice(words_from_db)
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
                    words_from_db.remove(word)

                    # Append to list 2 of words to be rendered
                    words.append(word_dict)

                else:
                    # TODO: Create logic if the word does not appear in the target sentence
                    pass

            print('challenge -en')
            print(words)
            return render_template('challenge.html', words=words, english_view=english_view, lng=lng)

        else:
            print('challenge foreign')

            words = UserTranslation.query.filter_by(user_id=user_id, destination_language=lng).all()
            print(words)

            return render_template('challenge.html', words=words, english_view=english_view, lng=lng)
            



# Options for languages: 'eng', 'spa', 'por', 'ger', 'ita'
@main.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':

        # Check which of the 2 forms has been submitted
        if ('src_tra_1' in request.form): 
            # Translate the word with function from helpers.py
            text_to_translate = request.form.get('src_tra_1')
            dst_language = request.form.get('dst_lng_1')

            output = translate_api(text_to_translate, dst_language)
            id = current_user.id

            # Query database to get the language that the user used most recently
            lng_recent = User.query.filter_by(id=id).first().lng_recent

            # If not the same, update the most recent
            if dst_language != lng_recent:
                User.query.filter_by(id=id).update({'lng_recent': dst_language})
                db.session.commit()
                print(dst_language)
                print('dst langa and recent lang no match so commited ^^')
                # Reassign the dst language for the page reload
                lng_recent = dst_language
            
            if output is None:
                # return error
                return render_template('404.html', dev_text='error with translation helper')
            else:
                # Redirect to the same page and include the text_to_translate and the translation
                # Note: this would be better with Ajax but for the moment leave it as is

                # Save to database with user's id etc.
                print(lng_recent)
                print('reloading the page again')
                return render_template('translate.html', input=text_to_translate, output=output, lng_recent=lng_recent)

        # User has submitted form 2 (to save phrase to database)
        else:
            output = request.form.get('translation-result')
            # Save to database
            print('saving below to db')
            print(request.form)
            # hardcode while test database
            destination_language = request.form.get('dst_lng_2')
            input = request.form.get('src_tra_2')
            output = request.form.get('dst_tra_2')
            
            user_id = current_user.id
            # Don't currenlty have comments
            if request.form.get('comment'):
                comment = request.form.get('comment')
                # TODO: work out best practice for adding comment in this model
                record = UserTranslation(destination_language, input, output, user_id)
            else:
                record = UserTranslation(destination_language, input, output, user_id)

            # Also add the last language used to the database
            # Check what the last language used was

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
        id = current_user.id
        # Query database to get the language that the user used most recently
        lng_recent = User.query.filter_by(id=id).first().lng_recent
        print(lng_recent)
        print('get ^^ lang --')
        return render_template('translate.html', lng_recent=lng_recent)
