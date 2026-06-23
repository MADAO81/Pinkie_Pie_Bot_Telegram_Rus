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
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, timeout=15.0) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка при запросе к andychef.ru: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Ищем ссылки на рецепты
                    recipe_links = []
                    
                    # Вариант 1: Ссылки в тегах article
                    for article in soup.find_all('article'):
                        link = article.find('a', href=True)
                        if link and '/recipes/' in link['href']:
                            href = link['href']
                            if href.startswith('/'):
                                href = f"{self.base_url}{href}"
                            if href not in recipe_links:
                                recipe_links.append(href)
                    
                    # Вариант 2: Все ссылки с /recipes/
                    if not recipe_links:
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if '/recipes/' in href and 'http' not in href:
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                if href not in recipe_links:
                                    recipe_links.append(href)

                    if not recipe_links:
                        logger.warning("⚠️ Рецепты не найдены на главной странице")
                        return await self._get_recipe_from_url(f"{self.base_url}/recipes/")

                    random_link = random.choice(recipe_links)
                    logger.info(f"📖 Выбран рецепт: {random_link}")

                    return await self._parse_recipe(random_link)

        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return None

    async def _get_recipe_from_url(self, url: str) -> Optional[Dict]:
        """Получение рецепта с конкретного URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15.0) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    recipe_links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/recipes/' in href and 'http' not in href:
                            if href.startswith('/'):
                                href = f"{self.base_url}{href}"
                            if href not in recipe_links:
                                recipe_links.append(href)
                    
                    if not recipe_links:
                        return None
                    
                    random_link = random.choice(recipe_links)
                    return await self._parse_recipe(random_link)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при получении рецепта: {e}")
            return None

    async def _parse_recipe(self, url: str) -> Optional[Dict]:
        """Парсинг деталей рецепта."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15.0) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка при запросе к рецепту: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    # Название рецепта
                    title = None
                    for tag in ['h1', 'h2', 'h3']:
                        title_tag = soup.find(tag)
                        if title_tag and title_tag.text.strip():
                            title = title_tag.text.strip()
                            break
                    
                    if not title:
                        title = "Рецепт"

                    # Ингредиенты
                    ingredients = []
                    
                    # Ищем список ингредиентов
                    for ul in soup.find_all('ul'):
                        # Проверяем, что список содержит ингредиенты
                        items = ul.find_all('li')
                        if items and len(items) > 1:
                            # Проверяем, что это похоже на ингредиенты
                            for li in items:
                                text = li.text.strip()
                                if text and len(text) > 2 and not text.startswith('http'):
                                    ingredients.append(text)
                            if len(ingredients) > 2:
                                break
                    
                    # Если не нашли - ищем по классам
                    if not ingredients:
                        for item in soup.find_all('li', class_=lambda x: x and ('ingredient' in x.lower() or 'ingr' in x.lower())):
                            text = item.text.strip()
                            if text and len(text) > 2:
                                ingredients.append(text)

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
                    
                    # Если не нашли - ищем по классам
                    if not instructions:
                        for item in soup.find_all('li', class_=lambda x: x and ('instruction' in x.lower() or 'step' in x.lower())):
                            text = item.text.strip()
                            if text and len(text) > 5:
                                instructions.append(text)

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
