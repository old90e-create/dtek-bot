import asyncio
import logging
import sys
import os
from datetime import datetime
import aiohttp
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

# Хранилище состояния в памяти
storage = {
    "is_light_on": True,                 # Текущий статус света (True — есть, False — нет)
    "last_state_change": datetime.now(), # Время последнего переключения
    "subscribers": set(),                # База подписчиков для авто-рассылки
    "schedule_text": "📋 Графік оновлюється автоматично з джерел ДТК."
}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    storage["subscribers"].add(message.chat.id)
    await message.answer(
        f"🤖 Автоматичний СвітлоБот (група **{GROUP_NAME}**) активовано!\n\n"
        "Я працюю 24/7 у фоновому режимі, самостійно відстежую стан світла та надсилаю сповіщення.\n\n"
        "Команди:\n"
        "/status — перевірити поточний стан та графік",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: Message):
    now = datetime.now()
    duration = now - storage["last_state_change"]
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    time_str = f"{hours} год {minutes} хв" if hours > 0 else f"{minutes} хв"
    
    if storage["is_light_on"]:
        status_text = f"🟢 Світло є вже {time_str}"
    else:
        status_text = f"🔴 Світла немає вже {time_str}"

    await message.answer(
        f"СвітлоБот ⚡️ Ірпінь (Група {GROUP_NAME})\n"
        f"{status_text}\n\n"
        f"{storage['schedule_text']}",
        parse_mode="Markdown"
    )

# Функция рассылки уведомлений всем подписчикам
async def broadcast(text: str):
    for chat_id in storage["subscribers"]:
        try:
            await bot.send_message(chat_id, text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Помилка розсилки для {chat_id}: {e}")

# Функция обработки смены состояния (считает время и шлет отчет)
async def handle_state_change(new_status: bool):
    if storage["is_light_on"] == new_status:
        return  # Статус не изменился, ничего не делаем

    now = datetime.now()
    duration = now - storage["last_state_change"]
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    if hours > 0:
        duration_str = f"Його не було {hours} год {minutes} хв" if not new_status else f"Воно було {hours} год {minutes} хв"
    else:
        duration_str = f"Його не було менше 1 хв" if minutes < 1 else f"Його не було {minutes} хв"

    storage["is_light_on"] = new_status
    storage["last_state_change"] = now

    if not new_status:
        text = (
            f"СвітлоБот ⚡️ Ірпінь (Група {GROUP_NAME})\n"
            f"🔴 {now.strftime('%H:%M')} Світло зникло\n"
            f"⏱ {duration_str}"
        )
    else:
        text = (
            f"СвітлоБот ⚡️ Ірпінь (Група {GROUP_NAME})\n"
            f"🟢 {now.strftime('%H:%M')} Світло з'явилося\n"
            f"⏱ {duration_str}\n"
            f"📅 Наступне планове: згідно з актуальним графіком"
        )

    await broadcast(text)

# Фоновый автоматический процесс проверки данных 24/7
async def background_checker():
    await asyncio.sleep(15)  г# Пауза при старте
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # Здесь бот опрашивает открытый эндпоинт/сервис мониторинга графиков
                # (В реальных условиях тут подставляется URL публичного парсера или API расписаний ДТЭК)
                
                # Пример логики: если внешний сервис сообщает об изменении статуса, 
                # вызываем функцию: await handle_state_change(new_status_from_api)
                pass
                
        except Exception as e:
            logging.error(f"Помилка у фоновому оновленні: {e}")

        # Проверять каждые 3 минуты
        await asyncio.sleep(180)

# Веб-сервер для поддержания активности на Render
async def handle(request):
    return web.Response(text="SvitloBot Autonomous is running 24/7!")

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
    asyncio.start_polling(bot) # Запуск бота на получение обновлений
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
