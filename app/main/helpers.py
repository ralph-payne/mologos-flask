import os, requests, re

# https://pypi.org/project/googletrans/
from googletrans import Translator
from time import sleep
import copy # Used for Deep Copying lists

from .. import db
from ..models import BulkTranslate, Definition, DictionaryExample, UserExample, User, Word, UserLanguagePreference

translator = Translator()

# Declare constant list which holds the languages
LANGUAGE_CODES = [
    { 'code': 'en', 'lng_eng': 'English', 'lng_src': 'English', 'active': False },
    { 'code': 'de', 'lng_eng': 'German', 'lng_src': 'Deutsch' ,'active': False },
    { 'code': 'es', 'lng_eng': 'Spanish', 'lng_src': 'español' ,'active': False },
    { 'code': 'it', 'lng_eng': 'Italian', 'lng_src': 'italiano' ,'active': False },
    { 'code': 'pt', 'lng_eng': 'Portuguese', 'lng_src': 'português' ,'active': True },
    { 'code': 'la', 'lng_eng': 'Latin', 'lng_src': 'Latine' ,'active': False },
    { 'code': 'el', 'lng_eng': 'Greek', 'lng_src': 'Ελληνικά', 'active': False },
    { 'code': 'fr', 'lng_eng': 'French', 'lng_src': 'Français', 'active': False },
    { 'code': 'pl', 'lng_eng': 'Polish', 'lng_src': 'Polskie', 'active': False }
]


def generate_language_codes():
    list_of_language_codes = [
        { 'code': 'en', 'lng_eng': 'English', 'lng_src': 'English', 'filename': 'img/flags/en.png', 'active': True },
        { 'code': 'de', 'lng_eng': 'German', 'lng_src': 'Deutsch' ,'filename': 'img/flags/de.png', 'active': False },
        { 'code': 'es', 'lng_eng': 'Spanish', 'lng_src': 'español' ,'filename': 'img/flags/es.png', 'active': True },
        { 'code': 'it', 'lng_eng': 'Italian', 'lng_src': 'italiano' ,'filename': 'img/flags/it.png', 'active': False },
        { 'code': 'pt', 'lng_eng': 'Portuguese', 'lng_src': 'português' ,'filename': 'img/flags/pt.png', 'active': True },
        { 'code': 'la', 'lng_eng': 'Latin', 'lng_src': 'Latine' ,'filename': 'img/flags/la.png', 'active': False },
        { 'code': 'el', 'lng_eng': 'Greek', 'lng_src': 'Ελληνικά', 'filename': 'img/flags/el.png', 'active': False },
        { 'code': 'fr', 'lng_eng': 'French', 'lng_src': 'Français', 'filename': 'img/flags/fr.png', 'active': False },
        { 'code': 'pl', 'lng_eng': 'Polish', 'lng_src': 'Polskie', 'filename': 'img/flags/pl.png', 'active': False }
    ]

    return list_of_language_codes


