#!/usr/bin/env python
"""
Скрипт для создания тестовых данных по оплате.
"""

import os
import sys
import django
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
          
from fotball.models import PaymentSettings, PaymentInvoice, GroupKidGarden, Child
from fotball.payment_service import PaymentService


def create_payment_settings():
    """Создать настройки оплаты для всех детских садов."""
    print("Создание настроек оплаты...")
    
    kindergartens = GroupKidGarden.objects.all()
    
    for kindergarten in kindergartens:
        setting, created = PaymentSettings.objects.get_or_create(
            kindergarten=kindergarten,
            defaults={
                'price_per_training': 500.00,
                'default_trainings_per_month': 8,
                'invoice_generation_day': 25,
                'is_active': True
            }
        )
        
        if created:
            print(f"✓ Создана настройка для {kindergarten.name}")
        else:
            print(f"- Настройка для {kindergarten.name} уже существует")


def create_test_invoices():
    """Создать тестовые счета на оплату."""
    print("\nСоздание тестовых счетов...")
    
    # Получаем всех активных детей
    children = Child.objects.filter(is_active=True)[:5]  # Берем первых 5 для теста
    
    if not children:
        print("Нет активных детей для создания счетов")
        return
    
    # Создаем счета на текущий и следующий месяц
    current_month = date.today().replace(day=1)
    next_month = current_month + relativedelta(months=1)
    
    months = [current_month, next_month]
    
    for month in months:
        months_ru = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_display = f"{months_ru[month.month - 1]} {month.year}"
        print(f"\nСоздание счетов на {month_display}:")
        
        for child in children:
            try:
                invoice = PaymentService.generate_invoice_for_child(child, month)
                print(f"✓ Создан счет для {child.full_name}: {invoice.total_amount} ₽")
            except Exception as e:
                print(f"✗ Ошибка создания счета для {child.full_name}: {e}")


def show_payment_statistics():
    """Показать статистику по оплате."""
    print("\n" + "="*50)
    print("СТАТИСТИКА ПО ОПЛАТЕ")
    print("="*50)
    
    # Настройки оплаты
    settings = PaymentSettings.objects.all()
    print(f"\nНастройки оплаты ({settings.count()}):")
    for setting in settings:
        print(f"  {setting.kindergarten.name}:")
        print(f"    Стоимость: {setting.price_per_training} ₽/тренировка")
        print(f"    По умолчанию: {setting.default_trainings_per_month} тренировок/месяц")
        print(f"    День генерации: {setting.invoice_generation_day}")
        print(f"    Активно: {'Да' if setting.is_active else 'Нет'}")
    
    # Счета на оплату
    invoices = PaymentInvoice.objects.all().order_by('-invoice_month')
    print(f"\nСчета на оплату ({invoices.count()}):")
    
    if invoices:
        # Группируем по месяцам
        from collections import defaultdict
        by_month = defaultdict(list)
        
        for invoice in invoices:
            by_month[invoice.invoice_month].append(invoice)
        
        for month, month_invoices in by_month.items():
            months_ru = [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]
            month_display = f"{months_ru[month.month - 1]} {month.year}"
            print(f"\n  {month_display}:")
            total_amount = sum(inv.total_amount for inv in month_invoices)
            print(f"    Счетов: {len(month_invoices)}")
            print(f"    Общая сумма: {total_amount} ₽")
            
            # Статистика по статусам
            status_counts = defaultdict(int)
            for inv in month_invoices:
                status_counts[inv.status] += 1
            
            for status, count in status_counts.items():
                print(f"    {PaymentInvoice._meta.get_field('status').choices[next(i for i, (k, v) in enumerate(PaymentInvoice._meta.get_field('status').choices) if k == status)][1]}: {count}")
    
    print(f"\nАктивных детей: {Child.objects.filter(is_active=True).count()}")
    print(f"Детских садов: {GroupKidGarden.objects.count()}")


def main():
    print("Создание тестовых данных по оплате")
    print("="*40)
    
    try:
        # Создаем настройки оплаты
        create_payment_settings()
        
        # Создаем тестовые счета
        create_test_invoices()
        
        # Показываем статистику
        show_payment_statistics()
        
        print("\n✓ Тестовые данные по оплате созданы успешно!")
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
