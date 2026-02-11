# Generated manually: распознанные данные с чека

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fotball', '0025_payment_invoice_qr_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentreceipt',
            name='parsed_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Сумма с чека'),
        ),
        migrations.AddField(
            model_name='paymentreceipt',
            name='parsed_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата с чека'),
        ),
        migrations.AddField(
            model_name='paymentreceipt',
            name='parsed_bank',
            field=models.CharField(blank=True, choices=[('sber', 'Сбербанк'), ('vtb', 'ВТБ'), ('ozon', 'Озон'), ('tbank', 'Т-Банк'), ('alfa', 'Альфа-Банк'), ('other', 'Другой')], max_length=20, null=True, verbose_name='Банк с чека'),
        ),
        migrations.AddField(
            model_name='paymentreceipt',
            name='parsed_raw_preview',
            field=models.TextField(blank=True, verbose_name='Фрагмент текста чека (для проверки)'),
        ),
        migrations.AddField(
            model_name='paymentreceipt',
            name='amount_match',
            field=models.BooleanField(blank=True, null=True, verbose_name='Сумма совпадает со счётом'),
        ),
    ]
