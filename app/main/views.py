from datetime import datetime
import random

from flask import flash, redirect, render_template, request, session, url_for, current_app
from . import main
from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, Word

from flask_login import current_user, login_required

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary, translate_api, bulk_translate, lng_dict, is_english

# These imports are down here as they will get moved to a new file eventually
from ..models import InternationalAccent
from .international_accent_list import international_accent_list
from .starting_data import starting_data

# Homepage
@main.route('/')
def index():
    test_user_email = 'test1234@gmail.com'
    test_user_exists = User.query.filter_by(email=test_user_email).first()

    if not test_user_exists:
        user = User(email= test_user_email,
                username='test1234',
                password='12341234')
        db.session.add(user)
        db.session.commit()

    accent_exists = InternationalAccent.query.filter_by(html_entity='Agrave;').first()

    # Add all the International Accents into the database
    if not accent_exists:
        for item in international_accent_list: 
            id = item['id']
            character = item['character']
            html_entity = item['entitycode']
            alt_code = item['altcode']
            language = item['language']

            special_character = InternationalAccent(id=id, character=character, language=language, alt_code=alt_code, html_entity=html_entity)
            db.session.add(special_character)
                
        db.session.commit()

    test_user = User.query.filter_by(email=test_user_email).scalar()
    # These is a more efficient way to do this with the load_only function https://code-examples.net/en/q/afefd4
    test_user_id = test_user.id
    has_data = UserExample.query.filter_by(user_id=test_user_id).first()
    all_examples = UserExample.query.filter_by(user_id=test_user_id).all()

    # If it's the same length, don't add any more
    if len(starting_data) != len(all_examples):
        # Reset the data by deleting whatever is already there
        UserExample.query.filter_by(user_id=test_user_id).delete()
        for item in starting_data:
            language = item['language']
            word = item['word']
            example = item['example']

            if language == 'english':
                record = UserExample(example=example, word=word, user_id=test_user_id, translation=False, src=None, dst='en')
                db.session.add(record)

            else:
                dst = item['dst']
                record = UserExample(example=example, word=word, user_id=test_user_id, translation=True, src='en', dst=dst)
                db.session.add(record)

        db.session.commit()

    return render_template('index.html')


@main.route('/add', methods=['POST'])
@login_required
def add():
    if request.method == 'POST':
        # Get word from URL query parameters
        word = request.args.get('word')
        # Get posted form input
        user_example = request.form.get('user-example')
    
        # Insert User's Example sentence into database
        record = UserExample(example=user_example, word=word, user_id=current_user.id, translation=False, src=None, dst='en')
        db.session.add(record)
        db.session.commit()

        return redirect(url_for('main.list', lng='en'))


@main.route('/delete/<lng>/<id>')
@login_required
def delete(lng, id):
    UserExample.query.filter_by(id=id).delete() # Hard delete data
    db.session.commit()
    return redirect(url_for('main.list', lng=lng))


# 4: DEFINITION
@main.route('/definition/<word>')
def define(word):
    # Use helper function (found in helpers.py) to look up word in database dictionary    
    local_dictionary_result = lookup_db_dictionary(word)

    if local_dictionary_result is not None:
        return render_template('definition.html', word=local_dictionary_result, source='local')

    # If not found in local dictionary, use the API
    else:
        # Lookup the word in the API helper function, which returns a dict
        api_return_value = lookup_api(word)

        # Return a cannot find if it couldn't be found
        if api_return_value is None:
            flash(f'{word} was not found')
            # TODO => change logic to render a "did you mean X" page (Nice to Have Version2 Feature)
            # TODO => get rid of the word in the url parameters as well

        else:
            word = api_return_value['word']
            pronunciation = api_return_value['pronunciation']
            etymology = api_return_value['etymology']
            definitions = api_return_value['definitions']
            examples = api_return_value['examples']
            source = 'oxford'

            print(f'{word}: {etymology} [{source}]')

            if examples == []:
                print('empty examples')

            for i in examples:
                print(i)

            # Add to local dictionary database
            new_word = Word(word, etymology, pronunciation)
            db.session.add(new_word)
            
            # There is a more efficient way with lastrowid but I can't get it to work right now
            word_query_inefficient = Word.query.filter_by(word=word).one()

            # Get that word ID            
            last_row_id = word_query_inefficient.id


            # Add each of the definitions to the database
            for definition in definitions:
                record = Definition(last_row_id, definition, source)
                db.session.add(record)

            # Add each of the examples to the database
            # NOT WORKING
            for example in examples:
                record = DictionaryExample(last_row_id, example, source)
                db.session.add(record)

            translation_list = bulk_translate(word)

            db.session.commit()
    
        return render_template('definition.html', word=api_return_value, translation_list=translation_list)


