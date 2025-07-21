# - Кнопка сброса — добавь кнопку, которая будет сбрасывать игру, очищая
# все ячейки поля и начиная новую партию.
# - Вариант ничьей — если все клетки поля заполнены, но победителя нет, показывай сообщение о ничьей.
# - Улучшение интерфейса — поработай над дизайном игры, сделай её более привлекательной и удобной для пользователя.
# - Выбор для игрока — добавь возможность выбрать, чем будет играть игрок (крестиком или ноликом),
# перед началом игры.
# - Счетчик побед — добавь счетчик побед для каждого игрока (самое масштабное расширение проекта).
# - Игра до трех побед — реализуй систему, в которой игра продолжается до трех побед одного из игроков.

import tkinter as tk
from tkinter import messagebox
import random

window = tk.Tk()
window.title("Крестики-нолики")
window.geometry("300x350")

rand = random.randint(0,1)
if rand == 0:
    current_player = "X"
else:
    current_player = "0"

def check_winner():
   for i in range(3):
       if buttons[i][0]["text"] == buttons[i][1]["text"] == buttons[i][2]["text"] != "":
           return True
       if buttons[0][i]["text"] == buttons[1][i]["text"] == buttons[2][i]["text"] != "":
           return True

   if buttons[0][0]["text"] == buttons[1][1]["text"] == buttons[2][2]["text"] != "":
       return True
   if buttons[0][2]["text"] == buttons[1][1]["text"] == buttons[2][0]["text"] != "":
       return True

   itEnd = True
   for i in range(3):
       for j in range(3):
           if buttons[i][j]["text"] == "":
               itEnd = False
               break
   if itEnd:
       begin()
   else:
       return False


def on_click(row, col):
   global current_player, buttons, game

   if buttons[row][col]['text'] != "":
       return

   buttons[row][col]['text'] = current_player

   if check_winner():
       messagebox.showinfo("Гейм окончен",f"Игрок {current_player} победил!")
       game[current_player] = game[current_player] + 1
       if game[current_player] == 3:
           messagebox.showinfo("Игра окончена", f"Игрок {current_player} победил!")
       else:
           messagebox.showinfo("Следующий гейм", f"Счет X={game['X']} 0={game['0']}")


   current_player = "0" if current_player == "X" else "X"

def begin():

    global buttons

    buttons = []

    for i in range(3):
       row = []
       for j in range(3):
           btn = tk.Button(window, text="", font=("Arial", 20), width=5, height=2, command=lambda r=i, c=j: on_click(r, c))
           btn.grid(row=i, column=j)
           row.append(btn)
       buttons.append(row)

    btn = tk.Button(window, text="Сброс", font=("Arial", 20), width=5, height=2, command=lambda : begin())
    btn.grid(row=4, column=2)


begin()
game = {"X":0,"0":0}

window.mainloop()
