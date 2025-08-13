import requests
from bs4 import BeautifulSoup
import time

def scrape_quotes(pages=3, delay=1):
    base_url = "http://quotes.toscrape.com/page/{}/"
    all_quotes = []

    for page in range(1, pages+1):
        url = base_url.format(page)
        print(f"Парсим страницу {page}: {url}")
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Пропускаем страницу {page}, код {resp.status_code}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        quotes = soup.find_all("div", class_="quote")

        for q in quotes:
            text = q.find("span", class_="text").get_text()
            author = q.find("small", class_="author").get_text()
            tags = [t.get_text() for t in q.find_all("a", class_="tag")]
            all_quotes.append({
                "text": text,
                "author": author,
                "tags": tags
            })
        time.sleep(delay)  # дружелюбная задержка

    # Выводим результат
    for i, q in enumerate(all_quotes, start=1):
        print(f"{i}. «{q['text']}» — {q['author']} [{', '.join(q['tags'])}]")

if __name__ == "__main__":
    scrape_quotes(pages=10, delay=0.5)