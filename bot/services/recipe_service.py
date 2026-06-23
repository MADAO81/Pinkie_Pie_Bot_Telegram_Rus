# bot/services/recipe_service.py
"""
Сервис для парсинга рецептов с food.ru.
Только сладости и выпечка.

Автор: MADAO81
Версия: 3.1
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
        # Категории: торты, пирожные, печенье, кексы, пироги
        self.categories = [
            "/categories/deserts/torti",      # Торты
            "/categories/deserts/pirozhnye",  # Пирожные
            "/categories/deserts/pechene",    # Печенье
            "/categories/deserts/keksy",      # Кексы
            "/categories/deserts/pirogi",     # Пироги
            "/categories/deserts/deserti"     # Десерты
        ]

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта сладостей с food.ru.
        """
        try:
            # Выбираем случайную категорию
            category = random.choice(self.categories)
            url = f"{self.base_url}{category}"
            logger.info(f"🔍 Ищем рецепты в категории: {category}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10.0) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ food.ru не отвечает (статус: {response.status})")
                        return self._get_fallback_recipe()

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Ищем ссылки на рецепты
                    recipe_links = []
                    
                    # Ищем карточки рецептов
                    for card in soup.find_all('a', href=True):
                        href = card.get('href', '')
                        if href and '/recipes/' in href and href not in recipe_links:
                            # Проверяем, что это не категория
                            if '?page=' not in href and 'category' not in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if 'recipe' in href:
                                    recipe_links.append(href)
                    
                    # Если ссылок мало, пробуем страницу с рецептами
                    if len(recipe_links) < 5:
                        logger.info("🔍 Пробуем страницу рецептов")
                        recipe_links = await self._get_recipe_links_from_page()

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

    async def _get_recipe_links_from_page(self) -> List[str]:
        """
        Получение ссылок на рецепты со страницы.
        """
        try:
            url = f"{self.base_url}/recipes"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10.0) as response:
                    if response.status != 200:
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if href and '/recipes/' in href and href not in links:
                            if '?page=' not in href and 'category' not in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if 'recipe' in href:
                                    links.append(href)
                    return links
        except Exception as e:
            logger.error(f"❌ Ошибка при получении ссылок: {e}")
            return []

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
                    ingr_section = soup.find('div', class_=lambda x: x and ('ingredient' in x.lower() or 'ingr' in x.lower()) if x else None)
                    
                    if ingr_section:
                        for li in ingr_section.find_all('li'):
                            text = li.text.strip()
                            if text and len(text) > 2:
                                ingredients.append(text)
                    
                    # Если не нашли через класс, ищем через ul
                    if not ingredients:
                        for ul in soup.find_all('ul'):
                            items = ul.find_all('li')
                            if items and len(items) > 2:
                                # Проверяем, что это ингредиенты (есть цифры или граммы)
                                for li in items[:10]:
                                    text = li.text.strip()
                                    if text and len(text) > 3:
                                        ingredients.append(text)
                                if len(ingredients) > 2:
                                    break

                    # Инструкции
                    instructions = []
                    inst_section = soup.find('div', class_=lambda x: x and ('instruction' in x.lower() or 'step' in x.lower()) if x else None)
                    
                    if inst_section:
                        for p in inst_section.find_all('p'):
                            text = p.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)
                    
                    # Если не нашли через класс, ищем через ol
                    if not instructions:
                        for ol in soup.find_all('ol'):
                            for li in ol.find_all('li'):
                                text = li.text.strip()
                                if text and len(text) > 5:
                                    instructions.append(text)
                            if len(instructions) > 2:
                                break

                    # Если нет инструкций — ищем любой текст
                    if not instructions:
                        content = soup.find('div', class_='content') or soup.find('article') or soup
                        for p in content.find_all('p') if content else []:
                            text = p.text.strip()
                            if text and len(text) > 20 and not text.startswith('Подписаться'):
                                instructions.append(text)
                            if len(instructions) > 3:
                                break

                    # Проверяем, что это рецепт сладостей
                    if title and ('торт' in title.lower() or 
                                 'пирож' in title.lower() or 
                                 'печень' in title.lower() or 
                                 'кекс' in title.lower() or 
                                 'десерт' in title.lower() or
                                 'маффин' in title.lower() or
                                 'капкейк' in title.lower() or
                                 'сладк' in title.lower() or
                                 'шоколад' in title.lower() or
                                 'конфет' in title.lower()):
                        pass  # Это сладость
                    elif title:
                        # Если название не содержит явных признаков сладости
                        # Проверяем ингредиенты
                        sweet_words = ['сахар', 'мука', 'шоколад', 'крем', 'сгущенк', 'варенье', 'джем', 'мед']
                        if ingredients:
                            ingr_text = ' '.join(ingredients).lower()
                            for word in sweet_words:
                                if word in ingr_text:
                                    break
                            else:
                                # Если нет сладких ингредиентов — пропускаем
                                logger.warning(f"⚠️ Рецепт пропущен (не сладость): {title}")
                                return self._get_fallback_recipe()

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
            }
        ]
        recipe = random.choice(recipes)
        logger.info(f"📖 Использован резервный рецепт: {recipe['title']}")
        return recipe
