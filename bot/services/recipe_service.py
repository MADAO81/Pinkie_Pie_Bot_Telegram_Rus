# bot/services/recipe_service.py
"""
Сервис для парсинга рецептов с edimdoma.ru.
Только выпечка и сладости.

Автор: MADAO81
Версия: 3.3
"""

import logging
import random
from typing import Optional, Dict, List
import aiohttp
from bs4 import BeautifulSoup
from bot.config import Config

# Настройка логирования
logger = logging.getLogger(__name__)


class RecipeService:
    """
    Класс для получения рецептов с сайта edimdoma.ru.
    """

    def __init__(self):
        """Инициализация сервиса рецептов."""
        self.base_url = "https://www.edimdoma.ru"
        self.recipes_url = f"{self.base_url}/recipes"
        
        # Резервные рецепты (на случай недоступности сайта)
        self.fallback_recipes = self._get_fallback_recipes()

    def _get_fallback_recipes(self) -> List[Dict]:
        """Возвращает список резервных рецептов."""
        return [
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
                "title": "🧇 Вафли хрустящие",
                "ingredients": "• Мука — 250 г\n• Молоко — 300 мл\n• Яйца — 2 шт\n• Масло растительное — 100 мл\n• Сахар — 80 г",
                "instructions": "1. Смешать сухие ингредиенты.\n2. Добавить молоко, яйца и масло.\n3. Перемешать до однородности.\n4. Выпекать в вафельнице до золотистого цвета."
            },
            {
                "title": "🧁 Маффины с черникой",
                "ingredients": "• Мука — 250 г\n• Сахар — 150 г\n• Яйцо — 2 шт\n• Молоко — 200 мл\n• Масло — 80 мл\n• Черника — 150 г",
                "instructions": "1. Смешать сухие ингредиенты.\n2. Добавить яйца, молоко и масло.\n3. Аккуратно добавить чернику.\n4. Выпекать при 180°C 20-25 минут."
            },
            {
                "title": "🍰 Медовик классический",
                "ingredients": "• Мёд — 100 г\n• Сахар — 150 г\n• Яйца — 2 шт\n• Мука — 300 г\n• Сода — 1 ч.л.\n• Сметана — 400 г для крема",
                "instructions": "1. Мёд, сахар и яйца нагреть на водяной бане.\n2. Добавить муку и соду, замесить тесто.\n3. Разделить на коржи, выпекать при 180°C 5-7 минут.\n4. Прослоить кремом из сметаны с сахаром."
            },
            {
                "title": "🍩 Пончики дрожжевые",
                "ingredients": "• Мука — 500 г\n• Молоко — 250 мл\n• Дрожжи — 10 г\n• Яйцо — 1 шт\n• Сахар — 80 г\n• Масло сливочное — 50 г",
                "instructions": "1. Дрожжи растворить в тёплом молоке.\n2. Добавить яйцо, сахар, масло и муку.\n3. Замесить тесто, дать подойти.\n4. Сформировать пончики, обжарить во фритюре."
            },
            {
                "title": "🥧 Шарлотка с яблоками",
                "ingredients": "• Яйца — 3 шт\n• Сахар — 150 г\n• Мука — 150 г\n• Яблоки — 3-4 шт\n• Корица — по вкусу",
                "instructions": "1. Яйца взбить с сахаром до пены.\n2. Добавить муку, перемешать.\n3. Яблоки нарезать, выложить в форму.\n4. Залить тестом, выпекать при 180°C 30 минут."
            },
            {
                "title": "🍫 Брауни шоколадный",
                "ingredients": "• Шоколад тёмный — 200 г\n• Масло сливочное — 150 г\n• Сахар — 200 г\n• Яйца — 3 шт\n• Мука — 100 г\n• Какао — 30 г",
                "instructions": "1. Шоколад с маслом растопить на водяной бане.\n2. Добавить сахар и яйца, перемешать.\n3. Добавить муку и какао.\n4. Выпекать при 180°C 25-30 минут."
            },
            {
                "title": "🥐 Круассаны из слоёного теста",
                "ingredients": "• Тесто слоёное — 500 г\n• Масло сливочное — 50 г\n• Сахарная пудра — для посыпки",
                "instructions": "1. Тесто разморозить и раскатать.\n2. Нарезать треугольниками.\n3. Свернуть в круассаны.\n4. Выпекать при 200°C 15-20 минут."
            },
            {
                "title": "🧁 Капкейки с кремом",
                "ingredients": "• Мука — 180 г\n• Сахар — 150 г\n• Яйца — 2 шт\n• Молоко — 120 мл\n• Масло — 100 г\n• Сливки — 200 мл для крема",
                "instructions": "1. Взбить масло с сахаром.\n2. Добавить яйца, молоко и муку.\n3. Выпекать при 180°C 20 минут.\n4. Украсить кремом из сливок."
            }
        ]

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта с edimdoma.ru.
        """
        try:
            logger.info("🔍 Ищем рецепты на edimdoma.ru...")
            
            # Пробуем несколько страниц с рецептами выпечки
            urls_to_try = [
                f"{self.base_url}/recepty/deserty",      # Десерты
                f"{self.base_url}/recepty/pirogi",       # Пироги
                f"{self.base_url}/recepty/pechenie",     # Печенье
                f"{self.base_url}/recepty/torty",        # Торты
                f"{self.base_url}/recepty/keksy",        # Кексы
                f"{self.base_url}/recepty/pirozhnye",    # Пирожные
            ]
            
            # Перемешиваем URL для случайности
            random.shuffle(urls_to_try)
            
            for url in urls_to_try[:3]:  # Пробуем первые 3
                logger.info(f"🔍 Пробуем: {url}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10.0) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'lxml')
                            
                            # Ищем ссылки на рецепты
                            recipe_links = []
                            for a in soup.find_all('a', href=True):
                                href = a.get('href', '')
                                if href and '/recepty/' in href and href not in recipe_links:
                                    # Исключаем категории
                                    if '/recepty/' in href and '?' not in href and len(href.split('/')) > 3:
                                        if not href.startswith('http'):
                                            href = f"{self.base_url}{href}"
                                        if href != url:
                                            recipe_links.append(href)
                            
                            if recipe_links:
                                random_link = random.choice(recipe_links)
                                logger.info(f"📖 Выбран рецепт: {random_link}")
                                recipe = await self._parse_recipe(random_link)
                                if recipe and recipe.get('title'):
                                    return recipe
            
            # Если ничего не нашли
            logger.warning("⚠️ Не удалось получить рецепты с edimdoma.ru")
            return self._get_fallback_recipe()

        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return self._get_fallback_recipe()

    async def _parse_recipe(self, url: str) -> Optional[Dict]:
        """
        Парсинг деталей рецепта с edimdoma.ru.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10.0) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Название рецепта
                    title = None
                    for tag in ['h1']:
                        title_tag = soup.find(tag)
                        if title_tag:
                            text = title_tag.text.strip()
                            if text and len(text) > 3:
                                title = text
                                break

                    # Ингредиенты
                    ingredients = []
                    
                    # Ищем список ингредиентов
                    for ul in soup.find_all('ul'):
                        items = ul.find_all('li')
                        if items and len(items) > 1:
                            for li in items:
                                text = li.text.strip()
                                if text and len(text) > 2:
                                    ingredients.append(text)
                            if len(ingredients) > 2:
                                break

                    # Инструкции
                    instructions = []
                    
                    # Ищем нумерованный список или параграфы с инструкциями
                    for ol in soup.find_all('ol'):
                        for li in ol.find_all('li'):
                            text = li.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)
                        if len(instructions) > 2:
                            break

                    # Если нет ol - ищем параграфы с цифрами
                    if not instructions:
                        for p in soup.find_all('p'):
                            text = p.text.strip()
                            if text and len(text) > 10 and any(c.isdigit() for c in text[:10]):
                                instructions.append(text)
                            if len(instructions) > 3:
                                break

                    ingredients_text = "\n".join(
                        [f"• {i}" for i in ingredients[:10]]
                    ) if ingredients else "Ингредиенты не найдены"

                    instructions_text = "\n".join(
                        [f"{i+1}. {instructions[i]}" for i in range(min(len(instructions), 8))]
                    ) if instructions else "Инструкции не найдены"

                    return {
                        "title": title or "Рецепт с edimdoma.ru",
                        "ingredients": ingredients_text,
                        "instructions": instructions_text,
                        "url": url
                    }

        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге рецепта: {e}")
            return None

    def _get_fallback_recipe(self) -> Dict:
        """Возвращает случайный резервный рецепт."""
        recipe = random.choice(self.fallback_recipes)
        logger.info(f"📖 Использован резервный рецепт: {recipe['title']}")
        return recipe
