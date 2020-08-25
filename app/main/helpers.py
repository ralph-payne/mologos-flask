import os
import requests


# import requests
# import json
# app_id = "<your_app_id>"
# app_key = "<your_app_key>"
# language = "en-gb"
# word_id = "example"
# url = "https://od-api.oxforddictionaries.com:443/api/v2/entries/" + language + "/" + word_id.lower()
# r = requests.get(url, headers={"app_id": <your_app_id>, "app_key": <your_app_key>})


def lookup_api(word):
    """Look up word"""

    # Toggle for switching between APIs
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
            # print(oxford)

            # Loop through to get examples and definitions     
            definitions_list = []
            examples_list = []

            for a in oxford['results']:
                for b in a['lexicalEntries']:
                    for c in b['entries']:
                        for d in c['senses']:
                            for e in d['definitions']:
                                definitions_list.append(e)
                            for f in d['examples']:
                                examples_list.append(f['text'])

            oxford_return_val = {
                'word': oxford['results'][0]['id'], # str
                'pron': oxford['results'][0]['lexicalEntries'][0]['entries'][0]['pronunciations'][0]['phoneticSpelling'], # str
                'etymology': oxford['results'][0]['lexicalEntries'][0]['entries'][0]['etymologies'][0], # str
                'def': definitions_list, # list
                'examples': examples_list # list
            }

            return oxford_return_val

        else:
            merriam_webster = response_merriam_webster.json()

            merriam_webster_return_val = {
                'word': merriam_webster[0]['meta']['id'], # str
                'pron': merriam_webster[0]['hwi']['prs'], # str
                # TODO: Debug how to get the etymology from MW
                # 'etymology': merriam_webster[0]['et']['text'] # list
                'etymology': 'todo',
                'def': merriam_webster[0]['shortdef'], # list
                # hwi: headword information. # List of pronunciations (prs) from index 0
                'examples': [] # list

            }

            return merriam_webster_return_val

    except (KeyError, TypeError, ValueError):
        return None


# Requests Library
# The requests library is for your app to make HTTP request to other sites, usually APIs. It makes an outgoing request and returns the response from the external site.
