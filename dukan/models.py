from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

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
    opening_balance = models.FloatField(default=0)

    class Meta:
        abstract = True

class Item(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Shop(UpdatedInfo):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=264, blank=True, null=True)
    logo = models.ImageField(upload_to ='uploads/', blank=True, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Supplier(BasicInfo):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Client(BasicInfo):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    current_balance = models.FloatField(default=0)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Bill(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.IntegerField(choices=[(1, "KG"), (2, "Nag")])
    rate = models.FloatField(default=0)
    bill_time = models.DateTimeField(default=timezone.now, editable=False)

class Payment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    payment_time = models.DateTimeField(default=timezone.now, editable=False)
