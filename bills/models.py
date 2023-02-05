from django.db import models
from django.utils import timezone

from sabzi_mandi.models import CustomFloatField
from shops.models import Shop, Item
from clients.models import Client
from suppliers.models import Supplier
from payments.models import ClientPayment


class ClientBill(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    is_draft = models.BooleanField(default=False)
    bill_date = models.DateField()
    balance = CustomFloatField(default=0)
    billed_amount = CustomFloatField(default=0)
    payment = models.ForeignKey(ClientPayment, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        db_table  = "client_bill"

class BillDetail(models.Model):
    bill = models.ForeignKey(ClientBill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.CharField(max_length=1, choices=[("k", "KG"), ("i", "Count")])
    rate = CustomFloatField()
    item_count = CustomFloatField()

    class Meta:
        db_table = "client_bill_detail"

class SupplierBill(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    is_draft = models.BooleanField(default=False)
    bill_date = models.DateField()
    balance = CustomFloatField(default=0)
    billed_amount = CustomFloatField(default=0)
    other_expence = models.JSONField(default=dict)
    cash = CustomFloatField(default=0)

    class Meta:
        db_table  = "supplier_bill"


class SupplierBillDetail(models.Model):
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.CharField(max_length=1, choices=[("k", "KG"), ("i", "Count")])
    rate = CustomFloatField()
    item_count = CustomFloatField()
    weight = CustomFloatField(null=True, blank=True)

    class Meta:
        db_table = "supplier_bill_detail"
