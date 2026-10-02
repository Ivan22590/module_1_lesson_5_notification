import threading
from datetime import datetime
import winsound
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes

class ReminderNotification:
    @staticmethod
    def show_desktop_notification(title: str, message: str):
        """Отображение системного уведомления Windows поверх всех окон"""
        # Пытаемся сначала показать через tkinter (гарантированно поверх всех окон)
        try:
            # Создаем минимальное окно для отображения уведомления
            root = tk.Tk()
            root.withdraw()  # Скрываем главное окно
            
            # Устанавливаем флаг для показа поверх всех окон
            root.wm_attributes("-topmost", True)
            
            # Создаем всплывающее окно с уведомлением
            messagebox.showinfo(title, message)
            
            root.destroy()
            print(f"Уведомление показано через tkinter: {title}")
            return
        except Exception as e:
            print(f"Ошибка через tkinter: {e}")
        
        # Если tkinter не работает, используем Windows MessageBox
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x00001000 | 0x00000040)
            print(f"Уведомление показано через MessageBox: {title}")
            return
        except Exception as e:
            print(f"Ошибка через MessageBox: {e}")
        
        # Последний вариант - звуковой сигнал
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            print(f"Звуковое уведомление: {title}")
        except:
            pass

    @staticmethod
    def play_sound():
        """Воспроизведение звука уведомления"""
        try:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except:
            # Если стандартный звук не доступен, используем другой способ
            try:
                winsound.Beep(800, 500)
            except:
                pass

def check_and_show_notifications(database, interval=10):
    """
    Фоновая функция для проверки и отображения уведомлений
    """
    def checker():
        while True:
            try:
                # Проверяем просроченные напоминания
                overdue_reminders = database.get_overdue_reminders()
                
                for reminder in overdue_reminders:
                    reminder_id, title, description, reminder_datetime, status, created_at = reminder
                    
                    # Обновляем статус просроченных напоминаний
                    database.update_reminder_status(reminder_id, 'Просрочено')
                    
                    # Отображаем уведомление
                    full_message = f"{title}\n{description}" if description else title
                    print(f"Показываем уведомление о просроченном напоминании: {title}")
                    ReminderNotification.show_desktop_notification(
                        "Напоминание просрочено!",
                        full_message
                    )
                    ReminderNotification.play_sound()
                
                # Проверяем текущие напоминания
                current_reminders = database.get_reminders_by_status('Ожидает')
                current_time = datetime.now()
                
                for reminder in current_reminders:
                    reminder_id, title, description, reminder_datetime, status, created_at = reminder
                    
                    # Проверяем формат даты и преобразуем в нужный формат
                    try:
                        reminder_dt = datetime.strptime(reminder_datetime, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            reminder_dt = datetime.strptime(reminder_datetime, '%Y-%m-%d %H:%M')
                        except ValueError:
                            continue  # Пропускаем неправильный формат
                    
                    # Проверяем, настал ли момент уведомления (в пределах 1 минуты)
                    # Для более точной проверки сравниваем только дату и время без секунд
                    time_diff = current_time - reminder_dt
                    seconds_diff = abs(time_diff.total_seconds())
                    
                    # Если напоминание должно сработать сейчас (в течение минуты)
                    if 0 <= seconds_diff <= 60:
                        # Обновляем статус напоминания
                        database.update_reminder_status(reminder_id, 'Готово')
                        
                        full_message = f"{title}\n{description}" if description else title
                        print(f"Показываем уведомление: {title}")
                        ReminderNotification.show_desktop_notification(
                            "Напоминание!",
                            full_message
                        )
                        ReminderNotification.play_sound()
                
            except Exception as e:
                print(f"Ошибка проверки уведомлений: {e}")
                import traceback
                traceback.print_exc()
            
            # Ждем перед следующей проверкой (проверяем каждые 10 секунд для большей точности)
            import time
            time.sleep(interval)
    
    # Запускаем фоновый поток
    thread = threading.Thread(target=checker, daemon=True)
    thread.start()
    return thread