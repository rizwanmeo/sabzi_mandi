from django.db import models
from django.utils import timezone

from shops.models import Shop, Item
from sabzi_mandi.models import BasicInfo
from sabzi_mandi.models import CustomFloatField


class Supplier(BasicInfo):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    class Meta:
        unique_together = [('shop', 'name'), ('shop', 'identifier')]

class SupplierBill(models.Model):
    Supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    is_draft = models.BooleanField(default=False)
    bill_date = models.DateField()
    balance = CustomFloatField(default=0)
    billed_amount = CustomFloatField(default=0)
    other_expence = models.JSONField(default=dict)


class SupplierBillDetail(models.Model):
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.CharField(max_length=1, choices=[("k", "KG"), ("i", "Count")])
    rate = CustomFloatField()
    item_count = CustomFloatField()
