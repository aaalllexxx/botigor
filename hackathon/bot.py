import json

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from main import Recognizer
import dotenv
import re
import codecs
import random

token = dotenv.get_key(".env", "TOKEN")

bot = Bot(token=token)
dp = Dispatcher(bot)
recognizer = Recognizer()
failure_phrases = ["Мы не совсем поняли ваш вопрос, можете, пожалуйста, сформулировать его по-другому?",
                   "я не очень понял, не мог бы ты переформулировать?",
                   "Фраза ошибки номер 3"]

with open("data_json/user_settings.json", "rb") as file:
    user_settings = json.loads(codecs.decode(file.read(), "utf-8-sig"))

with open("wordlists/greeting.txt", encoding="utf-8") as file:
    greetings = file.read().split("\n")


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_settings[message.chat.id] = "android"
    with open("data_json/user_settings.json", "w") as user_file:
        json.dump(user_settings, user_file)
    await bot.send_message(message.chat.id, f"Текущая система: {user_settings[message.chat.id]}")
    await bot.send_message(message.chat.id,
                           f"Напиши мне свой вид системы (android, ios, другое), чтобы я смог тебе помочь.")
    await bot.send_message(message.chat.id, random.choice(greetings))


@dp.message_handler(
    lambda message: message.text.lower() == "android" or message.text.lower() == "ios" or message.text.lower() == "другое")
async def set_android_system(message: types.Message):
    user_settings[message.chat.id] = message.text.lower()
    with open("data_json/user_settings.json", "w") as user_file:
        json.dump(user_settings, user_file)
    await bot.send_message(message.chat.id, f"Система изменена на {message.text}")


@dp.message_handler(content_types=["text"])
async def on_user_message(message: types.Message):
    with open("data_json/user_settings.json", "rb") as user_file:
        user_settings = json.loads(codecs.decode(user_file.read(), "utf-8-sig"))
    question = message.text
    data = recognizer.get_data(question)
    if data["status"] == 200:
        keys = list(data)
        if "OS" in keys:
            if data["OS"].lower() != user_settings.get(str(message.chat.id)):
                del data["status"]
                index = recognizer.data.index(data)
                if recognizer.data[index - 1]["Question"] == data["Question"]:
                    data = recognizer.data[index - 1]
                else:
                    data = recognizer.data[index + 1]
        steps = [i for i in list(data) if re.fullmatch("Step[0-9]*", i)]
        print(user_settings)
        await bot.send_message(message.chat.id,
                               f"✅ Ответ на вопрос: "
                               f"{data['Question']} "
                               f"(платформа {data.get('OS') or user_settings[str(message.chat.id)]})")
        resp = ""
        for n, key in enumerate(steps):
            resp += f"{n + 1}. {data[key]}\n"

        await bot.send_message(message.chat.id, resp)
    elif data["status"] == 404:
        await bot.send_message(message.chat.id, "⛔ " + random.choice(failure_phrases))


if __name__ == '__main__':
    executor.start_polling(dp)
