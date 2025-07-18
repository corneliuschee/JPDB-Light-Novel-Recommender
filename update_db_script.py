#Anki statistics reference: https://docs.ankiweb.net/stats.html
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from jpdb_functions import *
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, MetaData, Table, text

STARTID = int((datetime.now().replace(hour=4, minute=0, second=0, microsecond=0) - timedelta(days=1)).timestamp() * 1000) #Last day 4am 
CRT = datetime.fromtimestamp(1716235200, tz=timezone(offset=timedelta(hours=8), name='sgt')) #1716235200 is unix for creation of anki collection, got from querying the collection.anki2 db with 'SELECT crt FROM col'
DB_PATH = Path(os.getenv('DB_PATH')).resolve()

permission = anki_invoke('requestPermission')['permission']

engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}")
metadata = MetaData()
anki_vocab_table = Table('anki_vocab', metadata, autoload_with=engine)

if permission == 'granted':
    
    anki_invoke('sync') #Synchronizes the local Anki collections with AnkiWeb.
    core_previous_day_reviewed_cards = anki_invoke('cardReviews', deck = 'Core2.3k Version 3', startID = STARTID)
    core_cards_ids = list(set(card[1] for card in core_previous_day_reviewed_cards))
    core_cards = anki_invoke('cardsInfo', cards = core_cards_ids)
    
    #Iterate over core cards first; Since all cards in core are known, we do not need to check for new vocab.
    update_value_dict = {} #to iterate through to update each vid using sqlalchemy
    all_core_cards_reviews = anki_invoke('getReviewsOfCards', cards = core_cards_ids)
    

    for core_card in core_cards:
        card_id = core_card['cardId']
        vocab = core_card['fields']['Word']['value']
        due = core_card['due'] #days from CRT
        vocab_review_count = core_card['reps']
        lapses = core_card['lapses']
        percent_correct = int(round(((vocab_review_count - lapses) / vocab_review_count) * 100, 0))
        
    
        vocab_data = lookup_vocab_vidless(vocab)
        vid = vocab_data['vid']
        
        update_value_dict[vid] = {
            'percent_correct': percent_correct,
            'due': (CRT + timedelta(days=due)).strftime("%Y-%m-%d 00:00:00.000000"),
            'again_count': lapses + len([review for review in all_core_cards_reviews[f'{card_id}'] if review['type'] == 0 and review['ease'] == 1]), #type 0 review means a review where vocab is being learnt (new vocab), ease = 1 is where again button was clicked. #these initial agains are not included in the computation of percent correct
            'reviews': vocab_review_count
        }
        

    #Now for mining deck
    mining_previous_day_reviewed_cards = anki_invoke('cardReviews', deck = 'Mining', startID = STARTID)
    new_vocab_card_ids = list(set(vocab[1] for vocab in mining_previous_day_reviewed_cards if vocab[-1] == 0)) #Check the previous day reviewed cards if the review type == 0 (learning card state) to filter out for new vocab.
    new_vocab_card_ids.sort(reverse=False) #so that anki vocab gets added in order 
    mining_cards_ids = list(set(card[1] for card in mining_previous_day_reviewed_cards if card[0] not in core_cards_ids)) #there are some duplicates in mining this ensures no double-counting
    mining_cards = anki_invoke('cardsInfo', cards = mining_cards_ids)

    mining_new_cards_list = []
    all_mining_cards_reviews = anki_invoke('getReviewsOfCards', cards = mining_cards_ids)
    
    for mining_card in mining_cards:
        card_id = mining_card['cardId']
        vocab = mining_card['fields']['Word']['value']
        due = mining_card['due'] #days from CRT
        vocab_review_count = mining_card['reps']
        lapses = mining_card['lapses']
        percent_correct = int(round(((vocab_review_count - lapses) / vocab_review_count) * 100, 0))
        
    
        vocab_data = lookup_vocab_vidless(vocab)
        vid = vocab_data['vid']
        
        
        if card_id not in new_vocab_card_ids:
            update_value_dict[vid] = {
                'percent_correct': percent_correct,
                'due': (CRT + timedelta(days=due)).strftime("%Y-%m-%d 00:00:00.000000"),
                'again_count': lapses + len([review for review in all_mining_cards_reviews[f'{card_id}'] if review['type'] == 0 and review['ease'] == 1]), #same as above
                'reviews': vocab_review_count
            }
        
        else:
            reading = mining_card['fields']['WordReadingHiragana']['value']
            sid = vocab_data['sid']
            frequency_rank = vocab_data['frequency rank']
            mining_new_cards_list.append({
                'vocab': vocab,
                'reading': reading,
                'vid': vid,
                'sid': sid,
                'frequency_rank': frequency_rank,
                'percent_correct': percent_correct,
                'due': (CRT + timedelta(days=due)),
                'again_count': lapses + len([review for review in all_mining_cards_reviews[f'{card_id}'] if review['type'] == 0 and review['ease'] == 1]), #same as above
                'reviews': vocab_review_count
            })
    
    #update anki_vocab table
    with engine.begin() as conn:

        try:
            conn.execute(
                text("UPDATE anki_vocab SET percent_correct = :pc, reviews = :reviews WHERE vid = :vid"),
                [{"vid": vid, "pc": v["percent_correct"], "reviews": v['reviews']} for vid, v in update_value_dict.items()]
            )
        
        except:
            pass
        
        for new_vocab in mining_new_cards_list:
            try:
                #insert new vocab
                conn.execute(anki_vocab_table.insert().values(**new_vocab))
            except IntegrityError:
                continue
        