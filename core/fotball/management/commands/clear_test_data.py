"""
Команда для очистки тестовых данных
"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Очистка тестовых данных о группах, детях, тренировках и посещениях'

    def handle(self, *args, **options):
        self.stdout.write("🗑️ Очистка тестовых данных...")
        
        # Используем прямые SQL запросы для избежания каскадных проблем
        with connection.cursor() as cursor:
            try:
                # Получаем количество записей
                cursor.execute("SELECT COUNT(*) FROM fotball_attendance")
                attendance_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM fotball_trainingschedule")
                schedule_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM fotball_child")
                children_count = cursor.fetchone()[0]
                
                # Проверяем существование связанных таблиц
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'fotball_trainer_groups'
                    )
                """)
                trainer_groups_exists = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'fotball_paymentsettings'
                    )
                """)
                payment_settings_exists = cursor.fetchone()[0]
                
                if trainer_groups_exists:
                    cursor.execute("SELECT COUNT(*) FROM fotball_trainer_groups")
                    trainer_groups_count = cursor.fetchone()[0]
                else:
                    trainer_groups_count = 0
                
                if payment_settings_exists:
                    cursor.execute("SELECT COUNT(*) FROM fotball_paymentsettings")
                    payment_settings_count = cursor.fetchone()[0]
                else:
                    payment_settings_count = 0
                
                cursor.execute("SELECT COUNT(*) FROM fotball_groupkidgarden")
                groups_count = cursor.fetchone()[0]
                
                # Удаляем в правильном порядке
                cursor.execute("DELETE FROM fotball_attendance")
                self.stdout.write(f"  ✅ Удалено посещений: {attendance_count}")
                
                cursor.execute("DELETE FROM fotball_trainingschedule")
                self.stdout.write(f"  ✅ Удалено расписаний: {schedule_count}")
                
                cursor.execute("DELETE FROM fotball_child")
                self.stdout.write(f"  ✅ Удалено детей: {children_count}")
                
                # Удаляем связи тренеров с группами
                if trainer_groups_exists and trainer_groups_count > 0:
                    cursor.execute("DELETE FROM fotball_trainer_groups")
                    self.stdout.write(f"  ✅ Удалено связей тренер-группа: {trainer_groups_count}")
                
                # Удаляем настройки оплаты (они ссылаются на группы)
                if payment_settings_exists and payment_settings_count > 0:
                    cursor.execute("DELETE FROM fotball_paymentsettings")
                    self.stdout.write(f"  ✅ Удалено настроек оплаты: {payment_settings_count}")
                
                cursor.execute("DELETE FROM fotball_groupkidgarden")
                self.stdout.write(f"  ✅ Удалено групп: {groups_count}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Ошибка: {e}"))
                return
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Данные успешно очищены!"))
        self.stdout.write(self.style.WARNING("Теперь запустите: python manage.py create_attendance_data"))

