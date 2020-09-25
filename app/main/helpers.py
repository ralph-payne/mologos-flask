import os
# The requests library is for your app to make HTTP request to other sites, usually APIs. It makes an outgoing request and returns the response from the external site.
import requests

# https://pypi.org/project/googletrans/
from googletrans import Translator

from .. import db
# from ..models import Definition, Sentence, Word
from ..models import Definition, DictionaryExample, UserExample, User, Word

# Init Translator
translator = Translator()

def lookup_api(word):
    # Toggle for switching between APIs (Oxford API has a monthly limit of 1000)
    primary_api_is_oxford = True

    # Contact API
    try:
        if primary_api_is_oxford:
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
        if primary_api_is_oxford:
            oxford = response_oxford.json()
            # Loop through to get examples and definitions     
            definitions_list = []
            examples_list = []

            # The things that will break the API are if the word doesn't have any examples
            # Or if the word doesn't have any etymology

            # house, dolphin, great, cat, comb do not work

            for a in oxford['results']:
                for b in a['lexicalEntries']:
                    for c in b['entries']:
                        for d in c['senses']:
                            try:
                                for e in d['definitions']:
                                    definitions_list.append(e)
                            except:
                                pass

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
                'examples': examples_list # list
            }

            return oxford_return_val

        else:
            merriam_webster = response_merriam_webster.json()

            merriam_webster_return_val = {
                'word': merriam_webster[0]['meta']['id'], # str
                'pronunciation': merriam_webster[0]['hwi']['prs'], # str
                # TODO: Debug how to get the etymology from MW
                # 'etymology': merriam_webster[0]['et']['text'] # list
                'etymology': 'todo',
                'definitions': merriam_webster[0]['shortdef'], # list
                # hwi: headword information. # List of pronunciations (prs) from index 0
                'examples': [] # list
            }

            return merriam_webster_return_val

    except (KeyError, TypeError, ValueError):
        return None


def lookup_db_dictionary(word):
    # Create route with dynamic component
    # Lookup the word in the local dictionary
    # first() returns only the first result or None if there are no results
    local_dictionary_res = Word.query.filter_by(word=word).first()
    # TODO => check if .commit() is necessary here

    # If found, display template with data from the local dictionary
    if local_dictionary_res is not None:
        # TODO => Check efficiency of having three different database look ups.
        # TODO => Can you use JOIN TABLES instead here?
        # Look up definitions
        # definitions_list = Definition.query.filter_by(word=word).all()

        # Returns Type <class 'flask_sqlalchemy.BaseQuery'>
        definitions_base_query = Definition.query.filter_by(word=word)
        # This is a list of type <class 'app.models.Definition'>

        # Parse to list <class 'flask_sqlalchemy.BaseQuery'>
        # TODO => Make this more efficient (it shouldn't be two steps)
        definitions_list = []
        for row in definitions_base_query:
            definitions_list.append(row.definition)

        # Look up examples (By setting user ID to 0, you avoid retrieving user examples)
        examples_base_query = DictionaryExample.query.filter_by(word=word).all()

        # Close database connection
        db.session.commit()

        examples_list = []
        for row in examples_base_query:
            examples_list.append(row.example)

        # Create dictionary and merge results
        word_dict = {
            'word': local_dictionary_res.word,
            'pronunciation': local_dictionary_res.pronunciation,
            'etymology': local_dictionary_res.etymology,
            'definitions': definitions_list,
            'examples': examples_list,
        }

        return word_dict
    
    else:
        db.session.commit()
        return None


def translate_api(src_text, dest_language):

    if src_text:
        # Version 1 only has option to translate from english.
        source_lang = 'en'

        # result is a dictionary with properties text, src, dest, extra_data...
        result = translator.translate(src_text, src=source_lang, dest=dest_language)
        
        return result.text

    else:
        return None


def lng_dict(lng):

    lng_codes = [
        { 'code': 'de', 'lng_eng': 'German', 'lng_src': 'Deutsch' },
        { 'code': 'es', 'lng_eng': 'Spanish', 'lng_src': 'español' },
        { 'code': 'pt', 'lng_eng': 'Portuguese', 'lng_src': 'português' },
        { 'code': 'en', 'lng_eng': 'English', 'lng_src': 'English' },
        { 'code': 'it', 'lng_eng': 'Italian', 'lng_src': 'italiano' }
    ]

    for code in lng_codes:
        if code['code'] == lng:
            return code

    return None

# Is English Helper returns a boolean result, which in turn determines the correct view for the templates
def is_eng(lng):
    if lng == 'en':
        return True
    else:
        return False