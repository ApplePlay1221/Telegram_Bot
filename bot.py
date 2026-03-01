import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import db
from scheduler_instance import scheduler
from handlers import common, booking, admin, cancellation

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def on_startup():
    """Действия при запуске бота"""
    # Устанавливаем bot в scheduler после его создания
    scheduler.bot = bot
    await scheduler.start()
    await scheduler.restore_jobs()
    logging.info("Бот запущен!")

async def on_shutdown():
    """Действия при остановке бота"""
    await scheduler.shutdown()
    db.close()
    logging.info("Бот остановлен!")

async def main():
    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    dp.include_router(cancellation.router)

    # Запуск
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())