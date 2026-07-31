# bot/services/recipe_service.py
"""
Сервис рецептов для Пинки Пай.
Работает с SQLite базой данных рецептов.

Автор: MADAO81
Версия: 1.0
"""

import sqlite3
import random
from typing import Optional, Dict
from bot.config import Config


class RecipeService:
    def __init__(self):
        self.db_path = Config.RECIPES_DB

    def get_random_recipe(self) -> Optional[Dict]:
        """Возвращает случайный рецепт."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT title, ingredients, instructions, category FROM recipes ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "name": row['title'],
                "ingredients": row['ingredients'],
                "instructions": row['instructions'],
                "category": row['category']
            }
        return None

    def format_recipe(self, recipe: Dict) -> str:
        """Форматирует рецепт для вывода."""
        return (
            f"🧁 *{recipe['name']}*\n\n"
            f"📝 *Ингредиенты:*\n{recipe['ingredients']}\n\n"
            f"👩‍🍳 *Приготовление:*\n{recipe['instructions']}\n\n"
            f"💡 *Совет от Пинки Пай:* Добавь щепотку волшебства и хорошего настроения! 🎈"
        )
