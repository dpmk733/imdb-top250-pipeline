import pandas as pd

def transform_movies(data_list):
    """
    Converts raw list of dicts to a pandas DataFrame and performs cleaning.
    """
    if not data_list:
        print("No data to transform.")
        return pd.DataFrame()

    df = pd.DataFrame(data_list)
    
    # Ensure types
    df['ranking'] = df['ranking'].astype(int)
    df['year'] = df['year'].astype(int)
    df['rating'] = df['rating'].astype(float)
    
    # Filter out invalid rows
    df = df[df['imdb_id'] != "N/A"]
    
    print(f"Transformed data shape: {df.shape}")
    return df
