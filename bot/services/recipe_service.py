# bot/services/recipe_service.py
"""
Сервис для парсинга рецептов с andychef.ru.

Автор: MADAO81
Версия: 2.0
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
    Класс для получения рецептов с сайта andychef.ru.
    """

    def __init__(self):
        """Инициализация сервиса рецептов."""
        self.base_url = Config.RECIPE_URL

    async def get_random_recipe(self) -> Optional[Dict]:
        """
        Получение случайного рецепта с andychef.ru.

        Returns:
            Optional[Dict]: Данные о рецепте или None в случае ошибки
        """
        try:
            # Получаем список рецептов с главной страницы
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=15.0) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка при запросе к andychef.ru: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Ищем ссылки на рецепты
                    recipe_links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/recipes/' in href and 'http' not in href:
                            full_url = f"{self.base_url}{href}"
                            if full_url not in recipe_links:
                                recipe_links.append(full_url)

                    if not recipe_links:
                        logger.warning("⚠️ Рецепты не найдены на главной странице")
                        return None

                    # Выбираем случайный рецепт
                    random_link = random.choice(recipe_links)
                    logger.info(f"📖 Выбран рецепт: {random_link}")

                    # Парсим детали рецепта
                    return await self._parse_recipe(random_link)

        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с andychef.ru: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return None

    async def _parse_recipe(self, url: str) -> Optional[Dict]:
        """
        Парсинг деталей рецепта.

        Args:
            url (str): URL рецепта

        Returns:
            Optional[Dict]: Данные о рецепте или None в случае ошибки
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15.0) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка при запросе к рецепту: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Название рецепта
                    title_tag = soup.find('h1')
                    title = title_tag.text.strip() if title_tag else "Рецепт"

                    # Ингредиенты
                    ingredients = []
                    ingredient_items = soup.find_all('li', class_='ingredient')
                    for item in ingredient_items[:10]:  # Ограничиваем 10 ингредиентами
                        text = item.text.strip()
                        if text:
                            ingredients.append(text)

                    ingredients_text = "\n".join(
                        [f"• {i}" for i in ingredients]
                    ) if ingredients else "Ингредиенты не найдены"

                    # Инструкции
                    instructions = []
                    steps = soup.find_all('div', class_='instruction')
                    for i, step in enumerate(steps[:8], 1):  # Ограничиваем 8 шагами
                        text = step.text.strip()
                        if text:
                            instructions.append(f"{i}. {text}")

                    instructions_text = "\n".join(
                        instructions
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

    async def search_recipes(self, query: str) -> List[Dict]:
        """
        Поиск рецептов по запросу.

        Args:
            query (str): Поисковый запрос

        Returns:
            List[Dict]: Список найденных рецептов
        """
        # TODO: Реализовать поиск рецептов
        # Пока возвращаем пустой список
        return []
