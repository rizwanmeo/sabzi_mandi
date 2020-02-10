from django.contrib import admin
from django.utils.html import format_html

from .models import *
from clients.models import Client
from suppliers.models import Supplier
from client_bills.models import ClientBill, ClientPayment

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

class ClientBillAdmin(admin.ModelAdmin):
    list_display = ['client', 'is_draft', 'bill_time']

class ClientPaymentAdmin(admin.ModelAdmin):
    list_display = ['client', 'amount', 'payment_time']

admin.site.register(Shop, ShopAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Item)
admin.site.register(ClientBill, ClientBillAdmin)
admin.site.register(ClientPayment, ClientPaymentAdmin)
