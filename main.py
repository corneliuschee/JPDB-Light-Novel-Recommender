import pandas as pd
import time, random, datetime, math, json, sqlite3, os
from collections import defaultdict
from jpdb_functions import *
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Boolean, Float, select, insert, update, delete, and_, or_, func, Table, Text, ForeignKey, text, delete, DateTime
from sklearn.decomposition import NMF, PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler, Normalizer
from sklearn.pipeline import make_pipeline
import matplotlib.pyplot as plt
import numpy as np

SID = os.getenv("SID")


### EDA ###

##JPDB Novel Data ##
# df = pd.read_csv("jpdb_novel_data.csv")
# df.columns = df.columns.str.strip()
# # print(df.head())
# # print(df.shape)
# # print(df.columns)
# # print(df.describe())
# # print(df.dtypes)


# #Drop useless columns
# df.drop(['Unnamed: 0', 'Unnamed: 15', 'Known unique words'], axis=1, inplace= True)
# # print(df.head())


# #Check for any duplicates / NA values
# # print(df.nunique())
# # print(df.isna().any())


## Anki vocab df ##
# anki_core_df = pd.read_excel("anki_core.xlsx", engine='openpyxl')
# # print(anki_core_df.tail())
# # print(anki_core_df.columns)

# #Drop "WordReading" as that column is only populated by cards in the Mining deck"
# anki_core_df.drop(["WordReadingHiragana"], inplace=True, axis=1)
# anki_core_df.rename(columns={"Sort Field": "Vocab"}, inplace=True)
# # print(anki_core_df.tail())


# anki_mining_df = pd.read_excel("anki_mining.xlsx", engine='openpyxl')
# # print(anki_mining_df.tail())
# # print(anki_mining_df.columns)

# #Drop the "Reading" Column as that column is only populated by cards in the Core 2.3k deck.
# anki_mining_df.drop(["Reading"], inplace=True, axis = 1)
# anki_mining_df.rename(columns={"WordReadingHiragana": "Reading", "Sort Field": "Vocab"}, inplace=True)
# # print(anki_mining_df.tail())


# ## Concat the two df together ##
# anki_df = pd.concat([anki_core_df, anki_mining_df], ignore_index = True)
# # print(anki_df.head())
# # print(len(anki_df))

# anki_df['Vocab'] = anki_df["Vocab"].str.strip()
# anki_df['Reading'] = anki_df['Reading'].str.strip()
# #Length increased to 4353, confirms successful concatanation


# ## Check for duplicate vocab and drop them based on Vocab and Reading column ##
# anki_duplicates = anki_df.duplicated(subset=['Vocab', "Reading"])
# # print(anki_df[anki_duplicates])
# # print(f"Number of duplicates: {len(anki_df[anki_duplicates])}")

# print(f"Initial length before dropping duplicates: {len(anki_df)}")
# anki_df = anki_df[~anki_duplicates]
# print(f"Final length before dropping duplicates: {len(anki_df)}")

# #Check datatypes
# print(anki_df.dtypes)

# #Filter out cards that haven't been reviewed
# anki_df = anki_df[~anki_df['Due'].astype(str).str.contains('New')]
# # print(len(anki_df))

# #Blacklist all cards in the Core2.3k deck
# anki_df['Blacklisted'] = (anki_df['Deck'] == 'Core2.3k Version 3')

# #Drop card column as its irrelevant
# anki_df.drop(['Card'], inplace=True, axis=1)

# #Check which columns have NaN values
# nan_cols = [i for i in anki_df.columns if anki_df[i].isna().any()]
# print(nan_cols) #Only "Again Count" column has NaN values

# #Fill NaN values with 0
# anki_df.fillna(0, inplace=True)
# anki_df['Again Count'] = anki_df['Again Count'].astype(int)

# #Change Percent Correct column to float datatypes
# anki_df['Percent Correct'] = anki_df['Percent Correct'].astype(str).str.strip('%')
# anki_df['Percent Correct'] = anki_df['Percent Correct'].astype(float)


# #Change Due Column to datetime
# anki_df['Due'] = anki_df['Due'].astype('datetime64[s]')

# #Create vid, sid, frequency rank columns
# anki_df = anki_df.apply(enrich_vocab, axis = 1)


# #Save new df as a separate csv
# anki_df.to_csv(os.path.join(os.getcwd(), 'anki_df.csv'))

