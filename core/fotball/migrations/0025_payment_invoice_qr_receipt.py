# Generated manually: QR на счёт + чеки об оплате

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fotball', '0024_parentcommentread'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentinvoice',
            name='qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='payment_qr/', verbose_name='QR-код для оплаты'),
        ),
        migrations.CreateModel(
            name='PaymentReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_file', models.FileField(upload_to='payment_receipts/%Y/%m/', verbose_name='Файл чека')),
                ('status', models.CharField(choices=[('pending', 'На проверке'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending', max_length=20, verbose_name='Статус')),
                ('admin_comment', models.TextField(blank=True, verbose_name='Комментарий администратора')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата проверки')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='fotball.paymentinvoice', verbose_name='Счет')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_receipts', to='fotball.user', verbose_name='Проверил')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fotball.user', verbose_name='Загрузил (родитель)')),
            ],
            options={
                'verbose_name': 'Чек об оплате',
                'verbose_name_plural': 'Чеки об оплате',
                'ordering': ['-created_at'],
            },
        ),
    ]
