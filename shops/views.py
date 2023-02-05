from django.db.models import Sum
from django.shortcuts import render
from django.contrib import messages

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from .models import *
from sabzi_mandi.views import *


class ShopListView(CustomListView):
    model = Shop
    template_name = "shops/list.html"
    filterset_fields = ["name"]


class ShopCreateView(CustomCreateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "phone", "address", "logo"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        super(ShopCreateView, self).form_valid(form)
        if form.instance.logo:
            form.instance.make_thumbnail()
        msg = 'Shop: [%s] was creates succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ShopUpdateView(CustomUpdateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "phone", "address", "logo"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ShopUpdateView, self).form_valid(form)
        if form.instance.logo:
            form.instance.make_thumbnail()
        msg = 'Shop: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())


@login_required(login_url='/login/')
def make_default_shop(request):
    shop_id = request.POST.get("shop_id", 0)
    shop = Shop.objects.get(id=shop_id)
    if request.method == "POST":
        Shop.objects.filter(is_default=True).update(is_default=False)
        shop.is_default = True
        shop.save()
        msg = 'Shop: [%s] was set to default.' % shop.name
        messages.add_message(request, messages.INFO, msg)
    else:
        msg = 'Error: Request was invalid for shop [%s].' % shop.name
        messages.add_message(request, messages.ERROR, msg)
    return HttpResponseRedirect("/shops")


from bills.models import SupplierBill
from ledger.models import ClientLedger
@login_required(login_url='/login/')
def shop_cashbook_view(request):
    context = {}

    date = request.GET.get("date", "")
    if bool(date):
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        date = datetime.date.today()

    object_list1 = ShopCashbook.objects.filter(shop=request.shop, time__gte=date, cash_type='i')
    object_list2 = ShopCashbook.objects.filter(shop=request.shop, time__gte=date, cash_type='e')
    
    income_amount = object_list1.aggregate(total_amount=Sum('amount'))
    income_amount = income_amount.get("total_amount") or 0

    expense_amount = object_list2.aggregate(total_amount=Sum('amount'))
    expense_amount = expense_amount.get("total_amount") or 0

    payment_qs = ClientLedger.objects.filter(client__shop=request.shop, tx_date__gte=date, tx_id__startswith='payment')
    payment_vs = payment_qs.aggregate(total_amount=Sum('payment_amount'))

    cash_amount = 0
    total_expense = 0
    columns = ["cash", "other_expence"]
    supplier_bill_qs = SupplierBill.objects.filter(supplier__shop=request.shop, bill_date__gte=date, cash__gt=0)
    supplier_bill_vs = list(supplier_bill_qs.values(*columns))
    #supplier_cash_vs = supplier_cash_qs.aggregate(total_amount=Sum('cash'))
    #print("supplier_cash_vs", supplier_cash_vs)

    for row in supplier_bill_vs:
        other_expence = row["other_expence"]
        if "vahicle_rent" in other_expence:
            total_expense += float(other_expence["vahicle_rent"])
        if "farmer_wages" in other_expence:
            total_expense += float(other_expence["farmer_wages"])
        if "labour_cost" in other_expence:
            total_expense += float(other_expence["labour_cost"])
        if "begs_amount" in other_expence:
            total_expense += float(other_expence["begs_amount"])
        if "market_tax" in other_expence:
            total_expense += float(other_expence["market_tax"])
        if "beg_rope" in other_expence:
            total_expense += float(other_expence["beg_rope"])
        if "cash_amount" in other_expence:
           total_expense += float(other_expence["cash_amount"])

        is_cash = other_expence.get("is_cash")
        if is_cash == 'y':
            cash_amount += row["cash"]

    init_amount = 1000
    context["cashbook_date"] = date
    context["object_list1"] = object_list1
    context["object_list2"] = object_list2
    context["payment_amount"] = payment_vs.get("total_amount") or 0
    context["init_amount"] = init_amount
    context["expense_amount"] = total_expense
    context["supplier_cash_amount"] = cash_amount
    context["total_income_amount"] = income_amount + init_amount + cash_amount + context["payment_amount"]
    context["total_expense_amount"] = expense_amount + total_expense
    context["remaining_amount"] = context["total_income_amount"] - context["total_expense_amount"]
    return render(request, 'shops/cashbook.html', context)


class ShopCashbookCreateView(CustomCreateView):
    model = ShopCashbook
    success_url = "/shops/cashbook"
    template_name = "shops/cashbook_form.html"
    fields = ["name", "description", "amount", "cash_type"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        super(ShopCashbookCreateView, self).form_valid(form)
        msg = 'Shop cash: [%s] was creates succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ShopCashbookUpdateView(CustomUpdateView):
    model = Shop
    success_url = "/shops/cashbook"
    template_name = "shops/cashbook_form.html"
    fields = ["name", "description", "amount", "cash_type"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ShopCashbookUpdateView, self).form_valid(form)
        msg = 'Shop cash: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())
