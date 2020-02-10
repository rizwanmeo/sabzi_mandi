import os
import datetime
from io import StringIO, BytesIO

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage as storage
from PIL import Image

from sabzi_mandi.models import UpdatedInfo, BasicInfo

class Item(models.Model):
    name = models.CharField(max_length=200, unique=True)

def validate_file_ext(value):
    ext = value.name.split(".")[-1]
    if ext not in ['.png', '.jpg', '.jpeg']:
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
    phone = models.CharField(max_length=16, blank=True, null=True)
    is_default = models.BooleanField(default=False)

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
