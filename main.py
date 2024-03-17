import asyncio
import json
import logging
import sys
import typing
from os import getenv

import re
# TODO: Добавить проверку корректности дат (Только протестировать)
#   Проверка, что записываемся на будущее, а не на прошлое (Только протестировать)
#   Написать аннотации, комментарии

from schedule import Schedule

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, MagicData
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram import F

# Bot token can be obtained via https://t.me/BotFather
with open("config.txt", "r") as f:
    TOKEN: str = f.readline()

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
schedule = Schedule("schedule.json")


@dp.message(F.text.lower() == "контакты")
async def show_contacts_handler(message: Message) -> None:
    contact_info: str = "Мы находимся по адресу: г. A, улица B, дом X.\nНаши контакты: +x(xxx)xxx-xx-xx"
    await message.answer(contact_info)
    await command_start_handler(message)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    schedule.reset_booking_date()
    start_message: str = "Здравствуйте! Это бот для записи в парикмахерскую N."
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
    await message.answer(start_message, reply_markup=keyboard)


@dp.message(F.text.lower().in_({"записаться", "выбрать другую дату"}))
async def choose_date_handler(message: types.Message) -> None:
    schedule.reset_booking_date()
    builder = ReplyKeyboardBuilder()
    closest_free_days = schedule.get_closest_dates(7, schedule.date_have_free_records)
    for day in closest_free_days:
        builder.add(types.KeyboardButton(text=str(day["date"])))
    builder.adjust(3)
    await message.answer(
        "Выберите дату или напишите желаемую в формате: dd.mm.yyyy",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message(F.text.regexp(r'\d\d\.\d\d\.\d\d\d\d'))
async def chosen_date_handler(message: types.Message) -> None:
    if not schedule.is_booking_date_set():
        if not schedule.set_booking_date(message.text):
            await message.answer("Упс... Кажется, на эту дату записаться нельзя.")
            await choose_date_handler(message)
            return
    builder = ReplyKeyboardBuilder()
    free_records = schedule.get_date_records(schedule.any_record)
    if not free_records:
        schedule.reset_booking_date()
        await message.answer("К сожалению, в этот день нет свободных записей. Пожалуйста, выберите другую дату.")
        await choose_date_handler(message)
        return
    for record_time in free_records:
        builder.add(types.KeyboardButton(text=record_time))
    builder.add(types.KeyboardButton(text="Выбрать другую дату"))
    builder.adjust(3)
    await message.answer(
        "Выберите время из предложенных",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message(F.text.regexp(r'\d\d\:\d\d'))
async def chosen_time_handler(message: types.Message) -> None:
    builder = ReplyKeyboardBuilder()
    if not schedule.is_booking_date_set():
        await message.answer("Упс... Почему-то не выбрана дата. Попробуйте еще раз")
        await choose_date_handler(message)
        return
    if not schedule.is_time_correct(message.text):
        await message.answer("Хмм... Такого времени не существует")
        await chosen_date_handler(message)
        return
    if not schedule.is_record_free(message.text):
        await message.answer("К сожалению, нельзя записаться на данное время. Выберите другое")
        await chosen_date_handler(message)
        return
    schedule.book_record(message.text)
    schedule.reset_booking_date()
    await message.answer("Поздравляю, вы записаны!")
    await command_start_handler(message)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
