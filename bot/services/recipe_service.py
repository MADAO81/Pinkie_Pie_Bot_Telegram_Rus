# bot/services/recipe_service.py
"""
Сервис для парсинга рецептов с food.ru.

Автор: MADAO81
Версия: 3.0
"""

import logging
import random
import re
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
        self.recipes_url = f"{self.base_url}/recipes"
        
        # Резервные рецепты на случай недоступности сайта
        self.fallback_recipes = [
            {
                "title": "🍰 Классический бисквит",
                "ingredients": "• Яйца — 4 шт\n• Сахар — 150 г\n• Мука — 150 г\n• Ванильный сахар — 1 ч.л.\n• Соль — щепотка",
                "instructions": "1. Яйца взбить с сахаром до пышной светлой массы.\n2. Добавить муку и ванильный сахар, аккуратно перемешать лопаткой.\n3. Выпекать в форме при 180°C 30-35 минут."
            },
            {
                "title": "🧁 Кексы с шоколадом",
                "ingredients": "• Мука — 200 г\n• Сахар — 150 г\n• Какао-порошок — 40 г\n• Яйца — 2 шт\n• Молоко — 200 мл\n• Масло растительное — 80 мл\n• Разрыхлитель — 1 ч.л.",
                "instructions": "1. Смешать сухие ингредиенты.\n2. Добавить яйца, молоко и масло.\n3. Перемешать до однородности.\n4. Выпекать при 180°C 20-25 минут."
            },
            {
                "title": "🥞 Блины на молоке",
                "ingredients": "• Мука — 250 г\n• Молоко — 500 мл\n• Яйца — 2 шт\n• Сахар — 2 ст.л.\n• Соль — 0,5 ч.л.\n• Масло растительное — 2 ст.л.",
                "instructions": "1. Яйца взбить с сахаром и солью.\n2. Добавить молоко и муку, перемешать до однородности.\n3. Добавить масло, дать постоять 15 минут.\n4. Жарить на разогретой сковороде."
            },
            {
                "title": "🍪 Овсяное печенье",
                "ingredients": "• Масло сливочное — 100 г\n• Сахар — 100 г\n• Яйцо — 1 шт\n• Овсяные хлопья — 150 г\n• Мука — 100 г\n• Разрыхлитель — 0,5 ч.л.",
                "instructions": "1. Сливочное масло растереть с сахаром.\n2. Добавить яйцо, перемешать.\n3. Добавить хлопья, муку и разрыхлитель.\n4. Выпекать при 180°C 15-20 минут."
            },
            {
                "title": "🍌 Банановый хлеб",
                "ingredients": "• Бананы спелые — 3 шт\n• Яйца — 2 шт\n• Сахар — 100 г\n• Мука — 200 г\n• Масло сливочное — 80 г\n• Сода — 1 ч.л.\n• Соль — щепотка",
                "instructions": "1. Бананы размять вилкой.\n2. Добавить яйца, сахар и растопленное масло.\n3. Добавить муку, соду и соль.\n4. Выпекать в форме при 180°C 45-50 минут."
            }
        ]

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта с food.ru.
        Если сайт недоступен — используется резервный список.
        """
        try:
            logger.info("🔍 Пробуем получить рецепты с food.ru...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.recipes_url, timeout=10.0) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ food.ru не отвечает (статус: {response.status})")
                        return self._get_fallback_recipe()

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Ищем ссылки на рецепты
                    recipe_links = []
                    
                    # Вариант 1: Ссылки в article
                    for article in soup.find_all('article'):
                        link = article.find('a', href=True)
                        if link and '/recipes/' in link['href']:
                            href = link['href']
                            if href.startswith('/'):
                                href = f"{self.base_url}{href}"
                            if href not in recipe_links and 'recipe' in href:
                                recipe_links.append(href)
                    
                    # Вариант 2: Ссылки с классом recipe-card
                    if not recipe_links:
                        for card in soup.find_all('div', class_=lambda x: x and 'recipe-card' in x.lower() if x else False):
                            link = card.find('a', href=True)
                            if link and '/recipes/' in link['href']:
                                href = link['href']
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if href not in recipe_links and 'recipe' in href:
                                    recipe_links.append(href)
                    
                    # Вариант 3: Любые ссылки с /recipes/
                    if not recipe_links:
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href and '/recipes/' in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if href not in recipe_links and 'recipe' in href:
                                    recipe_links.append(href)

                    if not recipe_links:
                        logger.warning("⚠️ Рецепты не найдены на food.ru")
                        return self._get_fallback_recipe()

                    # Выбираем случайный рецепт
                    random_link = random.choice(recipe_links)
                    logger.info(f"📖 Выбран рецепт: {random_link}")

                    recipe = await self._parse_recipe(random_link)
                    if recipe:
                        return recipe
                    else:
                        return self._get_fallback_recipe()

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с food.ru: {e}")
            return self._get_fallback_recipe()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return self._get_fallback_recipe()

    async def _parse_recipe(self, url: str) -> Optional[Dict]:
        """
        Парсинг деталей рецепта с food.ru.

        Args:
            url (str): URL рецепта

        Returns:
            Optional[Dict]: Данные о рецепте или None в случае ошибки
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10.0) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка при запросе к рецепту: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Название рецепта
                    title = None
                    for tag in ['h1']:
                        title_tag = soup.find(tag)
                        if title_tag and title_tag.text.strip():
                            title = title_tag.text.strip()
                            break
                    
                    # Если не нашли h1, пробуем другие теги
                    if not title:
                        for tag in ['h2', 'h3']:
                            title_tag = soup.find(tag)
                            if title_tag and title_tag.text.strip():
                                title = title_tag.text.strip()
                                break
                    
                    if not title:
                        title = "Рецепт с food.ru"

                    # Ингредиенты
                    ingredients = []
                    
                    # Ищем ингредиенты в списках
                    for ul in soup.find_all('ul'):
                        items = ul.find_all('li')
                        if items and len(items) > 1:
                            for li in items:
                                text = li.text.strip()
                                if text and len(text) > 2 and not text.startswith('http'):
                                    ingredients.append(text)
                            if len(ingredients) > 2:
                                break
                    
                    # Если не нашли, ищем по классам
                    if not ingredients:
                        for item in soup.find_all('li', class_=lambda x: x and ('ingredient' in x.lower() or 'ingr' in x.lower() if x else False)):
                            text = item.text.strip()
                            if text and len(text) > 2:
                                ingredients.append(text)
                    
                    # Если всё ещё нет, ищем в div с ингредиентами
                    if not ingredients:
                        for div in soup.find_all('div', class_=lambda x: x and ('ingredients' in x.lower() or 'ingr' in x.lower() if x else False)):
                            for li in div.find_all('li'):
                                text = li.text.strip()
                                if text and len(text) > 2:
                                    ingredients.append(text)
                            if ingredients:
                                break

                    ingredients_text = "\n".join(
                        [f"• {i}" for i in ingredients[:10]]
                    ) if ingredients else "Ингредиенты не найдены"

                    # Инструкции
                    instructions = []
                    
                    # Ищем нумерованный список
                    for ol in soup.find_all('ol'):
                        for li in ol.find_all('li'):
                            text = li.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)
                        if len(instructions) > 2:
                            break
                    
                    # Если не нашли, ищем по классам
                    if not instructions:
                        for item in soup.find_all('li', class_=lambda x: x and ('instruction' in x.lower() or 'step' in x.lower() if x else False)):
                            text = item.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)
                    
                    # Если нет ol, ищем в div с инструкциями
                    if not instructions:
                        for div in soup.find_all('div', class_=lambda x: x and ('instructions' in x.lower() or 'steps' in x.lower() if x else False)):
                            for p in div.find_all('p'):
                                text = p.text.strip()
                                if text and len(text) > 10:
                                    instructions.append(text)
                            if instructions:
                                break

                    instructions_text = "\n".join(
                        instructions[:8]
                    ) if instructions else "Инструкции не найдены"

                    return {
                        "title": title,
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
