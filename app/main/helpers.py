import os
# The requests library is for your app to make HTTP request to other sites, usually APIs. It makes an outgoing request and returns the response from the external site.
import requests

from .. import db
# from ..models import Definition, Sentence, Word
from ..models import Definition, DictionaryExample, UserExample, User, Word

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
            print('--- response from Oxford API ---')
            # print(oxford)
            print('--- end of response from Oxford API ---')

            # Loop through to get examples and definitions     
            definitions_list = []
            examples_list = []

            # The things that will break the API are if the word doesn't have any examples
            # Or if the word doesn't have any etymology
            # ginger does not have examples

            # Ginger now works
            # Messy works because I added try and expect for etymology
            # house does not work
            # dolphin does not work
            # great does not work

            for a in oxford['results']:
                print(f'results: {len(a)}')
                for b in a['lexicalEntries']:
                    print(f'Lexical Entries: {len(b)}')
                    for c in b['entries']:
                        print(f'Entries: {len(c)}')
                        for d in c['senses']:
                            print(f'Senses: {len(d)}')
                            for e in d['definitions']:
                                print(f'Definitions: {len(e)}')
                                print(e)
                                definitions_list.append(e)
                
                            # Catch any definitions which don't have examples with try except
                            try:
                                for f in d['examples']:
                                    print(f'Examples: {len(f)}')
                                    print(f)
                                    examples_list.append(f['text'])
                            except:
                                examples_list = []

            # Anticipate that not all words have an etymology
            try:
                etymology = oxford['results'][0]['lexicalEntries'][0]['entries'][0]['etymologies'][0]
            except:
                etymology = None

            oxford_return_val = {
                'word': oxford['results'][0]['id'], # str
                'pronunciation': oxford['results'][0]['lexicalEntries'][0]['entries'][0]['pronunciations'][0]['phoneticSpelling'], # str
                'etymology': etymology, # str
                'definitions': definitions_list, # list
                'examples': examples_list # list
            }

            print('--- Printing parsed value from Oxford API ---')
            print(oxford_return_val)
            print('--- end of printing value ---')

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