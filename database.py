import sqlite3
from datetime import datetime
from typing import List, Tuple

class ReminderDatabase:
    def __init__(self, db_path: str = "reminders.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание таблиц в базе данных при необходимости"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создание таблицы напоминаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                reminder_datetime TEXT NOT NULL,
                status TEXT DEFAULT 'Ожидает',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                repeat_pattern TEXT DEFAULT NULL
            )
        ''')
        
        # Проверка наличия столбца repeat_pattern и его добавление при необходимости
        try:
            cursor.execute('SELECT repeat_pattern FROM reminders LIMIT 1')
        except sqlite3.OperationalError:
            # Столбец отсутствует, добавляем его
            cursor.execute('ALTER TABLE reminders ADD COLUMN repeat_pattern TEXT DEFAULT NULL')
        
        conn.commit()
        conn.close()
    
    def add_reminder(self, title: str, description: str, reminder_datetime: str, repeat_pattern: str = None) -> int:
        """Добавление нового напоминания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем текущее локальное время для создания записи
        local_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO reminders (title, description, reminder_datetime, status, created_at, repeat_pattern)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, reminder_datetime, 'Ожидает', local_created_at, repeat_pattern))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Удаление напоминания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def update_reminder_status(self, reminder_id: int, status: str) -> bool:
        """Обновление статуса напоминания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE reminders SET status = ? WHERE id = ?', (status, reminder_id))
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return updated
    
    def get_all_reminders(self) -> List[Tuple]:
        """Получение всех напоминаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reminders ORDER BY reminder_datetime')
        reminders = cursor.fetchall()
        
        conn.close()
        return reminders
    
    def get_reminders_by_status(self, status: str) -> List[Tuple]:
        """Получение напоминаний по статусу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reminders WHERE status = ? ORDER BY reminder_datetime', (status,))
        reminders = cursor.fetchall()
        
        conn.close()
        return reminders
    
    def get_overdue_reminders(self) -> List[Tuple]:
        """Получение просроченных напоминаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE reminder_datetime < ? AND status != 'Готово' AND status != 'Отменено'
            ORDER BY reminder_datetime
        ''', (current_time,))
        
        reminders = cursor.fetchall()
        
        conn.close()
        return reminders
    
    def update_overdue_status(self):
        """Автоматическое обновление статуса просроченных напоминаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE reminders 
            SET status = 'Просрочено' 
            WHERE reminder_datetime < ? AND status != 'Готово' AND status != 'Отменено'
        ''', (current_time,))
        
        updated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        return updated_count
    
    def get_reminders_with_repeat(self) -> List[Tuple]:
        """Получение напоминаний с повторением"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reminders WHERE repeat_pattern IS NOT NULL AND repeat_pattern != "" ORDER BY reminder_datetime')
        reminders = cursor.fetchall()
        
        conn.close()
        return reminders
    
    def update_reminder_datetime(self, reminder_id: int, new_datetime: str) -> bool:
        """Обновление даты и времени напоминания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE reminders SET reminder_datetime = ? WHERE id = ?', (new_datetime, reminder_id))
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return updated