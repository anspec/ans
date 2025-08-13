def process_table(input_data):
    # Преобразуем входные данные в список строк
    data = input_data.split()

    # Извлекаем количество строк и столбцов
    rows = int(data[0])
    cols = int(data[1])

    # Проверяем, достаточно ли данных для указанной таблицы
    if len(data[2:]) != rows * cols:
        raise ValueError("Количество элементов таблицы не соответствует указанным размерам.")

    # Извлекаем числа таблицы и преобразуем их в двумерный список
    table = []
    numbers = list(map(int, data[2:]))
    for i in range(rows):
        table.append(numbers[i * cols:(i + 1) * cols])

    # Заменяем отрицательные числа на нули
    processed_table = []
    for row in table:
        processed_row = [0 if x < 0 else x for x in row]
        processed_table.append(processed_row)

    # Выводим обработанную таблицу построчно
    for row in processed_table:
        print(" ".join(map(str, row)))

input_data = input("введите таблицу чисел") # пример 3 4 -1 2 -3 4 5 -6 7 8 9 10 -11 12
process_table(input_data)