import datetime

from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse

from .forms import *
from .models import *
from clients.models import Client

from sabzi_mandi.views import *

class ClientBillListView(CustomListView):
    model = ClientBill
    template_name = "client_bills/list.html"
    filterset_fields = ["client", "bill_date"]

    def get_context_data(self, **kwargs):
        context = super(ClientBillListView, self).get_context_data(**kwargs)

        object_list = context["object_list"]
        object_list = object_list.filter(client__shop=self.request.shop, is_draft=False)
        columns = ["id", "client__name", "created_time", "is_draft", "bill_date",
                   "balance", "billed_amount", "payment__amount", "billdetail__rate",
                   "billdetail__item__name", "billdetail__unit", "billdetail__item_count"]
        data = {}
        vs = list(object_list.values(*columns))
        for row in vs:
            row_data = {}
            row_data["id"] = row["id"]
            row_data["pk"] = row["id"]
            row_data["client"] = {"name": row["client__name"]}
            row_data["created_time"] = row["created_time"]
            row_data["is_draft"] = row["is_draft"]
            row_data["bill_date"] = row["bill_date"]
            row_data["balance"] = row["balance"]
            row_data["billed_amount"] = row["billed_amount"]
            row_data["payment"] = {"amount": row["payment__amount"] or 0}
            row_data["total_items"] = 1
            row_data["billdetail"] = []

            row_data["previous_amount"] = row_data["balance"] - row["billed_amount"] + row_data["payment"]["amount"]
            detail = {}
            detail["item"] = {"name": row["billdetail__item__name"]}
            detail["rate"] = row["billdetail__rate"]
            detail["unit"] = "KG" if row["billdetail__unit"] == "k" else "Count"
            detail["item_count"] = row["billdetail__item_count"]

            row_data["billdetail"].append(detail)

            try:
                data[row["id"]]["billdetail"].append(detail)
                data[row["id"]]["total_items"] += 1
            except KeyError:
                data[row["id"]] = row_data

        context["object_list"] = data.values()

        client_id = self.request.GET.get("client", "")
        client_id=int(client_id) if client_id.isdigit() else 0
        qs = Client.objects.filter(shop=self.request.shop)
        context["client_list"] = list(qs.values("id", "name"))
        context["selected_client"] = client_id
        client_id = self.request.GET.get("client", "")

        selected_date = self.request.GET.get("bill_date", "")
        if selected_date == "":
            selected_date = datetime.date.today().strftime("%Y-%m-%d")
        context["selected_date"] = selected_date

        return context

def get_client_choices(form, shop_id):
    choices = [("", "Select a client for bill")]
    client_qs = form.fields["client"].queryset.filter(shop_id=shop_id)
    choices += list(client_qs.values_list("id", "name"))
    return choices

class ClientBillCreateView(CustomCreateView):
    model = ClientBill
    form_class = ClientBillForm
    success_url = "/client-bills"
    template_name = "client_bills/form.html"

    def form_valid(self, form):
        today = datetime.date.today()
        form.instance.is_draft = True
        payment_amount = form.cleaned_data.get("payment", 0)
        description = "payment received against bill on %s" % today.strftime("%Y-%m-%d")
        payment_obj = ClientPayment()
        payment_obj.client = form.instance.client
        payment_obj.payment_date = today
        payment_obj.amount = payment_amount
        payment_obj.description = description
        payment_obj.save()
        form.instance.payment = payment_obj
        ClientBill.objects.filter(client=form.instance.client, is_draft=True).delete()
        super(ClientBillCreateView, self).form_valid(form)
        msg = 'Client: [%s] bill was added succfully. Please add bill detail'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        obj = ClientBill.objects.get(client=form.instance.client, is_draft=True)
        success_url = "/client-bills/%d/detail-create/?shop_id=%d"
        return HttpResponseRedirect(success_url % (self.object.pk, self.request.shop.pk))

    def get_context_data(self, **kwargs):
        context = super(ClientBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].choices = get_client_choices(form, self.request.shop.id)
        form.fields["bill_date"].initial = datetime.date.today().strftime("%Y-%m-%d")
        return context

class ClientBillUpdateView(CustomUpdateView):
    model = ClientBill
    form_class = ClientBillForm
    success_url = "/client-bills"
    template_name = "client_bills/form.html"

    def form_valid(self, form):
        super(ClientBillUpdateView, self).form_valid(form)
        payment_amount = form.cleaned_data.get("payment", 0)
        self.object.payment.amount = payment_amount
        self.object.payment.save()

        msg = 'Client: [%s] bill was updated succfully. Please add bill detail'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)

        success_url = "/client-bills/%d/detail-create/?shop_id=%d"
        return HttpResponseRedirect(success_url % (self.object.pk, self.request.shop.pk))

    def get_context_data(self, **kwargs):
        context = super(ClientBillUpdateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].choices = get_client_choices(form, self.request.shop.id)
        form.initial["payment"] = self.object.payment.amount
        form.initial["bill_date"] = form.initial["bill_date"].strftime("%Y-%m-%d")
        return context

