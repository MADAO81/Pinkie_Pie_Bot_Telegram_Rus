# bot/core/context_manager.py
"""
Менеджер контекста диалогов.
Хранение истории общения в SQLite (30 дней).

Автор: MADAO81
Версия: 2.0
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bot.config import Config


class ContextManager:
    """
    Класс для управления историей диалогов.
    Хранит сообщения пользователей и ответы бота в SQLite.
    """

    def __init__(self):
        """Инициализация менеджера контекста."""
        self.db_path = Config.CONVERSATIONS_DB
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Создаём таблицу, если её нет
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Создаём индекс для быстрого поиска по user_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON conversations (user_id)
            """)

            # Создаём индекс для быстрого удаления старых записей
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON conversations (timestamp)
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")

    def get_context(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Получение последних сообщений пользователя.

        Args:
            user_id (int): ID пользователя
            limit (int): Количество последних сообщений

        Returns:
            List[Dict]: Список сообщений в формате:
                [{"role": "user", "content": "..."}, ...]
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Удаляем старые записи (старше 30 дней)
            expire_date = datetime.now() - timedelta(days=Config.CONTEXT_EXPIRE_DAYS)
            cursor.execute(
                "DELETE FROM conversations WHERE timestamp < ?",
                (expire_date,)
            )
            conn.commit()

            # Получаем последние сообщения
            cursor.execute("""
                SELECT role, content FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))

            rows = cursor.fetchall()
            conn.close()

            # Возвращаем в правильном порядке (от старых к новым)
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

        except Exception as e:
            print(f"Ошибка при получении контекста: {e}")
            return []

    def save_context(self, user_id: int, user_message: str, bot_response: str):
        """
        Сохранение сообщений в контекст.

        Args:
            user_id (int): ID пользователя
            user_message (str): Сообщение пользователя
            bot_response (str): Ответ бота
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Сохраняем сообщение пользователя
            cursor.execute("""
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, "user", user_message))

            # Сохраняем ответ бота
            cursor.execute("""
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, "assistant", bot_response))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Ошибка при сохранении контекста: {e}")

    def clear_context(self, user_id: int):
        """
        Очистка истории диалога пользователя.

        Args:
            user_id (int): ID пользователя
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,)
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Ошибка при очистке контекста: {e}")

    def get_stats(self, user_id: int) -> Dict:
        """
        Получение статистики по диалогам пользователя.

        Args:
            user_id (int): ID пользователя

        Returns:
            Dict: Статистика
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Общее количество сообщений
            cursor.execute(
                "SELECT COUNT(*) FROM conversations WHERE user_id = ?",
                (user_id,)
            )
            total = cursor.fetchone()[0]

            # Количество сообщений пользователя
            cursor.execute(
                "SELECT COUNT(*) FROM conversations WHERE user_id = ? AND role = 'user'",
                (user_id,)
            )
            user_msgs = cursor.fetchone()[0]

            # Количество ответов бота
            cursor.execute(
                "SELECT COUNT(*) FROM conversations WHERE user_id = ? AND role = 'assistant'",
                (user_id,)
            )
            bot_msgs = cursor.fetchone()[0]

            # Дата последнего сообщения
            cursor.execute("""
                SELECT timestamp FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (user_id,))
            last_msg = cursor.fetchone()

            conn.close()

            return {
                "total": total,
                "user_messages": user_msgs,
                "bot_messages": bot_msgs,
                "last_message": last_msg[0] if last_msg else None
            }

        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}
