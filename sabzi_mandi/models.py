import datetime

from django.db import models
from django.utils import timezone
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


class CustomFloatField(models.FloatField):
    def __init__(self, *args, **kwargs):
        super(CustomFloatField, self).__init__(*args, **kwargs)

    def clean(self, value, model_instance):
        value = super(CustomFloatField, self).clean(value, model_instance)
        return round(value, 2)


@deconstructible
class PaymentValidator(BaseValidator):
    message = _('Ensure this value is not equal to %(limit_value)s.')
    code = 'min_value'

    def compare(self, a, b):
        return a == b


class UpdatedInfo(models.Model):
    created_time = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True

class BasicInfo(UpdatedInfo):
    name = models.CharField(max_length=200)
    cnic = models.CharField(max_length=16, blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    address = models.CharField(max_length=264, blank=True, null=True)
    opening_balance = CustomFloatField()
    current_balance = CustomFloatField()
    identifier = models.IntegerField()

    class Meta:
        abstract = True

class PaymentMixin(models.Model):
    amount = CustomFloatField(validators=[PaymentValidator(0)])
    is_draft = models.BooleanField(default=False)
    payment_date = models.DateField()
    payment_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True