class ClientBillDeleteView(CustomDeleteView):
    model = ClientBill
    success_url = "/client-bills"

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not self.get_object().is_draft:
            raise Http404
        super(ClientBillDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Client: [%s] bill was delete succfully.' % self.object.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class BillDetailCreateView(CustomCreateView):
    model = BillDetail
    template_name = "client_bills/bill_detail_form.html"
    fields = ["item", "unit", "rate", "item_count"]

    def get_success_url(self):
        return ""

    def form_valid(self, form):
        form.instance.bill = self.request.bill
        super(BillDetailCreateView, self).form_valid(form)
        msg = 'Client: [%s] bill detail was added succfully.' % self.request.bill.client.name
        success_url = "/client-bills/%d/detail-create/?shop_id=%d"
        return HttpResponseRedirect(success_url % (self.request.bill.pk, self.request.shop.pk))

    def get_context_data(self, **kwargs):
        context = super(BillDetailCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["item"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["unit"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["unit"].widget.attrs["data-searchdisable"] = "true"

        object_list = []
        selected_items = []
        billed_amount = 0
        qs = BillDetail.objects.filter(bill=self.request.bill)
        vs = list(qs.values("item__id", "item__name", "unit", "rate", "item_count"))
        for row in vs:
            detail_obj = {}
            detail_obj["name"] = row["item__name"]
            detail_obj["unit"] = "KG" if row["unit"] == 'k' else "Count"
            detail_obj["rate"] = row["rate"]
            detail_obj["item_count"] = row["item_count"]
            detail_obj["amount"] = row["rate"] * row["item_count"]
            billed_amount += detail_obj["amount"]
            object_list.append(detail_obj)
            selected_items.append(row["item__id"])

        # Load Item choices
        choices = [("", "Select an item")]
        qs = Item.objects.all()
        vs = list(qs.values_list("id", "name"))
        form.fields["item"].choices = choices + vs
        form.fields["unit"].choices = form.fields["unit"].choices[1:]

        context["object_list"] = object_list
        context["billed_amount"] = billed_amount
        return context

    def get_bill_obj(self, bill_id):
        try:
            return ClientBill.objects.get(id=bill_id)
        except:
            raise Http404

    def get(self, request, *args, **kwargs):
        request.bill = self.get_bill_obj(kwargs.get("bill_id", 0))
        return super(BillDetailCreateView, self).get(request)

    def post(self, request, *args, **kwargs):
        request.bill = self.get_bill_obj(kwargs.get("bill_id", 0))
        return super(BillDetailCreateView, self).post(request)

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
                    bill_id = bill_obj.id
            except ClientBill.DoesNotExist:
                bill_obj = ClientBill(client=client_obj, is_draft=True)
                bill_obj.save()
                bill_id = bill_obj.id

            form.instance.bill = bill_obj
            form.save()
            data = {"id": form.instance.id, "unit": form.instance.get_unit_display(),
                    "rate": form.instance.rate, "item": form.instance.item.name,
                    "item_count": form.instance.item_count}
            return JsonResponse({"status": True, "data": data, "bill_id": bill_id})
        else:
            return JsonResponse({"status": False, "errors": form.errors})
    return JsonResponse({"status": False, "description": "Invalid request"})

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
                draft_bill["billed_amount"] += detail_obj["rate"] * detail_obj["item_count"]
            draft_bills.append(draft_bill)
        data["draft_bills"] = draft_bills
        data["balance"] = client.current_balance

    return JsonResponse({"status": True, "data": data})

@login_required(login_url='/login/')
def done_drafted_bill(request, bill_id):
    try:
        bill_obj = ClientBill.objects.get(id=int(bill_id), is_draft=True)
    except:
        raise Http404

    redirect_url = "/client-bills/?shop_id=%d" % request.shop.pk
    if request.method == "POST":
        billed_amount = 0
        billdetail_vs = bill_obj.billdetail_set.values("rate", "item_count")
        for detail_obj in billdetail_vs:
            billed_amount += detail_obj["rate"] * detail_obj["item_count"]
        bill_obj.is_draft = False
        bill_obj.billed_amount = billed_amount

        bill_obj.client.current_balance += billed_amount
        if bill_obj.payment:
            bill_obj.client.current_balance -= bill_obj.payment.amount

        bill_obj.balance = bill_obj.client.current_balance
        bill_obj.client.save()
        bill_obj.save()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
    else:
        redirect_url = "/client-bills/%d/detail-create/?shop_id=%d" % (bill_id, request.shop.pk)
    return HttpResponseRedirect(redirect_url)


@login_required(login_url='/login/')
def print_bill(request, bill_id):
    context = {}

    try:
        obj = ClientBill.objects.get(id=int(bill_id), is_draft=False)
    except:
        raise Http404

    if request.method == "GET":

        if obj.payment:
            obj.previous_balance = obj.balance - obj.billed_amount + obj.payment.amount
        else:
            obj.previous_balance = obj.balance - obj.billed_amount
        obj.after_bill_balance = obj.previous_balance + obj.billed_amount

        context["obj"] = obj
        qs = obj.billdetail_set.all()
        vs = list(qs.values("item__name", "unit", "rate", "item_count"))
        data = []
        total_item_count = 0
        total_item_weight = 0
        for row in vs:
            detail_obj = {}
            detail_obj["name"] = row["item__name"]
            detail_obj["rate"] = row["rate"]
            detail_obj["item_count"] = row["item_count"]
            detail_obj["amount"] = row["rate"] * row["item_count"]
            detail_obj["unit"] = row["unit"]
            if row["unit"] == 'k':
                total_item_weight += row["item_count"]
            else:
                total_item_count += row["item_count"]

            data.append(detail_obj)

        context["bill_detail_list"] = data
        context["total_item_count"] = total_item_count
        context["total_item_weight"] = total_item_weight

    return render(request, 'client_bills/print.html', context)

@login_required(login_url='/login/')
def delete_client_bill_detail(request, detail_id):
    if request.method == "DELETE":
        try:
            obj = BillDetail.object.get(id=detail_id)
            obj.delete()
            return JsonResponse({"status": True, "description": "Successfully deleted"})
        except:
            return JsonResponse({"status": False, "description": "Invalid bill ID"})
    return JsonResponse({"status": False, "description": "Invalid Request"})

