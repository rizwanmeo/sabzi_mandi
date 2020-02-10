from django.db import models
from django.utils import timezone

from shops.models import Shop, Item
from clients.models import Client
from payments.models import ClientPayment


class ClientBill(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    bill_time = models.DateTimeField(default=timezone.now, editable=False)
    is_draft = models.BooleanField(default=False)
    balance = models.IntegerField(default=0)
    billed_amount = models.IntegerField(default=0)
    payment = models.ForeignKey(ClientPayment, blank=True, null=True, on_delete=models.CASCADE)

class BillDetail(models.Model):
    bill = models.ForeignKey(ClientBill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.CharField(max_length=1, choices=[("k", "KG"), ("i", "Item")])
    rate = models.IntegerField()
    item_count = models.IntegerField()
