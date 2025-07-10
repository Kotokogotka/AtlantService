from django.db import models

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


class Trainer(models.Model):
    """
    Тренер.

    Содержит контактную информацию о тренере и список детских садов/групп, где он работает.

    Поля:
        full_name (str): ФИО тренера.
        phone (str): Контактный телефон.
        work_space (str): Номера садов и групп, где ведёт занятия.
    """
    full_name = models.CharField(max_length=200,  verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    work_space = models.CharField(max_length=500, verbose_name="Номер сада и группы где ведет заниятие данный тренер")

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
    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, related_name='groups', verbose_name="Тренер в групе")


class Child(models.Model):
    """
    Ребёнок.

    Содержит контактную информацию о ребёнке и его родителе, а также принадлежность к группе.

    Поля:
        full_name (str): ФИО ребёнка.
        birth_date (date): Дата рождения.
        parent_name (str): Имя родителя.
        phone_number (str): Телефон родителя.
        group (GroupKidGarden): Группа, в которой занимается ребёнок.
        is_active (bool): Посещает ли тренировки.
    """
    full_name = models.CharField(max_length=250, verbose_name="ФИО ребенка")
    birth_date = models.DateField(verbose_name="Дата рождения")
    parent_name = models.CharField(max_length=250, verbose_name="Имя родителя")
    phone_number = models.CharField(max_length=12, verbose_name="Номер телефона родителя")
    group = models.ForeignKey(GroupKidGarden, on_delete=models.SET_NULL, null=True, related_name='children', verbose_name="Группа ребенка")
    is_active = models.BooleanField(default=True, verbose_name="Посещает тренировки Да\Нет")


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
