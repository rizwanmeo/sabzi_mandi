# Generated by Django 3.0.1 on 2020-07-05 15:52

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import sabzi_mandi.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('ledger', '0001_initial'),
    ]

    sql = """
        CREATE OR REPLACE VIEW ledger_clientledger_editable AS
        SELECT l.* 
        FROM ledger_clientledger AS l 
        JOIN (SELECT MAX(id) AS id, client_id FROM ledger_clientledger GROUP BY client_id) AS r 
        USING(id);
    """

    operations = [
        migrations.RunSQL(sql)
    ]
