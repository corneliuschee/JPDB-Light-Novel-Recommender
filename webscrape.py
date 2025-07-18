import time, random
import pandas as pd
import re, os, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
from jpdb_functions import *
from sqlalchemy import create_engine, MetaData, select, update,  Table

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

TARGET_URL = "https://jpdb.io/novel-difficulty-list"
SID = os.getenv("SID")
API_KEY = os.getenv("API_KEY")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/135.0.0.0 Safari/537.36",
    "Accept": "text/html",
    
}

cookies = {
    "sid": SID
}

offset = 0
novel_data = {}


##Scrape for novel id, novel title, and its statistics. 
##Each page has 50 titles so we increase offset by 50 everytime.
# while offset < 1500:

#     if offset != 0:
#         time.sleep(random.uniform(1, 5))

#     url = f"{TARGET_URL}?offset={offset}"
#     print(f"Scraping: {url}")

#     response = requests.get(url=url, headers=headers, cookies= cookies)

#     if response.status_code != 200:
#         print(f"Failed at offset {offset}")
#         break


#     soup = BeautifulSoup(response.text, "html.parser")
#     novel_entries = soup.find_all("div", attrs={'style': 'display: flex; flex-wrap: wrap;'})

#     for entry in novel_entries:
#         title = entry.find("h5").get_text(strip=True)
#         stats_table = entry.find("table", attrs={"class": "cross-table data-right-align"})
#         id = re.search(r"(\d+)", entry.find("a", attrs={"class": "outline"})['href']).group(1)

#         novel_data[id] = {}
#         novel_data[id]["Title"] = title

#         for row in stats_table.find_all("tr"):
#             key = row.find("th").get_text(strip=True)
#             value = row.find("td").get_text(strip=True)
#             novel_data[id][key] = value

#     offset += 50

# #Create and save the dataframe.
# df = pd.DataFrame(novel_data).transpose()
# df.reset_index(inplace=True)
# df.rename(columns={"index": "novel_id"}, inplace=True)
# df.to_csv("jpdb_novel_data.csv", header=True)



# engine = create_engine('sqlite:///jpdb_novels.db')
# metadata = MetaData()
# novels = Table('novels', metadata, autoload_with=engine)
# vocab = Table('vocab', metadata, autoload_with=engine)

# # Updating vocab table to check if vocab is blacklisted or not. ##

# with engine.begin() as conn:
#     select_stmt = select(novels)
#     result_proxy = conn.execute(select_stmt).fetchall()
#     current_novel_index = 1199

#     blacklisted_words = conn.execute(select(vocab).where(vocab.c.blacklisted == True))    
#     vocab_vid_set = {vocab_entry[0] for vocab_entry in blacklisted_words}
#     print(f"Starting length: {len(vocab_vid_set)}")

#     for entry in result_proxy[1200:]:
#         current_novel_index += 1
#         novel_id = entry[0]
#         novel_name = entry[1]
        
        
#         #Create the prebuilt deck with vocab in jpdb account
#         create_prebuilt(novel_id=novel_id, sid=SID)
#         deck_data = get_decks()['decks'][0]
#         user_deck_id = deck_data[0]

#         novel_lookup_stmt = select(novels)
#         novel_lookup_stmt = novel_lookup_stmt.where(novels.c.novel_id == novel_id)
#         current_novel_data = conn.execute(novel_lookup_stmt).fetchone()
#         blacklisted_word_count = int(current_novel_data[-1])
#         offset = 0

#         while offset < blacklisted_word_count: #deck with highest blacklisted vocab is 1187
#             if offset != 0:
#                 time.sleep(random.uniform(0.25, 0.75))

#             url = f"https://jpdb.io/deck?id={user_deck_id}&show_only=blacklisted&offset={offset}"
#             response = requests.get(url=url, headers=headers, cookies= cookies)

#             soup2 = BeautifulSoup(response.text, "html.parser")
#             vocabs = soup2.find_all("div", attrs={"class": 'vocabulary-spelling'})
            
            
#             for v in vocabs:
#                 vocab_vid = int(re.search(r'/vocabulary/(\d+)', v.find("a")['href']).group(1))
#                 vocab_vid_set.add(vocab_vid)
            
#             offset += 50
        
#         update_stmt = update(vocab).where(vocab.c.vid.in_(vocab_vid_set)).values(blacklisted = True)
#         conn.execute(update_stmt)
#         delete_deck(user_deck_id)
#         print(f"Deck index {current_novel_index} done")

#     blacklisted_words = conn.execute(select(vocab).where(vocab.c.blacklisted == True))        
#     vocab_vid_set = {vocab_entry[0] for vocab_entry in blacklisted_words}
#     print(f"Ending length: {len(vocab_vid_set)}")