# -*- coding: utf-8 -*-
"""Создаёт начальных админов при первом запуске (для деплоя на Render и т.п.)."""
from django.core.management.base import BaseCommand
from fotball.models import User

# Логин / пароль для начальных суперпользователей
INITIAL_SUPERUSERS = [
    ('Kotokogotka', 'Qwe114qwe114'),
    ('Osip', 'Qwe114qwe114'),
]


class Command(BaseCommand):
    help = 'Создаёт начальных администраторов (Kotokogotka, Osip), если их ещё нет'

    def handle(self, *args, **options):
        for username, password in INITIAL_SUPERUSERS:
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Пользователь уже существует: {username}'))
                continue
            User.objects.create(username=username, password=password, role='admin')
            self.stdout.write(self.style.SUCCESS(f'Создан администратор: {username}'))
