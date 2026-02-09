# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date

from fotball.models import User, Trainer, Parent, Child, GroupKidGarden


# Учётные данные для теста всех ролей (логин / пароль)
TEST_CREDENTIALS = {
    'admin': ('admin', 'admin123'),
    'parent': ('parent', 'parent123'),
    'trainer': ('trainer', 'trainer123'),
}


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей для всех ролей: Админ, Родитель, Тренер'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать пользователей (удалить и создать заново)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        for role, (username, password) in TEST_CREDENTIALS.items():
            self.create_or_update_user(role, username, password, force=force)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Учётные данные для теста ==='))
        self.stdout.write('  Админ:   логин admin   пароль admin123')
        self.stdout.write('  Родитель: логин parent  пароль parent123')
        self.stdout.write('  Тренер:  логин trainer пароль trainer123')
        self.stdout.write('')

    def create_or_update_user(self, role, username, password, force=False):
        if force and User.objects.filter(username=username).exists():
            User.objects.filter(username=username).delete()
            self.stdout.write(self.style.WARNING(f'Удалён существующий пользователь: {username}'))

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Пользователь уже существует: {username} ({role})'))
            return

        if role == 'admin':
            User.objects.create(username=username, password=password, role='admin')
            self.stdout.write(self.style.SUCCESS(f'Создан Админ: {username} / {password}'))

        elif role == 'trainer':
            user = User.objects.create(username=username, password=password, role='trainer')
            # save() создаёт linked_trainer автоматически
            self.stdout.write(self.style.SUCCESS(f'Создан Тренер: {username} / {password}'))

        elif role == 'parent':
            parent = Parent.objects.create(
                full_name='Тестовый родитель (Мария Иванова)',
                phone='+7 (999) 000-00-00',
            )
            group, _ = GroupKidGarden.objects.get_or_create(
                name='Старшая группа',
                defaults={'kindergarten_number': '1', 'age_level': 'L'},
            )
            child = Child.objects.create(
                full_name='Тестовый ребёнок (Алексей Иванов)',
                birth_date=date(2018, 5, 15),
                parent_name=parent,
                group=group,
                is_active=True,
            )
            User.objects.create(
                username=username,
                password=password,
                role='parent',
                linked_child=child,
            )
            self.stdout.write(self.style.SUCCESS(f'Создан Родитель: {username} / {password} (ребёнок: {child.full_name}, группа: {group.name})'))
