from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class User(models.Model):
    """
    Пользователь системы.

    Описывает пользователя с одной из ролей: администратор, тренер или родитель.
    При регистрации создаётся привязка к соответствующему тренеру и/или ребёнку.

    Поля:
        username (str): Логин пользователя.
        password (str): Пароль пользователя.
        role (str): Роль пользователя (администратор, тренер, родитель).
        linked_trainer (Trainer): Привязанный тренер (если есть).
        linked_child (Child): Привязанный ребёнок (если есть).
    """
    ROLE_CHOICES = [
            ('admin', 'Администратор'),
            ('trainer', 'Тренер'),
            ('parent', 'Родитель')
        ]

    username = models.CharField(max_length=150, unique=True, verbose_name="Логин пользователя")
    password = models.CharField(max_length=128, verbose_name="Пароль пользователя")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="Роль пользователя")
    linked_trainer = models.ForeignKey('Trainer', null=True, blank=True, on_delete=models.SET_NULL, related_name='users_linked')
    linked_child = models.ForeignKey('Child', null=True, blank=True, on_delete=models.SET_NULL, related_name='users_linked')

    def save(self, *args, **kwargs):
        # Если пароль не захэширован, сделать это
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        
        # Сохраняем пользователя
        super().save(*args, **kwargs)

        # Если это роль тренера и у него нет связанного тренера, то создаем его
        if self.role == 'trainer' and not self.linked_trainer:
            trainer, created = Trainer.objects.get_or_create(
                full_name=f'Тренер {self.username}',
                defaults={
                    'phone': ''
                }
            )
            self.linked_trainer = trainer
            self.save(update_fields=['linked_trainer'])
            print(f'Тренер {self.username} создан и привязан к пользователю')
        
        # Если это родитель и у него нет связанного ребенка, создаем его
        elif self.role == 'parent' and not self.linked_child:
            child, created = Child.objects.get_or_create(
                full_name=f'Ребенок {self.username}',
                defaults={
                    'birth_date': timezone.now().date(),
                    'is_active': True
                }
            )
            self.linked_child = child
            self.save(update_fields=['linked_child'])
            print(f'Ребенок {self.username} создан и привязан к пользователю')

    


    def get_trainer_groups(self):
        """Получение группы тренера"""
        if self.role == 'trainer' and self.linked_trainer:
            return self.linked_trainer.groups.all()
        return GroupKidGarden.objects.none()

    
    def get_trainer_info(self):
        """Получение информации о тренере"""
        if self.role == 'trainer' and self.linked_trainer:
            return {
                'full_name': self.linked_trainer.full_name,
                'phone': self.linked_trainer.phone,
                'groups': [
                    {
                        'name': group.name,
                        'kindergarten_number': group.kindergarten_number,
                        'age_level': group.get_age_level_display()
                    } for group in self.linked_trainer.groups.all()
                ],
                'groups_count': self.linked_trainer.groups.count()
            }
        return None
    
    def get_parent_info(self):
        """Получение информации о родителе"""
        if self.role == 'parent' and self.linked_child:
            return {
                'full_name': self.linked_child.full_name,
                'birth_date': self.linked_child.birth_date,
                'group': self.linked_child.group.name if self.linked_child.group else None,
                'is_active': self.linked_child.is_active
            }
        return None


    def __str__(self):
        return self.username
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username

    def is_active(self):
        return True

    def has_perm(self, perm, obj=None):
        return True

    def has_perms(self, perm_list, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    

class Trainer(models.Model):
    """
    Тренер.

    Содержит контактную информацию о тренере и детский сад, где он работает.

    Поля:
        full_name (str): ФИО тренера.
        phone (str): Контактный телефон.
        kindergarten (GroupKidGarden): Детский сад, где работает тренер.
    """
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    work_space = models.CharField(max_length=500, verbose_name="Номер сада и группы где ведет заниятие данный тренер")
    groups = models.ManyToManyField('GroupKidGarden', blank=True, related_name='trainers', verbose_name="Группы")

    def __str__(self):
        return self.full_name


class GroupKidGarden(models.Model):
    """
    Группа детского сада.

    Описывает группу в детском саду с указанием возрастной категории.
    Тренеры назначаются через связь ManyToMany в модели Trainer.

    Поля:
        name (str): Название группы.
        kindergarten_number (str): Номер детского сада.
        age_level (str): Возрастная категория (младшая, средняя, старшая).
    """
    AGE_LEVELS = [
        ('S', 'Младшая'),
        ('M', 'Средняя'),
        ('L', 'Старшая')
    ]

    name = models.CharField(max_length=100, verbose_name="Название группы")
    kindergarten_number = models.CharField(max_length=20, verbose_name="Номер сада")
    age_level = models.CharField(max_length=1, choices=AGE_LEVELS, verbose_name="Возрастная группа")

    def __str__(self):
        return f"{self.name}"
    
    def get_primary_trainer(self):
        """Получить основного тренера группы (первого из списка)"""
        trainers = self.trainers.all()
        return trainers.first() if trainers.exists() else None
    
class Parent(models.Model):
    """
    Родитель.
    
    Содержит контактную информацию о родителе и его детях.
    
    Поля:
        full_name (str): ФИО родителя.
        phone (str): Контактный телефон.
        children (ManyToMany): Дети родителя.
    """
    full_name = models.CharField(max_length=250, verbose_name="ФИО родителя")
    phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    children = models.ManyToManyField('Child', blank=True, related_name='parents', verbose_name="Дети")
    
    def __str__(self):
        return self.full_name


class Child(models.Model):
    """
    Ребёнок.

    Содержит контактную информацию о ребёнке и принадлежность к группе.

    Поля:
        full_name (str): ФИО ребёнка.
        birth_date (date): Дата рождения.
        group (GroupKidGarden): Группа, в которой занимается ребёнок.
        is_active (bool): Посещает ли тренировки.
    """
    full_name = models.CharField(max_length=250, verbose_name="ФИО ребенка")
    birth_date = models.DateField(verbose_name="Дата рождения")
    parent_name = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, related_name='linked_parent', verbose_name="Имя родителя")
    group = models.ForeignKey(GroupKidGarden, on_delete=models.SET_NULL, null=True, related_name='children_group', verbose_name="Группа ребенка")
    is_active = models.BooleanField(default=True, verbose_name="Посещает тренировки Да\Нет")

    def __str__(self):
        return f"{self.full_name}"

