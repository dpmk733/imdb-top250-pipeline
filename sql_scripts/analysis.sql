-- Validation / analysis queries

-- 1) Total rows
SELECT COUNT(*) AS movies_rows FROM analytics.movies_top250;
SELECT COUNT(*) AS cast_rows FROM analytics.movie_cast;

-- 2) Basic integrity checks
-- movies: rank should be unique (in a perfect top list)
SELECT rank, COUNT(*) AS cnt
FROM analytics.movies_top250
GROUP BY rank
HAVING COUNT(*) > 1
ORDER BY cnt DESC;

-- cast: primary key prevents duplicates per (imdb_id, cast_order)
-- but you can still check if any imdb_id has fewer/more than expected cast entries
SELECT imdb_id, COUNT(*) AS cast_count
FROM analytics.movie_cast
GROUP BY imdb_id
ORDER BY cast_count ASC, imdb_id
LIMIT 20;

-- 3) Latest run(s)
SELECT run_id, status, started_at, finished_at, movies_rows, cast_rows
FROM analytics.etl_runs
ORDER BY started_at DESC
LIMIT 5;

-- 4) Quick sample
SELECT * FROM analytics.movies_top250 ORDER BY rank LIMIT 10;
SELECT * FROM analytics.movie_cast ORDER BY imdb_id, cast_order LIMIT 20;
