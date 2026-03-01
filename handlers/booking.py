from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import db
from keyboards.inline import (
    get_dates_keyboard, get_times_keyboard, get_main_keyboard,
    get_confirmation_keyboard
)
from config import ADMIN_ID, SCHEDULE_CHANNEL_ID
from scheduler_instance import scheduler  # Импортируем из отдельного файла

router = Router()

class BookingStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    confirmation = State()

@router.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Начало процесса записи"""
    # Проверяем, нет ли уже активной записи
    if db.check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "❌ У вас уже есть активная запись.\n"
            "Вы можете отменить её в разделе 'Отменить запись'.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
        return

    # Получаем доступные даты
    dates = db.get_available_dates()

    if not dates:
        await callback.message.edit_text(
            "😔 К сожалению, на ближайший месяц нет свободных дат.\n"
            "Попробуйте зайти позже или свяжитесь с мастером.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(BookingStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите удобную дату:",
        reply_markup=get_dates_keyboard(dates)
    )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("date_"))
async def process_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    date = callback.data.replace("date_", "")

    # Получаем доступное время для выбранной даты
    times = db.get_available_times(date)

    if not times:
        await callback.answer("На эту дату нет свободного времени", show_alert=True)
        return

    await state.update_data(selected_date=date)
    await state.set_state(BookingStates.waiting_for_time)

    # Форматируем дату для отображения
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"🕐 Выберите удобное время:",
        reply_markup=get_times_keyboard(times)
    )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_time, F.data.startswith("time_"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time = callback.data.replace("time_", "")

    await state.update_data(selected_time=time)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text(
        "✏️ Введите ваше <b>имя</b>:"
    )
    await callback.answer()

@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    name = message.text.strip()

    if len(name) < 2 or len(name) > 50:
        await message.answer("Пожалуйста, введите корректное имя (от 2 до 50 символов):")
        return

    await state.update_data(name=name)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer(
        "📞 Введите ваш <b>номер телефона</b>:\n"
        "Например: +7 (999) 123-45-67"
    )

@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()

    # Простая валидация телефона
    if len(phone) < 10 or not any(c.isdigit() for c in phone):
        await message.answer(
            "Пожалуйста, введите корректный номер телефона:"
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(BookingStates.confirmation)

    # Показываем подтверждение
    data = await state.get_data()
    date_obj = datetime.strptime(data['selected_date'], "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    text = (
        "<b>📝 Проверьте данные записи:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {data['selected_time']}\n\n"
        "Всё верно?"
    )

    await message.answer(text, reply_markup=get_confirmation_keyboard())

@router.callback_query(BookingStates.confirmation, F.data == "confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    data = await state.get_data()
    user = callback.from_user

    # Бронируем слот
    success, result = db.book_slot(
        user.id,
        user.username,
        data['name'],
        data['phone'],
        data['selected_date'],
        data['selected_time']
    )

    if not success:
        await callback.message.edit_text(
            f"❌ Ошибка при записи: {result}\n\n"
            "Попробуйте выбрать другое время.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    booking_id = result

    # Форматируем дату
    date_obj = datetime.strptime(data['selected_date'], "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")

    # Отправляем подтверждение пользователю
    await callback.message.edit_text(
        f"✅ <b>Запись подтверждена!</b>\n\n"
        f"👤 {data['name']}\n"
        f"📅 {formatted_date}\n"
        f"🕐 {data['selected_time']}\n\n"
        f"Ждём вас! ✨\n\n"
        f"<i>Если нужно отменить запись, используйте кнопку "
        f"«Отменить запись» в главном меню.</i>",
        reply_markup=get_main_keyboard()
    )

    # Отправляем уведомление администратору
    admin_text = (
        f"📝 <b>Новая запись!</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🆔 ID: {user.id}\n"
        f"💬 Username: @{user.username if user.username else 'нет'}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {data['selected_time']}"
    )
    await callback.bot.send_message(ADMIN_ID, admin_text)

    # Отправляем в канал с расписанием
    channel_text = (
        f"📅 <b>{formatted_date}</b>\n"
        f"🕐 {data['selected_time']} — {data['name']}"
    )
    await callback.bot.send_message(SCHEDULE_CHANNEL_ID, channel_text)

    # Планируем напоминание, если до записи больше 24 часов
    booking_datetime = datetime.strptime(
        f"{data['selected_date']} {data['selected_time']}",
        "%Y-%m-%d %H:%M"
    )
    reminder_time = booking_datetime - timedelta(hours=24)

    if reminder_time > datetime.now():
        await scheduler.schedule_reminder(
            booking_id,
            user.id,
            data['selected_date'],
            data['selected_time'],
            reminder_time
        )

    await state.clear()
    await callback.answer()

@router.callback_query(BookingStates.confirmation, F.data == "cancel")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Отмена записи (не подтверждение)"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Запись отменена. Вы можете записаться позже.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    dates = db.get_available_dates()
    await state.set_state(BookingStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите удобную дату:",
        reply_markup=get_dates_keyboard(dates)
    )
    await callback.answer()