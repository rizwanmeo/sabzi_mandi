# Generated by Django 3.0.1 on 2020-02-15 20:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20200216_0138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientpayment',
            name='payment_time',
        ),
        migrations.RemoveField(
            model_name='supplierpayment',
            name='payment_time',
        ),
    ]
