from django.db.models import Sum
from django.shortcuts import render
from django.contrib import messages

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .models import *
from sabzi_mandi.views import *
from .utils import get_shop_cashbook_data


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

@login_required(login_url='/login/')
def shop_cashbook_view(request):
    context = get_shop_cashbook_data(request)
    return render(request, 'shops/cashbook.html', context)

@login_required(login_url='/login/')
def shop_cashbook_print(request):
    context = get_shop_cashbook_data(request)
    return render(request, 'shops/cashbook_print.html', context)


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


class ShopCashOpeningBalanceView(CustomCreateView):
    model = ShopDailyRemainingCash
    success_url = "/shops/cashbook"
    template_name = "shops/cashbook_opening_balance.html"
    fields = ["amount"]

    def form_valid(self, form):
        form.instance.shop = self.request.shop
        date = datetime.date.today()
        try:
            obj = ShopDailyRemainingCash.objects.get(shop=self.request.shop, date__gte=date, date__lte=date)
            form.instance.pk = obj.pk
            form.instance.id = obj.id
        except ShopDailyRemainingCash.DoesNotExist:
            pass

        super(ShopCashOpeningBalanceView, self).form_valid(form)
        msg = 'Shop cashbook: [%s] opening balance was set succfully.' % self.request.shop.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

@login_required(login_url='/login/')
@require_http_methods(["POST"])
def update_shop_opening_cash(request):
    context = {}

    redirect_url = "/shops/cashbook/"
    date = request.GET.get("date", "")
    if bool(date):
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        msg = 'Refresh cashbook: [%s] Invlid date was selected.' % request.shop.name
        messages.add_message(self.request, messages.ERROR, msg)
        return HttpResponseRedirect(self.get_success_url())

    return render(request, 'shops/cashbook.html', context)
