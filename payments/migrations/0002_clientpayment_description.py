# Generated by Django 3.0.1 on 2020-02-10 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientpayment',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
