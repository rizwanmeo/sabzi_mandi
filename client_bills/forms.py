from django import forms

from .models import *

class ClientBillForm(forms.ModelForm):
    payment = forms.FloatField()
    
    class Meta:
        model = ClientBill
        fields = ["client", "bill_date"]


class ClientBillUpdateForm(forms.ModelForm):
    class Meta:
        model = ClientBill
        fields = ["bill_date"]


class BillDetailForm(forms.ModelForm):
    class Meta:
        model = BillDetail
        fields = ['item', 'unit', 'rate', 'item_count']

    def __init__(self, *args, **kwargs):
        super(BillDetailForm, self).__init__(*args, **kwargs)
        # Item choices
        item_choices = [("", "Select an Item")]
        item_choices += list(Item.objects.values_list("id", "name"))
        self.fields['item'].widget.attrs['class'] = 'fstdropdown-select'
        self.fields['unit'].widget.attrs['class'] = 'fstdropdown-select'
        self.fields['unit'].widget.attrs['data-searchdisable'] = "true"
        self.fields['item'].choices = item_choices
        self.fields['unit'].choices = self.fields['unit'].choices[1:]
