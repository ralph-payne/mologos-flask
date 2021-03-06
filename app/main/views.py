from datetime import datetime
import random

from flask import flash, redirect, render_template, request, session, url_for, current_app
from . import main
from .. import db
from ..models import BulkTranslate, Definition, DictionaryExample, UserExample, User, UserLanguagePreference, Word 

from flask_login import current_user, login_required

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_definition_api, lookup_db_dictionary, translate_api, bulk_translate, create_language_dict, is_english, parse_translation_list, to_bool, create_bulk_translate_dict, split_keyboard_into_rows, parse_user_examples_with_split, generate_language_codes, map_users_prefs_onto_langs,  convert_translation_dict_to_two_letters, split_user_sentence

# These imports are down here as they will get moved to a new file eventually
from ..models import InternationalAccent
from .international_accent_list import international_accent_list
from .starting_data import starting_data


# Homepage
@main.route('/')
def index():
    return render_template('index.html')


# ADD
@main.route('/add', methods=['POST'])
@login_required
def add():
    if request.method == 'POST':
        # Get word from URL query parameters
        word = request.args.get('word')

        # Get posted form input
        user_example = request.form.get('user_example')
        example_already_exists = to_bool(request.form.get('example_already_exists'))

        if example_already_exists:
            # Insert User's Example sentence into database
            UserExample.query.filter_by(user_id=current_user.id).filter_by(word=word).update({'example': user_example})
        else:
            record = UserExample(example=user_example, word=word, user_id=current_user.id, translation=False, src=None, dst='en')
            db.session.add(record)
        
        db.session.commit()

        return redirect(url_for('main.list', lng='en'))

# Use POST for destructive actions such as creation (I'm aware of the irony), editing, and deletion, because you can't hit a POST action in the address bar of your browser. Use GET when it's safe to allow a person to call an action. So a URL like: "http://myblog.org/admin/posts/delete/357" Should bring you to a conf
# https://stackoverflow.com/questions/46585/when-do-you-use-post-and-when-do-you-use-get
# POST is also more secure than GET, because you aren't sticking information into a URL. And so using GET as the method for an HTML form that collects a password or other sensitive information is not the best idea.
# One final note: POST can transmit a larger amount of information than GET. 'POST' has no size restrictions for transmitted data, whilst 'GET' is limited to 2048 characters.


@main.route('/delete/', methods=['POST'])
@login_required
def delete():
    id = request.form.get('word_id')
    lng = request.form.get('lng')
    current_page = request.form.get('current_page')

    UserExample.query.filter_by(id=id).delete()
    db.session.commit()
    db.session.close()

    if current_page == 'main.translate':
        return redirect(url_for('main.translate'))
    else:
        return redirect(url_for('main.list', lng=lng))


