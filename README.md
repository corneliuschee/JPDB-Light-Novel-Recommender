<img width="1000" height="350" alt="📖JPDB_Novel_Recommender" src="https://github.com/user-attachments/assets/21c56806-79c1-4b15-9a82-eaa3f4500af9" />

---

# 📚 Project Overview

The **JPDB Light Novel Recommender System** is a simple command-line personalised Japanese reading tool that recommends *light novels optimized for your current vocabulary level*. By combining your **[Anki](https://apps.ankiweb.net/) flashcard vocabulary** with **[JPDB](https://jpdb.io) vocabulary frequency information**, 
it identifies novels that are suitable at your current vocabulary coverage and retention.

The system uses **Non-negative Matrix Factorization (NMF)** to generate personalized rankings for each novel based on:

- Your known vocabulary coverage. 
- Word frequency ranks for each novel.  
- Novel difficulty, sentence length, and length metrics (from [JPDB](https://jpdb.io/novel-difficulty-list)). 
- Weighted Anki flashcard review history to prioritize familiarity.

It outputs a **ranked list of light novels (top 5)** that best match your current Japanese level compared to generalised recommendations online that uses JLPT levels.

<img width="1447" height="119" alt="top5nmfscores" src="https://github.com/user-attachments/assets/336c05e3-8f9f-483e-ba8a-17720d0fe663" />

---

## 🛠️ Built With

- **Python 3.11.3** - Language of choice
- **pandas** - Data manipulation and analysis
- **NumPy** - Numerical operations
- **SQLAlchemy** - Database ORM for SQLite
- **scikit-learn** - NMF model, PCA, scaling, and pipelines
- **PowerBI** - Data visualization
- **[JPDB API](https://jpdb.stoplight.io/)** - Vocabulary and deck management
- Anki ***[Advanced Browser](https://ankiweb.net/shared/info/874215009)*** and ***[export cards/notes from browser with metadata to csv or xlsx](https://ankiweb.net/shared/info/1967530655)*** add-ons to export flashcard data

---

## ⚠️ Note on Usage

This project relies on personal Anki flashcard data and a custom JPDB dataset stored in a local SQLite database.  

Because these datasets and database schemas are unique to my setup, **installation and database seeding instructions are not provided**.  

If you wish to adapt or use this project, you will need to:

- Export and prepare your own Anki vocabulary data in a compatible format  
- Collect or generate a JPDB light novel dataset  
- Adjust the database schema and code to fit your data  

This repository is primarily for personal use and demonstration of the recommender system concept.

---

## 📸 Screenshots

### PowerBI sample visualisations
<img width="1958" height="600" alt="Screenshot 2025-07-18 130329" src="https://github.com/user-attachments/assets/177e6fc3-9c6a-42c1-8daa-bae30d0e3483" />

<img width="1946" height="600" alt="Screenshot 2025-07-18 130513" src="https://github.com/user-attachments/assets/36057188-6154-43dc-a8ea-a0ec51439ac8" />

### Variance against PCA features
<img width="1900" height="480" alt="image" src="https://github.com/user-attachments/assets/16bbdae6-6a26-468e-b8ac-7e749a805b56" />

### Snapshot of database table containing flashcard statistics
<img width="1454" height="734" alt="image" src="https://github.com/user-attachments/assets/ecfde31a-b230-4541-98a9-58c985c8e33e" />

---

## 💭 Reflections

This project helped to visualise my Anki vocabulary statistics through PowerBI, working with SQLite databases, practice EDA and learning about unsupervised learning (NMF) & Principal Component Analysis (PCA).

### Main learning points
- Working with SQLite database using SQLAlchemy
- Unsupervised learning (NMF) & Principal Component Analysis (PCA)
- PowerBI visualisations

### Challenges
- JPDB API documentation did not cover some API endpoints required for the project (eg. get vocabulary frequency rank), worked around by reverse-engineering parts of the API workflow by inspecting network traffic and testing undocumented endpoints.
- **API rate limits** required batching and delays when pulling vocab data, as web scraping is [not officially allowed](https://jpdb.io/terms-of-use) on the JPDB.io website.
- Ensuring the **recommender scores were meaningful** with limited vocabulary data (3.8k flashcards at time of completion) and light novel data (1475 novels only).
- To keep the project manageable at my current level of knowledge, I limited the number of features used in the recommender model, dropping several (e.g., ‘Unique Kanji (used once)’, ‘Unique Words’) to avoid unnecessary complexity.”

