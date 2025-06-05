import tkinter as tk

def add_task():
    task = task_entry.get() #получаем слова из поля для ввода
    if task:
        listBox_to_do.insert(tk.END, task) #здесь с помощью константы END вставляем полученное слово в конец списка
        task_entry.delete(0, tk.END) #очищаем поле для ввода, от нулевого индекса и до конца

def delete_task():
    selected_widget = root.focus_get() #Получаем информацию об активном виджете
    selected_task = selected_widget.curselection() #с помощью функции **curselection** элемент, на который мы нажмём, будет передавать свой ID, индекс, в переменную  selected_task
    if selected_task:
        selected_widget.delete(selected_task) #удаляем выбранный элемент из выбранного списка

def take_in_work():
    selected_task = listBox_to_do.curselection()
    if selected_task:
        listBox_in_work.insert(tk.END, listBox_to_do.get(selected_task)) #Создаем аналогичную запись в гриде "В работе"
        listBox_to_do.delete(selected_task) #Удаляем запись из грида "К работе"

def complete_task():
    selected_task = listBox_in_work.curselection() #получаем выбранную записиь в блоке "В работе"
    if selected_task:
        listBox_done.insert(tk.END, listBox_in_work.get(selected_task)) #Создаем аналогичную запись в гриде "Сделано"
        listBox_in_work.delete(selected_task) #Удаляем запись из грида "В работе"

#Создаем и настраиваем главное окно программы
root = tk.Tk()
root.title("Task list")
root.geometry('910x420')
root.configure(background="#E0FFFF")

#Создаем фрейм
frame_bottom = tk.Frame(root, bg="#E0FFFF")
frame_bottom.pack(side=tk.BOTTOM, fill=tk.X)

#Создаем подпись и название для поля ввода задачи
text1 = tk.Label(root, text="Введите вашу задачу:", bg="#808080")
text1.pack(pady=5)
task_entry = tk.Entry(root, width=30, bg="chocolate")
task_entry.pack(pady=10)

#Создаем кнопки для работы с задачами
add_task_button = tk.Button(root, text="Добавить задачу", bg="#007bff", command=add_task)
add_task_button.pack(pady=5)

in_work_button = tk.Button(root, text="Взять в работу", bg="#007bff", command=take_in_work)
in_work_button.pack(pady=5)

complete_button = tk.Button(root, text="Отметить выполненной", bg="#007bff", command=complete_task)
complete_button.pack(pady=5)

delete_button = tk.Button(root, text="Удалить задачу", bg="#880808", command=delete_task)
delete_button.pack(pady=5)

#Создаем гриды, в которых будут отображаться задачи в зависимости от статуса
to_do_title = tk.Label(root, text="Что нужно сделать:", bg="#808080")
to_do_title.grid(row=0, column= 0, in_=frame_bottom)

in_work_title = tk.Label(root, text="В работе", bg="#808080")
in_work_title.grid(row=0, column= 1, in_=frame_bottom)

complete_title = tk.Label(root, text="Сделано", bg="#808080")
complete_title.grid(row=0, column= 2, in_=frame_bottom)

listBox_to_do = tk.Listbox(root, height=10, width=50, bg="#FFFFCC")
listBox_to_do.grid(row=1, column= 0, in_=frame_bottom)

listBox_in_work = tk.Listbox(root, height=10, width=50, bg="#99CCFF")
listBox_in_work.grid(row=1, column= 1, in_=frame_bottom)

listBox_done = tk.Listbox(root, height=10, width=50, bg="#99FF99")
listBox_done.grid(row=1, column= 2, in_=frame_bottom)

root.mainloop()