class Attendance(models.Model):
    """
    Посещаемость.

    Учет посещаемости ребёнка на тренировках. Заполняется тренером.

    Поля:
        child (Child): Ребёнок.
        group (GroupKidGarden): Группа.
        date (date): Дата тренировки.
        status (bool): Был/не был на тренировке.
        reason (str): Причина отсутствия (если не был).
    """
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendances', verbose_name="Имя ребенка")
    group = models.ForeignKey(GroupKidGarden, on_delete=models.CASCADE, related_name='attendances', verbose_name="Группа занимающегося")
    date = models.DateField(verbose_name="Дата посещения тренировки")
    status = models.BooleanField(verbose_name="Был\Не был")
    reason = models.TextField(null=True, blank=True, verbose_name="Причина отсутсвия")

    def __str__(self):
        return f"{self.child.full_name} - {self.date} ({'Был' if self.status else 'Не был'})"


class TrainingRate(models.Model):
    """
    Стоимость тренировки.

    Определяет стоимость одного занятия для каждой группы на определённую дату.

    Поля:
        group (GroupKidGarden): Группа.
        price (Decimal): Стоимость одного занятия.
        active_form (date): Дата начала действия цены.
    """
    group = models.ForeignKey('GroupKidGarden', 
                                 on_delete=models.CASCADE,
                                   related_name='training_rates', 
                                   verbose_name='Группа')
    price = models.DecimalField(max_digits=8,
                                 decimal_places=2,
                                verbose_name='Стоимость одного занятия')
    active_form = models.DateField(verbose_name="Дата начала действия цены")

    def __str__(self):
        return f"{self.group.name}: {self.price}руб. с {self.active_form}"


