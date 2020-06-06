# Generated by Django 3.0.1 on 2020-06-06 17:15

from django.db import migrations, models
import sabzi_mandi.models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_auto_20200329_0119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientpayment',
            name='amount',
            field=models.FloatField(validators=[sabzi_mandi.models.PaymentValidator(0)]),
        ),
        migrations.AlterField(
            model_name='supplierpayment',
            name='amount',
            field=models.FloatField(validators=[sabzi_mandi.models.PaymentValidator(0)]),
        ),
    ]
