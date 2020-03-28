from django.db import models
from django.utils import timezone

from clients.models import Client

class ClientLedger(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    tx_id = models.CharField(max_length=64)
    tx_time = models.DateTimeField(default=timezone.now, editable=False)
    tx_date = models.DateField()
    balance = models.IntegerField(default=0)
    bill_amount = models.IntegerField(default=0)
    payment_amount = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
