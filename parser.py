import requests
from bs4 import BeautifulSoup

# URL главной страницы CoinMarketCap
#url = 'https://v8.1c.ru/vse-programmy-1c/'
url = 'https://coinmarketcap.com/'

# Заголовки для имитации запроса от браузера
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# Отправляем GET-запрос
response = requests.get(url, headers=headers)

# Проверяем успешность запроса
if response.status_code == 200:
    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(response.content, 'lxml')

# Проверяем успешность запроса
if response.status_code == 200:
    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(response.content, 'lxml')

    # Находим таблицу с криптовалютами
    table = soup.find('table')

    # Проверяем, что таблица найдена
    if table:
        # Получаем все строки таблицы
        rows = table.find_all('tr')

        # Перебираем строки, пропуская заголовок
        for row in rows[1:]:
            # Получаем все ячейки в строке
            cols = row.find_all('td')
            if len(cols) >= 4:
                # Извлекаем название и цену криптовалюты
                name = cols[2].get_text(strip=True)
                price = cols[3].get_text(strip=True)
                print(f'{name}: {price}')
    else:
        print('Таблица с криптовалютами не найдена.')
else:
    print(f'Ошибка при запросе страницы: {response.status_code}')