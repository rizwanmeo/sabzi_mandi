from django.db import models

from clients.models import Client
from suppliers.models import Supplier
from sabzi_mandi.models import PaymentMixin

class SupplierPayment(PaymentMixin):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=1, default="i", choices=[("i", "Payment From Supplier"), ("o", "Payment To Supplier")])
    description = models.TextField(blank=True, null=True)

class ClientPayment(PaymentMixin):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
