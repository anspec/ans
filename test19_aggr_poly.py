import sqlite3

class Animal():
  def __init__(self,title:str,name:str,age:int,sound:str):
    self.title = title
    self.name = name
    self.age = age
    self.sound = sound
    self.vid = ""

  def make_sound(self):
    print(f"{self.title} по имени {self.name} возраст {self.age} издает звук {self.sound}")

  def eat(self, what_eat:str):
    print(f"{self.title} по имени {self.name} ест {what_eat}")

  def moving(self):
    pass

class Bird(Animal):
  def __init__(self,title:str,name:str,age:int,sound:str,move:str,house:bool):
    super().__init__(title,name,age,sound)
    self.move = move
    self.house = house
    self.vid = "Bird"

  def moving(self):
    if self.house:
      h = "в доме"
    else:
      h = "в природе"
    print(f"Птица {self.title} по имени {self.name} {h} {self.move}")

def make_sound(self):
  super().make_sound()
  print(f"Эта птица {h} {self.move}")

class Mammal(Animal):
  def __init__(self,title:str,name:str,age:int,sound:str,move:str,house:bool,mass:int):
    super().__init__(title,name,age,sound)
    self.move = move
    self.house = house
    self.mass = mass
    self.vid = "Mammal"

  def make_sound(self):
    super().make_sound()
    print(f"Это млекопитающее массой {self.mass}кг.")

class Reptile(Animal):
  def __init__(self,title:str,name:str,age:int,sound:str,len:int):
    super().__init__(title,name,age,sound)
    self.len = len
    self.vid = "Reptile"

  def moving(self):
    print(f"Рептилия {self.title} по имени {self.name} ползает длиной {self.len} " )

  def make_sound(self):
    super().make_sound()
    print(f"Эта рептилия длиной {self.len}м.")

class User():
  def __init__(self,user_id:int,user_name:str):
    self.user_id = user_id
    self.user_name = user_name

  def get_id(self):
    return self._user_id

  def get_info(self):
    print(f"id:{self._user_id} name:{self._user_name} ")


class Zookeeper(User):
  def feed_animal(self, anml: Animal, feed_name: str):
    print(f"{self.user_name}, {anml.title} {anml.name}, возраст {anml.age} положил {feed_name}")

  def info(self):
    print(f"Зоотехник {self.user_name} id {self.user_id}")

class Veterinarian(User):
  def heal_animal(self, anml:Animal, heal_name: str):
    print(f"{self.user_name},  {anml.title} {anml.name}, возраст {anml.age}  лечит {heal_name}")

  def info(self):
    print(f"Ветеринар {self.user_name} id {self.user_id}")

