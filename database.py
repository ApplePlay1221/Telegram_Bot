import sqlite3
import datetime
from config import DATABASE_PATH, WORK_HOURS_START, WORK_HOURS_END, SLOT_DURATION, DAYS_AHEAD

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.generate_initial_slots()

    def create_tables(self):
        # Таблица рабочих дней
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS working_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                is_working INTEGER DEFAULT 1,
                is_closed INTEGER DEFAULT 0
            )
        ''')

        # Таблица временных слотов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_available INTEGER DEFAULT 1,
                booked_by INTEGER DEFAULT NULL,
                booking_id INTEGER DEFAULT NULL,
                UNIQUE(date, time)
            )
        ''')

        # Таблица записей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                UNIQUE(user_id, date)
            )
        ''')

        self.conn.commit()

    def generate_initial_slots(self):
        """Генерация слотов на месяц вперед"""
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=DAYS_AHEAD)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            # Проверяем, существует ли уже этот день
            self.cursor.execute('SELECT id FROM working_days WHERE date = ?', (date_str,))
            if not self.cursor.fetchone():
                # По умолчанию все дни рабочие, кроме воскресенья
                is_working = 0 if current_date.weekday() == 6 else 1
                self.cursor.execute(
                    'INSERT INTO working_days (date, is_working) VALUES (?, ?)',
                    (date_str, is_working)
                )

            # Генерируем слоты только для рабочих дней
            self.cursor.execute('SELECT is_working, is_closed FROM working_days WHERE date = ?', (date_str,))
            day_info = self.cursor.fetchone()

            if day_info and day_info[0] == 1 and day_info[1] == 0:
                for hour in range(WORK_HOURS_START, WORK_HOURS_END):
                    for minute in [0, 30] if SLOT_DURATION == 30 else [0]:
                        time_str = f"{hour:02d}:{minute:02d}"

                        # Проверяем, существует ли уже такой слот
                        self.cursor.execute(
                            'SELECT id FROM time_slots WHERE date = ? AND time = ?',
                            (date_str, time_str)
                        )
                        if not self.cursor.fetchone():
                            self.cursor.execute(
                                'INSERT INTO time_slots (date, time) VALUES (?, ?)',
                                (date_str, time_str)
                            )

            current_date += datetime.timedelta(days=1)

        self.conn.commit()

    def check_subscription(self, user_id):
        """Проверка, есть ли у пользователя активная запись"""
        self.cursor.execute(
            'SELECT id FROM bookings WHERE user_id = ? AND date >= date("now")',
            (user_id,)
        )
        return self.cursor.fetchone() is not None

    def add_working_day(self, date_str):
        """Добавление рабочего дня"""
        self.cursor.execute(
            'INSERT OR REPLACE INTO working_days (date, is_working, is_closed) VALUES (?, 1, 0)',
            (date_str,)
        )
        self.conn.commit()
        self.generate_slots_for_date(date_str)

    def generate_slots_for_date(self, date_str):
        """Генерация слотов для конкретной даты"""
        for hour in range(WORK_HOURS_START, WORK_HOURS_END):
            for minute in [0, 30] if SLOT_DURATION == 30 else [0]:
                time_str = f"{hour:02d}:{minute:02d}"
                self.cursor.execute(
                    'INSERT OR IGNORE INTO time_slots (date, time) VALUES (?, ?)',
                    (date_str, time_str)
                )
        self.conn.commit()

    def remove_working_day(self, date_str):
        """Удаление рабочего дня"""
        self.cursor.execute(
            'UPDATE working_days SET is_working = 0 WHERE date = ?',
            (date_str,)
        )
        self.cursor.execute('DELETE FROM time_slots WHERE date = ?', (date_str,))
        self.conn.commit()

    def close_day(self, date_str):
        """Закрытие дня для записи"""
        self.cursor.execute(
            'UPDATE working_days SET is_closed = 1 WHERE date = ?',
            (date_str,)
        )
        self.cursor.execute(
            'UPDATE time_slots SET is_available = 0 WHERE date = ? AND is_available = 1',
            (date_str,)
        )
        self.conn.commit()

    def add_time_slot(self, date_str, time_str):
        """Добавление временного слота"""
        self.cursor.execute(
            'INSERT OR IGNORE INTO time_slots (date, time, is_available) VALUES (?, ?, 1)',
            (date_str, time_str)
        )
        self.conn.commit()

    def remove_time_slot(self, date_str, time_str):
        """Удаление временного слота"""
        self.cursor.execute(
            'DELETE FROM time_slots WHERE date = ? AND time = ?',
            (date_str, time_str)
        )
        self.conn.commit()

    def get_available_dates(self):
        """Получение доступных дат для записи"""
        self.cursor.execute('''
            SELECT DISTINCT ts.date 
            FROM time_slots ts
            JOIN working_days wd ON ts.date = wd.date
            WHERE ts.is_available = 1 
                AND wd.is_working = 1 
                AND wd.is_closed = 0
                AND ts.date >= date('now')
            ORDER BY ts.date
        ''')
        return [row[0] for row in self.cursor.fetchall()]

    def get_available_times(self, date_str):
        """Получение доступного времени для конкретной даты"""
        self.cursor.execute('''
            SELECT time FROM time_slots 
            WHERE date = ? AND is_available = 1
            ORDER BY time
        ''', (date_str,))
        return [row[0] for row in self.cursor.fetchall()]

    def book_slot(self, user_id, username, name, phone, date_str, time_str):
        """Бронирование слота"""
        try:
            # Начинаем транзакцию
            self.cursor.execute('BEGIN TRANSACTION')

            # Проверяем, нет ли у пользователя уже записи
            if self.check_subscription(user_id):
                self.cursor.execute('ROLLBACK')
                return False, "У вас уже есть активная запись"

            # Проверяем, доступен ли слот
            self.cursor.execute(
                'SELECT id FROM time_slots WHERE date = ? AND time = ? AND is_available = 1',
                (date_str, time_str)
            )
            slot = self.cursor.fetchone()
            if not slot:
                self.cursor.execute('ROLLBACK')
                return False, "Это время уже недоступно"

            # Создаем запись
            self.cursor.execute('''
                INSERT INTO bookings (user_id, username, name, phone, date, time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, name, phone, date_str, time_str))

            booking_id = self.cursor.lastrowid

            # Обновляем слот
            self.cursor.execute('''
                UPDATE time_slots 
                SET is_available = 0, booked_by = ?, booking_id = ?
                WHERE date = ? AND time = ?
            ''', (user_id, booking_id, date_str, time_str))

            self.conn.commit()
            return True, booking_id

        except Exception as e:
            self.cursor.execute('ROLLBACK')
            print(f"Error booking slot: {e}")
            return False, str(e)

    def cancel_booking(self, user_id, booking_id=None):
        """Отмена записи"""
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            if booking_id:
                # Отмена по ID записи (для админа)
                self.cursor.execute(
                    'SELECT date, time FROM bookings WHERE id = ?',
                    (booking_id,)
                )
                booking = self.cursor.fetchone()
                if not booking:
                    self.cursor.execute('ROLLBACK')
                    return False, "Запись не найдена"
                date_str, time_str = booking
            else:
                # Отмена своей записи пользователем
                self.cursor.execute('''
                    SELECT id, date, time FROM bookings 
                    WHERE user_id = ? AND date >= date('now')
                    ORDER BY date LIMIT 1
                ''', (user_id,))
                booking = self.cursor.fetchone()
                if not booking:
                    self.cursor.execute('ROLLBACK')
                    return False, "Запись не найдена"
                booking_id, date_str, time_str = booking

            # Удаляем запись
            self.cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))

            # Освобождаем слот
            self.cursor.execute('''
                UPDATE time_slots 
                SET is_available = 1, booked_by = NULL, booking_id = NULL
                WHERE date = ? AND time = ?
            ''', (date_str, time_str))

            self.conn.commit()
            return True, (date_str, time_str, booking_id)

        except Exception as e:
            self.cursor.execute('ROLLBACK')
            print(f"Error canceling booking: {e}")
            return False, str(e)

    def get_user_booking(self, user_id):
        """Получение текущей записи пользователя"""
        self.cursor.execute('''
            SELECT id, date, time, name, phone FROM bookings 
            WHERE user_id = ? AND date >= date('now')
            ORDER BY date LIMIT 1
        ''', (user_id,))
        return self.cursor.fetchone()

    def get_bookings_for_date(self, date_str):
        """Получение всех записей на дату"""
        self.cursor.execute('''
            SELECT b.id, b.time, b.name, b.phone, b.user_id, b.username
            FROM bookings b
            WHERE b.date = ?
            ORDER BY b.time
        ''', (date_str,))
        return self.cursor.fetchall()

    def get_all_future_bookings(self):
        """Получение всех будущих записей"""
        self.cursor.execute('''
            SELECT id, user_id, date, time, name, phone, notified
            FROM bookings 
            WHERE date >= date('now')
            ORDER BY date, time
        ''')
        return self.cursor.fetchall()

    def mark_notified(self, booking_id):
        """Отметить запись как уведомленную"""
        self.cursor.execute(
            'UPDATE bookings SET notified = 1 WHERE id = ?',
            (booking_id,)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

# Создаем глобальный экземпляр БД
db = Database()