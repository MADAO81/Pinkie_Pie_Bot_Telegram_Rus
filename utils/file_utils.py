# bot/utils/file_utils.py
"""
Утилиты для работы с файлами.
Сохранение, загрузка, удаление временных файлов.

Автор: MADAO81
Версия: 2.0
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from bot.config import Config


def ensure_directory(path: Path) -> bool:
    """
    Создаёт директорию, если её нет.

    Args:
        path (Path): Путь к директории

    Returns:
        bool: True если директория создана или существует
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Ошибка при создании директории {path}: {e}")
        return False


def save_file(data: bytes, filename: str, directory: Optional[Path] = None) -> Optional[Path]:
    """
    Сохраняет файл в указанную директорию.

    Args:
        data (bytes): Данные файла
        filename (str): Имя файла
        directory (Optional[Path]): Директория для сохранения

    Returns:
        Optional[Path]: Путь к сохранённому файлу или None в случае ошибки
    """
    if directory is None:
        directory = Config.DATA_DIR

    if not ensure_directory(directory):
        return None

    file_path = directory / filename

    try:
        with open(file_path, "wb") as f:
            f.write(data)
        return file_path
    except Exception as e:
        print(f"Ошибка при сохранении файла {file_path}: {e}")
        return None


def load_file(file_path: Path) -> Optional[bytes]:
    """
    Загружает файл в память.

    Args:
        file_path (Path): Путь к файлу

    Returns:
        Optional[bytes]: Данные файла или None в случае ошибки
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка при загрузке файла {file_path}: {e}")
        return None


def delete_file(file_path: Path) -> bool:
    """
    Удаляет файл.

    Args:
        file_path (Path): Путь к файлу

    Returns:
        bool: True если файл удалён
    """
    try:
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")
        return False


def delete_old_files(
    directory: Path,
    extension: Optional[str] = None,
    days_old: int = 7
) -> int:
    """
    Удаляет старые файлы из директории.

    Args:
        directory (Path): Директория
        extension (Optional[str]): Расширение файлов (например, ".ogg")
        days_old (int): Возраст файлов в днях

    Returns:
        int: Количество удалённых файлов
    """
    if not directory.exists():
        return 0

    deleted_count = 0
    now = datetime.now()

    for file_path in directory.iterdir():
        if file_path.is_file():
            # Проверяем расширение
            if extension and not file_path.suffix == extension:
                continue

            # Проверяем возраст файла
            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age = (now - modified_time).days

            if age > days_old:
                if delete_file(file_path):
                    deleted_count += 1

    return deleted_count


def get_file_size(file_path: Path) -> int:
    """
    Возвращает размер файла в байтах.

    Args:
        file_path (Path): Путь к файлу

    Returns:
        int: Размер файла в байтах
    """
    try:
        return file_path.stat().st_size
    except Exception:
        return 0


def get_file_extension(filename: str) -> str:
    """
    Возвращает расширение файла.

    Args:
        filename (str): Имя файла

    Returns:
        str: Расширение файла (например, ".txt")
    """
    return Path(filename).suffix


def list_files(
    directory: Path,
    extension: Optional[str] = None,
    sort_by_date: bool = False
) -> List[Path]:
    """
    Возвращает список файлов в директории.

    Args:
        directory (Path): Директория
        extension (Optional[str]): Расширение файлов
        sort_by_date (bool): Сортировать по дате изменения

    Returns:
        List[Path]: Список файлов
    """
    if not directory.exists():
        return []

    files = []
    for file_path in directory.iterdir():
        if file_path.is_file():
            if extension and not file_path.suffix == extension:
                continue
            files.append(file_path)

    if sort_by_date:
        files.sort(key=lambda x: x.stat().st_mtime)

    return files


def clean_temp_files():
    """
    Очищает временные файлы (аудио старше 1 дня).
    """
    audio_dir = Config.AUDIO_DIR
    if audio_dir.exists():
        deleted = delete_old_files(audio_dir, days_old=1)
        if deleted > 0:
            print(f"🧹 Удалено {deleted} временных аудиофайлов")
