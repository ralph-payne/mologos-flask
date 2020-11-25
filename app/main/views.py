from datetime import datetime
import random

from flask import flash, redirect, render_template, request, session, url_for, current_app
from . import main
from .. import db
from ..models import BulkTranslate, Definition, DictionaryExample, UserExample, User, UserLanguagePreference, Word 

from flask_login import current_user, login_required

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary, translate_api, bulk_translate, bulk_translate_excluding, create_language_dict, is_english, parse_translation_list, to_bool, create_bulk_translate_dict, split_keyboard_into_rows, parse_user_examples_with_split, generate_language_codes

# These imports are down here as they will get moved to a new file eventually
from ..models import InternationalAccent
from .international_accent_list import international_accent_list
from .starting_data import starting_data


@main.route('/init')
def init():
    # INITIALIZE DATABASE WITH STARTING DATA
    test_user_email = 'test1234@gmail.com'
    test_user_exists = User.query.filter_by(email=test_user_email).first()

    # Delete all test data
    InternationalAccent.query.delete()
    UserExample.query.delete()
    Word.query.delete()

    if not test_user_exists:
        user = User(email=test_user_email, 
                    username='test1234',
                    password='12341234')
        db.session.add(user)
        db.session.commit()

    accent_exists = InternationalAccent.query.filter_by(html_entity='Agrave;').first()

    # Add all the International Accents into the database
    if not accent_exists:
        for item in international_accent_list:
            id = int(item['id'])
            character = item['character']
            html_entity = item['entitycode']
            alt_code = item['altcode']
            language = item['language']
            row_num = item['rownum']
            in_use = item['inuse']

            special_character = InternationalAccent(id=id, character=character, language=language, alt_code=alt_code, html_entity=html_entity, row_num=row_num, in_use=in_use)
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
                # Check word already exists
                # use first() instead of one() https://stackoverflow.com/questions/24985989/check-if-one-is-empty-sqlalchemy
                word_already_exists_in_db = Word.query.filter_by(word=word).first()
                if not word_already_exists_in_db:
                    record_word = Word(word=word, etymology='', pronunciation='')
                    db.session.add(record_word)

                    word_query_inefficient = Word.query.filter_by(word=word).one()
                    last_row_id_inefficient = word_query_inefficient.id

                    record_user_example = UserExample(example=example, word=word, word_id=last_row_id_inefficient, user_id=test_user_id, translation=False, src=None, dst='en')

                    db.session.add(record_user_example)

            else:
                dst = item['dst']
                record = UserExample(example=example, word=word, word_id=None, user_id=test_user_id, translation=True, src='en', dst=dst)
                db.session.add(record)

        db.session.commit()

    return render_template('index.html')

# Homepage
@main.route('/')
def index():
    return render_template('index.html')


@main.route('/add', methods=['POST'])
@login_required
def add():
    if request.method == 'POST':
        # Get word from URL query parameters
        word = request.args.get('word')

        # Get posted form input
        user_example = request.form.get('user_example')
        word_id = request.form.get('word_id')
        example_already_exists = to_bool(request.form.get('example_already_exists'))

        if example_already_exists:
            # Insert User's Example sentence into database
            UserExample.query.filter_by(user_id=current_user.id).filter_by(word=word).update({'example': user_example})
        else:
            record = UserExample(example=user_example, word=word, word_id=word_id, user_id=current_user.id, translation=False, src=None, dst='en')
            db.session.add(record)
        
        db.session.commit()

        return redirect(url_for('main.list', lng='en'))


@main.route('/delete/<lng>/<id>')
@login_required
def delete(lng, id):
    UserExample.query.filter_by(id=id).delete() # Hard delete data
    db.session.commit()
    return redirect(url_for('main.list', lng=lng))


