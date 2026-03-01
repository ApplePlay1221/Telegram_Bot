from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import logging

class Scheduler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}

    async def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
        logging.info("Планировщик запущен")

    async def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logging.info("Планировщик остановлен")

    async def restore_jobs(self):
        """Восстановление задач после перезапуска"""
        if not self.bot:
            logging.error("Bot не инициализирован в планировщике")
            return
            
        bookings = self.db.get_all_future_bookings()
        now = datetime.now()

        for booking in bookings:
            booking_id, user_id, date_str, time_str, name, phone, notified = booking

            # Проверяем, не было ли уже уведомления
            if notified:
                continue

            # Формируем datetime записи
            booking_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            reminder_time = booking_datetime - timedelta(hours=24)

            # Если до записи меньше 24 часов или запись уже прошла, пропускаем
            if reminder_time <= now or booking_datetime <= now:
                continue

            # Планируем напоминание
            await self.schedule_reminder(booking_id, user_id, date_str, time_str, reminder_time)

    async def schedule_reminder(self, booking_id, user_id, date_str, time_str, reminder_time):
        """Планирование напоминания"""
        if not self.bot:
            logging.error("Bot не инициализирован в планировщике")
            return
            
        job_id = f"reminder_{booking_id}"

        # Добавляем задачу
        self.scheduler.add_job(
            self.send_reminder,
            trigger=DateTrigger(run_date=reminder_time),
            args=[user_id, date_str, time_str],
            id=job_id,
            replace_existing=True
        )

        self.jobs[booking_id] = job_id
        logging.info(f"Запланировано напоминание для записи {booking_id} на {reminder_time}")

    async def send_reminder(self, user_id, date_str, time_str):
        """Отправка напоминания"""
        if not self.bot:
            logging.error("Bot не инициализирован в планировщике")
            return
            
        try:
            # Форматируем дату для сообщения
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")

            text = (
                f"🔔 <b>Напоминание о записи</b>\n\n"
                f"Вы записаны на завтра, {formatted_date} в {time_str}.\n"
                f"Ждём вас! ✨"
            )

            await self.bot.send_message(user_id, text)

            # Отмечаем в базе, что уведомление отправлено
            # Нам нужно найти booking_id по user_id и дате
            bookings = self.db.get_all_future_bookings()
            for booking in bookings:
                if booking[1] == user_id and booking[2] == date_str and booking[3] == time_str:
                    self.db.mark_notified(booking[0])
                    break

            logging.info(f"Напоминание отправлено пользователю {user_id}")

        except Exception as e:
            logging.error(f"Ошибка при отправке напоминания: {e}")

    async def remove_job(self, booking_id):
        """Удаление задачи напоминания"""
        if booking_id in self.jobs:
            try:
                self.scheduler.remove_job(self.jobs[booking_id])
                del self.jobs[booking_id]
                logging.info(f"Задача напоминания {booking_id} удалена")
            except Exception as e:
                logging.error(f"Ошибка при удалении задачи: {e}")