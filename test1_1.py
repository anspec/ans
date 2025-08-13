def sum_between_min_max(s):
    # Преобразуем строку чисел в список
    lst = list(map(int, s.split()))

    # Находим минимальное и максимальное число, а также их индексы
    min_val = min(lst)
    max_val = max(lst)
    min_index = lst.index(min_val)
    max_index = lst.index(max_val)

    # Определяем диапазон между минимальным и максимальным индексом
    start = min(min_index, max_index) + 1  # Начало диапазона (не включая минимальный элемент)
    end = max(min_index, max_index)  # Конец диапазона (не включая максимальный элемент)

    # Суммируем числа в указанном диапазоне
    result = sum(lst[start:end])

    return result

input_string = input("Введите строку через пробел чисел с одним минимальным и максимальным числом")  #"3 8 1 4 9 2 5"  # Пример входных данных
result = sum_between_min_max(input_string)
print(f"Сумма чисел между минимальным и максимальным элементами в {input_string} равна {result}")
