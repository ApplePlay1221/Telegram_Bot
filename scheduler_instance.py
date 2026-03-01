# scheduler_instance.py
from scheduler import Scheduler
from database import db

# Создаем экземпляр scheduler без bot (будет установлен позже)
scheduler = Scheduler(None, db)