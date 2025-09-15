from django.core.management.base import BaseCommand
from fotball.models import User, Child, Parent, GroupKidGarden, Attendance
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Создает тестового пользователя-родителя с ребенком и данными посещаемости'

    def handle(self, *args, **options):
        try:
            # Проверяем, существует ли уже тестовый родитель
            if User.objects.filter(username='parent').exists():
                self.stdout.write(
                    self.style.WARNING('Тестовый родитель уже существует')
                )
                return

            # Создаем родителя
            parent = Parent.objects.create(
                full_name='Иванова Мария Петровна',
                phone='+7 (999) 123-45-67'
            )

            # Создаем группу, если её нет
            group, created = GroupKidGarden.objects.get_or_create(
                name='Старшая группа',
                defaults={
                    'kindergarten_number': 15,
                    'age_level': 'L'  # L = Старшая
                }
            )

            if created:
                self.stdout.write('Создана новая группа: Старшая группа')

            # Создаем ребенка
            child = Child.objects.create(
                full_name='Иванов Алексей Сергеевич',
                birth_date=date(2018, 5, 15),
                parent_name=parent,
                group=group,
                is_active=True
            )

            # Создаем пользователя-родителя
            user = User.objects.create(
                username='parent',
                password='parent123',
                role='parent',
                linked_child=child
            )

            # Создаем тестовые записи посещаемости за последние 2 месяца
            today = date.today()
            start_date = today - timedelta(days=60)
            
            # Создаем записи посещаемости (примерно 2-3 раза в неделю)
            current_date = start_date
            attendance_count = 0
            
            while current_date <= today:
                # Тренировки по понедельникам, средам и пятницам
                if current_date.weekday() in [0, 2, 4]:  # Понедельник, среда, пятница
                    # 80% вероятность присутствия
                    status = random.random() < 0.8
                    reason = None if status else random.choice([
                        'Болел',
                        'Семейные обстоятельства',
                        'Отпуск родителей',
                        'Плохое самочувствие'
                    ])
                    
                    Attendance.objects.create(
                        child=child,
                        group=group,
                        date=current_date,
                        status=status,
                        reason=reason
                    )
                    attendance_count += 1
                
                current_date += timedelta(days=1)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Тестовый родитель создан успешно!\n'
                    f'Логин: {user.username}\n'
                    f'Пароль: parent123\n'
                    f'Роль: {user.get_role_display()}\n'
                    f'Ребенок: {child.full_name}\n'
                    f'Группа: {group.name}\n'
                    f'Создано записей посещаемости: {attendance_count}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании тестового родителя: {e}')
            )
