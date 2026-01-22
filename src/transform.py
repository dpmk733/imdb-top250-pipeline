import pandas as pd


def transform(movies, cast):
    """Convert raw lists of dictionaries into cleaned pandas DataFrames."""
    movies_df = pd.DataFrame(movies)
    cast_df = pd.DataFrame(cast)

    if not movies_df.empty:
        movies_df["rank"] = pd.to_numeric(movies_df["rank"], errors="coerce").astype("Int64")
        movies_df["release_year"] = pd.to_numeric(movies_df["release_year"], errors="coerce").astype("Int64")
        movies_df["rating"] = pd.to_numeric(movies_df["rating"], errors="coerce")
        movies_df["title"] = movies_df["title"].astype(str).str.strip()
        movies_df["imdb_id"] = movies_df["imdb_id"].astype(str).str.strip()
        movies_df["imdb_url"] = movies_df["imdb_url"].astype(str).str.strip()

    if not cast_df.empty:
        cast_df["cast_order"] = pd.to_numeric(cast_df["cast_order"], errors="coerce").astype("Int64")
        cast_df["actor_name"] = cast_df["actor_name"].astype(str).str.strip()
        cast_df["character_name"] = cast_df.get("character_name", pd.Series(dtype="object")).astype("string")
        cast_df["imdb_id"] = cast_df["imdb_id"].astype(str).str.strip()
        cast_df["actor_url"] = cast_df.get("actor_url", pd.Series(dtype="object")).astype("string")

    return movies_df, cast_df
