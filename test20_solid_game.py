# Задание: Применение Принципа Открытости/Закрытости (Open/Closed Principle) в Разработке Простой Игры
#
# Цель: Цель этого домашнего задание - закрепить понимание и навыки применения принципа открытости/закрытости
# (Open/Closed Principle), одного из пяти SOLID принципов объектно-ориентированного программирования.
# Принцип гласит, что программные сущности (классы, модули, функции и т.д.) должны быть открыты для расширения,
# но закрыты для модификации.
#
# Задача: Разработать простую игру, где игрок может использовать различные типы оружия для борьбы с монстрами.
# Программа должна быть спроектирована таким образом, чтобы легко можно было добавлять новые типы оружия,
# не изменяя существующий код бойцов или механизм боя.

from abc import ABC, abstractmethod

class Weapon(ABC):
  @abstractmethod
  def __init__(self, name: str, name_from: str):
    self.name = name
    self.name_from = name_from

  def attack(self):
    pass


class Subject(ABC):
  @abstractmethod
  def __init__(self,name:str,name_to:str):
    self.name = name
    self.name_to = name_to
    self.weap = None

class Fighter(Subject):
  def __init__(self, name: str, name_to: str):
    super().__init__(name,name_to)

  def change_weapon(self, weap:Weapon):
    print(f"{self.name} выбирает {weap.name}")
    self.weap = weap

class Monster(Subject):
  def __init__(self, name: str, name_from: str):
    super().__init__(name,name_from)

class Sword(Weapon):
  def __init__(self, name: str, name_from: str):
    super().__init__(name, name_from)

  def attack(self):
    return f"ударил {self.name_from}"

class Bow(Weapon):
  def __init__(self, name: str, name_from: str):
    super().__init__(name, name_from)

  def attack(self):
    return f"пустил {self.name_from} стрелу"

def fm_attack( sub:Subject, sub_ag:Subject):
  if sub.weap != None:
    att = sub.weap.attack()
    print(f"{sub.name} {att} {sub_ag.name_to}.")
    print(f"{sub_ag.name} побежден!")

figh = Fighter("Боец","Бойцу")
monst = Monster("Монстр","в Монстра")

swrd = Sword("Меч","мечом")
bow = Bow("Лук","из лука")

figh.change_weapon(swrd)
fm_attack(figh,monst)

figh.change_weapon(bow)
fm_attack(figh,monst)
