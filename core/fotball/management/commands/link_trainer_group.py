from django.core.management.base import BaseCommand
from fotball.models import User, GroupKidGarden, Trainer


class Command(BaseCommand):
    help = 'Связывает тренера с группой для тестирования'

    def handle(self, *args, **options):
        try:
            # Находим тренера
            trainer_user = User.objects.get(username='trainer')
            trainer = trainer_user.linked_trainer
            
            if not trainer:
                self.stdout.write(
                    self.style.ERROR('Тренер не найден')
                )
                return
            
            # Находим группу
            group = GroupKidGarden.objects.get(name='Старшая группа')
            
            # Связываем тренера с группой
            trainer.groups.add(group)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Тренер {trainer.full_name} успешно связан с группой {group.name}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при связывании тренера с группой: {e}')
            )
