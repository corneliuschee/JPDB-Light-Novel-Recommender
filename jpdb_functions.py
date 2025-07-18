### Public API documentation: https://jpdb.stoplight.io/docs/jpdb/mgsimhgxpjpqe-jpdb-io-public-api

import json, urllib.request, os, re, requests
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

API_KEY = os.getenv("API_KEY")
SID = os.getenv("SID")

base_url = "https://jpdb.io/api/v1/"
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    'Content-Type': 'application/json',
}

cookies = {
    "sid": SID
}

# response = requests.get('https://jpdb.io/api/v1/ping', headers=headers)
# print(response)


#Returns deck id/name
def get_decks():
    body = {
    "fields": ['id', 'name', 'vocabulary_count', 'word_count', 'vocabulary_known_coverage', 'vocabulary_in_progress_coverage', 'is_built_in']
}
    response = requests.post(base_url + 'list-user-decks', headers=headers, json=body)
    return response.json()


#Returns a list of vocab, in the form of their vid and sid.
#Also returns the vocab occurance rate. Accepts only user created deck IDs.
def get_vocab(user_deck_id):
    body = {
        "id": user_deck_id,
        "fetch_occurences": True
    }

    response = requests.post(base_url + 'deck/list-vocabulary', headers=headers, json=body)
    return response.json()["vocabulary"]


#Looks up information about vocabulary for which you already have the IDs.
#Returns the vid (vocab id), sid (spelling id), spelling, reading, frequency rank and meanings.
#Frequency rank of a vocab is based on the built in decks database in jpdb.
def lookup_vocab(vocab):

    body = {
    "list": vocab,
    "fields": [
        "vid",
        "sid",
        "spelling",
        "reading",
        "frequency_rank",
        "meanings"
    ]
}
    response = requests.post(base_url + 'lookup-vocabulary', headers=headers, json=body)
    return response.json()['vocabulary_info']


#Deletes deck from jpdb account
def delete_deck(id):
    body = {
        "id": id
    }

    response = requests.post(base_url + 'deck/delete', json=body, headers=headers)
    return response.json()


#Creates an empty deck in jpdb account
def create_deck(name, position = 0):
    body = {
        "name": name,
        "position": position
    }

    response = requests.post(base_url + "deck/create-empty", json=body, headers=headers)
    return response.json()


#Adds vocab to deck
#vocab arugment: A list of 2-element arrays with a vid and sid of vocabulary cards to add
def add_vocab(deck_id, vocab):
    body = {
        "id": deck_id,
        "vocabulary": vocab,
    }

    response = requests.post(base_url + "deck/add-vocabulary", json=body, headers=headers)
    return response.json()



#NOT in public api, got from scraping the webpage while logged in and inspecting the post request triggered when clicking on "Add to deck"
def create_prebuilt(novel_id, sid):
    request_url = "https://jpdb.io/add_prebuilt_deck"
    #Starts a session
    session = requests.Session()
    session.cookies.set("sid", sid)


    headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": f"https://jpdb.io/novel/{novel_id}",
    "Origin": "https://jpdb.io",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    }


    body = {
        "id": novel_id
    }

    response = session.post(request_url, headers=headers, data=body)
    return(response.status_code)
                        

#Checks if vocab data has any missing values in sid, spelling, reading or frequency_rank fields and replaces them with 0 or "" for string and integer columns respectively.
def replace_empty_values(vocab_entry):
    if None in vocab_entry:
    
        if vocab_entry[4] == None:
            vocab_entry[4] = 0

        if vocab_entry[2] == None:
            vocab_entry[2] = ""
        
        if vocab_entry[3] == None:
            vocab_entry[3] = ""
        
        if vocab_entry[1] == None:
            vocab_entry[1] = 0
    
    
 #Lookups a vocab without the vid, returns a dictionary of the frequency, vid and sid. 
 #Could modify to lookup the meaning but not necessary for our usecase as we will not be using meaning in our model.
def lookup_vocab_vidless(vocab):
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/135.0.0.0 Safari/537.36",
    "Accept": "text/html",
    }

    frequency_rank = None
    vid = None
    sid = None

    response = requests.get(f'https://jpdb.io/search?q={vocab}', headers=headers, cookies=cookies)
    if response.status_code != 200:
        return {"frequency rank": frequency_rank,
                "vid": vid,
                "sid": sid}
    
    soup = BeautifulSoup(response.text, "html.parser")
    #Select first vocab entry
    jpdb_vocab_entry = soup.find("div", attrs={'class': 'result vocabulary'})

    

    if jpdb_vocab_entry:
        if jpdb_vocab_entry.find_next("div", attrs={'class': 'tag tooltip'}):
            frequency_rank = int(jpdb_vocab_entry.find_next("div", attrs={'class': 'tag tooltip'}).text.strip('Top').strip())
        
        id_container = jpdb_vocab_entry.find("div", attrs={'class': 'dropdown-content'})

        if id_container:
            href_link = id_container.find('a')['href']
            search = re.search(r'v=(\d+)&s=(\d+)', href_link)

            if search:
                vid = int(search.group(1))
                sid = int(search.group(2))
            
    
        return {"frequency rank": frequency_rank,
                "vid": vid,
                "sid": sid}
    
                            
#Function to use df.apply on.
def enrich_vocab(row):
    vocab_dict = lookup_vocab_vidless(row['Vocab'])
    if vocab_dict:
        row['vid'] = vocab_dict['vid']
        row['sid'] = vocab_dict['sid']
        row['frequency rank'] = vocab_dict['frequency rank']
    
    return row



def anki_connect_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


#Anki Connect API: https://git.sr.ht/~foosoft/anki-connect/
def anki_invoke(action, **params):
    requestJson = json.dumps(anki_connect_request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

