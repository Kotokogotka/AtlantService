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

    Описывает группу в детском саду с указанием возрастной категории и привязанного тренера.

    Поля:
        name (str): Название группы.
        kindergarten_number (str): Номер детского сада.
        age_level (str): Возрастная категория (младшая, средняя, старшая).
        trainer (Trainer): Тренер, ведущий занятия в группе.
    """
    AGE_LEVELS = [
        ('S', 'Младшая'),
        ('M', 'Средняя'),
        ('L', 'Старшая')
    ]

    name = models.CharField(max_length=100, verbose_name="Название группы")
    kindergarten_number = models.CharField(max_length=20, verbose_name="Номер сада")
    age_level = models.CharField(max_length=1, choices=AGE_LEVELS, verbose_name="Возрастная группа")
    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, related_name='assigned_groups', verbose_name="Тренер в групе")

    def __str__(self):
        return f"{self.name}"
    
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
