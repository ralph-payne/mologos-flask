import os
import requests

# https://pypi.org/project/googletrans/
from googletrans import Translator
from time import sleep

from .. import db
from ..models import Definition, DictionaryExample, UserExample, User, Word

translator = Translator()

def lookup_api(word):
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
            # Loop through to get examples and definitions     
            definitions_list = []
            examples_list = []

            erorr_count_def = 0
            erorr_count_exa = 0

            for a in oxford['results']:
                for b in a['lexicalEntries']:
                    for c in b['entries']:
                        for d in c['senses']:
                            try:
                                for definition in d['definitions']:
                                    definitions_list.append(definition)
                                    print('def')
                                    print(e)
                            except:
                                print('no def')
                                erorr_count_def += 1                                
                                pass

                            try: 
                                for example in d['examples']:
                                    examples_list.append(example['text'])
                                    print('--- in an example ---')
                                    print(f['text'])
                            except:
                                print('out of an example')
                                erorr_count_exa += 1
                                pass


            print('total errors')
            print(f'definition: {erorr_count_def}')
            print(f'examples  : {erorr_count_exa}')

            print('total results')
            print(f'definitions: {len(definitions_list)}')
            print(f'examples: {len(examples_list)}')

            # Anticipate that not all words have an etymology
            try:
                etymology = oxford['results'][0]['lexicalEntries'][0]['entries'][0]['etymologies'][0]
            except:
                etymology = None

            try:
                pronunciation = oxford['results'][0]['lexicalEntries'][0]['entries'][0]['pronunciations'][0]['phoneticSpelling']
            except:
                pronunciation = None

            print(oxford)

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
        # Get the id
        word_id = local_dictionary_result.id

        # TODO => Check efficiency of having three different database look ups.
        # TODO => Can you use JOIN TABLES instead here?

        # Returns Type <class 'flask_sqlalchemy.BaseQuery'>
        # definitions_base_query = Definition.query.filter_by(word=word)
        definitions_base_query = Definition.query.filter_by(word_id=word_id)
        # This is a list of type <class 'app.models.Definition'>

        # Parse to list <class 'flask_sqlalchemy.BaseQuery'>
        # TODO => Make this more efficient (it shouldn't be two steps)
        definitions_list = []
        for row in definitions_base_query:
            definitions_list.append(row.definition)

        examples_base_query = DictionaryExample.query.filter_by(word_id=word_id).all()
        db.session.close()

        examples_list = []
        for example in examples_base_query:
            examples_list.append(example.example)

        # Create dictionary and merge results
        word_dict = {
            'word': local_dictionary_result.word,
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
    while result == None:
        try:
            result = translator.translate(src_text, src='en', dest=dest_language)
        except Exception as error:
            print(f'error translating {src_text} into {dest_language}')
            translator = Translator()
            sleep(0.0001)
            pass
    return result.text


def bulk_translate(src_text):
    lng_codes = [
        { 'code': 'de', 'lng_eng': 'German', 'lng_src': 'Deutsch' },
        { 'code': 'es', 'lng_eng': 'Spanish', 'lng_src': 'español' },
        { 'code': 'pt', 'lng_eng': 'Portuguese', 'lng_src': 'português' },
        { 'code': 'en', 'lng_eng': 'English', 'lng_src': 'English' },
        { 'code': 'it', 'lng_eng': 'Italian', 'lng_src': 'italiano' }
    ]

    foo = []

    for a in lng_codes:
        goo = translate_api(src_text, a['code'])
        foo.append(goo)

    for b in foo:
        print(b)

    return foo
   

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


# Is English Helper returns a boolean result, which in turn determines the relevant view for the templates
def is_english(language):
    if language == 'en':
        return True
    else:
        return False