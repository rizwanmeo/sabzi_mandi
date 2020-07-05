# Generated by Django 3.0.1 on 2020-07-05 15:52

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import sabzi_mandi.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientLedger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tx_id', models.CharField(max_length=64)),
                ('tx_time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('tx_date', models.DateField()),
                ('balance', sabzi_mandi.models.CustomFloatField(default=0)),
                ('bill_amount', sabzi_mandi.models.CustomFloatField(default=0)),
                ('payment_amount', sabzi_mandi.models.CustomFloatField(default=0)),
                ('description', models.TextField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.Client')),
            ],
        ),
    ]
