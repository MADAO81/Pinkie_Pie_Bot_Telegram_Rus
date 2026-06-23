# bot/services/recipe_service.py
"""
Сервис для парсинга рецептов с food.ru.
Только сладости и выпечка.

Автор: MADAO81
Версия: 3.2
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
    Класс для получения рецептов с сайта food.ru.
    """

    def __init__(self):
        """Инициализация сервиса рецептов."""
        self.base_url = "https://food.ru"
        # Используем главную страницу рецептов с параметрами
        self.recipes_url = f"{self.base_url}/recipes"
        
        # Резервные рецепты (расширенный список)
        self.fallback_recipes = [
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
            }
        ]

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта с food.ru.
        """
        try:
            # Пробуем получить рецепты с главной страницы
            logger.info("🔍 Ищем рецепты на food.ru...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.recipes_url, timeout=10.0) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ food.ru не отвечает (статус: {response.status})")
                        return self._get_fallback_recipe()

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Ищем ссылки на рецепты
                    recipe_links = []
                    
                    # Ищем все ссылки на рецепты
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if href and '/recipes/' in href and href not in recipe_links:
                            # Исключаем категории и пагинацию
                            if '?' not in href or 'recipe' in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                # Проверяем, что это рецепт (не категория)
                                if '/recipes/' in href and 'recipe' in href:
                                    # Исключаем корневые страницы
                                    if href != self.recipes_url and href != f"{self.recipes_url}/":
                                        recipe_links.append(href)

                    # Если ссылок нет, пробуем другую страницу
                    if not recipe_links:
                        logger.info("🔍 Пробуем страницу рецептов с параметрами")
                        return await self._get_recipe_from_url(f"{self.base_url}/recipes?page=1")

                    if not recipe_links:
                        logger.warning("⚠️ Рецепты не найдены на food.ru")
                        return self._get_fallback_recipe()

                    # Выбираем случайный рецепт
                    random_link = random.choice(recipe_links)
                    logger.info(f"📖 Выбран рецепт: {random_link}")

                    recipe = await self._parse_recipe(random_link)
                    if recipe and recipe.get('title'):
                        return recipe
                    else:
                        return self._get_fallback_recipe()

        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return self._get_fallback_recipe()

    async def _get_recipe_from_url(self, url: str) -> Optional[Dict]:
        """
        Получение рецепта с конкретного URL.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10.0) as response:
                    if response.status != 200:
                        return self._get_fallback_recipe()

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    recipe_links = []
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if href and '/recipes/' in href and href not in recipe_links:
                            if '?' not in href or 'recipe' in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if '/recipes/' in href and 'recipe' in href:
                                    if href != url and href != f"{self.recipes_url}/":
                                        recipe_links.append(href)

                    if not recipe_links:
                        return self._get_fallback_recipe()

                    random_link = random.choice(recipe_links)
                    recipe = await self._parse_recipe(random_link)
                    return recipe if recipe else self._get_fallback_recipe()

        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return self._get_fallback_recipe()

    async def _parse_recipe(self, url: str) -> Optional[Dict]:
        """
        Парсинг деталей рецепта с food.ru.
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
                    
                    # Ищем через ul/li
                    for ul in soup.find_all('ul'):
                        items = ul.find_all('li')
                        if items and len(items) > 1:
                            for li in items:
                                text = li.text.strip()
                                if text and len(text) > 2 and not text.startswith('http'):
                                    ingredients.append(text)
                            if len(ingredients) > 2:
                                break

                    # Инструкции
                    instructions = []
                    
                    # Ищем через ol/li
                    for ol in soup.find_all('ol'):
                        for li in ol.find_all('li'):
                            text = li.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)
                        if len(instructions) > 2:
                            break

                    # Если нет ингредиентов или инструкций - пробуем найти в div
                    if not ingredients or not instructions:
                        content = soup.find('main') or soup.find('article') or soup
                        if content:
                            # Ищем в параграфах
                            for p in content.find_all('p'):
                                text = p.text.strip()
                                if text and len(text) > 10:
                                    if not ingredients and ('г' in text or 'мл' in text):
                                        ingredients.append(text)
                                    elif not instructions and len(text) > 20:
                                        instructions.append(text)

                    ingredients_text = "\n".join(
                        [f"• {i}" for i in ingredients[:10]]
                    ) if ingredients else "Ингредиенты не найдены"

                    instructions_text = "\n".join(
                        [f"{i+1}. {instructions[i]}" for i in range(min(len(instructions), 8))]
                    ) if instructions else "Инструкции не найдены"

                    return {
                        "title": title or "Рецепт с food.ru",
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
