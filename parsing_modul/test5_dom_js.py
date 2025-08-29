# Напишите программу, с помощью которой можно искать информацию на Википедии
# с помощью консоли.
# 1. Спрашивать у пользователя первоначальный запрос.
# 2. Переходить по первоначальному запросу в Википедии.
# 3. Предлагать пользователю три варианта действий:
# листать параграфы текущей статьи;
# перейти на одну из связанных страниц — и снова выбор из двух пунктов:
# - листать параграфы статьи;
# - перейти на одну из внутренних статей.
# выйти из программы.

import time

from pygame.pypm import Input
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#Библиотека, которая позволяет вводить данные на сайт с клавиатуры
from selenium.webdriver.common.by import By
#Библиотека с поиском элементов на сайте
import random

def get_paragraphs(driver):
    """Возвращает список параграфов текущей статьи"""
    paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.mw-parser-output > p")
    return [p.text.strip() for p in paragraphs if p.text.strip()]

def get_internal_links(driver, limit=0):
    """Возвращает список внутренних ссылок (макс. limit)"""
    links = driver.find_elements(By.CSS_SELECTOR, "div.mw-parser-output a[href^='/wiki/']")
    results = []
    seen = set()
    for link in links:
        href = link.get_attribute("href")
        text = link.text.strip()
        if href and text and href.startswith("https://") and text not in seen:
            seen.add(text)
            results.append((text, href))
        if limit > 0 and len(results) >= limit:
            break
    return results

def main():
    # Инициализация браузера
    driver = webdriver.Chrome()  # Или webdriver.Firefox()
    driver.get("https://ru.wikipedia.org")

    query = input("Введите запрос для Википедии: ").strip()

    # Вводим запрос в поисковую строку
    search_box = driver.find_element(By.NAME, "search")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    time.sleep(2)

    while True:
        print("\nВыберите действие:")
        print("1. Листать параграфы текущей статьи")
        print("2. Перейти на связанную страницу")
        print("3. Выйти")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            paragraphs = get_paragraphs(driver)
            for i, paragraph in enumerate(paragraphs, 1):
                print(f"\n[{i}] {paragraph}")
                nxt = input("Нажмите Enter для следующего параграфа или 'q' для выхода: ")
                if nxt.lower() == "q":
                    break

        elif choice == "2":
            links = get_internal_links(driver, limit=10)
            if not links:
                print("Связанных ссылок не найдено.")
                continue

            print("\nВыберите ссылку:")
            for i, (text, href) in enumerate(links, 1):
                print(f"{i}. {text} ({href})")

            try:
                idx = int(input("Введите номер ссылки: "))
                if 1 <= idx <= len(links):
                    driver.get(links[idx - 1][1])
                    time.sleep(2)
                else:
                    print("Неверный номер")
            except ValueError:
                print("Ошибка ввода")

        elif choice == "3":
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор, повторите.")

    driver.quit()

if __name__ == "__main__":
    main()


# hatnotes = []
# for element in browser.find_elements(By.TAG_NAME, "div")
# # Чтобы искать атрибут класса
# cl = element.get.attribute("class")
# if cl == "hatnote navigation-not-searchable":
#     hatnotes.append(element)
#
# print(hatnotes)
# hatnote = random.choice(hatnotes)
# #Для получения ссылки мы должны найти на сайте тег "a" внутри тега "div"
# link = hatnote.find_element(By.TAG_NAME, "a").get.attribute("href")
# browser.get(link)

# str_find = Input("Введите свой запрос")
#
# browser.get("https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0")
# #Проверяем по заголовку, тот ли сайт открылся
# assert "Википедия" in browser.title
# time.sleep(5)
# #Находим окно поиска
# search_box = browser.find.element(By.ID, "searchInput")
# #Прописываем ввод текста в поисковую строку. В кавычках тот текст, который нужно ввести
# search_box.send_keys("Солнечная система")
# #Добавляем не только введение текста, но и его отправку
# search_box.send_keys(Keys.RETURN)
# time.sleep(5)
#
