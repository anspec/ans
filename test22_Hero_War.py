# Задание: Разработать консольную игру "Битва героев" с использованием классов
# и разработать план проекта по этапам/или создать kanban доску для работы над данным
# проектом
#
# Общее описание:
# Создайте простую текстовую боевую игру, где игрок и компьютер управляют героями с различными
# характеристиками. Игра состоит из раундов, в каждом раунде игроки по очереди наносят урон
# друг другу, пока у одного из героев не закончится здоровье.
#
# Требования:
# Используйте ООП (Объектно-Ориентированное Программирование) для создания классов героев.
# Игра должна быть реализована как консольное приложение.
#
# Классы:
# Класс Hero:
#
# Атрибуты:
# Имя (name)
#
# Здоровье (health), начальное значение 100
# Сила удара (attack_power), начальное значение 20
#
# Методы:
# attack(other): атакует другого героя (other), отнимая здоровье в размере своей силы удара
# is_alive(): возвращает True, если здоровье героя больше 0, иначе False
#
# Класс Game:
# Атрибуты:
# Игрок (player), экземпляр класса Hero
# Компьютер (computer), экземпляр класса Hero
#
# Методы:
# start(): начинает игру, чередует ходы игрока и компьютера, пока один из героев не умрет.
# Выводит информацию о каждом ходе (кто атаковал и сколько здоровья осталось у противника)
# и объявляет победителя.

from abc import ABC, abstractmethod
import random

class Hero(ABC):
  def __init__(self,name:str):
    self.name = name
    self.health = 100
    self.attack_power = 20

class subject(Hero):
  def attack(self, other:Hero):
    other.health = other.health - self.attack_power

  def is_alive(self):
    return (self.health > 0)

class Game():
  def __init__(self,player:subject,computer:subject):
    self.player = player
    self.computer = computer

  def start(self):
    first = random.choice(["player", "computer"])
    while self.player.is_alive() and self.computer.is_alive():
      if first == "player":
        self.player.attack(self.computer)
        print(f"{self.player.name} атакует {self.computer.name}, после атаки у {self.computer.name} здоровье = {self.computer.health}")
        first = "computer"
      elif first == "computer":
        self.computer.attack(self.player)
        print(f"{self.computer.name} атакует {self.player.name}, после атаки у {self.player.name} здоровье = {self.player.health}")
        first = "player"

    if self.player.is_alive():
      print(f"Победил {self.player.name}")

    if self.computer.is_alive():
      print(f"Победил {self.computer.name}")

pl = subject("Игрок")
comp = subject("Компьютер")

game = Game(pl,comp)
game.start()