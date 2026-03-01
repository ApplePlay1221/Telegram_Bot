from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

from database import db
from keyboards.inline import get_main_keyboard, get_cancel_confirmation_keyboard
from config import ADMIN_ID
from scheduler_instance import scheduler

router = Router()
@router.callback_query(F.data == "cancel")
async def start_cancellation(callback: CallbackQuery):
    """Начало процесса отмены записи"""
    user_id = callback.from_user.id

    # Проверяем, есть ли активная запись
    booking = db.get_user_booking(user_id)

    if not booking:
        await callback.message.edit_text(
            "❌ У вас нет активных записей.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
        return

    booking_id, date, time, name, phone = booking

    # Форматируем дату
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    text = (
        "<b>❓ Вы действительно хотите отменить запись?</b>\n\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {time}\n\n"
        "<i>Это действие нельзя отменить.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_confirmation_keyboard(booking_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancellation(callback: CallbackQuery):
    """Подтверждение отмены записи"""
    booking_id = int(callback.data.replace("confirm_cancel_", ""))

    # Отменяем запись
    success, result = db.cancel_booking(callback.from_user.id, booking_id)

    if success:
        date_str, time_str, booking_id = result

        # Удаляем задачу напоминания
        await scheduler.remove_job(booking_id)

        # Форматируем дату
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")

        await callback.message.edit_text(
            f"✅ <b>Запись успешно отменена!</b>\n\n"
            f"📅 {formatted_date}\n"
            f"🕐 {time_str}\n\n"
            f"Если захотите записаться снова, воспользуйтесь меню.",
            reply_markup=get_main_keyboard()
        )

        # Уведомляем администратора
        await callback.bot.send_message(
            ADMIN_ID,
            f"❌ Пользователь @{callback.from_user.username or callback.from_user.id} "
            f"отменил запись на {formatted_date} в {time_str}"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при отмене записи. Возможно, она уже была отменена.",
            reply_markup=get_main_keyboard()
        )

    await callback.answer()