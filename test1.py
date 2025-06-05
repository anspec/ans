#Создай класс, аналогичный тому, который создал эксперт в уроке.
#Назови класс “Dog”, в аргументах функции пропиши характеристики (имя, порода, возраст, вес)
#и добавь методы (действия): спать, кушать и выводить информацию о себе.
#Создай два объекта класса: dog1 и dog2 с различными характеристиками.
#Используй для каждого объекта все 3 функции (метода).
#Также выведи вес объектов до еды и после еды,
#с учетом того, что к текущему весу объекта за один приём пищи прибавляется 0,5 килограмма.
class Dog:
    def __init__(self,name,poroda,age,weight):
        self.name = name
        self.poroda = poroda
        self.age = age
        self.weight = weight

    def sleep(self):
        print(f"{self.name} спит")
        return None

    def eat(self, food):
        print(f"{self.name} кушает {food}, прежний вес {self.weight}")
        self.weight = self.weight + 0.5
        print(f"{self.name} поел, новый вес {self.weight}")
        return None

    def info(self):
        print(f"{self.name} порода {self.poroda} возраст {self.age} вес {self.weight}")

dog1 = Dog("Петя", "noname", 5, 10)
dog2 = Dog("Муля", "болонка", 2, 2)
dog1.sleep()
dog2.sleep()
dog1.eat("колбасу")
dog2.eat("сыр")
dog1.info()
dog2.info()
