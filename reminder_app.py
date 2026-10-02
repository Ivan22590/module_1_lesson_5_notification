import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time
from database import ReminderDatabase
from notification import ReminderNotification, check_and_show_notifications

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Напоминалка")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Инициализация базы данных
        self.db = ReminderDatabase()
        
        # Запуск фоновой проверки уведомлений
        self.notification_thread = check_and_show_notifications(self.db, 30)
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка напоминаний при запуске
        self.load_reminders()
        
        # Обновление статусов просроченных напоминаний при запуске
        self.db.update_overdue_status()
    
    def create_widgets(self):
        # Фрейм для добавления новых напоминаний
        add_frame = ttk.LabelFrame(self.root, text="Добавить новое напоминание", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Заголовок
        ttk.Label(add_frame, text="Заголовок:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.title_entry = ttk.Entry(add_frame, width=50)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Описание
        ttk.Label(add_frame, text="Описание:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.description_entry = ttk.Entry(add_frame, width=50)
        self.description_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Дата и время
        ttk.Label(add_frame, text="Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.datetime_entry = ttk.Entry(add_frame, width=50)
        self.datetime_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.datetime_entry.insert(0, datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        # Кнопка добавления
        add_button = ttk.Button(add_frame, text="Добавить напоминание", command=self.add_reminder)
        add_button.grid(row=3, column=1, padx=5, pady=5, sticky=tk.E)
        
        # Фрейм для фильтрации
        filter_frame = ttk.LabelFrame(self.root, text="Фильтр по статусу", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Все")
        statuses = ["Все", "Ожидает", "Готово", "Просрочено", "Отменено"]
        
        for i, status in enumerate(statuses):
            radio = ttk.Radiobutton(filter_frame, text=status, variable=self.status_var, 
                                  value=status, command=self.filter_reminders)
            radio.grid(row=0, column=i, padx=5, pady=2, sticky=tk.W)
        
        # Кнопки управления
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Обновить список", command=self.load_reminders).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить выбранное", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отметить как Готово", command=self.mark_as_done).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отметить как Отменено", command=self.mark_as_cancelled).pack(side=tk.LEFT, padx=5)
        
        # Таблица напоминаний
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("ID", "Заголовок", "Описание", "Дата/Время", "Статус", "Создано")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # Настройка заголовков столбцов
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Вертикальная полоса прокрутки
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка события выбора строки
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Установка ширины столбцов
        self.tree.column("ID", width=50)
        self.tree.column("Заголовок", width=150)
        self.tree.column("Описание", width=200)
        self.tree.column("Дата/Время", width=150)
        self.tree.column("Статус", width=100)
        self.tree.column("Создано", width=150)
    
    def add_reminder(self):
        """Добавление нового напоминания"""
        title = self.title_entry.get().strip()
        description = self.description_entry.get().strip()
        datetime_str = self.datetime_entry.get().strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Введите заголовок напоминания")
            return
        
        try:
            # Проверяем формат даты
            datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ")
            return
        
        try:
            reminder_id = self.db.add_reminder(title, description, datetime_str)
            messagebox.showinfo("Успех", f"Напоминание добавлено с ID: {reminder_id}")
            self.clear_entries()
            self.load_reminders()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить напоминание: {str(e)}")
    
    def load_reminders(self):
        """Загрузка списка напоминаний"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получение напоминаний
        if self.status_var.get() == "Все":
            reminders = self.db.get_all_reminders()
        else:
            reminders = self.db.get_reminders_by_status(self.status_var.get())
        
        # Заполнение таблицы
        for reminder in reminders:
            reminder_id, title, description, reminder_datetime, status, created_at = reminder
            self.tree.insert("", tk.END, values=(
                reminder_id, title, description, reminder_datetime, status, created_at
            ))
    
    def filter_reminders(self):
        """Фильтрация напоминаний по статусу"""
        self.load_reminders()
    
    def clear_entries(self):
        """Очистка полей ввода"""
        self.title_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.datetime_entry.delete(0, tk.END)
        self.datetime_entry.insert(0, datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    def on_select(self, event):
        """Обработка выбора строки в таблице"""
        pass
    
    def delete_selected(self):
        """Удаление выбранного напоминания"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите напоминание для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить выбранное напоминание?"):
            for item in selected_items:
                values = self.tree.item(item, 'values')
                reminder_id = values[0]
                if self.db.delete_reminder(reminder_id):
                    self.tree.delete(item)
            messagebox.showinfo("Успех", "Напоминание успешно удалено")
    
    def mark_as_done(self):
        """Отметить как 'Готово'"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите напоминание для отметки")
            return
        
        for item in selected_items:
            values = self.tree.item(item, 'values')
            reminder_id = values[0]
            self.db.update_reminder_status(reminder_id, 'Готово')
            self.tree.item(item, values=(values[0], values[1], values[2], values[3], 'Готово', values[5]))
        
        messagebox.showinfo("Успех", "Напоминание отмечено как Готово")
    
    def mark_as_cancelled(self):
        """Отметить как 'Отменено'"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите напоминание для отметки")
            return
        
        for item in selected_items:
            values = self.tree.item(item, 'values')
            reminder_id = values[0]
            self.db.update_reminder_status(reminder_id, 'Отменено')
            self.tree.item(item, values=(values[0], values[1], values[2], values[3], 'Отменено', values[5]))
        
        messagebox.showinfo("Успех", "Напоминание отмечено как Отменено")

def main():
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()