# #Load new csv
# anki_df = pd.read_csv("anki_df.csv")
# print(anki_df.head())
# anki_df.drop(columns=['Unnamed: 0'], inplace=True)
# print(anki_df.head())

# #Check for NaN values
# print(anki_df.isnull().sum()) #71 rows have NaN values in the frequency rank
# #Filter the rows
# with pd.option_context("display.max_rows", 71):
#     print(anki_df[anki_df.isna().any(axis = 1)])

# #Exclude these rows since 71 is a low number out of 4000+ rows
# anki_df = anki_df.dropna(subset=['frequency rank'])
# print(anki_df.isnull().sum()) #0 Rows with NaN values
# anki_df['Due'] = pd.to_datetime(anki_df['Due'], errors='coerce')
# print(anki_df)


# #Check for duplicates in vid and drop them:
# anki_df = anki_df.drop_duplicates(subset=['vid'])

## Create connection to database ##
engine = create_engine('sqlite:///jpdb_project.db')
metadata = MetaData()



## Schema of novels table ##
# novels_table = Table(
#     'novels', metadata,
#     Column('novel_id', Integer(), unique=True, primary_key=True),
#     Column('Title', String(255)),
#     Column('Length (in words)', Integer()),
#     Column('Unique words', Integer()),
#     Column('Unique words (used once)', Integer()),
#     Column('Unique kanji', Integer()),
#     Column('Unique kanji (used once)', Integer()),
#     Column('Unique kanji readings', Integer()),
#     Column('Average difficulty', Integer()),
#     Column('Peak difficulty (90th percentile)', Integer()),
#     Column('Average sentence length', Float()),
#     Column('Characters', Integer()),
#     Column('Volumes', Integer()),
#     Column('Blacklisted unique words', Integer())
# )

# metadata.create_all(engine)
novels = Table('novels', metadata, autoload_with=engine)

## Insert data into novels database ##
# with engine.begin() as conn:
#     values_list = []
#     for index, row in df.iterrows():
#         novel_dict = {
#             "novel_id": row['novel_id'],
#             "Title": row['Title'],
#             "Length (in words)": row['Length (in words)'],
#             "Unique words": row['Unique words'],
#             "Unique words (used once)": row['Unique words (used once)'],
#             'Unique kanji': row['Unique kanji'],
#             'Unique kanji (used once)': row['Unique kanji (used once)'],
#             'Unique kanji readings': row['Unique kanji readings'],
#             "Average difficulty": int(row['Average difficulty'].split('/')[0]),
#             "Peak difficulty (90th percentile)": int(row['Peak difficulty (90th percentile)'].split('/')[0]),
#             "Average sentence length": row['Average sentence length'],
#             "Characters": row['Characters'],
#             "Volumes": row['Volumes'],
#             "Blacklisted unique words": row['Blacklisted unique words']
#         }

#         values_list.append(novel_dict)
        
#     stmt = insert(novels_table)
#     result_proxy = conn.execute(stmt, values_list)
#     print(result_proxy.rowcount) #Inserted 1475 rows



# Schema for vocab table ##
# vocab_table = Table(
#     'vocab', metadata,
#     Column('vid', Integer(), unique = True, primary_key=True),
#     Column('sid', Integer(), nullable=False),
#     Column('spelling', String(255)),
#     Column('reading', String(255)),
#     Column('frequency_rank', Integer()),
#     Column('meanings', Text()),
#     Column('blacklisted', Boolean())
# )

# metadata.create_all(engine)
vocab = Table('vocab', metadata, autoload_with=engine)



## Create a many to many datebase schema. ##
# novel_vocab_table = Table(
#     'novel_vocab', metadata,
#     Column('novel_id', Integer(), ForeignKey('novels.novel_id')),
#     Column('vid', Integer(), ForeignKey('vocab.vid'))
# )

# metadata.create_all(engine)                                        
novel_vocab = Table('novel_vocab', metadata, autoload_with=engine)



##Create Anki vocab database schema ##
# anki_vocab_table = Table('anki_vocab', metadata,
#                          Column("id", Integer(), primary_key=True, autoincrement=True),
#                          Column("vocab", String(255), nullable=False),
#                          Column("reading", String(255)),
#                          Column("vid", Integer(), unique=True),
#                          Column("sid", Integer()),
#                          Column("frequency_rank", Integer()),
#                          Column("percent_correct", Float()),
#                          Column("due", DateTime()),
#                          Column("again_count", Integer()),
#                          Column("reviews", Integer()))

