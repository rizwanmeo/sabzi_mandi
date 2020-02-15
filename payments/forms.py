from django.forms import ModelForm

from .models import *

class SupplierPaymentForm(ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['supplier', 'amount', 'payment_type', 'description']

    def __init__(self, *args, **kwargs):
        super(SupplierPaymentForm, self).__init__(*args, **kwargs)
        # Item choices
        #item_choices = [("", "Select an Item")]
        #item_choices += list(Item.objects.values_list("id", "name"))
        self.fields['supplier'].widget.attrs['class'] = 'fstdropdown-select'
