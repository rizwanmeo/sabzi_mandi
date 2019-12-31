from django.contrib import admin
from django.utils.html import format_html

from dukan.models import *

class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'address', 'image_tag']
    readonly_fields = ['created_time', 'last_modified']

    def image_tag(self, obj):
        return format_html('<img src="{}" />'.format(obj.logo.url))

    image_tag.short_description = 'Logo'

class SupplierAdmin(admin.ModelAdmin):
    list_display = ['shop', 'name', 'cnic', 'phone', 'address', 'opening_balance']
    readonly_fields = ['created_time', 'last_modified']

class ClientAdmin(admin.ModelAdmin):
    list_display = ['shop', 'name', 'cnic', 'phone', 'address', 'opening_balance']
    readonly_fields = ['created_time', 'last_modified']

class BillAdmin(admin.ModelAdmin):
    list_display = ['client', 'item', 'unit', 'rate', 'bill_time']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['client', 'amount', 'payment_time']

admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Item)
admin.site.register(Bill, BillAdmin)
admin.site.register(Payment, PaymentAdmin)
