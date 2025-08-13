import random
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import sqlite3

conn = sqlite3.connect("newstmsk.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS news (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               title TEXT,
               link TEXT,
               time TEXT,
               team TEXT 
               )''')

cursor.execute("DELETE FROM news")

conn.commit()

url = "https://tomsk.ru/"
response = requests.get(url)
response.encoding = 'utf-8'
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all('div', class_="post-item__info", limit=100)

    for i in range(len(titles)):  # 0, 1, 2, 3, 4
        title_div = titles[i]

        stru = {'title':'','link':'','time':'','team':''}
        for j in range(len(title_div.contents)):  # 0, 1, 2, 3, 4
            title_div_ch = title_div.contents[j]

            if title_div_ch.name == 'div':
                stru_key = ''
                if title_div_ch.has_attr("class"):
                   if 'post-item__categories' in title_div_ch["class"]:
                       stru_key = 'team'
                   elif 'post-item__time' in title_div_ch["class"]:
                           stru_key = 'time'
                   elif 'post-item__title' in  title_div_ch["class"]:
                           stru_key = 'title'
                   else:
                       continue
                if stru_key != '':
                    title = title_div_ch.contents[0]
                    if title.name=='a' and title.has_attr("href"):
                        link = title["href"]
                        if link.startswith("/"):
                            link = url.rstrip("/") + link

                        if stru_key=='title':
                            stru['link'] = link
                        stru[stru_key] = title.text.strip()
                    else:
                        stru[stru_key] = title_div_ch.text.strip()

        #if stru['time'] != '':
        cursor.execute("INSERT INTO news (title,link,team,time) VALUES (?,?,?,?)", (stru['title'],stru['link'],stru['team'],stru['time']))
        print(f"{stru['team']}: {stru['title']} от {stru['time']} Ссылка: {stru['link']}")
        conn.commit()

else:
    print(f"Ошибка при загрузке страницы {response.status_code}")

conn.close()