@main.route('/definition', methods=['POST'])
def lookup():
    if request.method == 'POST':
        # TODO => parse the word
        word_to_lookup = request.form.get('word-to-lookup')
        return redirect(url_for('main.define', word=word_to_lookup))


# 5: TRANSLATE
@main.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':
        # Check which of the 2 forms has been submitted
        # Form 1 calls the Translation API
        if ('src_tra_1' in request.form): 
            text_to_translate = request.form.get('src_tra_1').strip()
            destination_language = request.form.get('dst_lng_1')
            
            # Translate word with function from helpers.py
            translate_api_output = translate_api(text_to_translate, destination_language)

            # new - 12 nov
            bulki = bulk_translate(text_to_translate)
            print(bulki)
            print(type(bulki))

            # Query database to get the language that the user used most recently
            lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent

            # If not the same, update the most recent
            if destination_language != lng_recent:
                User.query.filter_by(id=current_user.id).update({'lng_recent': destination_language})
                db.session.commit()
                # Reassign the dst language for the page reload
                lng_recent = destination_language
            
            if translate_api_output is None:
                # return error
                return render_template('404.html', dev_text='error with translation helper')
            else:
                return render_template('translate.html', input=text_to_translate, output=translate_api_output, lng_recent=lng_recent)

        # Form 2 saves phrase to database
        else:
            dst = request.form.get('dst_lng_2')
            input = request.form.get('src_tra_2')
            output = request.form.get('dst_tra_2')
            
            record = UserExample(example=output, word=input, user_id=current_user.id, translation=True, src='en', dst=dst)

            db.session.add(record)
            db.session.commit()

            flash(f'This word has been succesfully added to your dictionary!', 'flash-success')
            return redirect(url_for('main.translate'))

        return render_template('translate.html')

    else: # GET
        id = current_user.id
        # Query database to get the language that the user used most recently
        lng_recent = User.query.filter_by(id=id).first().lng_recent
        return render_template('translate.html', lng_recent=lng_recent)


# 6: LIST (returns a list of the user's saved words)
@main.route('/list/<lng>')
@login_required
def list(lng):
    page = request.args.get('page', 1, type=int)
    pagination = UserExample.query.filter_by(user_id=current_user.id, dst=lng).paginate(
        page, per_page=current_app.config['WORDS_PER_PAGE'], error_out=False)
    words = pagination.items
    return render_template('list.html', words=words, english=is_english(lng), 
    lng=lng_dict(lng), endpoint='.list', pagination=pagination)


