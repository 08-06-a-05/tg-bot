import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from schedule import Schedule

# TODO: Добавить проверку корректности дат (Только протестировать)
#   Проверка, что записываемся на будущее, а не на прошлое (Только протестировать)
#   Написать аннотации, комментарии
#   Заменить фильтр any_record на что-нибудь нормальное
#   Добавить использование множеств


with open("config.txt", "r") as f:
    TOKEN: str = f.readline()

dp = Dispatcher()
schedule = Schedule("schedule.json")
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "контакты")
async def show_contacts_handler(message: Message) -> None:
    contact_info: str = "Мы находимся по адресу: г. A, улица B, дом X.\nНаши контакты: +x(xxx)xxx-xx-xx"
    await message.answer(contact_info)
    await show_start_menu(message.chat.id)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    schedule.reset_booking_date()
    start_message: str = "Здравствуйте! Это бот для записи в парикмахерскую N."
    await message.answer(start_message)
    await show_start_menu(message.chat.id)


async def show_start_menu(chat_id: int) -> None:
    kb = [
        [
            types.KeyboardButton(text="Записаться"),
            types.KeyboardButton(text="Контакты")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    await bot.send_message(chat_id, "Пожалуйста, выберите действие", reply_markup=keyboard)


@dp.message(F.text.lower().in_({"записаться", "выбрать другую дату"}))
async def choose_date_handler(message: Message) -> None:
    await choose_date(message.chat.id)


async def choose_date(chat_id: int) -> None:
    schedule.reset_booking_date()
    builder = ReplyKeyboardBuilder()
    closest_free_days = schedule.get_closest_dates(7, schedule.date_have_free_records)
    for day in closest_free_days:
        builder.add(types.KeyboardButton(text=str(day["date"])))
    builder.adjust(3)
    await bot.send_message(chat_id=chat_id,
                           text="Выберите дату или напишите желаемую в формате: dd.mm.yyyy",
                           reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(F.text.regexp(r'\d\d\.\d\d\.\d\d\d\d'))
async def chosen_date_handler(message: Message) -> None:
    if not schedule.is_booking_date_set():
        if not schedule.set_booking_date(message.text):
            await message.answer("Упс... Кажется, на эту дату записаться нельзя.")
            await choose_date(message.chat.id)
            return
    await choose_time(message.chat.id)


async def choose_time(chat_id: int) -> None:
    builder = ReplyKeyboardBuilder()
    free_records = schedule.get_date_records(schedule.any_record)
    if not free_records:
        schedule.reset_booking_date()
        await bot.send_message(chat_id,
                               "К сожалению, в этот день нет свободных записей. Пожалуйста, выберите другую дату.")
        await choose_date(chat_id)
        return
    for record_time in free_records:
        builder.add(types.KeyboardButton(text=record_time))
    builder.add(types.KeyboardButton(text="Выбрать другую дату"))
    builder.adjust(3)
    await bot.send_message(chat_id,
                           "Выберите время из предложенных",
                           reply_markup=builder.as_markup(resize_keyboard=True),
                           )


@dp.message(F.text.regexp(r'\d\d\:\d\d'))
async def chosen_time_handler(message: Message) -> None:
    if not schedule.is_booking_date_set():
        await message.answer("Упс... Почему-то не выбрана дата. Попробуйте еще раз")
        await choose_date(message.chat.id)
        return
    if not schedule.is_time_correct(message.text):
        await message.answer("Хмм... Такого времени не существует")
        await choose_time(message.chat.id)
        return
    if not schedule.is_record_free(message.text):
        await message.answer("К сожалению, нельзя записаться на данное время. Выберите другое")
        await choose_time(message.chat.id)
        return
    schedule.book_record(message.text)
    schedule.reset_booking_date()
    await message.answer("Поздравляю, вы записаны!")
    await command_start_handler(message)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
