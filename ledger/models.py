from django.db import models
from django.utils import timezone

from clients.models import Client
from suppliers.models import Supplier
from sabzi_mandi.models import CustomFloatField

class LedgerMixin(models.Model):
    tx_id = models.CharField(max_length=64)
    tx_time = models.DateTimeField(default=timezone.now, editable=False)
    tx_date = models.DateField()
    balance = CustomFloatField(default=0)
    bill_amount = CustomFloatField(default=0)
    payment_amount = CustomFloatField(default=0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

class ClientLedger(LedgerMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

class ClientLedgerEditable(LedgerMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = "ledger_clientledger_editable"

class SupplierLedger(LedgerMixin):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:
        db_table = "supplier_ledger"

class SupplierLedgerEditable(LedgerMixin):
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.SET_NULL)

    class Meta:
        managed = False
        db_table = "supplier_ledger_editable"
