import psycopg2
import os
import time
import pandas as pd

def get_db_connection():
    # We add a small sleep just to give Postgres a chance to wake up
    # since we removed the retry logic.
    time.sleep(5) 
    
    return psycopg2.connect(
        host="imdb_db",
        database="imdb",
        user="postgres",
        password="postgres"
    )

def load_movies(df):
    if df.empty:
        print("No data to load.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Force Column Order
    df = df[['imdb_id', 'ranking', 'title', 'year', 'rating', 'movie_url']]

    # 2. Prepare Query
    insert_query = """
    INSERT INTO movies (imdb_id, ranking, title, year, rating, movie_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (imdb_id) DO UPDATE 
    SET ranking = EXCLUDED.ranking,
        rating = EXCLUDED.rating;
    """

    # 3. Convert Data
    data_tuples = list(df.itertuples(index=False, name=None))

    # 4. Execute and Commit
    cur.executemany(insert_query, data_tuples)
    conn.commit()
    
    print(f"SUCCESS: Loaded {len(df)} movies into the database.")

    cur.close()
    conn.close()
