#Python script to execute in PowerBI to connect PowerBI to sqlite3 db
import pandas as pd
import sqlite3
import os

#Connection to db
conn = sqlite3.connect('C:/Users/Admin/OneDrive/Documents/Coding Projects/JPDB Project/jpdb_project.db')


def load_all_tables(conn):
    tables = {}
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = cursor.fetchall()

    for table_name in table_names:
        tb_name = table_name[0]
        tables[tb_name] = pd.read_sql_query(f"SELECT * FROM {tb_name}", conn)
    
    return tables


#Load all tables in the db
tables = load_all_tables(conn)

novels = tables['novels']
novels

anki_vocab = tables['anki_vocab']
anki_vocab

vocab = tables['vocab']
vocab

novel_vocab = tables['novel_vocab']
novel_vocab

#Close the connection
conn.close()