from django.core.management.base import BaseCommand
from fotball.models import User


class Command(BaseCommand):
    help = 'Создает тестового пользователя-тренера'

    def handle(self, *args, **options):
        try:
            # Проверяем, существует ли уже тестовый пользователь
            if User.objects.filter(username='trainer').exists():
                self.stdout.write(
                    self.style.WARNING('Тестовый пользователь уже существует')
                )
                return

            # Создаем тестового пользователя-тренера
            user = User.objects.create(
                username='trainer',
                password='trainer123',  # Пароль будет автоматически захэширован
                role='trainer'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Тестовый пользователь создан успешно!\n'
                    f'Логин: {user.username}\n'
                    f'Пароль: trainer123\n'
                    f'Роль: {user.get_role_display()}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании пользователя: {e}')
            ) 