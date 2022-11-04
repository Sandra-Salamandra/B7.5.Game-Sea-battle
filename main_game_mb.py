from random import randint


# Собственные классы исключений
class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"


class BoardWrongShipException(BoardException):
    pass


# Собственный тип данных "точка" (класс точек на поле)
class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):  # метод __eq__, чтобы точки можно было проверять на равенство
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Dot({self.x}, {self.y})"


# Класс "Корабль" (корабль на игровом поле)
class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow
        self.l = l
        self.o = o
        self.lives = l

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):  # Проверка на попадание
        return shot in self.dots


# Класс "Игровое поле"
class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid  # нужно ли скрывать корабли на доске (для вывода доски врага) или нет (для своей доски).

        self.count = 0  # кол-во пораженных кораблей

        self.field = [["O"] * size for _ in range(size)]  # Пустое поле (сетка), заполненное 0

        self.busy = []  # Занятое место кораблем или место, в кот-е уже стреляли
        self.ships = []  # Список кораблей

    def __str__(self):  # вывод корабля на доску
        res = ""  # в список res будем записывать всю нашу доску
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | " + " | ".join(row) + " |"

        if self.hid:
            res = res.replace("■", "O")
        return res

    def out(self, d):  # находится ли точка за пределами доски
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    # метод обводит корабль по контуру. Помечает соседние точки, где корабля по правилам быть не может
    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:  # берем каждую точку корабля
            for dx, dy in near:  # по списку near
                cur = Dot(d.x + dx, d.y + dy)  # сдвигаем исходную точку на dx и dy
                if not (self.out(cur)) and cur not in self.busy:  # если точка не выходит за границы и не занята
                    if verb:
                        self.field[cur.x][cur.y] = "."  # точки вокруг корабля помечаем на поле точкой
                    self.busy.append(cur)  # записываем занятую точку или соседствующие в список занятых

    # ставит корабль на доску (если ставить не получается (выходит за границы или занята), выбрасываем исключения)
    def add_ship(self, ship):
        for d in ship.dots:  # по каждой точке корабля
            if self.out(d) or d in self.busy:  # если выходит за границы или занята, то выбрасываем исключения
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)  # записываем занятую точку или соседствующие в список занятых

        self.ships.append(ship)
        self.contour(ship)

    # делает выстрел по доске
    # (если есть попытка выстрелить за пределы и в использованную точку, нужно выбрасывать исключения)
    def shot(self, d):
        if self.out(d):  # если выходит за границы
            raise BoardOutException()

        if d in self.busy:  # если точка занята
            raise BoardUsedException()

        self.busy.append(d)  # записываем точку в список занятых

        for ship in self.ships:  # проверяем по списку кораблей
            if ship.shooten(d):    # ?? d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = "X"  # если попали, то рисуем Х
                if ship.lives == 0:  # если у корабля закончились жизни
                    self.count += 1  # прибавляем к счетчику пораженных кораблей
                    self.contour(ship, verb=True)  # обрисовываем точками вокруг корабля
                    print("Корабль уничтожен!")
                    return False  # сообщаем, что ход не нужно делать
                else:
                    print("Корабль ранен!")
                    return True  # сообщаем, что нужно повторить ход

        self.field[d.x][d.y] = "."  # если никуда не попали, то рисуем точку
        print("Мимо!")
        return False

    def begin(self):  # начало игра (перестрелка)
        # обнуляем список с точками, соседствующими с кораблями (до начала игры),
        # теперь он нужен, чтобы хранить точки, куда стрелял игрок
        self.busy = []

    def defeat(self):
        return self.count == len(self.ships)


# Класс "Игрок"
class Player:
    def __init__(self, board, enemy):  # в аргументы передаем две доски
        self.board = board
        self.enemy = enemy

    def ask(self):  # «спрашивает» игрока, в какую клетку он делает выстрел.
        raise NotImplementedError()

    def move(self):  # делаем выстрел
        while True:
            try:
                target = self.ask()  # запрашиваем у игрока координаты
                repeat = self.enemy.shot(target)  # если всё ок (без ошибок)
                return repeat
            except BoardException as e:  # если с ошибками
                print(e)


# Классы "игрок-компьютер" , "игрок-пользователь"
class AI(Player):  # "игрок-компьютер"
    def ask(self):
        d = Dot(randint(0, 5), randint(0, 5))  # случайные точки от 0 до 5
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d


class User(Player):  # "игрок-пользователь"
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()  # запрос координат

            if len(cords) != 2:   # проверяем, что введено два числа
                print(" Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):  # проверяем, что это числа
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)  # возвращаем нашу точку


# Класс "игра" и генерация досок
class Game:
    # Конструктор. Задаем размер доски, генерируем две случайные доскидля комп и игрока
    def __init__(self, size=6):
        self.lens = [3, 2, 2, 1, 1, 1, 1]  # список длины кораблей
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True  # для компьюnера скрываем корабли

        # создаем двух игроков
        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def try_board(self):  # каждый корабль расставлем на доску
        board = Board(size=self.size)  # создаем доску
        attempts = 0
        for l in self.lens:  # для каждой длины корабля пытаемся поставить корабль
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)  # добавлние корабля
                    break  # завершаем цикл while
                except BoardWrongShipException:
                    pass  # если есть исключение, что заново запускаем цикл
        board.begin()
        return board

    # метод генерирует случайную доску
    def random_board(self):
        board = None
        while board is None:  # пока доска не пустая
            board = self.try_board()
        return board

    # приветствие
    def greet(self):
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def print_boards(self):
        print("-" * 20)
        print("Доска пользователя:")
        print(self.us.board)
        print("-" * 20)
        print("Доска компьютера:")
        print(self.ai.board)
        print("-" * 20)

    # Игровой цикл
    def loop(self):
        num = 0  # номер хода
        while True:
            self.print_boards()
            if num % 2 == 0:  # если № хода четный, то ходит пользователь
                print("Ходит пользователь!")
                repeat = self.us.move()  # делаем выстрел
            else:  # если № хода нечетный, то ходит комп
                print("Ходит компьютер!")
                repeat = self.ai.move()

            if repeat:
                num -= 1

            # кол-во пораженных кораблей = кол-ву кораблей на доске
            if self.ai.board.defeat():  # self.ai.board.count == len(self.ai.board.ships):
                self.print_boards()
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.defeat():  # self.us.board.count == 7:
                self.print_boards()
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    # запуск игры. Сначала вызываем greet, а потом loop.
    def start(self):
        self.greet()
        self.loop()


g = Game()
g.start()
