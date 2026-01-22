"""
Команда для проверки дат в расписании и посещениях
"""
from django.core.management.base import BaseCommand
from fotball.models import TrainingSchedule, Attendance

class Command(BaseCommand):
    help = 'Проверка дат в расписании и посещениях'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Проверка дат в базе данных...")
        
        # Проверяем расписание
        schedules = TrainingSchedule.objects.all().order_by('date')
        if schedules.exists():
            first_schedule = schedules.first()
            last_schedule = schedules.last()
            self.stdout.write(f"\n📅 Расписание тренировок:")
            self.stdout.write(f"  - Всего записей: {schedules.count()}")
            self.stdout.write(f"  - Первая дата: {first_schedule.date}")
            self.stdout.write(f"  - Последняя дата: {last_schedule.date}")
            
            # Группируем по годам и месяцам
            dates_by_month = {}
            for schedule in schedules:
                year_month = schedule.date.strftime('%Y-%m')
                if year_month not in dates_by_month:
                    dates_by_month[year_month] = 0
                dates_by_month[year_month] += 1
            
            self.stdout.write(f"\n  📊 По месяцам:")
            for month, count in sorted(dates_by_month.items()):
                self.stdout.write(f"    - {month}: {count} тренировок")
        else:
            self.stdout.write("\n⚠️ Нет записей в расписании!")
        
        # Проверяем посещения
        attendances = Attendance.objects.all().order_by('date')
        if attendances.exists():
            first_attendance = attendances.first()
            last_attendance = attendances.last()
            self.stdout.write(f"\n✅ Посещения:")
            self.stdout.write(f"  - Всего записей: {attendances.count()}")
            self.stdout.write(f"  - Первая дата: {first_attendance.date}")
            self.stdout.write(f"  - Последняя дата: {last_attendance.date}")
        else:
            self.stdout.write("\n⚠️ Нет записей о посещениях!")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Проверка завершена!"))

