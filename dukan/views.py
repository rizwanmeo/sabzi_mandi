from django.db.models import Sum, Count
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView

from dukan.models import *
from dukan.forms import BillDetailForm

@login_required(login_url='/login/')
def index(request):
    context = {
        'name': 'Muhammad Rizwan',
        'daily_earn': '4,000',
        'monthly_earn': '74,000',
        'daily_purchase': '3,000',
        'monthly_purchase': '50,000',
    }

    shops = list(request.user.shop_set.values("id", "name"))
    context["shops_list"] = shops
    return render(request, 'index.html', context)

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
def get_earn_data(request):
    data = [1000, 2000, 3000,4000, 5000, 6000, 7000, 8000, 9000, 9000, 9000, 9000]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    max_value = 9000
    return JsonResponse({"status": True, "data": data, "labels": labels, "max_value": max_value})

@login_required(login_url='/login/')
def get_top_client(request):
    data = [1000, 2000, 3000,4000, 5000, 6000, 7000, 8000, 9000, 9000, 9000, 9000]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    max_value = 9000
    return JsonResponse({"status": True, "data": data, "labels": labels, "max_value": max_value})

class CustomLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/login"

class ShopListView(CustomLoginRequiredMixin, ListView):
    model = Shop
    template_name = "shops/list.html"

class ShopCreateView(CustomLoginRequiredMixin, CreateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "address", "logo"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        if form.instance.logo:
            form.instance.make_thumbnail()
        super(ShopCreateView, self).form_valid(form)
        msg = 'Shop: [%s] was creates succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ShopUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Shop
    success_url = "/shops"
    template_name = "shops/form.html"
    fields = ["name", "address", "logo"]

    def form_valid(self, form):
        form.instance.make_thumbnail()
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Shop: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierListView(CustomLoginRequiredMixin, ListView):
    model = Supplier
    template_name = "suppliers/list.html"

class SupplierCreateView(CustomLoginRequiredMixin, CreateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop_id = 1
        super(SupplierCreateView, self).form_valid(form)
        msg = 'Supplier: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class SupplierUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Supplier
    success_url = "/suppliers"
    template_name = "suppliers/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Supplier: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientListView(CustomLoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/list.html"

class ClientCreateView(CustomLoginRequiredMixin, CreateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.shop_id = 1
        super(ClientCreateView, self).form_valid(form)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = Client
    success_url = "/clients"
    template_name = "clients/form.html"
    fields = ["name", "address", "cnic", "phone", "opening_balance"]

    def form_valid(self, form):
        form.instance.last_modified = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Client: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientBillListView(CustomLoginRequiredMixin, ListView):
    model = ClientBill
    template_name = "client_bills/list.html"

    def get_context_data(self):
        context = super(ClientBillListView, self).get_context_data()
        object_list = context["object_list"]
        object_list = object_list.filter(client__shop=self.request.shop)
        object_list = object_list.annotate(amount=Sum('billdetail__rate'), items=Count('billdetail__item'))
        context["object_list"] = object_list
        return context


class ClientBillCreateView(CustomLoginRequiredMixin, CreateView):
    model = ClientBill
    success_url = "/client-bills"
    template_name = "client_bills/form.html"
    fields = ["client"]

    def form_valid(self, form):
        super(ClientBillCreateView, self).form_valid(form)
        msg = 'Client: [%s] was created succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a client for bill")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].widget.attrs["onChange"] = "onchangeEvent();"
        form.fields["client"].widget.attrs["required"] = False
        client_qs = form.fields["client"].queryset.filter(shop__owner=self.request.user)
        choices += list(client_qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        context["detail_form"] = BillDetailForm()
        return context


class ClientBillUpdateView(CustomLoginRequiredMixin, UpdateView):
    model = ClientBill
    success_url = "/client-bills"
    template_name = "client_bills/form.html"
    fields = ["client"]

    def form_valid(self, form):
        form.instance.bill_time = datetime.datetime.now()
        super(ClientUpdateView, self).form_valid(form)
        msg = 'Client: [%s] was updated succfully.' % form.instance.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(ClientBillUpdateView, self).get_context_data(**kwargs)
        form = context["form"]
        choices = [("", "Select a client for bill")]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].widget.attrs["required"] = False
        client_qs = form.fields["client"].queryset.filter(shop__owner=self.request.user)
        choices += list(client_qs.values_list("id", "name"))
        form.fields["client"].choices = choices
        context["detail_list"] = self.object.billdetail_set.all()
        context["detail_form"] = BillDetailForm()
        return context

@login_required(login_url='/login/')
def client_bill_detail(request, client_id, bill_id=0):
    client_obj = Client.objects.get(id=client_id, shop=request.shop)
    if request.method == "POST":
        form = BillDetailForm(request.POST)
        if form.is_valid():
            try:
                if int(bill_id) > 0:
                    bill_obj = ClientBill.objects.get(id=bill_id, client_id=client_id)
                else:
                    bill_obj = ClientBill.objects.annotate(item_count=Count('billdetail')).get(client_id=client_id, is_draft=True, item_count=0)
            except ClientBill.DoesNotExist:
                bill_obj = ClientBill(client=client_obj, is_draft=True)
                bill_obj.save()

            form.instance.bill = bill_obj
            form.save()
            data = {"id": form.instance.id, "unit": form.instance.get_unit_display(),
                    "rate": form.instance.rate, "item": form.instance.item.name,
                    "item_count": form.instance.item_count}
            return JsonResponse({"status": True, "data": data})
        else:
            return JsonResponse({"status": False, "errors": form.errors})
    return JsonResponse({"status": False, "description": "Invalid request"})

@login_required(login_url='/login/')
def get_drafted_bill_temp(request, client_id):
    client_qs = ClientBill.objects.filter(
        client_id=client_id, client__shop=request.shop, is_draft=True)
    client_qs = client_qs.order_by("-created_time")
    client_qs = client_qs.annotate(amount=Sum('billdetail__rate'), items=Count('billdetail__item'))
    data = list(client_qs.values())[:10]
    return JsonResponse({"status": True, "data": data})

@login_required(login_url='/login/')
def get_drafted_bill(request, client_id):
    data = {}
    draft_bills = []
    if request.method == "GET":
        client = Client.objects.get(id=client_id)
        kwargs = {
            "client_id":      client_id,
            "client__shop":   request.shop,
            "is_draft":       True}
        client_qs = ClientBill.objects.filter(**kwargs).order_by("-created_time")
        for obj in client_qs[:10]:
            draft_bill = {}
            billdetail_vs = list(obj.billdetail_set.values("rate", "item_count"))
            item_count = len(billdetail_vs)
            if item_count == 0: continue
            draft_bill["bill_id"] = obj.id
            draft_bill["billed_amount"] = 0
            draft_bill["item_count"] = item_count
            draft_bill["created_time"] = obj.created_time.strftime("%d %b, %Y %I:%M%p")
            for detail_obj in billdetail_vs:
                draft_bill["billed_amount"] += detail_obj["rate"] + detail_obj["item_count"]
            draft_bills.append(draft_bill)
        data["draft_bills"] = draft_bills
        data["balance"] = client.current_balance

    return JsonResponse({"status": True, "data": data})
