from django.core.management.base import BaseCommand
from django.utils import timezone
from fotball.models import User, Trainer, GroupKidGarden, Child, Parent
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Создает тестовые данные для системы'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')
        
        # Создаем тренеров
        trainers_data = [
            {
                'username': 'trainer1',
                'password': 'password123',
                'full_name': 'Иванов Иван Иванович',
                'phone': '+7 (999) 123-45-67',
                'work_space': 'Детский сад №1, группы 1-3'
            },
            {
                'username': 'trainer2',
                'password': 'password123',
                'full_name': 'Петрова Анна Сергеевна',
                'phone': '+7 (999) 234-56-78',
                'work_space': 'Детский сад №2, группы 4-6'
            }
        ]
        
        trainers = []
        for trainer_data in trainers_data:
            user, created = User.objects.get_or_create(
                username=trainer_data['username'],
                defaults={
                    'password': trainer_data['password'],
                    'role': 'trainer'
                }
            )
            
            if created:
                # Обновляем тренера
                trainer = user.linked_trainer
                trainer.full_name = trainer_data['full_name']
                trainer.phone = trainer_data['phone']
                trainer.work_space = trainer_data['work_space']
                trainer.save()
                
                trainers.append(trainer)
                self.stdout.write(f'Создан тренер: {trainer.full_name}')
            else:
                trainers.append(user.linked_trainer)
                self.stdout.write(f'Тренер уже существует: {user.linked_trainer.full_name}')
        
        # Создаем группы
        groups_data = [
            {'name': 'Солнышко', 'kindergarten_number': 'ДС №1', 'age_level': 'S'},
            {'name': 'Звездочка', 'kindergarten_number': 'ДС №1', 'age_level': 'M'},
            {'name': 'Радуга', 'kindergarten_number': 'ДС №1', 'age_level': 'L'},
            {'name': 'Улыбка', 'kindergarten_number': 'ДС №2', 'age_level': 'S'},
            {'name': 'Смешинка', 'kindergarten_number': 'ДС №2', 'age_level': 'M'},
            {'name': 'Веселинка', 'kindergarten_number': 'ДС №2', 'age_level': 'L'},
        ]
        
        groups = []
        for group_data in groups_data:
            group, created = GroupKidGarden.objects.get_or_create(
                name=group_data['name'],
                kindergarten_number=group_data['kindergarten_number'],
                defaults={
                    'age_level': group_data['age_level']
                }
            )
            
            if created:
                groups.append(group)
                self.stdout.write(f'Создана группа: {group.name}')
            else:
                groups.append(group)
                self.stdout.write(f'Группа уже существует: {group.name}')
        
        # Привязываем группы к тренерам
        for i, trainer in enumerate(trainers):
            # Каждый тренер ведет 3 группы
            start_idx = i * 3
            trainer_groups = groups[start_idx:start_idx + 3]
            trainer.groups.set(trainer_groups)
            self.stdout.write(f'Тренер {trainer.full_name} ведет группы: {", ".join([g.name for g in trainer_groups])}')
        
        # Создаем родителей
        parents_data = [
            {'full_name': 'Сидорова Мария Петровна', 'phone': '+7 (999) 345-67-89'},
            {'full_name': 'Козлов Дмитрий Александрович', 'phone': '+7 (999) 456-78-90'},
            {'full_name': 'Морозова Елена Владимировна', 'phone': '+7 (999) 567-89-01'},
            {'full_name': 'Волков Сергей Николаевич', 'phone': '+7 (999) 678-90-12'},
            {'full_name': 'Новикова Ольга Игоревна', 'phone': '+7 (999) 789-01-23'},
            {'full_name': 'Лебедев Андрей Викторович', 'phone': '+7 (999) 890-12-34'},
        ]
        
        parents = []
        for parent_data in parents_data:
            parent, created = Parent.objects.get_or_create(
                full_name=parent_data['full_name'],
                defaults={'phone': parent_data['phone']}
            )
            
            if created:
                parents.append(parent)
                self.stdout.write(f'Создан родитель: {parent.full_name}')
            else:
                parents.append(parent)
                self.stdout.write(f'Родитель уже существует: {parent.full_name}')
        
        # Создаем детей
        children_names = [
            'Алексей', 'Мария', 'Дмитрий', 'Анна', 'Сергей', 'Елена',
            'Андрей', 'Ольга', 'Николай', 'Татьяна', 'Виктор', 'Ирина',
            'Михаил', 'Наталья', 'Павел', 'Юлия', 'Александр', 'Светлана',
            'Владимир', 'Екатерина', 'Игорь', 'Ангелина', 'Роман', 'Кристина'
        ]
        
        children = []
        for i, group in enumerate(groups):
            # В каждой группе 4 ребенка
            for j in range(4):
                child_index = i * 4 + j
                if child_index < len(children_names):
                    # Генерируем случайную дату рождения (3-6 лет)
                    years_old = random.randint(3, 6)
                    birth_date = date.today() - timedelta(days=years_old * 365 + random.randint(0, 365))
                    
                    child, created = Child.objects.get_or_create(
                        full_name=f"{children_names[child_index]} {parents[child_index % len(parents)].full_name.split()[0]}",
                        defaults={
                            'birth_date': birth_date,
                            'parent_name': parents[child_index % len(parents)],
                            'group': group,
                            'is_active': random.choice([True, True, True, False])  # 75% активных
                        }
                    )
                    
                    if created:
                        children.append(child)
                        self.stdout.write(f'Создан ребенок: {child.full_name} в группе {group.name}')
                    else:
                        children.append(child)
                        self.stdout.write(f'Ребенок уже существует: {child.full_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Тестовые данные созданы успешно!\n'
                f'Тренеров: {len(trainers)}\n'
                f'Групп: {len(groups)}\n'
                f'Родителей: {len(parents)}\n'
                f'Детей: {len(children)}'
            )
        ) 