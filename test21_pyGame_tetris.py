import pygame
import random

# Инициализация Pygame
pygame.init()

# Размеры окна
SCREEN_WIDTH = 300  # ширина окна
SCREEN_HEIGHT = 600  # высота окна
BLOCK_SIZE = 30  # размер одного блока

# Установка размеров сетки
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # Циан
    (255, 165, 0),  # Оранжевый
    (0, 0, 255),    # Синий
    (255, 0, 0),    # Красный
    (0, 255, 0),    # Зелёный
    (128, 0, 128),  # Фиолетовый
    (255, 255, 0),  # Жёлтый
]

# Фигуры Тетриса
SHAPES = [
    [[1, 1, 1, 1]],  # Линия
    [[1, 1], [1, 1]],  # Квадрат
    [[0, 1, 0], [1, 1, 1]],  # T-образная
    [[1, 0, 0], [1, 1, 1]],  # L-образная
    [[0, 0, 1], [1, 1, 1]],  # Обратная L-образная
    [[0, 1, 1], [1, 1, 0]],  # Z-образная
    [[1, 1, 0], [0, 1, 1]],  # Обратная Z-образная
]

# Экран
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Тетрис")

# Класс фигуры
class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.color = random.choice(COLORS)
        self.x = GRID_WIDTH // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

# Функция для проверки столкновений
def check_collision(grid, tetromino, offset_x=0, offset_y=0):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                new_x = tetromino.x + x + offset_x
                new_y = tetromino.y + y + offset_y
                if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                    return True
                if new_y >= 0 and grid[new_y][new_x]:
                    return True
    return False

# Функция для добавления фигуры в сетку
def merge_tetromino(grid, tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                #добавляем цвет в нужные координаты сетки, соотв. фигуре
                grid[tetromino.y + y][tetromino.x + x] = tetromino.color

# Функция для очистки заполненных линий
def clear_lines(grid):
    lines_to_clear = [i for i, row in enumerate(grid) if all(row)]
    for i in lines_to_clear:
        del grid[i]
        grid.insert(0, [0] * GRID_WIDTH)
    return len(lines_to_clear)

# Отображение сетки
def draw_grid():
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# Отображение всей сетки
def draw_board(grid):
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    screen,
                    cell,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                )

# Отображение текущей фигуры
def draw_tetromino(tetromino):
    for y, row in enumerate(tetromino.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    screen,
                    tetromino.color,
                    (
                        (tetromino.x + x) * BLOCK_SIZE,
                        (tetromino.y + y) * BLOCK_SIZE,
                        BLOCK_SIZE,
                        BLOCK_SIZE,
                    )
                )

# Главная функция игры
def main():
    clock = pygame.time.Clock()
    grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]   #Сетка из 0
    current_tetromino = Tetromino(random.choice(SHAPES))    #новая фигура
    fall_time = 0
    fall_speed = 700  # Нижняя граница (мс) на скорость падения (чем она выше, тем медленнее будет падать фигура
    score = 0

    running = True
    while running:
        screen.fill(BLACK)
        fall_time += clock.get_rawtime()
        clock.tick()

        # Падение фигуры
        if fall_time > fall_speed:
            fall_time = 0
            if not check_collision(grid, current_tetromino, offset_y=1):
                current_tetromino.y += 1 #падает по сетке
            else:
                #добавим фигуру в сетку
                merge_tetromino(grid, current_tetromino)
                #рассчитаем количество полностью заполненных строк и увеличим счет на это число
                score += clear_lines(grid)
                #формируем следующую фигуру
                current_tetromino = Tetromino(random.choice(SHAPES))
                #если она касается ранее заполненной фигурами сетки - игра окончена
                if check_collision(grid, current_tetromino):
                    print(f"Игра окончена! Ваш счёт: {score}")
                    running = False

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT: #нажали на крестик
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and not check_collision(grid, current_tetromino, offset_x=-1):
                    current_tetromino.x -= 1 #влево если есть возможность
                if event.key == pygame.K_RIGHT and not check_collision(grid, current_tetromino, offset_x=1):
                    current_tetromino.x += 1 #вправо если есть возможность
                if event.key == pygame.K_DOWN and not check_collision(grid, current_tetromino, offset_y=1):
                    current_tetromino.y += 1 #вниз если есть возможность
                if event.key == pygame.K_UP:
                    current_tetromino.rotate() #вращаем на 90 градусов и проверяем есть ли коллизия с сеткой
                    if check_collision(grid, current_tetromino): #коллизия есть - вращаем еще на 3*90=270 чтобы вернуться в прежний вид фигуры
                        current_tetromino.rotate()
                        current_tetromino.rotate()
                        current_tetromino.rotate()

        # Рисование
        draw_board(grid) #рисуем сетку
        draw_tetromino(current_tetromino)  #рисуем тек.фигуру
        draw_grid()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
