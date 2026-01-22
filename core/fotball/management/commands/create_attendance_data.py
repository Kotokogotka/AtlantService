"""
Management команда для создания тестовых данных посещений за сентябрь и октябрь 2024
"""
from django.core.management.base import BaseCommand
from fotball.models import GroupKidGarden as Group, Child, TrainingSchedule as Schedule, Attendance
from datetime import datetime, timedelta
import random

# Списки имен для генерации детей
FIRST_NAMES = [
    'Александр', 'Максим', 'Артём', 'Михаил', 'Иван', 'Дмитрий',
    'Анастасия', 'Мария', 'Дарья', 'Елизавета', 'Виктория', 'Полина',
    'Николай', 'Егор', 'Андрей', 'Владимир', 'Роман', 'Сергей',
    'София', 'Алиса', 'Ксения', 'Ольга', 'Екатерина', 'Анна'
]

LAST_NAMES = [
    'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов',
    'Васильев', 'Соколов', 'Михайлов', 'Новиков', 'Фёдоров', 'Морозов',
    'Волков', 'Алексеев', 'Лебедев', 'Семёнов', 'Егоров', 'Павлов',
    'Козлов', 'Степанов', 'Николаев', 'Орлов', 'Андреев', 'Макаров'
]

class Command(BaseCommand):
    help = 'Создание тестовых данных посещений за сентябрь и октябрь 2025'

    def handle(self, *args, **options):
        self.stdout.write("🏗️ Создание тестовых данных для таблицы посещений...")
        
        # 1. Получаем или создаем группы
        self.stdout.write("\n📚 Проверка групп...")
        groups = Group.objects.all()
        
        if groups.count() == 0:
            self.stdout.write("⚠️ Нет групп! Создаю тестовые группы...")
            # Создаем группы для 3 садов: в каждом саду есть младшая, средняя и старшая группы
            groups_data = [
                # Сад №1
                {'name': 'Васильки (младшая)', 'kindergarten_number': 1},
                {'name': 'Пчёлки (младшая)', 'kindergarten_number': 1},
                {'name': 'Коровки (средняя)', 'kindergarten_number': 1},
                {'name': 'Цветочки (средняя)', 'kindergarten_number': 1},
                {'name': 'Одуванчики (старшая)', 'kindergarten_number': 1},
                {'name': 'Бычки (старшая)', 'kindergarten_number': 1},
                # Сад №2
                {'name': 'Солнышко (младшая)', 'kindergarten_number': 2},
                {'name': 'Звёздочка (средняя)', 'kindergarten_number': 2},
                {'name': 'Радуга (старшая)', 'kindergarten_number': 2},
                # Сад №3
                {'name': 'Улыбка (младшая)', 'kindergarten_number': 3},
                {'name': 'Смешинка (средняя)', 'kindergarten_number': 3},
                {'name': 'Весёлая (старшая)', 'kindergarten_number': 3},
            ]
            
            groups = []
            for group_data in groups_data:
                group = Group.objects.create(**group_data)
                groups.append(group)
                self.stdout.write(f"  ✅ Создана группа: {group.name} (Сад №{group.kindergarten_number})")
        else:
            self.stdout.write(f"  ✅ Найдено {groups.count()} групп")
            groups = list(groups)
        
        # 2. Добавляем детей в каждую группу (по 10-12 детей)
        self.stdout.write("\n👶 Добавление детей...")
        
        for group in groups:
            existing_children = Child.objects.filter(group=group).count()
            children_to_add = random.randint(10, 12) - existing_children
            
            if children_to_add > 0:
                self.stdout.write(f"\n  Группа: {group.name}")
                for i in range(children_to_add):
                    first_name = random.choice(FIRST_NAMES)
                    last_name = random.choice(LAST_NAMES)
                    full_name = f"{last_name} {first_name}"
                    
                    if not Child.objects.filter(group=group, full_name=full_name).exists():
                        child = Child.objects.create(
                            group=group,
                            full_name=full_name,
                            birth_date=datetime(2018, random.randint(1, 12), random.randint(1, 28)).date()
                        )
                        self.stdout.write(f"    ✅ Добавлен: {child.full_name}")
            else:
                self.stdout.write(f"  ✅ Группа {group.name} уже имеет {existing_children} детей")
        
        # 3. Создаем расписание тренировок (2 раза в неделю: вторник и четверг)
        self.stdout.write("\n📅 Создание расписания тренировок...")
        
        # Используем текущий год
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        
        september_start = datetime(current_year, 9, 1).date()
        september_end = datetime(current_year, 9, 30).date()
        october_start = datetime(current_year, 10, 1).date()
        october_end = datetime(current_year, 10, current_day).date()  # до текущего дня
        
        self.stdout.write(f"  Период: {september_start} - {october_end}")
        
        for group in groups:
            self.stdout.write(f"\n  Группа: {group.name}")
            
            Schedule.objects.filter(group=group, date__range=[september_start, october_end]).delete()
            
            training_count = 0
            
            # Получаем или создаем тренера и администратора для группы
            from fotball.models import Trainer, User
            trainer = Trainer.objects.first()
            if not trainer:
                self.stdout.write("⚠️ Нет тренеров! Создаю тестового тренера...")
                trainer_user = User.objects.create(username='trainer_test', role='trainer')
                trainer = Trainer.objects.create(user=trainer_user, full_name='Тестовый Тренер')
            
            admin = User.objects.filter(role='admin').first()
            if not admin:
                self.stdout.write("⚠️ Нет админов! Создаю тестового админа...")
                admin = User.objects.create(username='admin_test', role='admin')
            
            # Генерируем расписание для сентября
            current_date = september_start
            while current_date <= september_end:
                if current_date.weekday() in [1, 3]:  # Вторник и Четверг
                    Schedule.objects.create(
                        group=group,
                        date=current_date,
                        time=f"{random.randint(9, 16)}:00:00",
                        trainer=trainer,
                        created_by=admin,
                        status='completed'  # Сентябрь - уже прошел
                    )
                    training_count += 1
                current_date += timedelta(days=1)
            
            # Генерируем расписание для октября
            current_date = october_start
            while current_date <= october_end:
                if current_date.weekday() in [1, 3]:
                    Schedule.objects.create(
                        group=group,
                        date=current_date,
                        time=f"{random.randint(9, 16)}:00:00",
                        trainer=trainer,
                        created_by=admin,
                        status='scheduled' if current_date > datetime.now().date() else 'completed'
                    )
                    training_count += 1
                current_date += timedelta(days=1)
            
            self.stdout.write(f"    ✅ Создано {training_count} тренировок")
        
        # 4. Создаем посещения для каждого ребенка
        self.stdout.write("\n✅ Создание записей посещений...")
        
        for group in groups:
            self.stdout.write(f"\n  Группа: {group.name}")
            
            schedules = Schedule.objects.filter(
                group=group,
                date__range=[september_start, october_end]
            ).order_by('date')
            
            children = Child.objects.filter(group=group)
            
            self.stdout.write(f"    Детей: {children.count()}, Тренировок: {schedules.count()}")
            
            Attendance.objects.filter(
                child__group=group,
                date__range=[september_start, october_end]
            ).delete()
            
            total_attendance = 0
            
            for child in children:
                for schedule in schedules:
                    rand = random.random()
                    
                    if rand < 0.8:
                        status = True
                        reason = None
                    elif rand < 0.9:
                        status = False
                        reason = None
                    else:
                        status = False
                        reason = 'справка о болезни'
                    
                    Attendance.objects.create(
                        child=child,
                        group=group,
                        date=schedule.date,
                        status=status,
                        reason=reason
                    )
                    total_attendance += 1
            
            self.stdout.write(f"    ✅ Создано {total_attendance} записей посещений")
        
        # 5. Статистика
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 ИТОГОВАЯ СТАТИСТИКА:")
        self.stdout.write("="*60)
        
        total_groups = Group.objects.count()
        total_children = Child.objects.count()
        total_schedules = Schedule.objects.filter(date__range=[september_start, october_end]).count()
        total_attendance = Attendance.objects.filter(date__range=[september_start, october_end]).count()
        
        self.stdout.write(f"  📚 Всего групп: {total_groups}")
        self.stdout.write(f"  👶 Всего детей: {total_children}")
        self.stdout.write(f"  📅 Всего тренировок (сентябрь-октябрь): {total_schedules}")
        self.stdout.write(f"  ✅ Всего записей посещений: {total_attendance}")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎉 Тестовые данные успешно созданы!"))
        self.stdout.write("="*60)

