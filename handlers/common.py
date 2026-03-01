from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

from config import CHANNEL_ID, CHANNEL_LINK
from keyboards.inline import get_main_keyboard, get_subscription_keyboard
from database import db  # Импортируем глобальный экземпляр

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Проверяем подписку на канал
    if await check_subscription(message.bot, user_id):
        await show_main_menu(message)
    else:
        await show_subscription_required(message)

async def check_subscription(bot, user_id):
    """Проверка подписки на канал"""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        # Если не удалось проверить (например, бот не админ в канале), считаем что подписан
        return True

async def show_main_menu(message: Message):
    """Показать главное меню"""
    text = (
        "<b>🌸 Добро пожаловать в бот мастера по маникюру!</b>\n\n"
        "Здесь вы можете:\n"
        "• Записаться на удобное время\n"
        "• Посмотреть портфолио\n"
        "• Ознакомиться с прайсом\n"
        "• Отменить запись\n\n"
        "Выберите действие:"
    )
    await message.answer(text, reply_markup=get_main_keyboard())

async def show_subscription_required(message: Message):
    """Показать сообщение о необходимости подписки"""
    text = (
        "📢 <b>Для записи необходимо подписаться на канал</b>\n\n"
        "Подпишитесь на наш канал, чтобы быть в курсе новостей и акций!"
    )
    await message.answer(text, reply_markup=get_subscription_keyboard())

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """Проверка подписки через callback"""
    if await check_subscription(callback.bot, callback.from_user.id):
        await callback.message.delete()
        await show_main_menu(callback.message)
    else:
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)

@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery):
    """Показать прайс-лист"""
    text = (
        "<b>💰 Прайс-лист</b>\n\n"
        "💅 <b>Маникюр:</b>\n"
        "• Френч — 1000₽\n"
        "• Квадрат — 500₽\n"
        "• Овальная форма — 600₽\n"
        "• Миндаль — 700₽\n\n"
        "🎨 <b>Дизайн:</b>\n"
        "• Однотонное покрытие — 800₽\n"
        "• Френч — 1000₽\n"
        "• Градиент — 1200₽\n"
        "• Слайдеры — +200₽\n\n"
        "✨ <b>Дополнительно:</b>\n"
        "• Укрепление гелем — 300₽\n"
        "• Ремонт одного ногтя — 100₽"
    )
    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    """Показать портфолио"""
    text = (
        "<b>📸 Портфолио</b>\n\n"
        "Нажмите на кнопку ниже, чтобы посмотреть мои работы в Pinterest:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_main_keyboard(show_portfolio_button=True)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await show_main_menu(callback.message)
    await callback.answer()