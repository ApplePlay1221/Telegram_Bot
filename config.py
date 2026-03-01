import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID администратора
ADMIN_ID = int(os.getenv('ADMIN_ID', '123456789'))

# Канал для проверки подписки
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel')  # Например: @manicure_channel или -100123456789
CHANNEL_LINK = os.getenv('CHANNEL_LINK', 'https://t.me/your_channel')

# Канал для расписания
SCHEDULE_CHANNEL_ID = os.getenv('SCHEDULE_CHANNEL_ID', '@schedule_channel')

# База данных
DATABASE_PATH = 'manicure_bot.db'

# Временные настройки
WORK_HOURS_START = 10  # Начало рабочего дня (10:00)
WORK_HOURS_END = 20    # Конец рабочего дня (20:00)
SLOT_DURATION = 60     # Длительность слота в минутах
DAYS_AHEAD = 30        # Дней вперед для расписания