# metadata.create_all(engine)
anki_vocab = Table('anki_vocab', metadata, autoload_with=engine)


##Adding anki vocab to db##
# with engine.begin() as connection:
#     insert_stmt = insert(anki_vocab)
#     anki_vocab_value_list = []
#     for index, row in anki_df.iterrows():
#         anki_vocab_dict = {
#             "id": index,
#             "vocab": row['Vocab'],
#             "reading": row['Reading'],
#             "vid": row['vid'],
#             "sid": row['sid'],
#             "frequency_rank": row['frequency rank'],
#             "percent_correct": row['Percent Correct'],
#             "again_count": row['Again Count'],
#             "due": row['Due'],
#             "reviews": row['Reviews']
#         }
    
#         anki_vocab_value_list.append(anki_vocab_dict)
    
#     connection.execute(insert_stmt, anki_vocab_value_list)



## Adding vocab data to db ##
# with engine.begin() as connection:
#     select_stmt = select(novels)
#     result_proxy = connection.execute(select_stmt).fetchall()
#     current_novel_index = 1299

#     #Create a set to track which vids (vocab id) have been seen
#     select_vid_stmt = select(vocab.c.vid)
#     vid_results = connection.execute(select_vid_stmt)
#     seen_vids = set(row[0] for row in vid_results)

#     for entry in result_proxy[1300:]:
#         current_novel_index += 1
#         novel_id = entry[0]
#         novel_name = entry[1]
        
        
#         #Create the prebuilt deck with vocab in jpdb account
#         create_prebuilt(novel_id=novel_id, sid=SID)
#         deck_data = get_decks()['decks'][0]
#         user_deck_id = deck_data[0]

#         deck_vocab_list = get_vocab(user_deck_id=user_deck_id)
#         vocab_data = lookup_vocab(deck_vocab_list)

#         vocab_value_list = []
#         novel_vocab_value_list = []
#         for vocab_entry in vocab_data:
            
#             vid = vocab_entry[0]

#             novel_vocab_dict = {
#                 "novel_id": novel_id,
#                 "vid": vid
#             }

#             novel_vocab_value_list.append(novel_vocab_dict)
            
#             if vid in seen_vids:
#                 continue
            
#             seen_vids.add(vid)

#             replace_empty_values(vocab_entry)
#             vocab_dict = {
#                 "vid": vid,
#                 "sid": vocab_entry[1],
#                 "spelling": vocab_entry[2],
#                 "reading": vocab_entry[3],
#                 "frequency_rank": int(vocab_entry[4]),
#                 "meanings": json.dumps(vocab_entry[5])
#             }
            
            
#             vocab_value_list.append(vocab_dict)
        
#         #Checks if vocab_value list is empty to prevent inserting empty list into table
#         if len(vocab_value_list) != 0:
#             vocab_insert_stmt = insert(vocab)
#             vocab_result_proxy = connection.execute(vocab_insert_stmt, vocab_value_list)

#         novel_vocab_insert_stmt = insert(novel_vocab)
#         novel_vocab_result_proxy = connection.execute(novel_vocab_insert_stmt, novel_vocab_value_list)

        
#         time.sleep(random.uniform(1, 3))
#         delete_deck(user_deck_id)
#         print(f"Vocab for {novel_name} added to table. Novel index {current_novel_index} done.")

# print("Done with updates")

## Updating new column blacklisted in vocab with False values for those not blacklisted.
# with engine.begin() as conn:
#     update_stmt = update(vocab).where(vocab.c.blacklisted == None).values(blacklisted = False)
#     conn.execute(update_stmt)

# with engine.begin() as conn:
#     anki_select_stmt = select(anki_vocab.c.vid)
#     anki_vids = conn.execute(anki_select_stmt).fetchall()


#     vocab_select_stmt = select(vocab.c.vid)
#     vocab_vids = conn.execute(vocab_select_stmt).fetchall()
   

#     i = 0
#     for vid in anki_vids:
#         if vid in vocab_vids:
#             i += 1
#     print(i) #3868 anki vocab inside vocab table out of 3876 anki vocab
    

## Modelling ##