def lookup_definition_api(word):
    # Toggle for switching between APIs (Oxford API has a monthly limit of 1000)
    is_primary_api_oxford_dictionary = True

    # Contact API
    try:
        if is_primary_api_oxford_dictionary:
            app_id = os.environ.get('API_ID_OXFORD')
            app_key = os.environ.get('API_KEY_OXFORD')
            language = "en-gb"
            url = "https://od-api.oxforddictionaries.com:443/api/v2/entries/" + language + "/" + word.lower()
            response_oxford = requests.get(url, headers={"app_id": app_id, "app_key": app_key})

        else:
            API_KEY_MERRIAM_WEBSTER = os.environ.get('API_KEY_MERRIAM_WEBSTER')       
            response_merriam_webster = requests.get(f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={API_KEY_MERRIAM_WEBSTER}')


    except requests.RequestException:
        print('failed to connect to API')
        return None

    # Parse response
    try:
        if is_primary_api_oxford_dictionary:
            oxford = response_oxford.json()
            # Loop through to get examples & definitions     
            definitions_list = []
            examples_list = []

            erorr_count_definition = 0
            erorr_count_example = 0

            for a in oxford['results']:
                for b in a['lexicalEntries']:
                    for c in b['entries']:
                        for d in c['senses']:
                            try:
                                for definition in d['definitions']:
                                    definitions_list.append(definition)
                            except:
                                erorr_count_definition += 1                                
                                pass

                            try: 
                                for example in d['examples']:
                                    examples_list.append(example['text'])
                            except:
                                erorr_count_example += 1
                                pass

            print(f'total results for "{word}" | definition: {len(definitions_list)} | examples  : {len(examples_list)}')
            print(f'total errors  for "{word}" | definition: {erorr_count_definition} | examples  : {erorr_count_example}')

            # Anticipate that not all words have an etymology
            try:
                etymology = oxford['results'][0]['lexicalEntries'][0]['entries'][0]['etymologies'][0]
            except:
                etymology = None

            try:
                pronunciation = oxford['results'][0]['lexicalEntries'][0]['entries'][0]['pronunciations'][0]['phoneticSpelling']
            except:
                pronunciation = None

            oxford_return_val = {
                'word': oxford['results'][0]['id'], # str
                'pronunciation': pronunciation,
                'etymology': etymology, # str
                'definitions': definitions_list, # list
                'examples': examples_list, # list,
                'source': 'oxford'
            }

            return oxford_return_val

        else:
            merriam_webster = response_merriam_webster.json()

            merriam_webster_return_val = {
                'word': merriam_webster[0]['meta']['id'], # str
                'pronunciation': merriam_webster[0]['hwi']['prs'], # str
                # TODO: Debug how to get the etymology from Merriam-Webster
                # 'etymology': merriam_webster[0]['et']['text'] # list
                'etymology': 'todo',
                'definitions': merriam_webster[0]['shortdef'], # list
                # hwi: headword information. # List of pronunciations (prs) from index 0
                'examples': [], # list
                'source': 'merriam-webster'
            }

            return merriam_webster_return_val

    except (KeyError, TypeError, ValueError):
        return None


def lookup_db_dictionary(word):
    # Look up word in the local dictionary
    local_dictionary_result = Word.query.filter_by(word=word).first()

    # If found, display template with data from the local dictionary
    if local_dictionary_result is not None:
        definitions_base_query = Definition.query.filter_by(word=word)
        word_id = local_dictionary_result.id

        definitions_list = []
        for row in definitions_base_query:
            definitions_list.append(row.definition)

        examples_base_query = DictionaryExample.query.filter_by(word=word).all()
        db.session.close()

        examples_list = []
        for example in examples_base_query:
            examples_list.append(example.example)

        print(f'Results from the local dict for {word}')
        print(f'Number of definitions: {len(definitions_list)}')
        print(f'Number of examples:    {len(examples_list)}')

        # Create dictionary and merge results
        word_dict = {
            'word': local_dictionary_result.word,
            'word_id': word_id,
            'pronunciation': local_dictionary_result.pronunciation,
            'etymology': local_dictionary_result.etymology,
            'definitions': definitions_list,
            'examples': examples_list,
        }

        return word_dict
    
    else:
        db.session.close()
        return None


# https://github.com/ssut/py-googletrans/issues/234
def translate_api(src_text, dest_language):
    translator = Translator()
    result = None

    # Check that dest_language is a language code
    if len(dest_language) != 2:
        return None

    while result == None:
        try:
            result = translator.translate(src_text, src='en', dest=dest_language)
        except Exception as error:
            print(f'Error translating {src_text} into {dest_language}')
            translator = Translator()
            sleep(0.0001)
            pass

    return result.text


def bulk_translate(src_text):
    language_codes = select_active_languages(generate_language_codes())

    translations = []

    for dict in language_codes:
        key_language = dict['lng_eng'].lower()
        value_translation = translate_api(src_text, dict['code'])

        translation = {
            key_language: value_translation,
        }

        translations.append(translation)

    return translations


def bulk_translate_excluding(src_text, language_to_exclude):
    language_codes = filter_out_english(generate_language_codes())
    translations = []

    for dict in language_codes:
        key_language = dict['lng_eng'].lower()
        value_translation = translate_api(src_text, dict['code'])

        translation = {
            key_language: value_translation,
        }
        translations.append(translation)

    return translations


def create_language_dict(lng):
    for code in generate_language_codes():
        if code['code'] == lng:
            return code

    return None


def convert_language_to_two_letter_code(language):
    for code in generate_language_codes():
        if code['lng_eng'].lower() == language.lower():
            return code['code']

    return None


def filter_out_english(CONSTANT_LANG_LIST):
    filtered_list = list(filter(lambda x: x['code'] != 'en', CONSTANT_LANG_LIST))

    return filtered_list


def select_active_languages(CONSTANT_LANG_LIST):
    filtered_list = list(filter(lambda x: x['active'] != False, CONSTANT_LANG_LIST))

    return filtered_list


# IsEnglish Helper returns a boolean result, which in turn determines the relevant view for the templates
def is_english(language):
    if language == 'en':
        return True
    else:
        return False


def parse_translation_list(bulk_translate_model, word_to_translate, user_id):
    langs_already_translated = []
    new_personalised_user_dict = {}
    language_codes = generate_language_codes()

    if bulk_translate_model is None:
        print('nothing from the database 12341')
        # Bulk Translate everything
        # Create a new Bulk Translate thing in database
        
        new_entry_for_bulk_translate = BulkTranslate(english=word_to_translate)
        db.session.add(new_entry_for_bulk_translate)
        db.session.commit()

    else:
        # https://stackoverflow.com/questions/16947276/flask-sqlalchemy-iterate-column-values-on-a-single-row
        bulk_translate_dict = dict((col, getattr(bulk_translate_model, col)) for col in bulk_translate_model.__table__.columns.keys())

        for language, translation in bulk_translate_dict.items():
            # Skip blank columns or the ID column
            if language == 'id' :
                # Skip the ID column
                pass
            if translation == None:
                # Skip any languages which haven't been translated yet
                pass
            else:
                # It's already been translated
                langs_already_translated.append(language)

        print(f'The number of langs for {word_to_translate} already translated is: {len(langs_already_translated)}')

    # Compare this against what the user's current lanugage preferences are
    user_language_preference = UserLanguagePreference.query.filter_by(user_id=user_id).first()
    user_language_prefs_dict = dict((col, getattr(user_language_preference, col)) for col in user_language_preference.__table__.columns.keys())

    for language, boolean_value in user_language_prefs_dict.items():
        if boolean_value == True and language != 'id' and language != 'user_id' and language != 'created':
            # Create a new key value pair inside the new dictionary
            new_personalised_user_dict[language] = ''

    # Loop through the new dict
    # The new dict new_personalised_user_dict tells you what the user wants
    for language in new_personalised_user_dict:
        # Check if it's already been translated
        if language in langs_already_translated:
            new_personalised_user_dict[language] = bulk_translate_dict[language]
        else:
            # Look up the translation using the API
            two_letter_language_code = convert_language_to_two_letter_code(language)
            new_translation = translate_api(word_to_translate, two_letter_language_code)

            # Update database
            BulkTranslate.query.filter_by(english=word_to_translate).update({language: new_translation})
            print(f'updated {language} with {new_translation} in Bulk Translate db')

            # Add to new dictionary
            new_personalised_user_dict[language] = new_translation

    # Close database connection
    db.session.commit()

    # Return a dictionary with what the user wants
    return new_personalised_user_dict


def to_bool(string_value):
    """
        Converts 'a string' to a boolean. Raises exception for invalid formats
    """
    if str(string_value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): 
        return False
    else:
        return True


def create_bulk_translate_dict(word, translation_list):
    # BAD CODE (18.11.2020). This should be cleaned up
    dict = {
        'english': word,
        'german':       '',
        'italian':      '',
        'portuguese':   '',
        'spanish':      '',
        'latin':        '',
        'greek':        ''
    }

    for translation_dict in translation_list:
        for language, translated_word in translation_dict.items():
            if language == 'german':
                dict['german'] = translated_word
            if language == 'spanish':
                dict['spanish'] = translated_word
            if language == 'italian':
                dict['italian'] = translated_word
            if language == 'portuguese':
                dict['portuguese'] = translated_word
            if language == 'latin':
                dict['latin'] = translated_word
            if language == 'greek':
                dict['greek'] = translated_word

    record_bulk_translate = BulkTranslate(
        english = dict['english'],
        german = dict['german'],
        italian = dict['italian'],
        portuguese = dict['portuguese'],
        spanish = dict['spanish'],
        latin = dict['latin'],
        greek = dict['greek']
    )                                             

    return record_bulk_translate


def split_keyboard_into_rows(keyboard):
    keyboard_split_into_rows = []

    number_of_accents = len(keyboard)

    # Declare empty lists
    # https://stackoverflow.com/questions/13520876/how-can-i-make-multiple-empty-lists-in-python
    row_one, row_two, row_three = ([] for i in range(3))

    for element in keyboard:
        if element.row_num == 1:
            row_one.append(element)
        if element.row_num == 2:
            row_two.append(element)
        if element.row_num == 3:
            row_three.append(element)

    keyboard_split_into_rows = [row_one, row_two, row_three]

    return keyboard_split_into_rows



# Example:
# user_examples = {
#     'id': 3,
#     'user_example': 'god here is',
#     'user_example_parased': ['god', 'here', 'is']
# }
def parse_user_examples_with_split(user_examples_from_db):
    ids = list(map(lambda x: x.id, user_examples_from_db))
    user_examples_examples = list(map(lambda x: x.example, user_examples_from_db))    

    user_examples_parsed = []
    size = len(user_examples_from_db)

    for element in user_examples_from_db:
        list_of_split_words = split_to_words(element.example)

        user_examples_parsed.append(list_of_split_words)

    user_examples = []

    for i in range(size):
        dict = {
            'id': ids[i],
            'user_example': user_examples_examples[i],
            'user_examples_parsed': user_examples_parsed[i]
        }
        user_examples.append(dict)

    return user_examples


def split_to_words(sentence):
    return list(filter(lambda w: len(w) > 0, re.split('\W+', sentence)))


def map_users_prefs_onto_langs(language_codes, user_id):
    # https://stackoverflow.com/questions/16947276/flask-sqlalchemy-iterate-column-values-on-a-single-row

    user_language_preference = UserLanguagePreference.query.filter_by(user_id=user_id).first()

    user_language_prefs = dict((col, getattr(user_language_preference, col)) for col in user_language_preference.__table__.columns.keys())
    
    deep_copy_of_lang_codes = copy.deepcopy(language_codes) # Deep Copy the Original List

    for col, active_boolean in user_language_prefs.items():
        for language_code in deep_copy_of_lang_codes:
            # print(language_code['lng_eng'].lower())
            if col == language_code['lng_eng'].lower():
                language_code['active'] = active_boolean

    return deep_copy_of_lang_codes