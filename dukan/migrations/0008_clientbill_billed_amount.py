# Generated by Django 3.0.1 on 2020-01-12 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dukan', '0007_auto_20200108_0050'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientbill',
            name='billed_amount',
            field=models.FloatField(default=0),
        ),
    ]
