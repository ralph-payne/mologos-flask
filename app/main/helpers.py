import os

import requests

def lookup_api(word):
    """Look up word"""

    # Contact API
    try:
        API_KEY = os.environ.get('API_KEY')
        response = requests.get(f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={API_KEY}')

    except requests.RequestException:
        print('failed to connect to API')
        return None

    # Parse response
    try:
        dict_from_api = response.json()

        # If it returns an empty list, that's an error
        # TODO: tidy this conditional up.. Can you incorporate it into the try and except statement?)
        if (dict_from_api == []):
            return None

        # List of short definitions from index 0
        short_def_list = dict_from_api[0]['shortdef']

        # hwi: headword information. # List of pronunciations (prs) from index 0
        # https://dictionaryapi.com/products/json
        pronunciation_list = dict_from_api[0]['hwi']['prs']

        print(dict_from_api[0]['meta']['id'])
        
        # Return a dictionary with def and pron
        return {
            'word': dict_from_api[0]['meta']['id'], # str
            'def': dict_from_api[0]['shortdef'], # list
            'pron': dict_from_api[0]['hwi']['prs'] # list
        }

    except (KeyError, TypeError, ValueError):
        return None


# Requests Library
# The requests library is for your app to make HTTP request to other sites, usually APIs. It makes an outgoing request and returns the response from the external site.