# 4: DEFINITION ROUTE
@main.route('/definition/<word>')
def define(word):
    # Use helper function (found in helpers.py) to look up word in database dictionary    
    local_dictionary_result = lookup_db_dictionary(word)
    try:
        result_has_etymology = local_dictionary_result['etymology']
    except:
        result_has_etymology = False

    if local_dictionary_result is not None and result_has_etymology:
        word_id = local_dictionary_result['word_id']

        # Get the user_example if any
        try:
            user_example = UserExample.query.filter_by(user_id=current_user.id, word=word).first()
        except:
            user_example = None

        # Bulk translate
        bulk_translate_from_db = BulkTranslate.query.filter_by(english=word).first()
        translation_list = []

        if bulk_translate_from_db:
            # Use helper function to parse the returned value from the database
            translation_list = parse_translation_list(bulk_translate_from_db)

        return render_template('definition.html', word=local_dictionary_result, user_example=user_example, source='local', translation_list=translation_list)


    # If not found in local dictionary, use the API this means it is a new word and will have to be added to the Word table
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

            word_already_exists_in_db = Word.query.filter_by(word=word).first()

            if not word_already_exists_in_db:
                # Add to local dictionary database
                new_word = Word(word, etymology, pronunciation)
                db.session.add(new_word)
            else:
                # It's not a new word if the user has already done a bulk upload with the word
                # If this is the case, you need to update the existing entry
                # Update the database
                metadata = Word.query.filter_by(word=word).first()
                metadata.etymology = etymology
                metadata.pronuncation = pronunciation
                db.session.commit()
            
            # There is a more efficient way with lastrowid but I can't get it to work right now
            word_query_inefficient = Word.query.filter_by(word=word).one()

            # Add the id to the returned dict (this is the primary key that we be used for all lookups)
            api_return_value['word_id'] = word_query_inefficient.id

            # Add each of the definitions to the database
            for definition in definitions:
                record = Definition(word, definition, source)
                db.session.add(record)

            # Add each of the examples to the database
            for example in examples:
                record = DictionaryExample(word, example, source)
                db.session.add(record)

            # Check that word hasn't been translated already
            bulk_translate_from_db = BulkTranslate.query.filter_by(english=word).first()

            if bulk_translate_from_db:
                # Use helper function to parse the returned value from the database
                translation_list = parse_translation_list(bulk_translate_from_db)
            else:
                # Use the API to look up a Bulk Translation
                translation_list = bulk_translate(word)
                # Parse the returned value in order to store in the BulkTranslate model
                record_bulk_translate = create_bulk_translate_dict(word, translation_list)
                db.session.add(record_bulk_translate)
                db.session.commit()

        # first() returns the first result, or None if there are no results.
        user_example = UserExample.query.filter_by(user_id=current_user.id, word=word).first()

        return render_template('definition.html', word=api_return_value, translation_list=translation_list, user_example=user_example)


@main.route('/definition', methods=['POST'])
def lookup():
    if request.method == 'POST':
        word_to_lookup = request.form.get('word-to-lookup')
        return redirect(url_for('main.define', word=word_to_lookup))


# 5: TRANSLATE
@main.route('/translate/<lng>/', methods=['GET', 'POST'])
def translate(lng):
    if request.method == 'GET':
        id = current_user.id
        # Get the language that the user used most recently
        lng_recent = User.query.filter_by(id=id).first().lng_recent

        # Get the most recent translations from the user
        recent_translations = UserExample.query.filter_by(user_id=current_user.id).filter(UserExample.translation==True).all()

        language_codes = generate_language_codes()

        return render_template('translate.html', lng_recent=lng_recent, recent_translations=recent_translations, language_codes=language_codes)

    else: # POST
        # Form 1 calls the Translation API
        if ('text_to_translate' in request.form): 
            text_to_translate = request.form.get('text_to_translate').strip()
            destination_language_api = request.form.get('destination_language_api')

            # Translate word with function from helpers.py
            translate_api_output = translate_api(text_to_translate, destination_language_api)

            lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent

            # If not the same, update the most recent
            if destination_language_api != lng_recent:
                User.query.filter_by(id=current_user.id).update({'lng_recent': destination_language_api})
                db.session.commit()
                lng_recent = destination_language_api
            
            if translate_api_output is None:
                return render_template('errors/404.html', dev_text='Error with translation helper')
            else:
                return render_template('translate.html', input=text_to_translate, output=translate_api_output, lng_recent=lng_recent)

        # Form 2 saves phrase to database
        else:
            dst = request.form.get('dst_lng_2')
            input = request.form.get('src_tra_2')
            output = request.form.get('destination_language_add_db')
            record = UserExample(example=output, word=input, word_id=None, user_id=current_user.id, translation=True, src='en', dst=dst)
            db.session.add(record)
            db.session.commit()

            flash(f'You have have succesfully added {output} to your dictionary!', 'flash-success')
            return redirect(url_for('main.translate', lng=lng))

        return render_template('translate.html')


# 6: LIST (returns a list of the user's saved words)
@main.route('/list/<lng>')
@login_required
def list(lng):
    language_codes = generate_language_codes()    
    page = request.args.get('page', 1, type=int)
    # https://stackoverflow.com/questions/2128505/difference-between-filter-and-filter-by-in-sqlalchemy
    pagination = UserExample.query.filter_by(user_id=current_user.id, dst=lng).filter(UserExample.word != '').paginate(
        page, per_page=current_app.config['WORDS_PER_PAGE'], error_out=False)
    words = pagination.items

    return render_template('list.html', words=words, english=is_english(lng), lng=create_language_dict(lng), endpoint='.list', pagination=pagination, language_codes=language_codes)


