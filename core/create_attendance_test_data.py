#!/usr/bin/env python
"""
Скрипт для создания тестовых данных посещений за сентябрь и октябрь 2024
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import GroupKidGarden as Group, Child, TrainingSchedule as Schedule, Attendance, User, Trainer

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

def create_test_data():
    """Создание тестовых данных"""
    
    print("🏗️ Создание тестовых данных для таблицы посещений...")
    
    # 1. Получаем или создаем группы
    print("\n📚 Проверка групп...")
    groups = Group.objects.all()
    
    if groups.count() == 0:
        print("⚠️ Нет групп! Создаю тестовые группы...")
        # Создаем 3 группы разных возрастов
        groups_data = [
            {'name': 'Группа младшая А', 'kindergarten_number': 1},
            {'name': 'Группа средняя Б', 'kindergarten_number': 2},
            {'name': 'Группа старшая В', 'kindergarten_number': 3},
        ]
        
        groups = []
        for group_data in groups_data:
            group = Group.objects.create(**group_data)
            groups.append(group)
            print(f"  ✅ Создана группа: {group.name}")
    else:
        print(f"  ✅ Найдено {groups.count()} групп")
        groups = list(groups)
    
    # 2. Добавляем детей в каждую группу (по 10-12 детей)
    print("\n👶 Добавление детей...")
    
    for group in groups:
        existing_children = Child.objects.filter(group=group).count()
        children_to_add = random.randint(10, 12) - existing_children
        
        if children_to_add > 0:
            print(f"\n  Группа: {group.name}")
            for i in range(children_to_add):
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                full_name = f"{last_name} {first_name}"
                
                # Проверяем, что ребенок с таким именем еще не существует в группе
                if not Child.objects.filter(group=group, full_name=full_name).exists():
                    child = Child.objects.create(
                        group=group,
                        full_name=full_name,
                        birth_date=datetime(2018, random.randint(1, 12), random.randint(1, 28)).date()
                    )
                    print(f"    ✅ Добавлен: {child.full_name}")
        else:
            print(f"  ✅ Группа {group.name} уже имеет {existing_children} детей")
    
    # 3. Создаем расписание тренировок (2 раза в неделю: вторник и четверг)
    print("\n📅 Создание расписания тренировок...")
    
    # Сентябрь 2024
    september_start = datetime(2024, 9, 1).date()
    september_end = datetime(2024, 9, 30).date()
    
    # Октябрь 2024 (до сегодня)
    october_start = datetime(2024, 10, 1).date()
    october_end = datetime(2024, 10, 21).date()  # до сегодняшнего дня
    
    # Получаем или создаем тренера и администратора
    trainer = Trainer.objects.first()
    if not trainer:
        print("⚠️ Нет тренеров! Создаю тестового тренера...")
        trainer_user = User.objects.create(username='trainer_test', role='trainer')
        trainer = Trainer.objects.create(user=trainer_user, full_name='Тестовый Тренер')
    
    admin = User.objects.filter(role='admin').first()
    if not admin:
        print("⚠️ Нет админов! Создаю тестового админа...")
        admin = User.objects.create(username='admin_test', role='admin')
    
    for group in groups:
        print(f"\n  Группа: {group.name}")
        
        # Удаляем старое расписание для этой группы
        Schedule.objects.filter(group=group, date__range=[september_start, october_end]).delete()
        
        training_count = 0
        
        # Генерируем расписание для сентября
        current_date = september_start
        while current_date <= september_end:
            # Вторник (1) и Четверг (3)
            if current_date.weekday() in [1, 3]:
                Schedule.objects.create(
                    group=group,
                    date=current_date,
                    time=f"{random.randint(9, 16)}:00:00",
                    trainer=trainer,
                    created_by=admin,
                    status='completed'
                )
                training_count += 1
            current_date += timedelta(days=1)
        
        # Генерируем расписание для октября
        current_date = october_start
        while current_date <= october_end:
            # Вторник (1) и Четверг (3)
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
        
        print(f"    ✅ Создано {training_count} тренировок")
    
    # 4. Создаем посещения для каждого ребенка
    print("\n✅ Создание записей посещений...")
    
    for group in groups:
        print(f"\n  Группа: {group.name}")
        
        # Получаем все тренировки для группы
        schedules = Schedule.objects.filter(
            group=group,
            date__range=[september_start, october_end]
        ).order_by('date')
        
        # Получаем всех детей группы
        children = Child.objects.filter(group=group)
        
        print(f"    Детей: {children.count()}, Тренировок: {schedules.count()}")
        
        # Удаляем старые записи посещений
        Attendance.objects.filter(
            child__group=group,
            date__range=[september_start, october_end]
        ).delete()
        
        total_attendance = 0
        
        for child in children:
            for schedule in schedules:
                # 80% вероятность присутствия
                # 10% вероятность отсутствия без причины
                # 10% вероятность отсутствия по справке
                rand = random.random()
                
                if rand < 0.8:
                    # Присутствовал
                    status = True
                    reason = None
                elif rand < 0.9:
                    # Отсутствовал без причины
                    status = False
                    reason = None
                else:
                    # Отсутствовал по справке
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
        
        print(f"    ✅ Создано {total_attendance} записей посещений")
    
    # 5. Статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("="*60)
    
    total_groups = Group.objects.count()
    total_children = Child.objects.count()
    total_schedules = Schedule.objects.filter(date__range=[september_start, october_end]).count()
    total_attendance = Attendance.objects.filter(date__range=[september_start, october_end]).count()
    
    print(f"  📚 Всего групп: {total_groups}")
    print(f"  👶 Всего детей: {total_children}")
    print(f"  📅 Всего тренировок (сентябрь-октябрь): {total_schedules}")
    print(f"  ✅ Всего записей посещений: {total_attendance}")
    
    print("\n" + "="*60)
    print("🎉 Тестовые данные успешно созданы!")
    print("="*60)
    
    # Детальная статистика по группам
    print("\n📋 Детальная статистика по группам:")
    for group in groups:
        children_count = Child.objects.filter(group=group).count()
        schedules_count = Schedule.objects.filter(
            group=group,
            date__range=[september_start, october_end]
        ).count()
        attendance_count = Attendance.objects.filter(
            child__group=group,
            date__range=[september_start, october_end]
        ).count()
        
        print(f"\n  🏫 {group.name} (Номер: {group.kindergarten_number})")
        print(f"     - Детей: {children_count}")
        print(f"     - Тренировок: {schedules_count}")
        print(f"     - Записей посещений: {attendance_count}")
        
        # Статистика посещаемости
        attended = Attendance.objects.filter(
            child__group=group,
            date__range=[september_start, october_end],
            status=True
        ).count()
        
        missed = Attendance.objects.filter(
            child__group=group,
            date__range=[september_start, october_end],
            status=False,
            reason__isnull=True
        ).count()
        
        medical = Attendance.objects.filter(
            child__group=group,
            date__range=[september_start, october_end],
            status=False,
            reason__isnull=False
        ).count()
        
        print(f"     - Присутствовало (+): {attended}")
        print(f"     - Пропущено (пусто): {missed}")
        print(f"     - По справке (С): {medical}")

if __name__ == "__main__":
    try:
        create_test_data()
        print("\n✅ Скрипт выполнен успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

