from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

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

    def clean(self):
        bill_date = self.cleaned_data['bill_date']

        try:
            qs = ClientBill.objects.filter(client=self.instance.client)
            obj = qs.exclude(pk=self.instance.pk).latest('bill_date')
            if obj.bill_date > bill_date:
                raise ValidationError({
                    'bill_date': ValidationError(_('You cannot select less then %s.' % obj.bill_date)),
                })
        except ClientBill.DoesNotExist:
            pass

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


class SupplierBillForm(forms.ModelForm):
    farmer_name       = forms.CharField(max_length=256, required=False)
    is_cash           = forms.CharField(max_length=1, required=True)
    payment           = forms.FloatField(required=False)
    commission_amount = forms.FloatField(required=True)
    unloading_cost    = forms.FloatField(required=True)
    vahicle_rent      = forms.FloatField(required=False)
    farmer_wages      = forms.FloatField(required=False)
    labour_cost       = forms.FloatField(required=False)
    begs_amount       = forms.FloatField(required=False)
    market_tax        = forms.FloatField(required=False)
    beg_rope          = forms.FloatField(required=False)
    cash_amount       = forms.FloatField(required=False)

    class Meta:
        model = SupplierBill
        fields = ["supplier", "bill_date"]

class SupplierBillDetailForm(forms.ModelForm):
    class Meta:
        model = SupplierBillDetail
        fields = ['item', 'unit', 'rate', 'item_count', 'weight']

    def __init__(self, *args, **kwargs):
        super(SupplierBillDetailForm, self).__init__(*args, **kwargs)
        # Item choices
        item_choices = [("", "Select an Item")]
        item_choices += list(Item.objects.values_list("id", "name"))
        self.fields['item'].widget.attrs['class'] = 'fstdropdown-select'
        self.fields['unit'].widget.attrs['class'] = 'fstdropdown-select'
        self.fields['unit'].widget.attrs['data-searchdisable'] = "true"
        self.fields['item'].choices = item_choices
        self.fields['unit'].choices = self.fields['unit'].choices[1:]


class SupplierBillCashForm(forms.ModelForm):
    class Meta:
        model = SupplierBill
        fields = ["cash"]
