import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from schedule import Schedule

# TODO:
#   Добавить использование множеств
#   Добавить кнопку возвращения в главное меню из любого действия (Протестировать)


with open("config.txt", "r") as f:  # Получение токена бота
    TOKEN: str = f.readline()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))  # Объект бота

dp = Dispatcher()  # Обработчик пришедших сообщений
schedule = Schedule("schedule.json")  # Класс для работы с расписанием, в том числе бронирования


@dp.message(F.text.lower() == "контакты")
async def show_contacts_handler(message: Message) -> None:
    """
    Обработчик сообщения "Контакты". Выводит информацию о контактах.

    :param message: Сообщение, пришедшее от пользователя
    :return: None
    """
    # Вывод контактов
    contact_info: str = "Мы находимся по адресу: г. A, улица B, дом X.\nНаши контакты: +x(xxx)xxx-xx-xx"
    await message.answer(contact_info)
    await show_start_menu(message.chat.id)  # Возвращение на меню действий


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обработчик команды /start

    :param message: Пришедшее сообщение
    :return: None
    """
    # Очистка даты бронирования (если пользователь осуществлял бронирование, после чего написал /start
    schedule.reset_booking_date(message.chat.id)
    # Вывод приветствия
    start_message: str = "Здравствуйте! Это бот для записи в парикмахерскую N."
    await message.answer(start_message)
    # Вывод меню действий
    await show_start_menu(message.chat.id)


@dp.message(F.text.lower() == "меню")
async def show_contacts_handler(message: Message) -> None:
    """
    Обработчик сообщения "Меню". Возвращает пользователя на меню действий

    :param message: Сообщение, пришедшее от пользователя
    :return: None
    """
    schedule.reset_booking_date(message.chat.id)  # Освобождение переменной, хранящей выбранную дату записи
    # Вывод контактов
    await show_start_menu(message.chat.id)  # Возвращение на меню действий


async def show_start_menu(chat_id: int) -> None:
    """
    Функция отображает начальные кнопки: "Записаться" и "Контакты", а также пишет приглашение ко вводу.

    :param chat_id: Id чата, где необходимо вывести кнопки
    :return: None
    """
    # Создание кнопок клавиатуры
    kb = [
        [
            types.KeyboardButton(text="Записаться"),
            types.KeyboardButton(text="Контакты")
        ],
    ]
    # Создание клавиатуры
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    # Отправка сообщения с приглашением, отображение клавиатуры
    await bot.send_message(chat_id, "Пожалуйста, выберите действие", reply_markup=keyboard)


@dp.message(F.text.lower().in_({"записаться", "выбрать другую дату"}))
async def choose_date_handler(message: Message) -> None:
    """
    Обработчик сообщения о решении записаться. Вызывает функцию для выбора даты.

    :param message: Пришедшее сообщение
    :return: None
    """
    await choose_date(message.chat.id)  # Функция выбора даты


async def choose_date(chat_id: int) -> None:
    """
    Функция выбора даты. Отображает среди ближайших 7 дней те, на которые есть свободные записи.
    Пишет приглашение для ввода.

    :param chat_id: Id чата, в котором происходит выбор даты
    :return: None
    """
    schedule.reset_booking_date(chat_id)  # Освобождение переменной, хранящей выбранную дату записи

    closest_free_days = schedule.get_closest_dates(7, schedule.date_have_free_records)  # Выбор подходящих дат
    # Создание клавиатуры с датами
    builder = ReplyKeyboardBuilder()
    for day in closest_free_days:
        builder.add(types.KeyboardButton(text=str(day["date"])))
    builder.add(types.KeyboardButton(text="Меню"))
    builder.adjust(3)
    # Отправка сообщения
    await bot.send_message(chat_id=chat_id,
                           text="Выберите дату или напишите желаемую в формате: dd.mm.yyyy",
                           reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(F.text.regexp(r'\d\d\.\d\d\.\d\d\d\d'))
async def chosen_date_handler(message: Message) -> None:
    """
    Функция обработки сообщения с выбранной датой. Датой считается любое сообщение в формате:
    '[0-9][0-9].[0-9][0-9].[0-9][0-9][0-9][0-9]'.
    Проводит валидацию выбранной даты. Если дата некорректна, перенаправляет на повторный выбор даты.
    Если дата корректна, перенаправляет на выбор времени.

    :param message: Пришедшее сообщение.
    :return: None
    """
    if not schedule.set_booking_date(message.chat.id, message.text):  # Если не удалось установить дату записи
        await message.answer("Упс... Кажется, на эту дату записаться нельзя.")  # Вывод ошибки
        await choose_date(message.chat.id)  # Перенаправление на выбор даты
        return
    await choose_time(message.chat.id)  # Перенаправление на выбор времени


async def choose_time(chat_id: int) -> None:
    """
    Функция выбора времени. Находит свободные окна в выбранную пользователем дату и выводит их на экран.
    Если свободные окна не найдены, выводит сообщение об ошибке. Перенаправляет на выбор даты.
    Если время успешно выбрано, перенаправляет на функцию бронирования.

    :param chat_id: Id чата, где ведется бронирование
    :return: None
    """
    free_records = schedule.get_date_records(chat_id, schedule.free_record)  # Поиск свободных окон в выбранный день
    if not free_records:  # Окна не найдены
        # Вывод сообщения об ошибке
        await bot.send_message(chat_id,
                               "К сожалению, в этот день нет свободных записей. Пожалуйста, выберите другую дату.")
        await choose_date(chat_id)  # Перенаправление на выбор даты
        return
    # Создание клавиатуры со свободными окнами в этот день
    builder = ReplyKeyboardBuilder()
    for record_time in free_records:
        builder.add(types.KeyboardButton(text=record_time))
    builder.add(types.KeyboardButton(text="Выбрать другую дату"))
    builder.add(types.KeyboardButton(text="Меню"))
    builder.adjust(3)
    # Отправка ответа пользователю
    await bot.send_message(chat_id,
                           "Выберите время из предложенных",
                           reply_markup=builder.as_markup(resize_keyboard=True),
                           )


@dp.message(F.text.regexp(r'\d\d\:\d\d'))
async def chosen_time_handler(message: Message) -> None:
    """
    Обработчик выбранного времени. Временем считается любое сообщение вида '[0-9][0-9]:[0-9][0-9]'.
    Проверяет корректность выбранного времени. Если выбранное время находится в будущем и оно свободно, то бронирует его.
    Иначе выводит сообщение об ошибке, перенаправляет на выбор времени.

    :param message: Пришедшее сообщение
    :return: None
    """
    if not schedule.is_booking_date_set(message.chat.id):  # Если не установлена дата записи
        # Вывод сообщения об ошибке, перенаправление на выбор даты
        await message.answer("Упс... Почему-то не выбрана дата. Попробуйте еще раз")
        await choose_date(message.chat.id)
    elif not schedule.is_time_correct(message.text):  # Если выбранное время не существует вообще (например 25:61)
        # Вывод сообщения об ошибке, перенаправление на выбор времени
        await message.answer("Хмм... Такого времени не существует")
        await choose_time(message.chat.id)
    elif not schedule.is_record_free(message.chat.id, message.text):  # Если выбранное окно занято
        # Вывод сообщения об ошибке, перенаправление на выбор времени
        await message.answer("К сожалению, нельзя записаться на данное время. Выберите другое")
        await choose_time(message.chat.id)
    else:  # Иначе все хорошо
        schedule.book_record(message.chat.id, message.text)  # Бронирование окна
        schedule.reset_booking_date(message.chat.id)  # Сброс даты бронирования, для следующих броней
        await message.answer("Поздравляю, вы записаны!")  # Поздравительное сообщение
        await show_start_menu(message.chat.id)  # Возвращение к начальному меню


async def main() -> None:
    await dp.start_polling(bot)  # Запуск бота


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # Настройка бота
    asyncio.run(main())  # Запуск бота