# 4: DEFINITION ROUTE
@main.route('/definition/<word>', methods=['GET'])
def define(word):
    # Use helper function (found in helpers.py) to look up word in database dictionary    
    local_dictionary_result = lookup_db_dictionary(word)

    if local_dictionary_result is not None and local_dictionary_result['etymology'] and current_user.is_authenticated:
        word_id = local_dictionary_result['word_id']
        user_example = UserExample.query.filter_by(user_id=current_user.id, word=word).first()
        
        # Bulk translate
        bulk_translate_from_db = BulkTranslate.query.filter_by(english=word).first()
        db.session.close()

        translation_dict = parse_translation_list(bulk_translate_from_db, word, current_user.id)
        translation_dict_two_letters = convert_translation_dict_to_two_letters(translation_dict)

        return render_template('definition.html', word=local_dictionary_result, user_example=user_example, source='local', translation_dict=translation_dict_two_letters)

    # If not found in local dictionary, use the API and add new word Word table in db
    else:
        print(f'{word} was not found in local dictionary so going to use API')
        api_return_value = lookup_definition_api(word)

        if api_return_value is None:
            flash(f'{word} was not found')
            return redirect(url_for('main.index'))

        else:
            # Word was found by API
            word = api_return_value['word']
            pronunciation = api_return_value['pronunciation']
            print(f'{pronunciation} is the pronunciation of {word}')
            etymology = api_return_value['etymology']
            definitions = api_return_value['definitions']
            examples = api_return_value['examples']
            word_already_exists_in_db = Word.query.filter_by(word=word).first()

            if not word_already_exists_in_db:
                # Add to local dictionary database
                new_word = Word(word, etymology, pronunciation)
                db.session.add(new_word)
                db.session.commit()
            else:
                # It's not a new word if the user has already done a bulk upload with the word
                # If this is the case, you need to update the existing entry. Update the database
                Word.query.filter_by(word=word).update({'etymology': etymology})
                Word.query.filter_by(word=word).update({'pronunciation': pronunciation})

            # There is a more efficient way with lastrowid but I can't get it to work right now
            word_query_inefficient = Word.query.filter_by(word=word).one()
            # Add the id to the returned dict (this is the primary key that we be used for all lookups)
            api_return_value['word_id'] = word_query_inefficient.id

            # Add each of the definitions to the database
            for definition in definitions:
                record = Definition(word, definition, 'oxford')
                db.session.add(record)

            # Add each of the examples to the database
            for example in examples:
                record = DictionaryExample(word, example, 'oxford')
                db.session.add(record)

            db.session.commit()

            # Check that word hasn't been translated already
            bulk_translate_from_db = BulkTranslate.query.filter_by(english=word).first()
            print(f'Checking that {word} has been translated already: {bulk_translate_from_db}')

            translation_dict_two_letters = {}
            db.session.close()

            if bulk_translate_from_db is None and current_user.is_authenticated:
                print('inside of the bulk translation sideshow')
                translation_dict = bulk_translate(word, current_user.id)
            else:
                translation_dict = parse_translation_list(bulk_translate_from_db, word, current_user.id)

            if current_user.is_authenticated:
                translation_dict_two_letters = convert_translation_dict_to_two_letters(translation_dict)
                user_example = UserExample.query.filter_by(user_id=current_user.id, word=word).first()
                db.session.close()
            else:
                user_example = None

        return render_template('definition.html', word=api_return_value, translation_dict=translation_dict_two_letters, user_example=user_example)


@main.route('/definition', methods=['POST'])
def lookup():
    if request.method == 'POST':
        word_to_lookup = request.form.get('word-to-lookup')
        return redirect(url_for('main.define', word=word_to_lookup))


# 5: TRANSLATE
@main.route('/translate/', methods=['GET', 'POST'])
def translate():
    if request.method == 'GET':
        get_args_lng = request.args.get('lng')
        print(get_args_lng)

        if get_args_lng is not None:
            User.query.filter_by(id=current_user.id).update({'lng_recent': get_args_lng})
            db.session.commit()

        # Get the language that the user used most recently
        lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent
        max_size = current_app.config['RECENT_TRANSLATIONS_LIMIT']

        # Get the most recent translations from the user
        recent_translations = UserExample.query.filter_by(user_id=current_user.id).filter(UserExample.translation==True).order_by(UserExample.created.desc()).limit(max_size).all()
        db.session.close()

        mapped_languages = map_users_prefs_onto_langs(generate_language_codes(), current_user.id)

        return render_template('translate.html', lng_recent=lng_recent, recent_translations=recent_translations, language_codes=mapped_languages)

    else: # POST
        # Form 1 calls the Translation API
        if ('text_to_translate' in request.form): 
            text_to_translate = request.form.get('text_to_translate').strip()
            destination_language_api = request.form.get('destination_language_api')
            lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent

            # Translate word with function from helpers.py
            translate_api_output = translate_api(text_to_translate, destination_language_api)

            if translate_api_output is None:
                return render_template('errors/404.html', dev_text='Error with translation helper')

            # If not the same, update the most recent
            if destination_language_api != lng_recent:
                User.query.filter_by(id=current_user.id).update({'lng_recent': destination_language_api})
                db.session.commit()
                lng_recent = destination_language_api
            
            # Get the most recent translations from the user
            recent_translations = UserExample.query.filter_by(user_id=current_user.id).filter(UserExample.translation==True).order_by(UserExample.created.desc()).limit(10).all()

            mapped_languages = map_users_prefs_onto_langs(generate_language_codes(), current_user.id)

            return render_template('translate.html', input=text_to_translate, output=translate_api_output, lng_recent=lng_recent, recent_translations=recent_translations, language_codes=mapped_languages)

        # Form 2 saves phrase to database
        else:
            destination_language_add_db = request.form.get('destination_language_add_db')
            most_recent_translation_lang = request.form.get('most_recent_translation_lang')

            text_in_english = request.form.get('text_in_english_add_db')
            translation_output_add_db = request.form.get('translation_output_add_db')

            record = UserExample(example=translation_output_add_db, word=text_in_english, user_id=current_user.id, translation=True, src='en', dst=most_recent_translation_lang)

            db.session.add(record)
            db.session.commit()
            db.session.close()

            flash(f'You have have succesfully added {translation_output_add_db} to your dictionary!', 'flash-success')
            return redirect(url_for('main.translate'))

        return render_template('translate.html')


