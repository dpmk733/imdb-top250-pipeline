import requests
from bs4 import BeautifulSoup

def scrape_top_movies():
    url = "https://www.imdb.com/chart/top/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=1.0",
        "Cookie": "lc-main=en_US" 
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    movies = soup.find_all("li", class_="ipc-metadata-list-summary-item")

    results = []

    for li in movies:
        rank_el = li.select_one("div.ipc-signpost__text")
        if rank_el:
            ranking = rank_el.text.strip("#")
        else:
            ranking = None

        title_el = li.select_one("h3.ipc-title__text")
        if title_el:
            title = title_el.text.strip()
        else:
            title = None

        year_el = li.select("div.cli-title-metadata span")
        if year_el and len(year_el) > 0:
            year = year_el[0].text.strip()
        else:
            year = None

        rating_el = li.select_one("span.ipc-rating-star--rating")
        if rating_el:
            rating = rating_el.text.strip()
        else:
            rating = None

        link_el = li.select_one("a.ipc-title-link-wrapper")
        if link_el:
            link = "https://www.imdb.com" + link_el["href"]
        else:
            link = None

        if link:
            imdb_id = link.split("/title/")[1].split("/")[0]
        else:
            imdb_id = None

        movie_dict = {
            "ranking": ranking,
            "title": title,
            "year": year,
            "rating": rating,
            "imdb_id": imdb_id,
            "movie_url": link
        }

        results.append(movie_dict)

    return results
