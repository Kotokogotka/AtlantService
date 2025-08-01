"""
Утилиты для работы с кодировками и предотвращения ошибок Unicode
"""
import codecs
import chardet
from typing import Union, Optional


def safe_decode(data: Union[bytes, str], encoding: Optional[str] = None) -> str:
    """
    Безопасное декодирование данных с автоматическим определением кодировки
    
    Args:
        data: Данные для декодирования (bytes или str)
        encoding: Предпочтительная кодировка (опционально)
    
    Returns:
        str: Декодированная строка
    """
    if isinstance(data, str):
        return data
    
    if encoding:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    
    # Автоматическое определение кодировки
    detected = chardet.detect(data)
    detected_encoding = detected.get('encoding', 'utf-8')
    
    # Попробуем различные кодировки
    encodings_to_try = [
        detected_encoding,
        'utf-8',
        'cp1251',
        'windows-1251',
        'iso-8859-1',
        'latin-1'
    ]
    
    for enc in encodings_to_try:
        if enc:
            try:
                return data.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
    
    # Если ничего не помогло, используем errors='replace'
    return data.decode('utf-8', errors='replace')


def safe_encode(text: str, encoding: str = 'utf-8') -> bytes:
    """
    Безопасное кодирование текста
    
    Args:
        text: Текст для кодирования
        encoding: Кодировка (по умолчанию utf-8)
    
    Returns:
        bytes: Закодированные данные
    """
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, errors='replace')


def read_file_safe(file_path: str, encoding: Optional[str] = None) -> str:
    """
    Безопасное чтение файла с автоматическим определением кодировки
    
    Args:
        file_path: Путь к файлу
        encoding: Предпочтительная кодировка
    
    Returns:
        str: Содержимое файла
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    
    return safe_decode(raw_data, encoding)


def normalize_text(text: str) -> str:
    """
    Нормализация текста для предотвращения проблем с кодировкой
    
    Args:
        text: Исходный текст
    
    Returns:
        str: Нормализованный текст
    """
    import unicodedata
    
    # Нормализация Unicode
    normalized = unicodedata.normalize('NFC', text)
    
    # Удаление невидимых символов
    cleaned = ''.join(char for char in normalized if unicodedata.category(char) != 'Cc' or char in '\n\r\t')
    
    return cleaned.strip()


def fix_mojibake(text: str) -> str:
    """
    Исправление "mojibake" - неправильно декодированного текста
    
    Args:
        text: Текст с возможными проблемами кодировки
    
    Returns:
        str: Исправленный текст
    """
    # Распространенные случаи mojibake для русского текста
    mojibake_fixes = {
        'Ã°Ã¾Ã±Ã±Ã¨Ã©': 'русский',
        'Ðº': 'к',
        'Ð°': 'а',
        'Ñ': 'н',
        'Ñ€': 'р',
        'Ð¸': 'и',
        'Ð»': 'л',
        'Ñƒ': 'у',
        'Ñ‚': 'т',
        'Ð¾': 'о',
        'Ñ‹': 'ы',
        'Ð²': 'в',
        'Ñ‹': 'ы',
        'Ð¿': 'п',
        'Ñ': 'с',
        'Ð¼': 'м',
        'Ð¸': 'и',
        'Ñ‚': 'т',
        'ÑŒ': 'ь',
        'Ð±': 'б',
        'ÑŽ': 'ю',
        'Ñ': 'я',
    }
    
    result = text
    for wrong, correct in mojibake_fixes.items():
        result = result.replace(wrong, correct)
    
    return result