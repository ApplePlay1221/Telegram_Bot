from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from config import CHANNEL_LINK

def get_main_keyboard(show_portfolio_button=False):
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="💰 Прайс", callback_data="prices")],
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel")],
    ]

    if show_portfolio_button:
        keyboard.insert(1, [
            InlineKeyboardButton(
                text="📸 Смотреть портфолио",
                url="https://ru.pinterest.com/crystalwithluv/_created/"
            )
        ])
    else:
        keyboard.insert(1, [
            InlineKeyboardButton(text="📸 Портфолио", callback_data="portfolio")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_keyboard():
    """Клавиатура для проверки подписки"""
    keyboard = [
        [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_dates_keyboard(dates, prefix="date"):
    """Клавиатура с датами"""
    keyboard = []
    row = []

    for i, date_str in enumerate(dates):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Форматируем для отображения: "15.05 (ср)"
        display_text = date_obj.strftime("%d.%m")
        day_name = date_obj.strftime("%a")

        button = InlineKeyboardButton(
            text=f"{display_text} {day_name}",
            callback_data=f"{prefix}_{date_str}"
        )

        row.append(button)

        if len(row) == 3 or i == len(dates) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_times_keyboard(times):
    """Клавиатура с временными слотами"""
    keyboard = []
    row = []

    for i, time in enumerate(times):
        button = InlineKeyboardButton(text=time, callback_data=f"time_{time}")
        row.append(button)

        if len(row) == 3 or i == len(times) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_dates")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_confirmation_keyboard(booking_id):
    """Клавиатура подтверждения отмены"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"confirm_cancel_{booking_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить рабочий день", callback_data="admin_add_day")],
        [InlineKeyboardButton(text="➖ Удалить рабочий день", callback_data="admin_remove_day")],
        [InlineKeyboardButton(text="🔒 Закрыть день", callback_data="admin_close_day")],
        [InlineKeyboardButton(text="👁 Просмотреть записи", callback_data="admin_view_day")],
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="admin_cancel_booking")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)