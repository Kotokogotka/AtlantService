from django.core.management.base import BaseCommand
from django.utils import timezone
from fotball.payment_service import PaymentService
from fotball.models import PaymentSettings


class Command(BaseCommand):
    help = 'Генерирует счета на оплату на следующий месяц'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно генерировать счета независимо от даты',
        )
        
        parser.add_argument(
            '--target-month',
            type=str,
            help='Месяц для генерации в формате YYYY-MM (по умолчанию следующий месяц)',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        target_month_str = options['target_month']
        
        # Проверяем, нужно ли генерировать счета сегодня
        if not force and not PaymentService.should_generate_invoices_today():
            today = timezone.now().date()
            self.stdout.write(
                self.style.WARNING(
                    f'Сегодня ({today}) не день генерации счетов. '
                    f'Используйте --force для принудительной генерации.'
                )
            )
            return
        
        # Определяем целевой месяц
        if target_month_str:
            try:
                from datetime import datetime
                target_month = datetime.strptime(target_month_str, '%Y-%m').date().replace(day=1)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(
                        'Неверный формат месяца. Используйте YYYY-MM (например, 2024-03)'
                    )
                )
                return
        else:
            target_month = PaymentService.get_next_month()
        
        months_ru = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_display = f"{months_ru[target_month.month - 1]} {target_month.year}"
        self.stdout.write(f'Генерация счетов на {month_display}...')
        
        try:
            # Генерируем счета
            created_invoices = PaymentService.generate_invoices_for_month(target_month)
            
            if created_invoices:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно сгенерировано {len(created_invoices)} счетов на {month_display}'
                    )
                )
                
                # Показываем статистику
                total_amount = sum(invoice.total_amount for invoice in created_invoices)
                self.stdout.write(f'Общая сумма: {total_amount} ₽')
                
                # Группируем по детским садам
                from collections import defaultdict
                by_kindergarten = defaultdict(list)
                
                for invoice in created_invoices:
                    kindergarten = invoice.child.group.name
                    by_kindergarten[kindergarten].append(invoice)
                
                self.stdout.write('\nСтатистика по детским садам:')
                for kindergarten, invoices in by_kindergarten.items():
                    count = len(invoices)
                    amount = sum(inv.total_amount for inv in invoices)
                    self.stdout.write(f'  {kindergarten}: {count} счетов, {amount} ₽')
                    
            else:
                self.stdout.write(
                    self.style.WARNING('Не было создано ни одного счета')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при генерации счетов: {e}')
            )
            raise e
        
        # Показываем информацию о настройках
        self.stdout.write('\nТекущие настройки оплаты:')
        settings = PaymentSettings.objects.filter(is_active=True)
        
        if settings.exists():
            for setting in settings:
                self.stdout.write(
                    f'  {setting.kindergarten.name}: '
                    f'{setting.price_per_training} ₽/тренировка, '
                    f'день генерации: {setting.invoice_generation_day}'
                )
        else:
            self.stdout.write('  Нет активных настроек оплаты')
