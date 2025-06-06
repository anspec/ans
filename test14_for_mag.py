#Ты разрабатываешь программное обеспечение для сети магазинов.
#Каждый магазин в этой сети имеет свои особенности, но также существуют общие
#характеристики, такие как адрес, название и ассортимент товаров.
#Ваша задача — создать класс `Store`,
#который можно будет использовать для создания различных магазинов.

class Store:
  def __init__(self,name:str,adres:str):
    self.name =  name
    self.adres = adres
    self.assort = []

  def addItems(self, name:str, price:int):
    items = {'name':name,'price':price}
    self.assort.append(items)
    n = len(self.assort)
    print(f"В {self.name} добавили товар {name} по цене {price}, в ассортименте {n} товаров")

  def delItems(self, name:str):
    for items in self.assort:
      if items['name'] == name:
        price = items['price']
        self.assort.remove(items)
        n = len(self.assort)
        print(f"В {self.name} исключили товар {name} по цене {price}, осталось {n} товаров")
        break

  def priceValue(self, name: str):
    price = None
    for items in self.assort:
      if items['name'] == name:
        price = items['price']
        break
    print(f"В {self.name} у товара {name} цена {price}")
    return price

  def changePrice(self, name: str, newprice:int):
      price = None
      for items in self.assort:
        if items['name'] == name:
          price = items['price']
          items['price'] = newprice
          print(f"В {self.name} у товара {name} цену {price} заменили на {newprice}")
          break

mag1 = Store("Ясенево_1","Соловьиный проезд, 1")
mag2 = Store("Коломенская_1","м.Коломенская")
mag3 = Store("Красная пресня","Малая Грузинская, 5")

mag1.addItems("Яблоки",100)
mag1.addItems("Груши",130)
mag1.addItems("Молоко",90)
mag1.addItems("Масло",250)
mag1.addItems("Сыр",100)

mag2.addItems("Яблоки",110)
mag2.addItems("Груши",120)
mag2.addItems("Молоко",95)
mag2.addItems("Масло",255)
mag2.addItems("Сыр",130)

mag3.addItems("Яблоки",150)
mag3.addItems("Груши",170)
mag3.addItems("Молоко",120)
mag3.addItems("Масло",290)
mag3.addItems("Сыр",160)

mag3.delItems("Груши")
mag3.priceValue("Яблоки")
mag3.changePrice("Яблоки", 180)
mag3.priceValue("Яблоки")

mag3.priceValue("Сыр")
mag3.changePrice("Сыр", 310)
mag3.priceValue("Сыр")

