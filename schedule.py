import datetime
import json
from typing import Callable, Any, Optional


class Schedule:
    """
    Класс для работы с расписанием.
    """
    def __init__(self, filename: str) -> None:
        self.booking_date: Optional[datetime.date] = None  # Дата, на которую пользователь планирует осуществить бронь
        with open(filename, "r") as f:
            self.schedule: dict[str, Any] = json.load(f)  # Расписание

    def reset_booking_date(self) -> None:
        """
        Очистка даты бронирования.

        :return: None
        """
        self.booking_date = None

    def set_booking_date(self, str_date: str) -> bool:
        """
        Установка даты бронирования.

        :param str_date: Дата бронирования в формате строки
        :return: Успешность установки даты
        """
        if not self.is_date_correct(str_date):
            return False
        self.booking_date = datetime.date(day=int(str_date[:2]), month=int(str_date[3:5]), year=int(str_date[6:]))
        if not self.is_date_exist():
            self.reset_booking_date()
            return False
        return True

    def is_booking_date_set(self) -> None:
        """
        Функция проверяет, установлена ли дата бронирования.

        :return: None
        """
        return self.booking_date is not None

    @staticmethod
    def is_date_correct(str_date: str) -> bool:
        """
        Функция проверяет, существует ли дата, переданная в виде строки

        :param str_date: Дата
        :return: Результат проверки
        """
        try:
            datetime.datetime.strptime(str_date, "%d.%m.%Y")
        except ValueError:
            return False
        else:
            return True

    def is_date_exist(self) -> bool:
        """
        Функция проверяет, есть ли переданная дата в расписании.

        :return: None
        """
        try:
            year_data = self.schedule[str(self.booking_date.year)]
            month_data = year_data["months"][self.booking_date.month - 1]
            day_data = month_data["days"][self.booking_date.day - 1]
            return self.booking_date >= datetime.date.today()
        except (ValueError, KeyError):
            return False

    @staticmethod
    def is_time_correct(str_time: str) -> bool:
        """
        Функция проверяет, существует ли переданное в виде строки время

        :param str_time: Время
        :return: Результат проверки
        """
        try:
            datetime.datetime.strptime(str_time, "%H:%M")
        except ValueError:
            return False
        else:
            return True

    def get_date_records(self, sort_filter: Callable[[dict[str, Any]], bool]) -> tuple[str, ...]:
        """
        Функция возвращает кортеж записей, которые удовлетворяют фильтру sort_filter, а также их дата - дата
        бронирования

        :param sort_filter: Функция-фильтр
        :return: Выбранные записи
        """
        if self.booking_date is None:
            return tuple()
        result: list[str] = []
        year_data = self.schedule[str(self.booking_date.year)]
        month_data = year_data["months"][self.booking_date.month - 1]
        day_data = month_data["days"][self.booking_date.day - 1]
        for record_time, record_state in day_data["records"].items():
            if record_state == 0:
                result.append(record_time)
        return tuple(result)

    def book_record(self, str_time: str) -> bool:
        """
        Функция бронирует запись. Время брони передается. Дата брони хранится в self.booking_date.

        :param str_time: Время брони
        :return: Успешность бронирования
        """
        if not self.is_time_correct(str_time):
            return False
        try:
            year_data = self.schedule[str(self.booking_date.year)]
            month_data = year_data["months"][self.booking_date.month - 1]
            day_data = month_data["days"][self.booking_date.day - 1]
            day_data["records"][str_time] = 1
            return True
        except (ValueError, KeyError):
            return False

    def is_record_free(self, str_time: str) -> bool:
        """
        Проверяет, можно ли записаться на данное время.

        :param str_time: Время
        :return: Свободно ли окно
        """
        try:
            year_data = self.schedule[str(self.booking_date.year)]
            month_data = year_data["months"][self.booking_date.month - 1]
            day_data = month_data["days"][self.booking_date.day - 1]
            is_future = self.booking_date > datetime.date.today() or \
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