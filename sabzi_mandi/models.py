from django.db import models
from django.utils import timezone

class UpdatedInfo(models.Model):
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    last_modified = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True

class BasicInfo(UpdatedInfo):
    name = models.CharField(max_length=200)
    cnic = models.CharField(max_length=16, blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    address = models.CharField(max_length=264, blank=True, null=True)
    opening_balance = models.IntegerField(default=0)

    class Meta:
        abstract = True

class PaymentMixin(models.Model):
    amount = models.IntegerField(default=0)
    payment_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True
