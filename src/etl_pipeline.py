from extract import scrape_top_movies
from transform import transform_movies
from load import load_movies

def run_pipeline():
    print("Starting extraction...")
    raw = scrape_top_movies()

    print("Transforming data...")
    df = transform_movies(raw)

    print("Loading into PostgreSQL...")
    load_movies(df)

    print("ETL pipeline finished.")

if __name__ == "__main__":
    run_pipeline()
