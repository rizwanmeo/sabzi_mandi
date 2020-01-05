import os
import datetime
from io import StringIO, BytesIO

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage as storage
from PIL import Image

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

def validate_file_ext(value):
    if value.name.endswith('.png') or value.name.endswith('.jpg'):
        limit = 1024 * 1024
        if value.size > limit:
            raise ValidationError('File too large. Size should not exceed 1 MB.')
        else:
            return
    raise ValidationError(u'Unsupported file, You can upload only png, jpeg and jpg files')

def content_file_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (datetime.datetime.now().strftime('%s'), ext)
    return os.path.join('uploads', filename)


class Shop(UpdatedInfo):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=264, blank=True, null=True)
    logo = models.ImageField(upload_to =content_file_name, validators=[validate_file_ext], blank=True, null=True)
    logo_thumbnail = models.ImageField(upload_to='shops_thumbs/', editable=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def make_thumbnail(self):
        """
        Create and save the thumbnail for the photo (simple resize with PIL).
        """
        fh = storage.open(self.logo.name, 'rb')
        try:
            image = Image.open(fh)
        except Exception as e:
            print("Exception as e: ", e)
            return False

        image.thumbnail((200, 200), Image.ANTIALIAS)
        fh.close()

        # Path to save to, name, and extension
        thumb_name, thumb_extension = os.path.splitext(self.logo.name)
        thumb_extension = thumb_extension.lower()

        thumb_filename = thumb_name + '_thumb' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False    # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        image.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

        # Load a ContentFile into the thumbnail field so it gets saved
        self.logo_thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=True)
        temp_thumb.close()

        return True

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

class ClientBill(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now, editable=False)
    bill_time = models.DateTimeField(default=timezone.now, editable=False)
    is_draft = models.BooleanField(default=False)

class BillDetail(models.Model):
    bill = models.ForeignKey(ClientBill, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    unit = models.CharField(max_length=1, choices=[("k", "KG"), ("i", "Item")])
    rate = models.FloatField(default=0)

class ClientPayment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    payment_time = models.DateTimeField(default=timezone.now, editable=False)
