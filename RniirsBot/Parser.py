import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sqlite3

def should_ignore_url(url):
    return '#' in url or 'PAGEN_2' in url or 'rss' in url

def get_title_link_intro_and_date(soup, url):
    results = []
    title_tag = soup.find('h1', class_='news-detail-title')
    intro_tag = soup.find('div', class_='news-detail-intro')
    date_tag = soup.find('span', class_='news-date-time')

    if title_tag and intro_tag and date_tag:
        title = title_tag.get_text(strip=True)
        intro = intro_tag.get_text(strip=True)
        date = date_tag.get_text(strip=True)
        results.append((title, url, intro, date))
    return results

def scrape_page(url, visited, topics, conn):
    if url in visited:
        return
    visited.add(url)

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"{e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    if soup.find('h1', class_='news-detail-title'):
        title_links_intros_dates = get_title_link_intro_and_date(soup, url)
        cursor = conn.cursor()
        for title, link, intro, date in title_links_intros_dates:
            for topic_name, topic_prefix in [
                ('биология', '/news/biology/'),
                ('медицина', '/news/medicine/'),
                ('физика', '/news/physics/'),
                ('химия', '/news/chemistry/'),
                ('математика', '/news/maths/'),
                ('агрокультура', '/news/agriculture/'),
                ('инженерные науки', '/news/engineering-sciences/'),
                ('науки о земле', '/news/earth-sciences/'),
                ('гуманитарные науки', '/news/humanitarian-sciences/'),
            ]:
                if topic_prefix in link:
                    cursor.execute("INSERT INTO news (topic, title, link, intro, date) VALUES (?, ?, ?, ?, ?)", (topic_name, title, link, intro, date))
                    conn.commit()
                    break

    links = soup.find_all('a', href=True)
    for link in links:
        full_url = urljoin(url, link['href'])
        if should_ignore_url(full_url):
            continue

        if (urlparse(full_url).path.startswith(('/news/biology/', '/news/medicine/', '/news/physics/', '/news/chemistry/', '/news/maths/', '/news/agriculture/', '/news/engineering-sciences/', '/news/earth-sciences/', '/news/humanitarian-sciences/')) and
            urlparse(full_url).netloc == urlparse(url).netloc):
            scrape_page(full_url, visited, topics, conn)



start_url = 'https://rscf.ru/news/'
visited_urls = set()
topics = {}

conn = sqlite3.connect('news_titles.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS news (
        topic TEXT,
        title TEXT,
        link TEXT,
        intro TEXT,
        date TEXT
    )
''')

scrape_page(start_url, visited_urls, topics, conn)
conn.close()

print("Данные успешно записаны в базу данных news_titles.db")
scrape_page(start_url, visited_urls, topics, conn)
conn.close()

print("Данные успешно записаны в базу данных news_titles.db")