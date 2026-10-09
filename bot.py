Python
import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Вставь сюда токен своего бота от @BotFather
TOKEN = "8754277663:AAErLiAi1Zazsi1m-EL2zOM82uefDBr4e3s"

# Твоя группа отключений
GROUP_NAME = "6.1"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных в памяти бота
storage = {
    "last_known_status": True,  # True — свет есть, False — отключен
    "schedule": {
        "00:00 - 04:00": False,
        "04:00 - 08:00": True,
        "08:00 - 12:00": False,
        "12:00 - 16:00": True,
        "16:00 - 20:00": False,
        "20:00 - 24:00": True,
    }
}

subscribers = set()  # Список ID пользователей для рассылки

@dp.message(Command("start"))
async def cmd_start(message: Message):
    subscribers.add(message.chat.id)
    await message.answer(
        f"🤖 Привіт! Бот моніторингу світла для групи **{GROUP_NAME}** активовано.\n\n"
        "Команди:\n"
        "/status — перевірити поточний стан та графік\n"
        "/set_on — позначити, що світло УВІМКНУЛИ\n"
        "/set_off — позначити, що світло ВИМКНУЛИ",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: Message):
    status_now = "🟢 Увімкнено (Світло є)" if storage["last_known_status"] else "🔴 Вимкнено (Світла немає)"
    
    schedule_text = "\n".join([
        f"🕒 {time_slot}: {'🟢 Є' if is_on else '🔴 Немає'}" 
        for time_slot, is_on in storage["schedule"].items()
    ])
    
    await message.answer(
        f"📍 **Група:** {GROUP_NAME}\n"
        f"⚡️ **Статус зараз:** {status_now}\n\n"
        f"📋 **Поточний графік:**\n{schedule_text}",
        parse_mode="Markdown"
    )

@dp.message(Command("set_on"))
async def cmd_set_on(message: Message):
    await update_light_status(True)
    await message.answer("✅ Статус змінено: світло УВІМКНЕНО. Підписникам надіслано сповіщення.")

@dp.message(Command("set_off"))
async def cmd_set_off(message: Message):
    await update_light_status(False)
    await message.answer("⚠️ Статус змінено: світло ВИМКНЕНО. Підписникам надіслано сповіщення.")

async def update_light_status(is_on: bool):
    if storage["last_known_status"] != is_on:
        storage["last_known_status"] = is_on
        
        status_text = "УВІМКНУЛИ 🟢" if is_on else "ВИМКНУЛИ 🔴"
        text = (
            f"💡 **УВАГА! Зміна стану світла!**\n"
            f"Група: **{GROUP_NAME}**\n"
            f"Світло **{status_text}**"
        )
        
        for chat_id in subscribers:
            try:
                await bot.send_message(chat_id, text, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Не вдалося надіслати повідомлення для {chat_id}: {e}")

# Простой веб-сервер для Render (чтобы хостинг видел, что сервис живой)
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передает порт через переменную окружения PORT, по умолчанию берем 10000
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.info(f"Web server started on port {port}")

async def main():
    # Запускаем веб-сервер и телеграм-бота одновременно
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
