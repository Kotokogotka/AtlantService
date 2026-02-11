# Generated manually for ParentCommentRead

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fotball', '0023_alter_schedulechangenotification_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentCommentRead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_read_at', models.DateTimeField(verbose_name='Время последнего просмотра')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fotball.child', verbose_name='Ребёнок')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fotball.user', verbose_name='Родитель')),
            ],
            options={
                'verbose_name': 'Прочитанные комментарии (родитель)',
                'verbose_name_plural': 'Прочитанные комментарии (родители)',
                'unique_together': {('user', 'child')},
            },
        ),
    ]