# 6: LIST (returns a list of the user's saved words)
@main.route('/list/<lng>')
@login_required
def list(lng):
    mapped_languages = map_users_prefs_onto_langs(generate_language_codes(), current_user.id)  
    page = request.args.get('page', 1, type=int)
    # https://stackoverflow.com/questions/2128505/difference-between-filter-and-filter-by-in-sqlalchemy
    pagination = UserExample.query.filter_by(user_id=current_user.id, dst=lng).filter(UserExample.word != '').paginate(
        page, per_page=current_app.config['WORDS_PER_PAGE'], error_out=False)
    words = pagination.items

    return render_template('list.html', words=words, english=is_english(lng), lng=create_language_dict(lng), endpoint='.list', pagination=pagination, language_codes=mapped_languages, user_id=current_user.id)


@main.route('/update_word/<lng>/<id>', methods=['POST'])
@login_required
def update_word(lng, id):
    metadata = UserExample.query.filter_by(user_id=current_user.id, id=id).first()

    metadata.example = request.form.get('edited-example')
    metadata.starred = int(request.form.get('star_boolean'))
    metadata.ignored = int(request.form.get('eye_boolean'))
    metadata.last_modified = datetime.utcnow()

    db.session.commit()
    db.session.close()

    return redirect(url_for('main.list', lng=lng))


# 7: EDIT
@main.route('/edit/<lng>/<id>', methods=['GET'])
@login_required
def edit(lng, id):
    # Word contains etymology and pronunciation
    user_example = UserExample.query.filter_by(id=id).first()
    db.session.close()

    if lng == 'en':
        word_details = Word.query.filter_by(id=id).first()
        db.session.close()
        
        try:
            definition = Definition.query.filter_by(word=word_details.word).first()
            db.session.close()
        except:
            definition = 'Temporarily using a try and except to prevent None Type error'

        return render_template('edit.html', word=word, word_details=word_details, definition=definition, lng=create_language_dict(lng), is_english=is_english(lng))
        # This should just be a redirect to the define page

    else:
        # Declare list of keyboard accents for language
        keyboard = InternationalAccent.query.filter_by(language=lng, in_use=1).all()
        keyboard_split_into_rows = split_keyboard_into_rows(keyboard)

        # Check if there already is a bulk translate
        bulk_translate_from_db = BulkTranslate.query.filter_by(english=user_example.word).first()
        db.session.close()

        if bulk_translate_from_db:
            # Use helper function to parse the returned value from the database
            translation_dict = parse_translation_list(bulk_translate_from_db, user_example.word, current_user.id)
        else:
            # Use the API to bulk translate
            translation_dict = bulk_translate(user_example.word, current_user.id)
            # This returns a list when we actually want a dictionary
            # Save the results to the database
            record_bulk_translate = create_bulk_translate_dict(user_example.word, translation_dict)
            db.session.add(record_bulk_translate)
            db.session.commit()
            db.session.close()

        # Convert translation_dict
        # Helper function takes the translation dictionary and converts the keys from
        # long names (spanish) to the two letter equivalent

        translation_dict_two_letters = convert_translation_dict_to_two_letters(translation_dict)

        return render_template('edit.html', word=user_example, keyboard=keyboard_split_into_rows, lng=create_language_dict(lng), translation_dict=translation_dict_two_letters)


