import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

# Вставь сюда свой токен бота от @BotFather
TOKEN = "8754277663:AAErLiAi1Zazsi1m-EL2zOM82uefDBr4e3s"

# Твоя группа отключений
GROUP_NAME = "6.1"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных в памяти бота
storage = {
    "last_known_status": True,  # True — свет есть, False — отключен
    "schedule_text": "📋 Графік поки не встановлено. Очікуйте оновлення."
}

subscribers = set()  # Список ID пользователей для автоматической рассылки

@dp.message(Command("start"))
async def cmd_start(message: Message):
    subscribers.add(message.chat.id)
    await message.answer(
        f"🤖 Привіт! Бот моніторингу світла для групи **{GROUP_NAME}** активовано.\n\n"
        "Я автоматично надсилатиму оновлення графіків та сповіщення.\n\n"
        "Команди:\n"
        "/status — перевірити поточний стан та актуальний графік",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: Message):
    status_now = "🟢 Увімкнено (Світло є)" if storage["last_known_status"] else "🔴 Вимкнено (Світла немає)"
    
    await message.answer(
        f"📍 **Група:** {GROUP_NAME}\n"
        f"⚡️ **Статус зараз:** {status_now}\n\n"
        f"{storage['schedule_text']}",
        parse_mode="Markdown"
    )

# Команда для обновления графика: /update и текст нового графика
@dp.message(Command("update"))
async def cmd_update(message: Message, command: CommandObject):
    if not command.args:
        await message.answer(
            "⚠️ Будь ласка, вкажіть текст графіку після команди.\n"
            "Приклад:\n`/update 📋 **Графік на сьогодні:**\n08:00 - 12:00 — відключення\n...`",
            parse_mode="Markdown"
        )
        return

    # Сохраняем новый график
    new_schedule = f"📋 **Актуальний графік (група {GROUP_NAME}):**\n\n{command.args}"
    storage["schedule_text"] = new_schedule

    # Формируем текст для автоматической рассылки
    broadcast_text = (
        f"🔔 **УВАГА! Оновлено графік відключень світла!**\n"
        f"Група: **{GROUP_NAME}**\n\n"
        f"{new_schedule}"
    )

    # Автоматически рассылаем всем подписанным пользователям
    success_count = 0
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id, broadcast_text, parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            logging.error(f"Не вдалося надіслати сповіщення для {chat_id}: {e}")

    await message.answer(f"✅ Графік успішно оновлено і розіслано підписникам ({success_count} чол.)!")

# Фоновая проверка состояния (для будущих автоматических доработок)
async def background_checker():
    await asyncio.sleep(10)
    while True:
        try:
            # Здесь в будущем можно завязать дополнительную логику
            pass
        except Exception as e:
            logging.error(f"Помилка у фоновому завданні: {e}")
        await asyncio.sleep(300)

# Веб-сервер для поддержания активности на Render
async def handle(request):
    return web.Response(text="DTEK Auto Bot with Schedule is running 24/7!")

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
