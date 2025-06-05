import tkinter as tk

def main():
    root = tk.Tk()
    root.title("Моё приложение")
    root.geometry("300x200")
    label = tk.Label(root, text="Привет, это tkinter!")
    label.pack()
    root.mainloop()

if __name__ == "__main__":
    main()