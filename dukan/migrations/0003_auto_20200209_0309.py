# Generated by Django 3.0.1 on 2020-02-08 22:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dukan', '0002_supplierpayment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='supplierpayment',
            old_name='paymentType',
            new_name='payment_type',
        ),
    ]
