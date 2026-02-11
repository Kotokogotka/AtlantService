# -*- coding: utf-8 -*-
"""
Парсинг данных с чеков об оплате (Сбербанк, ВТБ, Озон, Т-Банк, Альфа-Банк и др.).
Извлекает текст из PDF/изображений и находит сумму, дату и банк.
"""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime


# Ключевые слова для определения банка (нижний регистр для поиска)
BANK_KEYWORDS = {
    'sber': ['сбербанк', 'сбер', 'sberbank', 'sber'],
    'vtb': ['втб', 'vtb', 'внешторгбанк'],
    'ozon': ['озон', 'ozon'],
    'tbank': ['т-банк', 'т банк', 'тинькофф', 'тинькофф', 't-bank', 'tbank', 'tinkoff'],
    'alfa': ['альфа-банк', 'альфа банк', 'alfa', 'альфа'],
}


def _extract_text_from_pdf(file_path):
    """Извлечь текст из PDF (первая страница)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = []
        for i in range(min(3, len(doc))):  # первые 3 страницы
            text.append(doc[i].get_text())
        doc.close()
        return '\n'.join(text)
    except Exception:
        return ''


def _extract_text_from_image(file_path):
    """Извлечь текст из изображения через OCR (если доступен tesseract)."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        # Поддержка русского и английского
        text = pytesseract.image_to_string(img, lang='rus+eng')
        return text or ''
    except Exception:
        return ''


def extract_text_from_receipt_file(file_path):
    """
    Извлечь текст из файла чека (PDF или изображение).
    Возвращает строку текста или пустую строку при ошибке.
    """
    file_path = str(file_path)
    lower = file_path.lower()
    if lower.endswith('.pdf'):
        return _extract_text_from_pdf(file_path)
    if lower.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')):
        return _extract_text_from_image(file_path)
    return ''


def _normalize_amount(value):
    """Преобразовать строку суммы в Decimal. Поддержка форматов: 1 500,00 / 1500.00 / 1500,50"""
    if not value:
        return None
    # убрать пробелы, заменить запятую на точку
    s = re.sub(r'\s+', '', value.strip()).replace(',', '.')
    # оставить только цифры и одну точку
    s = re.sub(r'[^\d.]', '', s)
    if not s:
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _parse_amounts(text):
    """
    Найти в тексте суммы в рублях. Возвращает список Decimal.
    Типичные форматы: 1 500,00 ₽ | 1500.00 руб | Сумма: 2000,50
    """
    amounts = []
    # Паттерны: число с пробелами/запятыми/точками + руб/₽
    patterns = [
        r'(?:сумма|итого|переведено|оплачено|к\s+оплате|всего|amount)\s*[:.]?\s*(\d[\d\s]*[,.]?\d*)\s*(?:руб|р\.|₽|руб\.)?',
        r'(\d[\d\s]{0,10})[,.](\d{2})\s*(?:руб|р\.|₽|руб\.)',
        r'(\d[\d\s]{0,10})[,.](\d{2})\s*[рR]',
        r'(?:руб|₽)\s*(\d[\d\s]*[,.]?\d*)',
        r'(\d{1,8})[,.](\d{2})\s*(?:руб|₽)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            g = m.groups()
            if len(g) == 1:
                val = _normalize_amount(g[0])
            else:
                val = _normalize_amount((g[0] or '') + '.' + (g[1] or '0'))
            if val is not None and 0 < val < 10 ** 8:
                amounts.append(val)
    # Уникальные, по убыванию — чаще всего нужна максимальная (итого)
    seen = set()
    unique = []
    for a in sorted(amounts, reverse=True):
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique


def _parse_date(text):
    """Найти дату в формате dd.mm.yyyy или dd/mm/yyyy."""
    patterns = [
        r'\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b',
        r'\b(\d{1,2})[./](\d{1,2})[./](\d{2})\b',
        r'\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            g = m.groups()
            try:
                if len(g[0]) == 4:  # year first
                    y, mo, d = int(g[0]), int(g[1]), int(g[2])
                else:
                    d, mo, y = int(g[0]), int(g[1]), int(g[2])
                    if y < 100:
                        y += 2000 if y < 50 else 1900
                if 1 <= mo <= 12 and 1 <= d <= 31:
                    return datetime(y, mo, d).date()
            except (ValueError, TypeError):
                continue
    return None


def _detect_bank(text):
    """Определить банк по ключевым словам в тексте."""
    text_lower = text.lower()
    for bank_code, keywords in BANK_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return bank_code
    return 'other'


def parse_receipt(text, expected_amount_decimal, tolerance=Decimal('0.01')):
    """
    Распарсить текст чека и проверить соответствие суммы.
    
    :param text: строка текста с чека
    :param expected_amount_decimal: ожидаемая сумма (Decimal), из счёта
    :param tolerance: допустимое расхождение суммы
    :return: dict с ключами parsed_amount, parsed_date, parsed_bank, amount_match, raw_preview
    """
    expected = Decimal(str(expected_amount_decimal))
    result = {
        'parsed_amount': None,
        'parsed_date': None,
        'parsed_bank': None,
        'amount_match': None,
        'raw_preview': (text[:1500] if text else '').strip(),
    }
    if not text or not text.strip():
        return result
    amounts = _parse_amounts(text)
    result['parsed_amount'] = amounts[0] if amounts else None
    result['parsed_date'] = _parse_date(text)
    result['parsed_bank'] = _detect_bank(text)
    if result['parsed_amount'] is not None and expected is not None:
        result['amount_match'] = abs(result['parsed_amount'] - expected) <= tolerance
    return result


def parse_receipt_file(file_path, expected_amount_decimal, tolerance=Decimal('0.01')):
    """
    Извлечь текст из файла чека и распарсить.
    Возвращает тот же dict, что и parse_receipt.
    """
    text = extract_text_from_receipt_file(file_path)
    return parse_receipt(text, expected_amount_decimal, tolerance)
