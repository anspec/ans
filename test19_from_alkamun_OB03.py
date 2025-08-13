class Animal:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def make_sound(self):
        pass

    def eat(self):
        print(f"{self.name} ест")

    def __json__(self):
        pass

class Bird(Animal):
    def __init__(self, name, age, sound):
        super().__init__(name, age)
        self.sound = sound

    def make_sound(self):
        print(f"{self.name} издаёт звук {self.sound}")

    def eat(self):
        print(f"{self.name} клюёт")

    def __json__(self):
        return { 'class': 'Bird', 'name': self.name, 'age': self.age, 'sound': self.sound }

class Mammal(Animal):
    def __init__(self, name, age, sound):
        super().__init__(name, age)
        self.sound = sound

    def make_sound(self):
        print(f"{self.name} издаёт звук {self.sound}")

    def __json__(self):
        return { 'class': 'Mammal', 'name': self.name, 'age': self.age, 'sound': self.sound }

class Reptile(Animal):
    def __init__(self, name, age, sound=None):
        super().__init__(name, age)
        self.sound = sound

    def make_sound(self):
        if not self.sound:
            print(f"{self.name} молчит")
            return

        print(f"{self.name} издаёт звук {self.sound}")

    def __json__(self):
        return { 'class': 'Reptile', 'name': self.name, 'age': self.age, 'sound': self.sound }


class Post:
    def __init__(self, name):
        self.name = name

    def print(self):
        pass

    def __json__(self):
        pass


class ZooKeeper(Post):
    def print(self):
        print(f"{self.name} - смотритель зоопарка")

    def feed_animal(self):
        print(f"Смотритель зоопарка {self.name} кормит животных")

    def __json__(self):
        return {'class': 'ZooKeeper', 'name': self.name}


class Veterinarian(Post):
    def print(self):
        print(f"{self.name} - ветеринар")

    def heal_animal(self):
        print(f"Ветеринар {self.name} лечит животных")

    def __json__(self):

class Zoo:
    def __init__(self, address=""):
        self.address = address
        self.__animals = []
        self.__staff = []

    def add_animals(self, animals):
        for animal in animals:
            self.__animals.append(animal)

    def add_worker(self, worker):
        self.__staff.append(worker)
        return worker

    def print(self):
        print(f"Зоопарк, {self.address}")

        print("Животные:")
        for animal in self.__animals:
            print(f"{animal.name}, {animal.age}")

        print()
        print("Сотрудники:")
        for worker in self.__staff:
            worker.print()

    def save_to_file(self, file_name):
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(self, f, default=lambda o: o.__json__() if hasattr(o, '__json__') else None, indent=2)
        print(f"Информация сохранена в файл {file_name}")

    def load_from_file(self, file_name):
        if not os.path.exists(file_name):
            print(f"Не найден файл {file_name}")
            return

            with open(file_name, "r") as f:
                res = json.load(f)

            self.address = res["address"]
            self.__animals.clear()
            self.__staff.clear()

            for item in res["animals"]:
                if item["class"] == "Bird":
                    self.__animals.append(Bird(item["name"], item["age"], item["sound"]))
                elif item["class"] == "Mammal":
                    self.__animals.append(Mammal(item["name"], item["age"], item["sound"]))
                elif item["class"] == "Reptile":
                    self.__animals.append(Reptile(item["name"], item["age"], item["sound"]))

            for item in res["staff"]:
                if item["class"] == "ZooKeeper":
                    self.__staff.append(ZooKeeper(item["name"]))
                elif item["class"] == "Veterinarian":
                    self.__staff.append(Veterinarian(item["name"]))

            print(f"Информация загружена из файла {file_name}")

    def __json__(self):
        return {'address': self.address, 'animals': self.__animals, 'staff': self.__staff}

    def animal_sound(animals):
        for animal in animals:
            animal.make_sound()

        # 1, 2 класс Animal и наследники
        animals = [
            Bird("Кукушка", "2 года", "ку-ку"),
            Mammal("Осёл", "3 года", "иа-а"),
            Reptile("Змея", "1 год", "ш-ш-ш"),
            Reptile("Черепаха", "6 мес")
        ]

        # 3 полиморфизм
        animal_sound(animals)
        print()

        # 4 класс `Zoo`
        zoo = Zoo("село Кукуево")
        zoo.add_animals(animals)

        # 5. классы для сотрудников,
        zk = zoo.add_worker(ZooKeeper("Ольга Николаевна"))
        vet = zoo.add_worker(Veterinarian("Сергей Петрович"))
        zoo.print()

        print()
        zk.feed_animal()
        vet.heal_animal()
        print()

        # Сохранение информации в файл
        fn = "zoo.json"
        zoo.save_to_file(fn)

        # Эагрузка из файла в пустой класс зоопарка
        new_zoo = Zoo()
        new_zoo.load_from_file(fn)
        new_zoo.print()