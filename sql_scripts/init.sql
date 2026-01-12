CREATE TABLE IF NOT EXISTS movies (
    imdb_id TEXT PRIMARY KEY,
    ranking INTEGER,
    title TEXT,
    year INTEGER,
    rating FLOAT,
    movie_url TEXT
);
