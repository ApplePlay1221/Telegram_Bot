# Telegram_Bot

Бот для маникюрного салона

Структура данных: 

manicure_bot/
├── bot.py                 # Главный файл запуска
├── config.py              # Конфигурация
├── database.py            # Работа с БД
├── scheduler.py           # Класс планировщика
├── scheduler_instance.py  # Глобальный экземпляр scheduler
├── requirements.txt       # Зависимости
├── .env                   # Переменные окружения
├── handlers/
│   ├── __init__.py
│   ├── common.py
│   ├── booking.py
│   ├── admin.py
│   └── cancellation.py
├── keyboards/
│   ├── __init__.py
│   └── inline.py
└── states/
    ├── __init__.py
    └── booking.py