# 7: EDIT
@main.route('/edit/<lng>/<id>', methods=['GET', 'POST'])
@login_required
def edit(lng, id):
    if request.method == 'POST':
        updated_example = request.form.get('edited-example')
        star_bool = int(request.form.get('star_boolean'))
        hide_bool = int(request.form.get('eye_boolean'))
        last_modified = datetime.utcnow()

        metadata = UserExample.query.filter_by(user_id=current_user.id, id=id).first()
        metadata.example = updated_example
        metadata.starred = star_bool
        metadata.ignored = hide_bool
        metadata.last_modified = last_modified
        db.session.commit()

        # Redirect to User List
        return redirect(url_for('main.list', lng=lng))

    else: # GET
        # Word contains etymology and pronunciation
        word = UserExample.query.filter_by(id=id).first()
        if lng == 'en':
            word_details = Word.query.filter_by(id=id).first()
            definition = Definition.query.filter_by(word=word_details.word).first()
            return render_template('edit.html', word=word, word_details=word_details, definition=definition, lng=create_language_dict(lng))
        else:
            # Declare list of keyboard accents for language
            keyboard = InternationalAccent.query.filter_by(language=lng, in_use=1).all()
            keyboard_split_into_rows = split_keyboard_into_rows(keyboard)

            # Check if there already is a bulk translate
            bulk_translate_from_db = BulkTranslate.query.filter_by(english=word.word).first()
            translation_list = []

            if bulk_translate_from_db:
                # Use helper function to parse the returned value from the database
                translation_list = parse_translation_list(bulk_translate_from_db)
            else:
                # Use the API to bulk translate
                translation_list = bulk_translate_excluding(word.word, 'en')
                # Save the results to the database
                record_bulk_translate = create_bulk_translate_dict(word.word, translation_list)
                db.session.add(record_bulk_translate)
                db.session.commit()

            return render_template('edit.html', word=word, keyboard=keyboard_split_into_rows, lng=create_language_dict(lng), translation_list=translation_list)


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

        return render_template('results.html', results=results, lng=create_language_dict(lng), english=is_english(lng))

    else: # GET (Show Challenge Page)
        language_codes = generate_language_codes()
        # English view differs from foreign view
        if (is_english(lng)):
            # Filter out words which have been ignored by the user
            # Filter out any blanks
            words_from_db = UserExample.query.filter_by(user_id=current_user.id, dst=lng, ignored=False).filter(UserExample.word != '').filter(UserExample.example != '').all()
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

            return render_template('challenge.html', words=words, lng=create_language_dict(lng), english=is_english(lng), language_codes=language_codes, endpoint='.challenge')

        else: # Foreign Language Challenge
            words = UserExample.query.filter_by(user_id=current_user.id, dst=lng).all()
            return render_template('challenge.html', words=words, lng=create_language_dict(lng), english=is_english(lng), language_codes=language_codes, endpoint='.challenge')


# ?: PROFILE
@main.route('/profile/<lng>')
@login_required
def profile(lng):
    user_details = User.query.filter_by(id=current_user.id).first()

    # Not in use right now, but it will be on Thu 26 Nov 2020
    languages = UserLanguagePreference.query.filter_by(user_id=current_user.id).all()

    if not languages:
        # Create new
        record_preferences = UserLanguagePreference(user_id=current_user.id)
        db.session.add(record_preferences)
        db.session.commit()

    # if None, create a language prefs for the user
    return render_template('profile.html', user_details=user_details, languages=languages, language_codes=generate_language_codes())


# ?: UPLOAD
@main.route('/upload/<lng>', methods=['GET', 'POST'])
@login_required
def upload(lng):
    if request.method == 'POST':
        uploaded_text = request.form.get('upload_text_area').strip()
        uploaded_language = request.form.get('select_language')
        user_id = current_user.id

        # Count number of newlines
        newlines = len(uploaded_text.split('\n'))
        split_list = uploaded_text.split('\n')

        for example in split_list:
            record_user_example = UserExample(example=example, word=None, word_id=None, user_id=current_user.id, translation=False, src=None, dst='en')
            db.session.add(record_user_example)

        db.session.commit()

        return redirect(url_for('main.select_target_word', lng=lng))
    
    else: # GET Request
        lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent

        return render_template('upload.html', lng_recent=lng_recent)


# ?: UPLOAD
@main.route('/select-target-word/<lng>')
@login_required
def select_target_word(lng):
    # Use user id to find the most recent examples; filter on any without a target word
    user_examples_from_db = UserExample.query.filter_by(user_id=current_user.id).filter_by(word=None).all()

    user_examples = parse_user_examples_with_split(user_examples_from_db)

    return render_template('select_target_word.html', user_examples=user_examples, lng=create_language_dict(lng))


@main.route('/add-target-words/<lng>', methods=['POST'])
@login_required
def add_target_words(lng):
    # Get all the hidden inputs from the form
    target_words = request.form.getlist('target_word')
    user_example_ids = request.form.getlist('user_example_id')

    # Loop through
    for i in range(len(target_words)):
        word = target_words[i]
        id = user_example_ids[i]
        UserExample.query.filter_by(user_id=current_user.id).filter_by(id=id).update({'word': word})

    # Update the database
    db.session.commit()

    return redirect(url_for('main.list', lng=lng))


@main.route('/update_preferences/', methods=['POST'])
@login_required
def update_preferences():
    # Get list of new preferences with request.form.getlist

    # Update database

    # Commit to database

    # Redirect to Profile
    
    # Give alert saying that your preferences have been updated
    return redirect(url_for('main.profile'))