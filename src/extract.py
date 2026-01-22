import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


IMDB_BASE = "https://www.imdb.com"
_TT_RE = re.compile(r"/title/(tt\d+)/?")


def _new_driver(selenium_remote_url, page_load_timeout):
    """Create a Remote Chrome driver that talks to the selenium container."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=en-US")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Remote(
        command_executor=selenium_remote_url,
        options=opts,
    )
    driver.set_page_load_timeout(page_load_timeout)
    return driver


def _looks_blocked(html):
    """Detect common IMDb 'robot check' / blocked pages."""
    lower = html.lower()
    return (
        "verify that you're not a robot" in lower
        or "javascript is disabled" in lower
        or "enable javascript" in lower
        or "robot check" in lower
    )


def _safe_text(el):
    if not el:
        return None
    return el.get_text(strip=True)


def extract_top_list(driver, imdb_top250_url, top_n, wait_timeout):
    """Extract movies from the IMDb Top Rated page (up to top_n)."""
    print(f"[extract] Opening Top page: {imdb_top250_url}")
    driver.get(imdb_top250_url)

    # Wait for any content at all (IMDb is JS-heavy).
    WebDriverWait(driver, wait_timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)

    html = driver.page_source
    if _looks_blocked(html):
        raise RuntimeError("IMDb returned a verification/blocked page. Try later or reduce TOP_N.")

    soup = BeautifulSoup(html, "lxml")

    # On chart pages, IMDb uses anchors with class "ipc-title-link-wrapper".
    anchors = soup.find_all("a", {"class": "ipc-title-link-wrapper"})

    movies = []
    seen_ids = set()

    for a in anchors:
        href = a.get("href") or ""
        if "/title/" not in href:
            continue

        m = _TT_RE.search(href)
        if not m:
            continue

        imdb_id = m.group(1)
        if imdb_id in seen_ids:
            continue

        li = a.find_parent("li")
        if not li:
            continue

        title_raw = a.get_text(strip=True) or ""

        # Common format: "1. The Shawshank Redemption"
        rank = None
        title = title_raw
        m2 = re.match(r"^(\d+)\.\s*(.+)$", title_raw)
        if m2:
            rank = int(m2.group(1))
            title = m2.group(2).strip()

        # Year (IMDb HTML changes sometimes; try a couple selectors)
        year = None
        for sel in [
            "span.cli-title-metadata-item",
            "span.sc-7ab21ed2-6",
        ]:
            y_el = li.select_one(sel)
            y_txt = _safe_text(y_el)
            if y_txt and y_txt.isdigit() and len(y_txt) == 4:
                year = int(y_txt)
                break

        # Rating (IMDb HTML changes; try a couple patterns)
        rating = None
        for sel in [
            "span.ipc-rating-star--rating",
            'div[data-testid="ratingGroup--imdb-rating"] span',
        ]:
            r_el = li.select_one(sel)
            r_txt = _safe_text(r_el)
            if r_txt:
                try:
                    rating = float(r_txt)
                    break
                except ValueError:
                    pass

        imdb_url = IMDB_BASE + href.split("?")[0]

        movies.append(
            {
                "imdb_id": imdb_id,
                "rank": rank,  # might be None; we fill missing later
                "title": title,
                "release_year": year,
                "rating": rating,
                "imdb_url": imdb_url,
            }
        )
        seen_ids.add(imdb_id)

        if len(movies) >= top_n:
            break

    # If rank was missing in HTML, fill it sequentially.
    for i, row in enumerate(movies, start=1):
        if row.get("rank") is None:
            row["rank"] = i

    print(f"[extract] Extracted {len(movies)} movies.")
    return movies


def extract_cast_for_movie(driver, imdb_id, imdb_url, cast_top_n, wait_timeout):
    """Extract top billed cast for a single movie."""
    print(f"[extract] Opening title page for cast: {imdb_url}")
    driver.get(imdb_url)

    WebDriverWait(driver, wait_timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1.5)

    html = driver.page_source
    if _looks_blocked(html):
        raise RuntimeError(f"Blocked when opening title page for {imdb_id}")

    soup = BeautifulSoup(html, "lxml")

    cast = []

    # IMDb title pages often mark actor links with data-testid="title-cast-item__actor".
    actor_links = soup.select('a[data-testid="title-cast-item__actor"]')

    for idx, a in enumerate(actor_links[:cast_top_n], start=1):
        actor_name = a.get_text(strip=True)
        actor_href = a.get("href") or ""
        actor_url = (IMDB_BASE + actor_href.split("?")[0]) if actor_href.startswith("/") else actor_href

        # Try to find character name within the same cast item container.
        container = a.find_parent(attrs={"data-testid": "title-cast-item"}) or a.find_parent("div")
        character_name = None
        if container:
            cand = (
                container.select_one('[data-testid="cast-item-characters-link"]')
                or container.select_one("ul li")
            )
            if cand:
                character_name = cand.get_text(" ", strip=True)

        cast.append(
            {
                "imdb_id": imdb_id,
                "cast_order": idx,
                "actor_name": actor_name,
                "character_name": character_name,
                "actor_url": actor_url,
            }
        )

    print(f"[extract] Extracted {len(cast)} cast members for {imdb_id}")
    return cast


def run_extraction(selenium_remote_url, imdb_top250_url, top_n, cast_top_n, page_load_timeout, wait_timeout):
    """High-level function: create driver, scrape movies + cast, close driver."""
    driver = _new_driver(selenium_remote_url, page_load_timeout)
    try:
        movies = extract_top_list(driver, imdb_top250_url, top_n, wait_timeout)

        all_cast = []
        for m in movies:
            try:
                all_cast.extend(
                    extract_cast_for_movie(
                        driver,
                        imdb_id=m["imdb_id"],
                        imdb_url=m["imdb_url"],
                        cast_top_n=cast_top_n,
                        wait_timeout=wait_timeout,
                    )
                )
            except Exception as e:
                print(f"[extract] WARNING: Cast extraction failed for {m.get('imdb_id')}: {e}")

        return movies, all_cast

    finally:
        try:
            driver.quit()
        except Exception:
            pass
