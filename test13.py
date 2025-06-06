
#Задача: Создай класс `Task`, который позволяет управлять задачами (делами).
#У задачи должны быть атрибуты: описание задачи, срок выполнения и статус
#(выполнено/не выполнено). Реализуй функцию для добавления задач,
#отметки выполненных задач и вывода списка текущих (не выполненных) задач.

from datetime import date

class Task:
  def __init__(self, define: str, end_task:date, status: bool=False):
    self.define = define
    self.begin_task = date.today()
    self.end_task = end_task
    self.status = status

  def made(self):
    self.status = True

  def info(self):
    if self.status:
      s = 'Выполнена'
    else:
      s = 'Не выполнена'

    print(f"Задача {self.define} c {self.begin_task} до {self.end_task} статус {s}")

class Tasks:
  def __init__(self):
    self.mas_tsk = []

  def add_task(self, tsk:Task):
    self.mas_tsk.append(tsk)

  def list_no_made(self):
    for tsk in self.mas_tsk:
      if not tsk.status:
        tsk.info()

tsks = Tasks()
tsk1 = Task("Написать на Пайтоне пример бота", date(2025,6,10), False )
tsks.add_task(tsk1)
tsk2 = Task("Написать на Пайтоне пример класса", date(2025,6,12), True  )
tsks.add_task(tsk2)
tsk3 = Task("Покормить кошку", date(2025,6,13), True  )
tsks.add_task(tsk3)
tsk4 = Task("Съездить на дачу", date(2025,6,14), False  )
tsks.add_task(tsk4)
tsk5 = Task("Тренировка", date(2025,6,14), True  )
tsks.add_task(tsk5)

tsks.list_no_made()


