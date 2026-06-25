# scripts/create_recipe_db.py
"""
Скрипт для создания базы данных рецептов.
Запустить один раз для инициализации.

Автор: MADAO81
Версия: 1.0
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "recipes.db"


def init_db():
    """Создаёт таблицу для рецептов."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            category TEXT DEFAULT 'выпечка',
            source TEXT DEFAULT 'база'
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ База данных создана: {DB_PATH}")


if __name__ == "__main__":
    init_db()