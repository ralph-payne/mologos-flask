from datetime import datetime
import random

from flask import flash, redirect, render_template, request, session, url_for
from . import main
from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, UserTranslation, Word

from flask_login import current_user, login_required

# Helper functions for parsing results from API and database dictionary
from .helpers import lookup_api, lookup_db_dictionary, translate_api, lng_dict, is_eng

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
        user_example = request.form.get('user-example')
    
        # Insert User's Example sentence into database
        record = UserExample(example=user_example, word=word, user_id=current_user.id, translation=False, src=None, dst='en', original=None)
        db.session.add(record)
        db.session.commit()

        return redirect(url_for('main.list', lng='en'))


# Returns a list of the user's saved words
@main.route('/list/<lng>')
@login_required
def list(lng):
    words = UserExample.query.filter_by(user_id=current_user.id, dst=lng).all()
    return render_template('list.html', words=words, eng=is_eng(lng), lng=lng_dict(lng))


@main.route('/delete/<lng>/<id>')
@login_required
def delete(lng, id):
    # Hard delete data
    UserExample.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('main.list', lng=lng))


# TODO => think about what the best dynamic route would look like
@main.route('/edit/<lng>/<id>', methods=['GET', 'POST'])
@login_required
def edit(lng, id):
    if request.method == 'POST':
        # Get values from form
        updated_example = request.form.get('edited-example') 
        last_modified = datetime.utcnow()

        star_bool = int(request.form.get('star_boolean'))
        ignored_bool = int(request.form.get('eye_boolean'))

        ## Temp do two separate options
        if (lng == 'en'):
            metadata = UserExample.query.filter_by(user_id=current_user.id, id=id).first()
            metadata.example = updated_example
      
        else:
            metadata = UserTranslation.query.filter_by(user_id=current_user.id, id=id).first()
            metadata.output = updated_example

        metadata.starred = star_bool
        metadata.ignored = ignored_bool
        metadata.last_modified = last_modified

        db.session.commit()

        # Redirect to User List
        return redirect(url_for('main.list', lng=lng))

    else: # GET
        word_details = False
        definition = False
        if lng == 'en':
            word = UserExample.query.filter_by(id=id).first()

            # Word contains etymology and pronunciation
            # todo => make this a lookup on the id rather than the word
            word_details = Word.query.filter_by(word=word.word).first()

            definition = Definition.query.filter_by(word=word.word).first()
        else:
            word = UserTranslation.query.filter_by(id=id).first()

        return render_template('edit.html', word=word, word_details=word_details, definition=definition, lng=lng_dict(lng))


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
    
        return render_template('definition.html', word=api_return_val)


@main.route('/definition', methods=['POST'])
def lookup():
    if request.method == 'POST':
        # TODO => parse the word
        word_to_lookup = request.form.get('word-to-lookup')
        return redirect(url_for('main.define', word=word_to_lookup))


@main.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':
        # Check which of the 2 forms has been submitted
        # Form 1 calls the Translation API
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
                # Reassign the dst language for the page reload
                lng_recent = dst_language
            
            if output is None:
                # return error
                return render_template('404.html', dev_text='error with translation helper')
            else:
                return render_template('translate.html', input=text_to_translate, output=output, lng_recent=lng_recent)

        # User has submitted form 2 (to save phrase to database)
        else:
            output = request.form.get('translation-result')
            dst = request.form.get('dst_lng_2')
            input = request.form.get('src_tra_2')
            output = request.form.get('dst_tra_2')
            
            record = UserExample(example=output, word='', user_id=current_user.id, translation=True, src='en', dst=dst, original=input)

            db.session.add(record)
            db.session.commit()

            flash(f'{output} has been successfully added to your dictionary!')
            return redirect(url_for('main.translate'))

        return render_template('translate.html')

    # GET request
    else:
        id = current_user.id
        # Query database to get the language that the user used most recently
        lng_recent = User.query.filter_by(id=id).first().lng_recent
        return render_template('translate.html', lng_recent=lng_recent)


@main.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('user_profile.html', user=current_user)


@main.route('/challenge/<lng>', methods=['GET', 'POST'])
@login_required
def challenge(lng):
    # POST request so check results
    if request.method == 'POST':
        # Declare arrays to store data from forms
        word_ids = request.form.getlist('word_id')
        stars = request.form.getlist('star_boolean')
        skips = request.form.getlist('eye_boolean')
        guesses = request.form.getlist('user_guess')
        target_words = request.form.getlist('target_word')

        # Temp separating eng and foreign, but on v2 they will merge into one model
        if (lng != 'en'):
            translations = request.form.getlist('translation')
        else:
            translations = []

        # Declare empty list to store results and get length of words submitted
        results = []
        size = len(word_ids)

        for i in range(size):
            if (is_eng(lng)):
                translation = ''
                result_bool = 1 if target_words[i].lower() == guesses[i].lower() else 0
            else:
                translation = translations[i]
                result_bool = 1 if translations[i].lower() == guesses[i].lower() else 0

            # Create dictionary
            result_dict = {
                'id': word_ids[i], 
                'target_word': target_words[i],
                'starred': stars[i],
                'skipped': skips[i],
                'user_guess': guesses[i],
                'result': result_bool,
                'translation': translation
            }

            results.append(result_dict)
            metadata = UserExample.query.filter_by(user_id=current_user.id, id=word_ids[i]).first()

            if (result_bool):
                metadata.success = UserExample.success + 1
            else:
                metadata.fail = UserExample.fail + 1

            if (skips[i]):
                metadata.skip = 1

            if (stars[i]):
                metadata.starred = 1

            db.session.commit()

        return render_template('results.html', results=results, lng=lng_dict(lng), eng=is_eng(lng))

    # GET
    else:
        # English view differs
        if (is_eng(lng)):
            words_from_db = UserExample.query.filter_by(user_id=current_user.id, dst=lng).all()
            # Declare list which will hold dictionaries of each word
            words = []

            # Start loop and add words until the list is at the maximum size
            while len(words) <= 5 and len(words_from_db) != 0:
                word = random.choice(words_from_db)

                # After choosing a random word, retrieve the example sentence
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

                    # Remove word from list 1 (bucket of words) to avoid duplicates
                    words_from_db.remove(word)
                    # Append to list 2 of words to be rendered
                    words.append(word_dict)

                else:
                    # Skip if word does not appear in target sentence
                    words_from_db.remove(word)

            return render_template('challenge.html', words=words, lng=lng_dict(lng), eng=is_eng(lng))

        else:
            words = UserExample.query.filter_by(user_id=current_user.id, dst=lng).all()
            return render_template('challenge.html', words=words, lng=lng_dict(lng), eng=is_eng(lng))