import pandas as pd
import  math, os
from collections import defaultdict
from jpdb_functions import *
from sqlalchemy import create_engine, MetaData, select, Table
from sklearn.decomposition import NMF, PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler, Normalizer
from sklearn.pipeline import make_pipeline
import matplotlib.pyplot as plt
import numpy as np

SID = os.getenv("SID")

## Create connection to database ##
engine = create_engine('sqlite:///jpdb_project.db')
metadata = MetaData()

## Load the database tables using metadata ##
novels = Table('novels', metadata, autoload_with=engine)
vocab = Table('vocab', metadata, autoload_with=engine)                                      
novel_vocab = Table('novel_vocab', metadata, autoload_with=engine)
anki_vocab = Table('anki_vocab', metadata, autoload_with=engine)

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