#We will use NMF to build a reccomender system.
with engine.begin() as conn:
    known_vids = {anki_vid for (anki_vid, ) in conn.execute(select(anki_vocab.c.vid)).fetchall()}
    novel_vocab_rows = conn.execute(select(novel_vocab.c.novel_id, novel_vocab.c.vid)).fetchall()

    #anki_score = percent_correct × log(1 + review_count)
    #We will compute all anki vocab and ignore if vocab is blacklisted in novel since its a very small proportion
    anki_vocab_rows = conn.execute(select(anki_vocab.c.vid, anki_vocab.c.percent_correct, anki_vocab.c.reviews)).fetchall()
    anki_vocab_weighted_score_dict = {
        vid: round(float(p_correct) * math.log10(1 + int(reviews)), 3)
        for vid, p_correct, reviews in anki_vocab_rows
        }   #Use log to balance between accuracy and quantity. Without it, highly reviewed words will dominate.
    
    
    #Compute only vocab freq rank for non blacklisted vocab
    vocab_freq_rank = {
        vid: rank
        for vid, rank, blacklisted in conn.execute(select(vocab.c.vid, vocab.c.frequency_rank, vocab.c.blacklisted)).fetchall() if blacklisted == 0
    }

    df_novel_to_vids = defaultdict(set)
    df_anki_weighted_scores = defaultdict(list)
    

    for novel_id, vid in novel_vocab_rows:
        df_novel_to_vids[novel_id].add(vid)
        if vid in anki_vocab_weighted_score_dict:
            df_anki_weighted_scores[novel_id].append(anki_vocab_weighted_score_dict[vid])


    novel_coverage_dict =  {
        nid: round(len(known_vids & vids) / len(vids), 3) if vids else 0
        for nid, vids in df_novel_to_vids.items()
    }
    

    novel_anki_weighted_avg = {
        nid: round(sum(scores) / len(scores), 3)
        for nid, scores in df_anki_weighted_scores.items() if scores
    }

    novel_freq_rank_avg = {
    nid: round(sum(vocab_freq_rank[vid] for vid in vids if vid in vocab_freq_rank) / len(vids), 2)
    for nid, vids in df_novel_to_vids.items() if vids
    }
    

    novel_df = pd.read_sql_table('novels', con=engine)
    novel_df.columns = [str(col) for col in novel_df.columns]
    novel_df['Coverage'] = novel_df['novel_id'].map(novel_coverage_dict).fillna(0)
    novel_df['Anki Weighted Average'] = novel_df['novel_id'].map(novel_anki_weighted_avg).fillna(0)
    novel_df['Avg Vocab Freq Rank'] = novel_df['novel_id'].map(novel_freq_rank_avg).fillna(0)
    novel_df = novel_df.drop(columns=['novel_id', 'Volumes',  'Average difficulty', 'Unique kanji readings', 'Unique kanji (used once)', 'Unique words (used once)', 'Unique words', 'Blacklisted unique words'])
    
    novel_df = novel_df.set_index('Title')
    train_data = novel_df.copy()
    
    
    ##Check for instrinsic dimension of novel data.
    standardscaler = StandardScaler()
    pca = PCA()
    pipeline = make_pipeline(standardscaler, pca)
    pipeline.fit(train_data)
    features = range(pca.n_components_)

    # plt.bar(features, pca.explained_variance_)
    # plt.xticks(features)
    # plt.ylabel('variance')
    # plt.xlabel('PCA feature')
    # plt.show() #Elbow at about component 2 / 3 (pca feature 1 / 2). We will use n_components = 3

    
    # Scale features using MinMaxScaler
    scaler = MinMaxScaler()
    nmf = NMF(n_components=3)
    normalizer = Normalizer() #To prevent inflated NMF scores from feature rows with high magnitudes.
    pipeline = make_pipeline(scaler, nmf, normalizer)
    
    nmf_features = pipeline.fit_transform(train_data)
    nmf_components = nmf.components_
    #Topic 0 have higher weights on 'Unique Kanji', 'Anki Weighted Average' and 'Avg Vocab Freq Rank' colummns, corresponds to Kanji difficulty
    #Topic 1 have higher weights on 'Peak Difficulty (90th percentile)' and 'Coverage', corresponds to Challenging but readable vocab
    #Topic 2 have higher weights on 'Unique Kanji', 'Peak difficulty (90th percentile)' and 'Anki Weighted Average', corresponds to Balance between Kanji familiarity and difficulty

    topic_weights = np.array([0.5, 1.5, -0.5])
    novel_df['NMF_Score'] = nmf_features @ topic_weights # @ operator act as matrix multiplication not decorator
    recommended_novels = novel_df.sort_values('NMF_Score', ascending=False)
    #Get top 5 recommended novels to read based on current anki vocab knowledge
    print(recommended_novels.sort_values('NMF_Score', ascending=False).head(5))

