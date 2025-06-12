from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import sqlite3


options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

browser = webdriver.Chrome(options=options)

browser.get("https://www.wildberries.ru/")
time.sleep(7)

browser.execute_script("window.scrollTo(0, 2000)")
time.sleep(10)

#<a draggable="false" class="product-card__link j-card-link j-open-full-product-card"
# href="https://www.wildberries.ru/catalog/119056371/detail.aspx"
# aria-label="Набор гитариста (классическая 7 8) DaVinci"></a>

conn = sqlite3.connect("product.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS product_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    image_path TEXT NOT NULL
)
''')

product_links = browser.find_elements(By.CSS_SELECTOR, "a.product-card__link[aria-label]")
i = 1
for product_link in product_links[:20]:
  name = product_link.get_attribute("aria-label")
  print(name)

  try:
    image_path = f"screens/product_{i}.png"
    product_link.screenshot(image_path)
    cursor.execute("INSERT INTO product_list (name, image_path) VALUES (?, ?)", (name, image_path))
    conn.commit()
    i+=1
  except:
    print(f"Не удалось сохранить скриншот по товару {i} {name}")

conn.close()

#В данном случае используется именно CSS-селектор:
#мы ищем все теги <a>, у которых класс product-card__link и присутствует атрибут
# aria-label. Атрибуты часто указываются в квадратных скобках.
#Таким образом, все искомые элементы сохранятся в переменную product_links.
# Далее перебираем найденные элементы в цикле for и извлекаем из каждого атрибут
# с названием товара:
#product_links = browser.find_elements(By.CSS_SELECTOR,
# "a.product-card__link[aria-label]")
#for product_link in product_links:
#    print(product_link.get_attribute("aria-label"))


browser.quit()