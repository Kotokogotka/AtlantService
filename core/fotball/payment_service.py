from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Count
from django.utils import timezone
from .models import PaymentInvoice, PaymentSettings, Child, TrainingSchedule, MedicalCertificate


class PaymentService:
    """
    Сервис для работы с системой оплаты.
    
    Основные функции:
    - Расчет стоимости тренировок на месяц
    - Учет подтвержденных пропусков по болезни
    - Генерация счетов на оплату
    """
    
    @staticmethod
    def get_payment_settings(kindergarten):
        """
        Получить настройки оплаты для детского сада.
        
        Args:
            kindergarten: Объект GroupKidGarden
            
        Returns:
            PaymentSettings или создает с дефолтными значениями
        """
        settings, created = PaymentSettings.objects.get_or_create(
            kindergarten=kindergarten,
            defaults={
                'price_per_training': 500.00,
                'default_trainings_per_month': 8,
                'invoice_generation_day': 25,
                'is_active': True
            }
        )
        return settings
    
    @staticmethod
    def calculate_trainings_for_month(child, target_month):
        """
        Рассчитать количество тренировок для ребенка на месяц.
        
        Args:
            child: Объект Child
            target_month: date объект (первое число месяца)
            
        Returns:
            int: количество тренировок
        """
        # Определяем границы месяца
        month_start = target_month.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)
        
        # Ищем расписание тренировок для группы ребенка в этом месяце
        trainings = TrainingSchedule.objects.filter(
            group=child.group,
            date__gte=month_start,
            date__lte=month_end,
            status='scheduled'  # только запланированные тренировки
        ).count()
        
        if trainings > 0:
            # Если админ проставил расписание, используем его
            return trainings
        else:
            # Если расписания нет, используем дефолтное количество из настроек
            settings = PaymentService.get_payment_settings(child.group)
            return settings.default_trainings_per_month
    
    @staticmethod
    def calculate_confirmed_absences(child, target_month):
        """
        Рассчитать количество подтвержденных пропусков по болезни.
        
        Args:
            child: Объект Child
            target_month: date объект (первое число месяца)
            
        Returns:
            int: количество дней пропусков, за которые не нужно платить
        """
        # Определяем границы месяца
        month_start = target_month.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)
        
        # Находим все подтвержденные справки, которые пересекаются с этим месяцем
        confirmed_certificates = MedicalCertificate.objects.filter(
            child=child,
            status='confirmed',  # только подтвержденные админом
            date_from__lte=month_end,
            date_to__gte=month_start
        )
        
        total_absence_days = 0
        
        for cert in confirmed_certificates:
            # Определяем пересечение периода справки с месяцем
            absence_start = max(cert.date_from, month_start)
            absence_end = min(cert.date_to, month_end)
            
            # Считаем дни в этом периоде
            days_in_period = (absence_end - absence_start).days + 1
            total_absence_days += days_in_period
        
        # Теперь нужно понять, сколько тренировок было в эти дни
        # Для упрощения будем считать, что тренировки равномерно распределены по месяцу
        days_in_month = (month_end - month_start).days + 1
        total_trainings = PaymentService.calculate_trainings_for_month(child, target_month)
        
        # Пропорционально рассчитываем количество пропущенных тренировок
        if days_in_month > 0:
            missed_trainings = int((total_absence_days / days_in_month) * total_trainings)
            return min(missed_trainings, total_trainings)  # не больше общего количества
        
        return 0
    
    @staticmethod
    def generate_invoice_for_child(child, target_month):
        """
        Сгенерировать счет на оплату для ребенка.
        
        Args:
            child: Объект Child
            target_month: date объект (первое число месяца)
            
        Returns:
            PaymentInvoice: созданный или обновленный счет
        """
        # Получаем настройки оплаты
        settings = PaymentService.get_payment_settings(child.group)
        
        # Рассчитываем количество тренировок
        total_trainings = PaymentService.calculate_trainings_for_month(child, target_month)
        
        # Рассчитываем подтвержденные пропуски
        confirmed_absences = PaymentService.calculate_confirmed_absences(child, target_month)
        
        # Определяем срок оплаты (10 дней с момента выставления)
        due_date = timezone.now().date() + relativedelta(days=10)
        
        # Создаем или обновляем счет
        invoice, created = PaymentInvoice.objects.update_or_create(
            child=child,
            invoice_month=target_month,
            defaults={
                'total_trainings': total_trainings,
                'confirmed_absences': confirmed_absences,
                'price_per_training': settings.price_per_training,
                'due_date': due_date,
                'status': 'pending'
            }
        )
        
        return invoice
    
    @staticmethod
    def generate_invoices_for_month(target_month):
        """
        Сгенерировать счета для всех активных детей на месяц.
        
        Args:
            target_month: date объект (первое число месяца)
            
        Returns:
            list: список созданных счетов
        """
        # Получаем всех активных детей
        active_children = Child.objects.filter(is_active=True).select_related('group')
        
        created_invoices = []
        
        for child in active_children:
            try:
                invoice = PaymentService.generate_invoice_for_child(child, target_month)
                created_invoices.append(invoice)
            except Exception as e:
                print(f"Ошибка при создании счета для {child.full_name}: {e}")
                continue
        
        return created_invoices
    
    @staticmethod
    def get_next_month():
        """
        Получить первое число следующего месяца.
        
        Returns:
            date: первое число следующего месяца
        """
        today = timezone.now().date()
        next_month = today + relativedelta(months=1)
        return next_month.replace(day=1)
    
    @staticmethod
    def should_generate_invoices_today():
        """
        Проверить, нужно ли сегодня генерировать счета.
        
        Returns:
            bool: True если сегодня день генерации счетов
        """
        today = timezone.now().date()
        
        # Проверяем все активные настройки оплаты
        active_settings = PaymentSettings.objects.filter(is_active=True)
        
        for settings in active_settings:
            if today.day == settings.invoice_generation_day:
                return True
        
        return False