class MedicalCertificate(models.Model):
    """
    Справка о болезни ребенка.

    Содержит информацию о загруженной справке от родителя.

    Поля:
        child (Child): Ребёнок.
        parent (User): Родитель, загрузивший справку.
        certificate_file (FileField): Файл справки.
        date_from (date): Дата начала болезни.
        date_to (date): Дата окончания болезни.
        note (str): Примечание.
        absence_reason (str): Причина отсутствия для перерасчета.
        uploaded_at (datetime): Дата загрузки.
        status (str): Статус справки (pending, approved, rejected).
        admin_comment (str): Комментарий администратора.
        cost_per_lesson (Decimal): Стоимость одного занятия.
        total_cost (Decimal): Общая стоимость к оплате.
    """
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена')
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='medical_certificates', verbose_name="Ребенок")
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_certificates', verbose_name="Родитель")
    certificate_file = models.FileField(upload_to='medical_certificates/%Y/%m/%d/', verbose_name="Файл справки", null=True, blank=True)
    date_from = models.DateField(verbose_name="Дата начала болезни")
    date_to = models.DateField(verbose_name="Дата окончания болезни")
    note = models.TextField(verbose_name="Примечание", help_text="Дополнительная информация", blank=True, default='')
    absence_reason = models.TextField(verbose_name="Причина отсутствия", help_text="Описание причины отсутствия для перерасчета", default='')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    admin_comment = models.TextField(null=True, blank=True, verbose_name="Комментарий администратора")
    cost_per_lesson = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, verbose_name="Стоимость одного занятия")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Общая стоимость к оплате")

    def save(self, *args, **kwargs):
        # Автоматически рассчитываем общую стоимость
        if self.date_from and self.date_to:
            # Преобразуем строки в объекты date если необходимо
            if isinstance(self.date_from, str):
                from datetime import datetime
                self.date_from = datetime.strptime(self.date_from, '%Y-%m-%d').date()
            if isinstance(self.date_to, str):
                from datetime import datetime
                self.date_to = datetime.strptime(self.date_to, '%Y-%m-%d').date()
            
            days_absent = (self.date_to - self.date_from).days + 1
            # Ограничиваем максимальное количество дней (например, 365 дней)
            days_absent = min(days_absent, 365)
            self.total_cost = self.cost_per_lesson * days_absent
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Справка {self.child.full_name} от {self.uploaded_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Справка о болезни"
        verbose_name_plural = "Справки о болезнях"
        ordering = ['-uploaded_at']


class TrainingSchedule(models.Model):
    """
    Расписание тренировок.

    Содержит информацию о запланированных тренировках для групп.

    Поля:
        group (GroupKidGarden): Группа.
        date (date): Дата тренировки.
        time (time): Время тренировки.
        duration_minutes (int): Продолжительность в минутах.
        location (str): Место проведения.
        trainer (Trainer): Тренер.
        status (str): Статус тренировки (scheduled, completed, cancelled).
        notes (str): Дополнительные заметки.
        created_by (User): Администратор, создавший тренировку.
        created_at (datetime): Дата создания записи.
        updated_at (datetime): Дата последнего изменения.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Запланирована'),
        ('completed', 'Проведена'),
        ('cancelled', 'Отменена')
    ]

    group = models.ForeignKey(GroupKidGarden, on_delete=models.CASCADE, related_name='scheduled_trainings', verbose_name="Группа")
    date = models.DateField(verbose_name="Дата тренировки")
    time = models.TimeField(verbose_name="Время тренировки")
    duration_minutes = models.PositiveIntegerField(default=40, verbose_name="Продолжительность (минуты)")
    location = models.CharField(max_length=200, blank=True, default='', verbose_name="Место проведения")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='scheduled_trainings', verbose_name="Тренер")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус")
    notes = models.TextField(blank=True, default='', verbose_name="Заметки")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_trainings', verbose_name="Создано администратором")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    def __str__(self):
        return f"{self.group.name} - {self.date.strftime('%d.%m.%Y')} в {self.time.strftime('%H:%M')}"

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Расписание тренировок"
        ordering = ['date', 'time']
        unique_together = ['group', 'date', 'time']  # Предотвращаем дублирование


class TrainerComment(models.Model):
    """
    Комментарии тренера о ребенке.
    
    Тренер может оставлять комментарии о прогрессе, поведении или других аспектах.
    """
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='comments', verbose_name="Тренер")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='trainer_comments', verbose_name="Ребенок")
    comment_text = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    
    def __str__(self):
        return f"Комментарий для {self.child.full_name} от {self.trainer.full_name}"
    
    class Meta:
        verbose_name = "Комментарий тренера"
        verbose_name_plural = "Комментарии тренеров"
        ordering = ['-created_at']


class ScheduleChangeNotification(models.Model):
    """
    Уведомления об изменениях в расписании.
    
    Создается автоматически при изменении даты/времени тренировки.
    """
    NOTIFICATION_TYPES = [
        ('date_changed', 'Изменена дата'),
        ('time_changed', 'Изменено время'),
        ('both_changed', 'Изменены дата и время'),
        ('cancelled', 'Тренировка отменена')
    ]

    training = models.ForeignKey(TrainingSchedule, on_delete=models.CASCADE, related_name='change_notifications', verbose_name="Тренировка")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Тип изменения")
    old_date = models.DateField(null=True, blank=True, verbose_name="Старая дата")
    new_date = models.DateField(null=True, blank=True, verbose_name="Новая дата")
    old_time = models.TimeField(null=True, blank=True, verbose_name="Старое время")
    new_time = models.TimeField(null=True, blank=True, verbose_name="Новое время")
    message = models.TextField(verbose_name="Сообщение для пользователей")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notifications', verbose_name="Создано администратором")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_read_by_trainer = models.BooleanField(default=False, verbose_name="Прочитано тренером")
    
    def __str__(self):
        return f"Изменение тренировки {self.training.group.name} - {self.get_notification_type_display()}"
    
    def get_affected_parents(self):
        """Получить родителей, которых касается это изменение"""
        return User.objects.filter(
            role='parent',
            linked_child__group=self.training.group,
            linked_child__is_active=True
        )
    
    def get_affected_trainers(self):
        """Получить тренеров, которых касается это изменение"""
        return User.objects.filter(
            role='trainer',
            linked_trainer=self.training.trainer
        )
    
        class Meta:
            verbose_name = "Уведомление об изменении расписания"
            verbose_name_plural = "Уведомления об изменениях расписания"
            ordering = ['-created_at']


class NotificationRead(models.Model):
    """Модель для отслеживания прочитанных уведомлений пользователями"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    notification = models.ForeignKey(ScheduleChangeNotification, on_delete=models.CASCADE, verbose_name="Уведомление")
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Время прочтения")
    
    class Meta:
        unique_together = ('user', 'notification')
        verbose_name = "Прочитанное уведомление"
        verbose_name_plural = "Прочитанные уведомления"
        ordering = ['-read_at']
    
    def __str__(self):
        return f"{self.user.username} прочитал уведомление {self.notification.id}"