# 7: EDIT
@main.route('/edit/<lng>/<id>', methods=['GET', 'POST'])
@login_required
def edit(lng, id):
    if request.method == 'POST':
        updated_example = request.form.get('edited-example') 
        last_modified = datetime.utcnow()
        star_bool = int(request.form.get('star_boolean'))
        hide_bool = int(request.form.get('eye_boolean'))

        metadata = UserExample.query.filter_by(user_id=current_user.id, id=id).first()
        metadata.example = updated_example
        metadata.starred = star_bool
        metadata.ignored = hide_bool
        metadata.last_modified = last_modified
        db.session.commit()

        # Redirect to User List
        return redirect(url_for('main.list', lng=lng))

    else: # GET
        word_details = False
        definition = False
        # Word contains etymology and pronunciation
        word = UserExample.query.filter_by(id=id).first()
        if lng == 'en':
            # TODO => make this a lookup on the id rather than the word
            word_details = Word.query.filter_by(word=word.word).first()

            definition = Definition.query.filter_by(word=word.word).first()

            return render_template('edit.html', word=word, word_details=word_details, definition=definition, lng=lng_dict(lng))
        else:
            # Declare list of keyboard accents for language
            keyboard = InternationalAccent.query.filter_by(language=lng).all()

            return render_template('edit.html', word=word, keyboard=keyboard, lng=lng_dict(lng))


# 8: CHALLENGE
@main.route('/challenge/<lng>', methods=['GET', 'POST'])
@login_required
def challenge(lng):
    # ?: RESULTS
    if request.method == 'POST': # Check results
        # Declare arrays to store data from challenge form
        word_ids = request.form.getlist('word_id')
        target_words = request.form.getlist('target_word')
        stars = request.form.getlist('star_boolean')
        skips = request.form.getlist('eye_boolean')
        guesses = request.form.getlist('user_guess')

        # Temp separating eng and foreign, but on v2 they will merge into one model
        if (lng != 'en'):
            words_in_english = request.form.getlist('word-in-english')
        else:
            words_in_english = []

        # Declare empty list to store results
        results = []
        size = len(word_ids)

        for i in range(size):
            # result_bool = 1 if target_words[i].lower() == guesses[i].lower() else 0
            result_bool = 0

            if target_words[i].lower():
                result_bool = target_words[i].lower() == guesses[i].lower()

            metadata = UserExample.query.filter_by(user_id=current_user.id, id=word_ids[i]).first()
            metadata.attempt = UserExample.attempt + 1
            metadata.skip = 1 if skips[i] else 0
            metadata.starred = 1 if stars[i] else 0

            if (result_bool):
                metadata.success = UserExample.success + 1
            else:
                metadata.fail = UserExample.fail + 1

            # Update database
            db.session.commit()

            if (is_english(lng)):
                 word_in_english = ''
            else:
                word_in_english  = words_in_english[i]

            result_dict = {
                'id': word_ids[i],
                # Word (always in English)
                'target_word': target_words[i],
                'starred': stars[i],
                'skipped': skips[i],
                'user_guess': guesses[i],
                'result': result_bool,
                # 'translation': translation,
                # Either English Example or Foriegn Translation
                'example': metadata.example,
                'word_in_english': word_in_english
            }

            results.append(result_dict)

        return render_template('results.html', results=results, lng=lng_dict(lng), english=is_english(lng))

    else: # GET (Show Challenge Page)
        # English view differs from foreign view
        if (is_english(lng)):
            # Filter out words which have been ignored by the user
            words_from_db = UserExample.query.filter_by(user_id=current_user.id, dst=lng, ignored=False).all()
            # Declare list which will hold dictionaries of each word
            words = []

            # Start loop and add words until the list is at the maximum size
            while len(words) <= current_app.config['MAX_SIZE_CHALLENGE'] and len(words_from_db) != 0:
                word = random.choice(words_from_db)

                # After choosing a random word, retrieve the example sentence
                target_word = word.word
                user_sentence = word.example
                word_id = word.id

                # Check if the sentence contains the target word
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

                    # Remove word from list 1 (bucket of words) to avoid duplicates
                    words_from_db.remove(word)
                    # Append to list 2 of words to be rendered
                    words.append(word_dict)

                else:
                    # Skip if word does not appear in target sentence
                    words_from_db.remove(word)

            return render_template('challenge.html', words=words, lng=lng_dict(lng), english=is_english(lng))

        else: # Foreign Language Challenge
            words = UserExample.query.filter_by(user_id=current_user.id, dst=lng).all()
            return render_template('challenge.html', words=words, lng=lng_dict(lng), english=is_english(lng))


