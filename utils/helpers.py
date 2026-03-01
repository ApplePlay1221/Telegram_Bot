from datetime import datetime, timedelta

def format_date(date_str):
    """Форматирование даты из YYYY-MM-DD в DD.MM.YYYY"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d.%m.%Y")

def get_weekday_name(date_str):
    """Получение названия дня недели"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    return days[date_obj.weekday()]

def is_future_date(date_str):
    """Проверка, что дата в будущем"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    return date_obj >= datetime.now().date()

def is_within_24_hours(date_str, time_str):
    """Проверка, что дата и время в пределах 24 часов от сейчас"""
    booking_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    now = datetime.now()
    return booking_dt - now < timedelta(hours=24)