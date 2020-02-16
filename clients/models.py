from django.db import models

from shops.models import Shop
from sabzi_mandi.models import BasicInfo

class Client(BasicInfo):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
