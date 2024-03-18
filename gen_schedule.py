import calendar
import datetime
import json
import random


class RecordStates:
    """
    Вероятности получения записи определенного статуса.
    """
    free_prob = 0.59
    busy_prob = free_prob + 0.35
    not_available = busy_prob + 0.05

    @classmethod
    def state(cls) -> int:
        cur_state = random.random()
        if cur_state < cls.free_prob:
            return 0
        elif cur_state < cls.busy_prob:
            return random.randint(1_000_000, 4_000_000)
        else:
            return -1


def gen_day_schedule(is_workday: bool, date_range: datetime.timedelta) -> dict[str, int]:
    """
    Генерация дня расписания. Каждая запись с вероятностью, описанными в RecordStates, получает статус.

    :param is_workday: Является ли день рабочим
    :param date_range: Сколько дней должны иметь занятые записи
    :return: Расписание на день
    """
    day_schedule = {}
    if is_workday and date_range.days < 50:
        for i in range(7):
            cur_time = datetime.timedelta(hours=10, minutes=90 * i)
            cur_state = RecordStates.state()
            day_schedule[f"{cur_time.seconds // 3600:02}:{cur_time.seconds % 3600 // 60:02}"] = cur_state
    elif is_workday:
        for i in range(7):
            cur_time = datetime.timedelta(hours=10, minutes=90 * i)
            day_schedule[f"{cur_time.seconds // 3600:02}:{cur_time.seconds % 3600 // 60:02}"] = 0
    else:
        for i in range(7):
            cur_time = datetime.timedelta(hours=10, minutes=90 * i)
            day_schedule[f"{cur_time.seconds // 3600:02}:{cur_time.seconds % 3600 // 60:02}"] = 2
    return day_schedule


def is_workday(day_index: int) -> bool:
    """
    Проверка, является ли день рабочим. Праздники не учитываются. Не рабочий день - воскресенье.

    :param day_index: Номер дня в неделе - 1 (т.е. понедельник = 0, ..., воскресенье = 6)
    :return: Статус дня
    """
    return day_index <= 5


# Создание расписания
now = calendar.Calendar()
new_c = now.yeardayscalendar(2024, width=12)
schedule = {"2024": {"months": []}}
for month_index, month in enumerate(new_c[0]):
    cur_month = {"name": datetime.date(2024, month_index + 1, 1).strftime("%B"), "days": []}
    for week_index, week in enumerate(month):
        for day_index, day in enumerate(week):
            if day == 0:
                continue
            date_range = datetime.date(year=2024, month=month_index + 1, day=day) - datetime.date.today()
            cur_day = {
                "date": datetime.date(year=2024, month=month_index + 1, day=day).strftime("%d.%m.%Y"),
                "name": datetime.date(2024, month_index + 1, day).strftime("%A"),
                "week_day": datetime.date(2024, month_index + 1, day).weekday(),
                "is_workday": is_workday(day_index),
                "records": gen_day_schedule(is_workday(day_index), date_range)
            }
            cur_month["days"].append(cur_day)
    schedule["2024"]["months"].append(cur_month)

with open("schedule.json", "w") as f:
    json.dump(schedule, f, indent=2)

# with open("schedule.json", "r") as f:
#     data = json.load(f)

# print(data)
# print(schedule["2024"]["months"][0]["weeks"][0]["days"][0])