class Zoo():
  def __init__(self,name:str):
    self.animals = []
    self.zookeepers = []
    self.veterinarians = []
    self.name = name

  def add_animal(self, anml:Animal):
    self.animals.append(anml)

  def del_animal(self, anml:Animal):
    if anml in self.animals:
      self.animals.remove(anml)

  def add_veterinarian(self, vet_id:int, vet_name:str):
    vet = Veterinarian(vet_id,vet_name)
    self.veterinarians.append(vet)

  def del_veterinarian(self, vet:Veterinarian):
    if vet in self.veterinarians:
      self.veterinarians.remove(vet)

  def add_zookeeper(self, zk_id:int, zk_name:str):
    zk = Zookeeper(zk_id,zk_name)
    self.zookeepers.append(zk)

  def del_zookeeper(self, zookep:Zookeeper):
    if zookep in self.zookeepers:
      self.zookeepers.remove(zookep)

  def animal_info():
    print("Живность:\n")
    for anm in self.animals:
      anm.make_sound()

  def zookeepers_info():
    print("Зоотехники:\n")
    for zookep in self.zookeepers:
      zookep.info()

  def veterinarians_info():
    print("Ветеринары:\n")
    for vet in self.veterinarians:
      vet.info()

  def info(self):
    print("Состав зоопарка\n")
    print("Живность:\n")
    for anm in self.animals:
      anm.make_sound()
    print("Зоотехники:\n")
    for zookep in self.zookeepers:
      zookep.info()
    print("Ветеринары:\n")
    for vet in self.veterinarians:
      vet.info()

  def saveDb(self):

    conn = sqlite3.connect("zoo.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS animals (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   vid TEXT,
                   title TEXT,
                   name TEXT,
                   age INTEGER,
                   sound TEXT, 
                   zoo_id INTEGER 
                  )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS zookeepers (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_name TEXT,
                   user_id INTEGER,
                   zoo_id INTEGER 
                   )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS veterinarians (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_name TEXT,
                   user_id INTEGER,
                   zoo_id INTEGER 
                 )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS zoo (
                    zoo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zoo_name TEXT,
                    )''')
    conn.commit()

    for anm in self.animals:
      cursor.execute("INSERT INTO animals (vid,title,name,age,sound,zoo_id) VALUES (?,?,?,?,?)",
                     (anm.vid, anm.title, ans.name, anm.age, anm.sound, zoo_id))
    for zk in self.zookeepers:
      cursor.execute("INSERT INTO zookeepers (user_name,user_id,zoo_id) VALUES (?,?,?)",
                     (zk.user_name, zk.user_id, zoo_id))
    for vet in self.veterinarians:
      cursor.execute("INSERT INTO veterinarians (user_name,user_id,zoo_id) VALUES (?,?,?)",
                     (vet.user_name, vet.user_id, zoo_id))

    conn.commit()
    conn.close()

  def restoreDb(self):

    self.animals.clear()
    self.zookeepers.clear()
    self.veterinarians.clear()

    conn = sqlite3.connect("zoo.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS animals (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   vid TEXT,
                   title TEXT,
                   name TEXT,
                   age INTEGER,
                   sound TEXT, 
                   zoo_id INTEGER 
                  )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS zookeepers (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_name TEXT,
                   user_id INTEGER,
                   zoo_id INTEGER 
                   )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS veterinarians (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_name TEXT,
                   user_id INTEGER,
                   zoo_id INTEGER 
                 )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS zoo (
                    zoo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zoo_name TEXT,
                    )''')
    conn.commit()

    cursor.execute("SELECT zoo_id FROM zoo WHERE name = ?",(self.name))
    row = cursor.fetchone()
    if row:
      zoo_id = row.zoo_id

      cursor.execute("SELECT * FROM animals WHERE zoo_id = ?",(zoo_id))
      result = cursor.fetchall()
      for row in result:
        if row.vid=="Bird":
          self.add_animal(Bird(row.title, row.name, row.age, row.sound, row.move, row.house))
        elif row.vid == "Mammal":
          self.add_animal(Mammal(row.title, row.name, row.age, row.sound, row.move, row.house, row.mass))
        elif row.vid == "Reptile":
          self.add_animal(Reptile(row.title, row.name, row.age, row.sound, row.len))

      cursor.execute("SELECT * FROM zookeepers WHERE zoo_id = ?", (zoo_id))
      result = cursor.fetchall()
      for row in result:
        self.add_zookeeper(row.user_id, row.user_name)

      cursor.execute("SELECT * FROM veterinarians WHERE zoo_id = ?", (zoo_id))
      result = cursor.fetchall()
      for row in result:
        self.add_veterinarian(row.user_id, row.user_name)

    conn.close()


zoo = Zoo("Зоопарк 1")
zoo.add_animal(Bird("Ворона","Яшка",4,"противно каркает","скачет",False))
zoo.add_animal(Bird("Голубь","Мищка",2,"курлычет","хлопает крыльями",False))
zoo.add_animal(Mammal("Медведь","noname",2,"орет","быстро бегает на 4 лапах",False, 200))
zoo.add_animal(Mammal("Собака","Бобик",5,"гавкает","бегает",True, 10))
zoo.add_animal(Reptile("Крокодил","Гена",8,"ныряет",5))
zoo.add_animal(Reptile("Анаконда","noname",10,"шелестит",10))

zoo.add_zookeeper(1,"Зоотехник 1")
zoo.add_zookeeper(2,"Зоотехник 2")
zoo.add_zookeeper(3,"Зоотехник 3")
zoo.add_zookeeper(4,"Зоотехник 4")

zoo.add_veterinarian(1,"Ветеринар 1")
zoo.add_veterinarian(2,"Ветеринар 2")
zoo.add_veterinarian(3,"Ветеринар 3")

zoo.info()
