from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import db
from keyboards.inline import get_admin_keyboard, get_dates_keyboard
from config import ADMIN_ID
from scheduler_instance import scheduler

router = Router()

class AdminStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_booking_id = State()

def admin_only(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            await message.answer("⛔ У вас нет прав для выполнения этой команды.")
            return
        return await func(message, *args, **kwargs)
    return wrapper

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: Message):
    """Открыть админ-панель"""
    text = (
        "<b>🔧 Админ-панель</b>\n\n"
        "Выберите действие:"
    )
    await message.answer(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Назад в админ-панель"""
    await callback.message.edit_text(
        "<b>🔧 Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_day")
async def admin_add_day(callback: CallbackQuery, state: FSMContext):
    """Добавление рабочего дня"""
    # Генерируем даты на ближайшие 30 дней
    dates = []
    for i in range(30):
        date = datetime.now().date() + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))

    await state.set_state(AdminStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите дату для добавления:",
        reply_markup=get_dates_keyboard(dates, prefix="admin_add_day")
    )
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_date, F.data.startswith("admin_add_day_"))
async def process_add_day(callback: CallbackQuery, state: FSMContext):
    """Обработка добавления рабочего дня"""
    date = callback.data.replace("admin_add_day_", "")

    db.add_working_day(date)

    await callback.message.edit_text(
        f"✅ Рабочий день {date} успешно добавлен!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_remove_day")
async def admin_remove_day(callback: CallbackQuery, state: FSMContext):
    """Удаление рабочего дня"""
    dates = db.get_available_dates()

    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных дат для удаления.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(AdminStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите дату для удаления:",
        reply_markup=get_dates_keyboard(dates, prefix="admin_remove_day")
    )
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_date, F.data.startswith("admin_remove_day_"))
async def process_remove_day(callback: CallbackQuery, state: FSMContext):
    """Обработка удаления рабочего дня"""
    date = callback.data.replace("admin_remove_day_", "")

    db.remove_working_day(date)

    await callback.message.edit_text(
        f"✅ Рабочий день {date} удален.",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_close_day")
async def admin_close_day(callback: CallbackQuery, state: FSMContext):
    """Закрытие дня для записи"""
    dates = db.get_available_dates()

    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных дат для закрытия.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(AdminStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите дату для закрытия:",
        reply_markup=get_dates_keyboard(dates, prefix="admin_close_day")
    )
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_date, F.data.startswith("admin_close_day_"))
async def process_close_day(callback: CallbackQuery, state: FSMContext):
    """Обработка закрытия дня"""
    date = callback.data.replace("admin_close_day_", "")

    db.close_day(date)

    await callback.message.edit_text(
        f"✅ День {date} закрыт для записи.",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_view_day")
async def admin_view_day(callback: CallbackQuery, state: FSMContext):
    """Просмотр записей на день"""
    # Получаем все будущие даты с записями
    dates = []
    for i in range(30):
        date = datetime.now().date() + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        bookings = db.get_bookings_for_date(date_str)
        if bookings:
            dates.append(date_str)

    if not dates:
        await callback.message.edit_text(
            "❌ Нет записей на ближайшие дни.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(AdminStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите дату для просмотра:",
        reply_markup=get_dates_keyboard(dates, prefix="admin_view_day")
    )
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_date, F.data.startswith("admin_view_day_"))
async def process_view_day(callback: CallbackQuery, state: FSMContext):
    """Обработка просмотра записей на день"""
    date = callback.data.replace("admin_view_day_", "")
    bookings = db.get_bookings_for_date(date)

    if not bookings:
        await callback.message.edit_text(
            f"📅 <b>{date}</b>\n\nНа этот день нет записей.",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    text = f"<b>📅 Записи на {formatted_date}:</b>\n\n"

    for booking in bookings:
        booking_id, time, name, phone, user_id, username = booking
        text += (
            f"🕐 <b>{time}</b>\n"
            f"👤 {name}\n"
            f"📞 {phone}\n"
            f"🆔 {user_id}\n"
            f"💬 @{username if username else 'нет'}\n"
            f"🔹 ID записи: {booking_id}\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_cancel_booking")
async def admin_cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Отмена записи администратором"""
    # Собираем все будущие записи
    bookings = db.get_all_future_bookings()

    if not bookings:
        await callback.message.edit_text(
            "❌ Нет будущих записей для отмены.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    # Создаем клавиатуру с записями
    keyboard = []

    for booking in bookings[:10]:  # Ограничим 10 записями для удобства
        booking_id, user_id, date, time, name, phone, notified = booking
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m")
        button_text = f"{formatted_date} {time} - {name}"
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"admin_cancel_{booking_id}"
        )])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])

    await state.set_state(AdminStates.waiting_for_booking_id)
    await callback.message.edit_text(
        "Выберите запись для отмены:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(AdminStates.waiting_for_booking_id, F.data.startswith("admin_cancel_"))
async def process_admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Обработка отмены записи администратором"""
    booking_id = int(callback.data.replace("admin_cancel_", ""))

    # Отменяем запись
    success, result = db.cancel_booking(None, booking_id)

    if success:
        date_str, time_str, booking_id = result

        # Удаляем задачу напоминания
        await scheduler.remove_job(booking_id)

        # Уведомляем пользователя
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")

        user_text = (
            f"❌ <b>Ваша запись отменена администратором</b>\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"🕐 Время: {time_str}\n\n"
            f"Если у вас есть вопросы, свяжитесь с мастером."
        )

        try:
            # Пытаемся найти user_id по booking_id
            bookings = db.get_all_future_bookings()
            user_id = None
            for b in bookings:
                if b[0] == booking_id:
                    user_id = b[1]
                    break

            if user_id:
                await callback.bot.send_message(user_id, user_text)
        except:
            pass

        await callback.message.edit_text(
            "✅ Запись успешно отменена!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при отмене записи.",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()
    await callback.answer()