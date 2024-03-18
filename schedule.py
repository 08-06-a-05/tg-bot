import datetime
import json
from typing import Callable, Any, Optional


class Schedule:
    """
    Класс для работы с расписанием.
    """

    def __init__(self, filename: str) -> None:
        """
        Конструктор. Принимает имя файла, содержащего расписание в формате json.

        :param filename: Имя файла
        """
        self.booking_dates: dict[int: datetime.date] = {}  # Словарь дат броней (Id_пользователя: дата брони)
        # Этот словарь используется для хранения выбранной даты во время брони
        # После бронирования пользователем, информация о выбранной дате пользователем должна очищаться
        with open(filename, "r") as f:
            self.schedule: dict[str, Any] = json.load(f)  # Расписание

    def reset_booking_date(self, user_id: int) -> None:
        """
        Очистка даты бронирования для пользователя.

        :param user_id: Id пользователя
        :return: None
        """
        if user_id in self.booking_dates:
            self.booking_dates.pop(user_id)

    def set_booking_date(self, user_id: int, str_date: str) -> bool:
        """
        Установка даты бронирования для пользователя.

        :param user_id: Id пользователя
        :param str_date: Дата бронирования в формате строки
        :return: Успешность установки даты
        """
        if not self.is_date_correct(str_date):
            return False
        self.booking_dates[user_id] = datetime.date(day=int(str_date[:2]), month=int(str_date[3:5]),
                                                    year=int(str_date[6:]))
        if not self.is_user_date_exist(user_id):
            self.reset_booking_date(user_id)
            return False
        return True

    def is_booking_date_set(self, user_id: int) -> bool:
        """
        Функция проверяет, установлена ли дата бронирования.

        :type user_id: Id пользователя
        :return: Результат проверки
        """
        return user_id in self.booking_dates

    @staticmethod
    def is_date_correct(str_date: str) -> bool:
        """
        Функция проверяет, существует ли дата, переданная в виде строки.

        :param str_date: Дата
        :return: Результат проверки
        """
        try:
            datetime.datetime.strptime(str_date, "%d.%m.%Y")
        except ValueError:
            return False
        else:
            return True

    def is_user_date_exist(self, user_id: int) -> bool:
        """
        Функция проверяет, есть ли дата, выбранная пользователем, в расписании.

        :type user_id: Id пользователя
        :return: None
        """
        try:
            year_data = self.schedule[str(self.booking_dates[user_id].year)]
            month_data = year_data["months"][self.booking_dates[user_id].month - 1]
            day_data = month_data["days"][self.booking_dates[user_id].day - 1]
            return self.booking_dates[user_id] >= datetime.date.today()
        except (ValueError, KeyError):
            return False

    @staticmethod
    def is_time_correct(str_time: str) -> bool:
        """
        Функция проверяет, существует ли переданное в виде строки время.

        :param str_time: Время
        :return: Результат проверки
        """
        try:
            datetime.datetime.strptime(str_time, "%H:%M")
        except ValueError:
            return False
        else:
            return True

    def get_date_records(self, user_id: int, sort_filter: Callable[[str, int], bool]) -> tuple[str, ...]:
        """
        Функция возвращает кортеж записей, которые удовлетворяют фильтру sort_filter, а также их дата - дата
        бронирования. Выбранная пользователем дата передается в словаре self.booking_dates.

        :param user_id: Id пользователя
        :param sort_filter: Функция-фильтр
        :return: Выбранные записи
        """
        if user_id not in self.booking_dates:
            return tuple()
        result: list[str] = []
        year_data = self.schedule[str(self.booking_dates[user_id].year)]
        month_data = year_data["months"][self.booking_dates[user_id].month - 1]
        day_data = month_data["days"][self.booking_dates[user_id].day - 1]
        for record_time, record_state in day_data["records"].items():
            if sort_filter(record_time, record_state):
                result.append(record_time)
        return tuple(result)

    def book_record(self, user_id: int, str_time: str) -> bool:
        """
        Функция бронирует запись. Время брони передается. Дата брони хранится в self.booking_dates.

        :param user_id: Id пользователя
        :param str_time: Время брони
        :return: Успешность бронирования
        """
        if not self.is_time_correct(str_time):
            return False
        try:
            year_data = self.schedule[str(self.booking_dates[user_id].year)]
            month_data = year_data["months"][self.booking_dates[user_id].month - 1]
            day_data = month_data["days"][self.booking_dates[user_id].day - 1]
            day_data["records"][str_time] = 1
            return True
        except (ValueError, KeyError):
            return False

    def is_record_free(self, user_id: int, str_time: str) -> bool:
        """
        Проверяет, можно ли записаться на данное время. Дата хранится в словаре self.booking_dates.

        :param user_id: Id пользователя
        :param str_time: Время
        :return: Свободно ли окно
        """
        try:
            year_data = self.schedule[str(self.booking_dates[user_id].year)]
            month_data = year_data["months"][self.booking_dates[user_id].month - 1]
            day_data = month_data["days"][self.booking_dates[user_id].day - 1]
            is_future = self.booking_dates[user_id] > datetime.date.today() or \
                        datetime.datetime.strptime(str_time, "%H:%M").time() > datetime.datetime.now().time()
            return is_future and day_data["records"][str_time] == 0
        except (ValueError, KeyError):
            return False

    def get_closest_dates(self, days_range: int, sort_filter: Callable[[dict[str, Any]], bool]):
        """
        Возвращает ближайшие days_range дней, включая сегодняшний день, которые удовлетворяют функции фильтру.

        :param days_range: Сколько дней просмотреть
        :param sort_filter: Функция-фильтр
        :return: Дни, удовлетворяющие условиям
        """
        today: datetime.date = datetime.date.today()
        result: list[dict[str, Any]] = []
        for i in range(days_range):
            cur_date: datetime.date = today + datetime.timedelta(days=i)
            year_data = self.schedule[str(cur_date.year)]
            month_data = year_data["months"][cur_date.month - 1]
            day_data = month_data["days"][cur_date.day - 1]
            if sort_filter(day_data):
                result.append(day_data)
        return tuple(result)

    @staticmethod
    def any_record(record) -> bool:
        """
        Функция фильтр. Любая запись подходит.

        :param record: Запись
        :return: True всегда
        """
        return True

    @staticmethod
    def free_record(str_time: str, str_state: int) -> bool:
        """
        Функция фильтр. Запись должна быть свободна.

        :param str_time: Время записи
        :param str_state: Состояние записи
        :return: Результат проверки
        """
        return str_state == 0

    @staticmethod
    def date_have_free_records(date_info: dict[str, Any]) -> bool:
        """
        Функция фильтр. Возвращает True, если переданная дата содержит свободные окна.

        :param date_info: Информация о дате
        :return: Результат фильтрации
        """
        for record_state in date_info["records"].values():
            if record_state == 0:
                return True
        return False

    @staticmethod
    def date_dont_have_free_records(date_info: dict[str, Any]) -> bool:
        """
        Функция фильтр. Возвращает False, если переданная дата содержит свободные окна.

        :param date_info: Информация о дате
        :return: Результат фильтрации
        """
        for record_state in date_info["records"].values():
            if record_state == 0:
                return False
        return True


if __name__ == "__main__":
    pass