# Can't use endpoint reserverd word (TypeError: url_for() got multiple values for argument 'endpoint')
@main.route('/update_star_or_hide/<lng>/<id>/<endpoint_1>/<star_or_hide>/', methods=['GET'])
def update_star_or_hide(lng, id, endpoint_1, star_or_hide):
    if int(star_or_hide) == 0:
        is_ignored = UserExample.query.filter_by(id=id).first().ignored

        if is_ignored:
            UserExample.query.filter_by(id=id).update({'ignored': False})
        else:
            UserExample.query.filter_by(id=id).update({'ignored': True})

    if int(star_or_hide) == 1:
        is_starred = UserExample.query.filter_by(id=id).first().starred


        if is_starred:
            UserExample.query.filter_by(id=id).update({'starred': False})
        else:
           UserExample.query.filter_by(id=id).update({'starred': True})

    db.session.commit()
    db.session.close()

    if endpoint_1 == 'main.challenge':
        return redirect(url_for('main.challenge', lng=lng))

    if endpoint_1 == 'main.edit':
        return redirect(url_for('main.edit', lng=lng, id=id))

    else:
        word = UserExample.query.filter_by(id=id).first().word
        db.session.close()
        return redirect(url_for('main.define', word=word))


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
        words_in_english = []

        if (lng != 'en'):
            words_in_english = request.form.getlist('word-in-english')
            
        results = []

        for i in range(len(word_ids)):
            if target_words[i].lower() == guesses[i].lower():
                result_bool = 1
            else:
                result_bool = 0

            # Temp flush
            db.session.close()

            metadata = UserExample.query.filter_by(user_id=current_user.id, id=word_ids[i]).first()
            metadata.attempt = UserExample.attempt + 1
            metadata.skip = 1 if skips[i] else 0
            metadata.starred = 1 if stars[i] else 0

            if (result_bool):
                metadata.success = metadata.success + 1
            else:
                metadata.fail = metadata.fail + 1

            split_user_sentence_dict = split_user_sentence(metadata)

            result_dict = {
                'id': word_ids[i],
                'target_word': target_words[i],
                'starred': stars[i],
                'skipped': skips[i],
                'user_guess': guesses[i],
                'result': result_bool,
                'example': metadata.example, # Either English Example or Foriegn Translation
                'fail': metadata.fail,
                'success': metadata.success,
                'word_in_english': '',
                'split_user_sentence': split_user_sentence_dict
            }

            db.session.commit()
            db.session.close()

            if not is_english(lng):
                result_dict['word_in_english']  = words_in_english[i]

            results.append(result_dict)

        return render_template('results.html', results=results, lng=create_language_dict(lng), english=is_english(lng))

    else: # GET (Show Challenge Page)
        mapped_languages = map_users_prefs_onto_langs(generate_language_codes(), current_user.id)
        max_size_challenge = current_app.config['MAX_SIZE_CHALLENGE']

        # English view differs from foreign view
        if (is_english(lng)):
            # Filter out words which have been ignored by the user | Filter out blanks
            words_from_db = UserExample.query.filter_by(user_id=current_user.id, dst=lng, ignored=False).filter(UserExample.word != '').filter(UserExample.example != '').all()

            # Declare list which will hold dictionaries of each word
            words = []

            # Start loop and add words until the list is at the maximum size
            while len(words) <= max_size_challenge and len(words_from_db) != 0:
                word = random.choice(words_from_db)

                split_user_sentence_dict = split_user_sentence(word)

                # Check if the sentence contains the target word
                if split_user_sentence_dict:
                    # Remove word from list 1 (bucket of words) to avoid duplicates
                    words_from_db.remove(word)
                    # Append to list 2 of words to be rendered
                    words.append(split_user_sentence_dict)

                else:
                    # Skip if word does not appear in target sentence
                    words_from_db.remove(word)

            return render_template('challenge.html', words=words, lng=create_language_dict(lng), english=is_english(lng), language_codes=mapped_languages, endpoint='.challenge')

        else: # Foreign Language Challenge
            words = UserExample.query.filter_by(user_id=current_user.id, dst=lng).limit(max_size_challenge).all()
            return render_template('challenge.html', words=words, lng=create_language_dict(lng), english=is_english(lng), language_codes=mapped_languages, endpoint='.challenge')


