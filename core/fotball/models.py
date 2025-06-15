from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
            ('admin', 'Администратор'),
            ('trainer', 'Тренер'),
            ('parent', 'Родитель')
        ]

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    linked_trainer = models.ForeignKey('Trainer', null=True, blank=True, on_delete=models.SET_NULL)
    linked_child = models.ForeignKey('Child', null=True, blank=True, on_delete=models.SET_NULL)


class Trainer(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')


class Group(models.Model):
    AGE_LEVELS = [
        ('S', 'Младшая'),
        ('M', 'Средняя'),
        ('L', 'Старшая')
    ]

    name = models.CharField(max_length=100)
    kindergarten_number = models.CharField(max_length=20)
    age_level = models.CharField(max_length=1, choices=AGE_LEVELS)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)



