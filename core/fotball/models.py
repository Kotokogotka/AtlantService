from django.db import models

class User(models.Model):
    """
    Модель пользователя где задается одна из ролей
    В данной модели происходит регистрация пользователя и 
    создается привязка к саду и тренеру.
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
    Контактная информация о тренера и садах где работает тренер
    """
    full_name = models.CharField(max_length=200,  verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    work_space = models.CharField(max_length=500, verbose_name="Номер сада и группы где ведет заниятие данный тренер")

    def __str__(self):
        return self.full_name


class GroupKidGarden(models.Model):
    """
    Информацмия о группах в детском саду с привязкой к тренеру
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
    Контактная информация о ребенке
    """
    full_name = models.CharField(max_length=250, verbose_name="ФИО ребенка")
    birth_date = models.DateField(verbose_name="Дата рождения")
    parent_name = models.CharField(max_length=250, verbose_name="Имя родителя")
    phone_number = models.CharField(max_length=12, verbose_name="Номер телефона родителя")
    group = models.ForeignKey(GroupKidGarden, on_delete=models.SET_NULL, null=True, related_name='children', verbose_name="Группа ребенка")
    is_active = models.BooleanField(default=True, verbose_name="Посещает тренировки Да\Нет")


class Attendance(models.Model):
    """
    Учет посещаемости, данные заполняются тренером о присутсвиии или отсутсвии ребенка на тренировке
    """
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendances', verbose_name="Имя ребенка")
    group = models.ForeignKey(GroupKidGarden, on_delete=models.CASCADE, related_name='attendances', verbose_name="Группа занимающегося")
    date = models.DateField(verbose_name="Дата посещения тренировки")
    status = models.BooleanField(verbose_name="Был\Не был")
    reason = models.TextField(null=True, blank=True, verbose_name="Причина отсутсвия")


class TrainingRate(models.Model):
    """
    Определение стоимости для каждой группы в отдельности
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