# UPLOAD TRANSLATIONS
# This route saves translations that have been "bulked uploaded" by the user
@main.route('/upload/upload_translations/', methods=['POST'])
@login_required
def upload_translations():
        list_of_eng_words_for_bulk_upload = request.form.get('upload_text_area_left').strip()
        upload_target_word_right_84 = request.form.get('upload_target_word_right').strip()
        uploaded_language = request.form.get('select_language')
        user_id = current_user.id

        num_eng_words_to_upload = len(list_of_eng_words_for_bulk_upload.split('\n'))
        list_of_english_words_split = list_of_eng_words_for_bulk_upload.split('\n')
        word_limit = current_app.config['UPLOAD_MAXIMUM_CONSTANT']

        if num_eng_words_to_upload > word_limit:
            flash(f'You cannot upload more than {word_limit} words at a time')
            return redirect(url_for('main.upload'))

        # Check the number of target words is the same
        num_foreign_words_to_upload = len(upload_target_word_right_84.split('\n'))
        list_of_foreign_words_split = upload_target_word_right_84.split('\n')

        # If target words is blank, skip
        if num_foreign_words_to_upload == 0:
            pass
            # TODO, you will have to use Google Translate to bulk translate these
            flash(f'Please upload the translations as well')
            return redirect(url_for('main.upload'))
        elif num_foreign_words_to_upload != num_eng_words_to_upload:
            flash(f'The number of examples ({num_eng_words_to_upload}) must match the number of Target Words ({num_foreign_words_to_upload})')
            return redirect(url_for('main.upload'))
        
        # Continue as you do not need to do the English check of seeing if the target word is in the target sentence as these are translations
        # If we get therought the above if else statement, it means that the words have been uploaded successfully.
        # We can then loop through them all and add them to the database
        for i in range(num_eng_words_to_upload):
            target_word_to_add_to_db_828 = list_of_foreign_words_split[i].strip()
            foreign_word8137_to_add_to_db = list_of_english_words_split[i].strip()

            # TODO => Word ID is redundant? Or is it?? Check this!
            # You will clobber any previously loaded User Examples so you should find a work around for that
            record_user_example = UserExample(example=target_word_to_add_to_db_828, word=foreign_word8137_to_add_to_db, user_id=current_user.id, translation=True, src='en', dst=uploaded_language)
            db.session.add(record_user_example)
            
        db.session.commit()
        db.session.close()

        # Redirect to the list page.
        return redirect(url_for('main.list', lng=uploaded_language))


# ?: UPLOAD
@main.route('/upload/upload_english/', methods=['POST'])
@login_required
def upload_english():
    if request.method == 'POST':
        uploaded_text_with_sentences = request.form.get('upload_text_area_left').strip()
        upload_target_word_right = request.form.get('upload_target_word_right').strip()
        uploaded_language = request.form.get('select_language')

        # Count number of newlines_example_sentences_70
        newlines_example_sentences_70 = len(uploaded_text_with_sentences.split('\n'))
        split_list = uploaded_text_with_sentences.split('\n')
        word_limit = current_app.config['UPLOAD_MAXIMUM_CONSTANT']

        if newlines_example_sentences_70 > word_limit:
            flash(f'You cannot upload more than {word_limit} words at a time')
            return redirect(url_for('main.upload'))

        # Check the number of target words is the same
        length_target_words_71 = len(upload_target_word_right.split('\n'))
        list_of_target_words_72 = upload_target_word_right.split('\n')

        # If target words is blank, skip
        if length_target_words_71 == 0:
            pass
        elif length_target_words_71 != newlines_example_sentences_70:
            flash(f'The number of examples ({newlines_example_sentences_70}) must match the numbasdf aer of Target Words ({length_target_words_71})')
            return redirect(url_for('main.upload'))
        else:
            # Run a loop to see that each word is present in each sentence
            for i in range(length_target_words_71):
                target_word_to_search = list_of_target_words_72[i].strip().lower()
                sentence_which_should_contain_target_word = split_list[i].lower()

                # is this in that?
                if target_word_to_search in sentence_which_should_contain_target_word:
                    # print(f'Success with {target_word_to_search}')
                    pass
                else:
                    # print(f'Fail with {target_word_to_search}')
                    # print(f'Not in {sentence_which_should_contain_target_word:}')
                    # There's an error because the target word is not in the example string
                    flash(f'The number of examples ({newlines_example_sentences_70} == {length_target_words_71}) is the same but you have ERROR with {list_of_target_words_72[i]}')
                    return redirect(url_for('main.upload'))

                # If we get therought the above if else statement, it means that the words have been uploaded successfully.
                # We can then loop through them all and add them to the database
                # It's a bit inefficient running two loops. Or is it?? The first loop is to sanity check the data before adding anything to the databse

            for i in range(length_target_words_71):
                target_word_to_add_to_db_828 = list_of_target_words_72[i].strip()
                sentence_which_should_contain_target_word_add_to_db_8317 = split_list[i]

                # You will clobber any previously loaded User Examples so you should find a work around for that
                record_user_example = UserExample(word=target_word_to_add_to_db_828, example=sentence_which_should_contain_target_word_add_to_db_8317, user_id=current_user.id, translation=False, src=None, dst=uploaded_language)
                
                db.session.add(record_user_example)

            db.session.commit()
            db.session.close()

            # Redirect to the list page.
            return redirect(url_for('main.list', lng=uploaded_language))

        # If target words is different, return flash message
        # If target words is the same, run a check to see that each target word exists in the corresponding setence

    ##### stopped here ####
    # TODO #
        # This is when the user doesn't provide any target words
        for example in split_list:
            record_user_example = UserExample(example=example, word=None, user_id=current_user.id, translation=False, src=None, dst=uploaded_language)
            db.session.add(record_user_example)

        db.session.commit()

        return redirect(url_for('main.select_target_word'))


