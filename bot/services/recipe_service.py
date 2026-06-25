# bot/services/recipe_service.py
"""
Сервис для работы с рецептами из базы данных.
Если БД недоступна — использует резервные рецепты.

Автор: MADAO81
Версия: 3.0
"""

import logging
import sqlite3
import random
from typing import Optional, Dict, List
from pathlib import Path
from bot.config import Config

logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = Config.DATA_DIR / "recipes.db"


class RecipeService:
    """
    Класс для получения рецептов из БД.
    """

    def __init__(self):
        """Инициализация сервиса рецептов."""
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        """Проверяет, что БД существует."""
        if not self.db_path.exists():
            logger.warning(f"⚠️ База данных рецептов не найдена: {self.db_path}")
            logger.warning("⚠️ Будет использован резервный список рецептов")

    def _get_connection(self):
        """Возвращает соединение с БД."""
        return sqlite3.connect(self.db_path)

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта.
        Сначала из БД, если нет — из резервного списка.
        """
        # Пробуем получить из БД
        recipe = await self._get_recipe_from_db()
        if recipe:
            return recipe

        # Если БД недоступна — резервные рецепты
        logger.info("📖 Использован резервный рецепт")
        return self._get_fallback_recipe()

    async def _get_recipe_from_db(self) -> Optional[Dict]:
        """
        Получение случайного рецепта из БД.
        """
        try:
            if not self.db_path.exists():
                return None

            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем случайный рецепт
            cursor.execute("""
                SELECT title, ingredients, instructions, category
                FROM recipes
                ORDER BY RANDOM()
                LIMIT 1
            """)

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "title": row[0],
                    "ingredients": row[1],
                    "instructions": row[2],
                    "category": row[3]
                }
            return None

        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта из БД: {e}")
            return None

    def _get_fallback_recipe(self) -> Dict:
        """Возвращает случайный рецепт из резервного списка."""
        recipes = [
            {
                "title": "🍰 Классический бисквит",
                "ingredients": "• Яйца — 4 шт\n• Сахар — 150 г\n• Мука — 150 г\n• Ванильный сахар — 1 ч.л.",
                "instructions": "1. Яйца взбить с сахаром до пышной светлой массы.\n2. Добавить муку и ванильный сахар, аккуратно перемешать.\n3. Выпекать при 180°C 30-35 минут."
            },
            {
                "title": "🧁 Шоколадные кексы",
                "ingredients": "• Мука — 200 г\n• Сахар — 150 г\n• Какао — 40 г\n• Яйца — 2 шт\n• Молоко — 200 мл\n• Масло — 80 мл",
                "instructions": "1. Смешать сухие ингредиенты.\n2. Добавить яйца, молоко и масло.\n3. Перемешать до однородности.\n4. Выпекать при 180°C 20-25 минут."
            },
            {
                "title": "🥞 Блины на молоке",
                "ingredients": "• Мука — 250 г\n• Молоко — 500 мл\n• Яйца — 2 шт\n• Сахар — 2 ст.л.\n• Соль — 0,5 ч.л.",
                "instructions": "1. Яйца взбить с сахаром и солью.\n2. Добавить молоко и муку, перемешать.\n3. Добавить масло, дать постоять 15 минут.\n4. Жарить на разогретой сковороде."
            },
            {
                "title": "🍪 Овсяное печенье",
                "ingredients": "• Масло — 100 г\n• Сахар — 100 г\n• Яйцо — 1 шт\n• Овсяные хлопья — 150 г\n• Мука — 100 г",
                "instructions": "1. Масло растереть с сахаром.\n2. Добавить яйцо, перемешать.\n3. Добавить хлопья и муку.\n4. Выпекать при 180°C 15-20 минут."
            },
            {
                "title": "🍰 Медовик классический",
                "ingredients": "• Мёд — 100 г\n• Сахар — 150 г\n• Яйца — 2 шт\n• Мука — 300 г\n• Сода — 1 ч.л.\n• Сметана — 400 г для крема",
                "instructions": "1. Мёд, сахар и яйца нагреть на водяной бане.\n2. Добавить муку и соду, замесить тесто.\n3. Разделить на коржи, выпекать при 180°C 5-7 минут.\n4. Прослоить кремом из сметаны с сахаром."
            }
        ]
        return random.choice(recipes)

    async def search_recipes(self, query: str) -> List[Dict]:
        """Поиск рецептов по запросу."""
        results = []
        try:
            if not self.db_path.exists():
                return results

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT title, ingredients, instructions, category
                FROM recipes
                WHERE title LIKE ? OR ingredients LIKE ?
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))

            for row in cursor.fetchall():
                results.append({
                    "title": row[0],
                    "ingredients": row[1],
                    "instructions": row[2],
                    "category": row[3]
                })
            conn.close()

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске: {e}")

        return results
