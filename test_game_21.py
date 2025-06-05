import random

# Карты и их значения
cards = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11  # Туз (A) может быть 1 или 11, но это учтем позже
}

# Функция для подсчета очков
def calculate_score(hand):
    score = sum(cards[card] for card in hand)
    # Если есть туз (A) и сумма превышает 21, уменьшаем значение туза до 1
 #   if 'A' in hand and score > 21:
 #       score -= 10
    return score

# Функция для раздачи карты
def deal_card():
    return random.choice(list(cards.keys()))

# Логика игры
def play_game():
    print("Добро пожаловать в игру '21'!")

    # Рука игрока и компьютера
    player_hand = [deal_card(), deal_card()]
    computer_hand = [deal_card(), deal_card()]

    game_over = False

    while not game_over:
        # Показываем карты игрока и компьютера
        print(f"Ваши карты: {player_hand}, текущая сумма на картах: {calculate_score(player_hand)}")
        print(f"Первая карта компьютера: {computer_hand[0]}")

        # Проверяем, не набрал ли игрок 21 или больше
        if calculate_score(player_hand) == 21:
            print("Поздравляем, у вас 21!")
            game_over = True
            continue
        elif calculate_score(player_hand) > 21:
            print("Вы проиграли! Ваш счет больше 21.")
            game_over = True
            continue

        # Ход игрока
        action = input("Введите 'y', чтобы взять карту, или 'n', чтобы остановиться: ").lower()
        if action == 'y':
            player_hand.append(deal_card())
        elif action == 'n':
            game_over = True

    # Ход компьютера
    while calculate_score(computer_hand) < 17:
        computer_hand.append(deal_card())

    # Показываем итоговые руки и результаты
    print(f"Ваши финальные карты: {player_hand}, финальный счет: {calculate_score(player_hand)}")
    print(f"Карты компьютера: {computer_hand}, финальный счет: {calculate_score(computer_hand)}")

    player_score = calculate_score(player_hand)
    computer_score = calculate_score(computer_hand)

    if player_score > 21:
        print("Вы проиграли!")
    elif computer_score > 21 or player_score > computer_score:
        print("Вы выиграли!")
    elif player_score == computer_score:
        print("Ничья!")
    else:
        print("Компьютер выиграл!")

# Запуск игры
play_game()