# ?: UPLOAD
@main.route('/upload/', methods=['GET'])
@login_required
def upload():
    mapped_languages = map_users_prefs_onto_langs(generate_language_codes(), current_user.id)
    lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent

    if lng_recent is None:
        User.query.filter_by(id=current_user.id).update({'lng_recent': 'en'})
        lng_recent = User.query.filter_by(id=current_user.id).first().lng_recent
        db.session.commit()
        db.session.close()

    return render_template('upload.html', lng_recent=lng_recent, language_codes=mapped_languages, is_english=is_english(lng_recent))


# ?: UPLOAD
@main.route('/select-target-word/')
@login_required
def select_target_word():
    # Use user id to find the most recent examples; filter on any without a target word
    user_examples_from_db = UserExample.query.filter_by(user_id=current_user.id).filter_by(word=None).all()

    user_examples = parse_user_examples_with_split(user_examples_from_db)

    return render_template('select_target_word.html', user_examples=user_examples)


@main.route('/add-target-words/', methods=['POST'])
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
    db.session.close()

    return redirect(url_for('main.list', lng='en'))


# ?: PROFILE
@main.route('/profile/')
@login_required
def profile():
    user_details = User.query.filter_by(id=current_user.id).first()

    language_codes=generate_language_codes()
    # Not in use right now, but it will be on Thu 26 Nov 2020
    languages = UserLanguagePreference.query.filter_by(user_id=current_user.id).all()

    if not languages:
        # Create new
        record_preferences = UserLanguagePreference(user_id=current_user.id)
        db.session.add(record_preferences)
        db.session.commit()

    mapped_languages = map_users_prefs_onto_langs(language_codes, current_user.id)  
    
    # return render_template('test.html', user_language_preference_dict = user_language_preference_dict)

    # if None, create a language prefs for the user
    return render_template('profile.html', user_details=user_details, language_codes=mapped_languages)


@main.route('/update_preferences/', methods=['POST'])
@login_required
def update_preferences():
    # Get list of new preferences with request.form.getlist
    target_inputs = request.form.getlist('hidden_input_value')
    list_of_language_names = request.form.getlist('language_name')
    list_switched_on_langs = []

    for i in range(len(target_inputs)):
        language = list_of_language_names[i]
        active_boolean_value = int(target_inputs[i])

        if active_boolean_value == 1:
            UserLanguagePreference.query.filter_by(user_id=current_user.id).update({language: True})
        else:
            UserLanguagePreference.query.filter_by(user_id=current_user.id).update({language: False})
    
    db.session.commit()
    db.session.close()

    # Give alert saying that your preferences have been updated
    flash(f'You have have succesfully your language preferences!', 'flash-success')
    return redirect(url_for('main.profile', lng='en'))


@main.route('/contact_us/', methods=['GET'])
def contact_us():
    user_details = None
    
    if current_user.is_authenticated:
        user_details = current_user

    return render_template('contact_us.html', user_details=user_details)


@main.route('/faq/', methods=['GET'])
def faq():
    faq = []
    
    return render_template('faq.html', faq=faq)


@main.route('/about_us/', methods=['GET'])
def about_us():
    return render_template('about_us.html')


@main.route('/help_and_support/', methods=['GET'])
def help_and_support():
    user_details = None
    
    if current_user.is_authenticated:
        user_details = current_user

    return render_template('help_and_support.html', user_details=user_details)