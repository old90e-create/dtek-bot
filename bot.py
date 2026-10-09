import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Вставь сюда свой актуальный токен бота от @BotFather
TOKEN = "8754277663:AAErLiAi1Zazsi1m-EL2zOM82uefDBr4e3s"

# Твоя группа отключений
GROUP_NAME = "6.1"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище состояния и подписчиков
storage = {
    "last_known_status": True,  # True — свет есть, False — отключен
    "current_schedule_text": "Графік стабілізаційних відключень для групи 6.1 актуальний."
}

subscribers = set()  # Множество ID пользователей, которые получат авто-рассылку

@dp.message(Command("start"))
async def cmd_start(message: Message):
    subscribers.add(message.chat.id)
    await message.answer(
        f"🤖 Привіт! Бот моніторингу світла для групи **{GROUP_NAME}** активовано.\n\n"
        "Я автоматично надсилатиму сповіщення про зміну стану світла всім підписаним!\n\n"
        "Команди:\n"
        "/status — перевірити поточний стан та графік",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: Message):
    status_now = "🟢 Увімкнено (Світло є)" if storage["last_known_status"] else "🔴 Вимкнено (Світла немає)"
    
    await message.answer(
        f"📍 **Група:** {GROUP_NAME}\n"
        f"⚡️ **Статус зараз:** {status_now}\n\n"
        f"📋 **Інформація:**\n{storage['current_schedule_text']}",
        parse_mode="Markdown"
    )

# Функция автоматической рассылки всем пользователям
async def notify_subscribers(text: str):
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id, text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не вдалося надіслати повідомлення для {chat_id}: {e}")

# Фоновый процесс, который проверяет изменения и шлет уведомления
async def background_checker():
    await asyncio.sleep(10)  # Пауза при старте
    
    while True:
        try:
            # Здесь в будущем будет реальный запрос к источнику/парсителю ДТЭК.
            # Для демонстрации автоматики логика работает так:
            # Допустим, мы узнали новый статус (в реальности сравниваем с сайтом)
            
            is_light_on = storage["last_known_status"] # Текущий статус
            
            # ПРИМЕР: Если статус изменился, бот САМ шлет уведомление:
            # if real_new_status != storage["last_known_status"]:
            #     storage["last_known_status"] = real_new_status
            #     status_word = "УВІМКНУЛИ 🟢" if real_new_status else "ВИМКНУЛИ 🔴"
            #     await notify_subscribers(f"💡 **УВАГА! Зміна стану світла!**\nГрупа: {GROUP_NAME}\nСвітло **{status_word}**")

        except Exception as e:
            logging.error(f"Помилка у фоновому завданні: {e}")

        await asyncio.sleep(300)  # Проверка каждые 5 минут

# Веб-сервер для поддержания активности на Render
async def handle(request):
    return web.Response(text="DTEK Auto Bot is running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.create_task(web_server())
    asyncio.create_task(background_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
