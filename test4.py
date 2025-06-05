#Написать программу на языке программирования Python
#с использованием модуля Tkinter, которая позволяет пользователю в
#пройти квиз из заранее созданных вопросов и ответов, начисляя за каждый верный
#кначисляется 1, за неверный - 0.
# 1. tk.Tk() - создание основного окна приложения.
# 2. pack() - метод для управления расположением виджета в окне.
# 3. grid() - метод для расположения виджетов в сетке окна.
# 4. place() - метод для позиционирования виджетов с точными координатами.
#
# Для создания различных виджетов и их конфигурации:
#
# 1. tk.Label() - создание текстовой метки.
# 2. tk.Button() - создание кнопки.
# 3. tk.Entry() - создание поля ввода текста.
# 4. tk.Text() - создание многострочного текстового поля.
# 5. tk.Checkbutton() - создание флажка (чекбокса).
# 6. tk.Radiobutton() - создание радиокнопки.
# 7. tk.Listbox() - создание списка для выбора элементов.
# 8. tk.Canvas() - создание холста для рисования графики.
#
# Для работы с событиями и обработки пользовательского ввода:
#
# 1. bind() - метод для привязки событий к виджетам.
# 2. get() - метод для получения значения из поля ввода.
# 3. insert() - метод для вставки текста в виджет.
# 4. delete() - метод для удаления части текста из виджета.
# 5. curselection() - метод для получения выбранных элементов из списка или другого виджета.
# 6. itemconfig() - метод для конфигурации отдельных элементов в списке или холсте.

import tkinter as tk
from tkinter import messagebox

# Вопросы и ответы
questions = [
    {
        "question": "Какой язык программирования используется для разработки этой программы?",
        "options": ["Java", "Python", "C++"],
        "answer": "Python"
    },
    {
        "question": "Как называется самая большая планета Солнечной системы?",
        "options": ["Земля", "Юпитер", "Марс"],
        "answer": "Юпитер"
    },
    {
        "question": "Какой цвет получается при смешивании синего и красного?",
        "options": ["Фиолетовый", "Зеленый", "Оранжевый"],
        "answer": "Фиолетовый"
    },
    {
        "question": "Кто написал роман 'Война и мир'?",
        "options": ["Фёдор Достоевский", "Лев Толстой", "Антон Чехов"],
        "answer": "Лев Толстой"
    },
    {
        "question": "Какой океан является самым большим на Земле?",
        "options": ["Атлантический", "Тихий", "Индийский"],
        "answer": "Тихий"
    },
    {
        "question": "Как называется столица Франции?",
        "options": ["Берлин", "Париж", "Рим"],
        "answer": "Париж"
    },
    {
        "question": "Сколько минут в одном часе?",
        "options": ["60", "100", "90"],
        "answer": "60"
    },
    {
        "question": "Как называется первая планета от Солнца?",
        "options": ["Земля", "Меркурий", "Венера"],
        "answer": "Меркурий"
    },
    {
        "question": "Как называется процесс, при котором растения вырабатывают кислород?",
        "options": ["Фотосинтез", "Испарение", "Дыхание"],
        "answer": "Фотосинтез"
    },
    {
        "question": "Какой вид искусства связан с Микеланджело?",
        "options": ["Литература", "Живопись", "Музыка"],
        "answer": "Живопись"
    }
]

# Переменные для хранения текущего вопроса и результата
current_question = 0
score = 0

# Функция для обработки ответа
def check_answer(selected_option):
    global current_question, score, task_listBox

    mark = (questions[current_question]["options"][selected_option] == questions[current_question]["answer"])
    if mark:
        score += 1
        str = "верно"
    else:
        str ="неверно"
    task_listBox.insert(tk.END,f"{questions[current_question]["question"]} - Ответил: {questions[current_question]["answer"]} - Это {str}")

    current_question += 1

    if current_question < len(questions):
        load_question()
    else:
        show_result()

# Функция для загрузки следующего вопроса
def load_question():
    question_label.config(text=questions[current_question]["question"],bg="DarkOrchid")
    for i in range(3):
        options[i].config(text=questions[current_question]["options"][i],bg="white")

# Функция для отображения результата
def show_result():
    messagebox.showinfo("Результат", f"Ваш результат: {score} из {len(questions)}")
    root.destroy()

# Создание основного окна
root = tk.Tk()
root.title("Квиз")

# Виджеты интерфейса
question_label = tk.Label(root, text="", font=("Arial", 14), wraplength=400, justify="center")
question_label.pack(pady=20)

options = []
for i in range(3):
    btn = tk.Button(root, text="", font=("Arial", 12), command=lambda i=i: check_answer(i))
    btn.pack(padx=10)
    options.append(btn)

task_listBox = tk.Listbox(root, height=20, width=500, bg="LightPink1")
task_listBox.pack(pady=10)

# Загрузка первого вопроса
load_question()

# Запуск главного цикла
root.mainloop()

