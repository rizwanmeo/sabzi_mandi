import datetime

from django.db.models import Max
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import *
from .models import *
from sabzi_mandi.views import *
from clients.models import Client
from ledger.models import ClientLedgerEditable
from ledger.utils import update_ledger_date, delete_ledger
from ledger.utils import create_bill_ledger, create_payment_ledger

class ClientBillListView(CustomListView):
    model = ClientBill
    template_name = "client_bills/list.html"
    filterset_fields = ["client", "bill_date"]
    shop_lookup = "client__shop"

    def get_context_data(self, **kwargs):
        context = super(ClientBillListView, self).get_context_data(**kwargs)

        object_list = context["object_list"]
        object_list = object_list.filter(is_draft=False)
        if self.request.GET.get("bill_date") is None:
            today = datetime.date.today().strftime("%Y-%m-%d")
            object_list = object_list.filter(bill_date=today)
        columns = ["id", "client__name", "client__id", "created_time", "is_draft", "bill_date",
                   "balance", "billed_amount", "payment__amount", "billdetail__rate",
                   "billdetail__item__name", "billdetail__unit", "billdetail__item_count"]

        editable_bills = dict(ClientLedgerEditable.objects.values_list("client_id", "tx_id"))

        data = {}
        vs = list(object_list.values(*columns))
        for row in vs:
            row_data = {}
            row_data["id"] = row["id"]
            row_data["pk"] = row["id"]
            row_data["client"] = {"name": row["client__name"], "id": row["client__id"]}
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

            # Checking client payment can be edit or not
            client_id = row["client__id"]
            bill_tx_id = "bill-"+str(row["id"])
            if bill_tx_id == editable_bills.get(client_id, ""):
                row_data["editable"] = True

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
        # Only create when payment amount > 0
        if payment_amount > 0:
            payment_obj = ClientPayment()
            payment_obj.client = form.instance.client
            payment_obj.payment_date = today
            payment_obj.amount = payment_amount
            payment_obj.is_draft = False
            payment_obj.save()
            form.instance.payment = payment_obj

        ClientBill.objects.filter(client=form.instance.client, is_draft=True).delete()
        super(ClientBillCreateView, self).form_valid(form)
        msg = 'Client: [%s] bill was added succfully. Please add bill detail'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)
        obj = ClientBill.objects.get(client=form.instance.client, is_draft=True)
        success_url = "/client-bills/%d/detail-create/?" % self.object.pk
        success_url += self.request.GET.urlencode()
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super(ClientBillCreateView, self).get_context_data(**kwargs)
        form = context["form"]
        form.fields["client"].widget.attrs["class"] = "fstdropdown-select"
        form.fields["client"].choices = get_client_choices(form, self.request.shop.id)

        if self.request.GET.get("client"):
            form.fields["client"].initial = self.request.GET.get("client")

        bill_date = datetime.date.today().strftime("%Y-%m-%d")
        if self.request.GET.get("bill_date"):
            bill_date = self.request.GET.get("bill_date")
        form.fields["bill_date"].initial = bill_date
        return context

class ClientBillUpdateView(CustomUpdateView):
    model = ClientBill
    form_class = ClientBillUpdateForm
    success_url = "/client-bills"
    template_name = "client_bills/form.html"

    def form_valid(self, form):
        super(ClientBillUpdateView, self).form_valid(form)
        update_ledger_date("bill-%d" % form.instance.pk, form.cleaned_data["bill_date"])
        msg = 'Client: [%s] bill was updated succfully.'
        msg %= form.instance.client.name
        messages.add_message(self.request, messages.INFO, msg)

        success_url = "/client-bills"
        return HttpResponseRedirect(success_url+"/?"+self.request.GET.urlencode())

    def get_context_data(self, **kwargs):
        context = super(ClientBillUpdateView, self).get_context_data(**kwargs)
        try:
            bill_tx_id = "bill-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=bill_tx_id)
        except:
            raise Http404

        form = context["form"]
        form.initial["bill_date"] = form.initial["bill_date"].strftime("%Y-%m-%d")
        return context

class ClientBillDeleteView(CustomDeleteView):
    model = ClientBill
    success_url = "/client-bills"

    def get_context_data(self, **kwargs):
        context = super(ClientBillDeleteView, self).get_context_data(**kwargs)
        if self.object.is_draft:
            return context

        try:
            bill_tx_id = "bill-"+str(self.object.pk)
            ClientLedgerEditable.objects.get(tx_id=bill_tx_id)
        except:
            raise Http404
        return context

    def delete(self, request, *args, **kwargs):
        super(ClientBillDeleteView, self).delete(request, *args, **kwargs)
        if not self.object.is_draft:
            bill_tx_id = "bill-"+str(self.object.pk)
            delete_ledger(bill_tx_id)
            self.object.client.current_balance -= self.object.billed_amount
            self.object.client.save()

        msg = 'Client: [%s] bill was delete succfully.' % self.object.client.name
        messages.add_message(self.request, messages.INFO, msg)
        return HttpResponseRedirect(self.get_success_url())

class ClientBillDetailDeleteView(CustomDeleteView):
    model = BillDetail
    success_url = "/client-bills"

    def delete(self, request, *args, **kwargs):
        if not self.get_object().bill.is_draft:
            raise Http404

        super(ClientBillDetailDeleteView, self).delete(request, *args, **kwargs)
        msg = 'Client bill: Item [%s] was delete succfully from bill.' % self.object.item.name
        messages.add_message(self.request, messages.INFO, msg)
        get_success_url = "/client-bills/%s/detail-create/?" % self.object.bill_id
        get_success_url += self.request.GET.urlencode()
        return HttpResponseRedirect(get_success_url)

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
        billed_amount = 0
        qs = BillDetail.objects.filter(bill=self.request.bill)
        qs = qs.order_by("-id")
        vs = list(qs.values("id", "item__name", "unit", "rate", "item_count"))
        for row in vs:
            detail_obj = {}
            detail_obj["id"] = row["id"]
            detail_obj["name"] = row["item__name"]
            detail_obj["unit"] = "KG" if row["unit"] == 'k' else "Count"
            detail_obj["rate"] = row["rate"]
            detail_obj["item_count"] = row["item_count"]
            detail_obj["amount"] = row["rate"] * row["item_count"]
            billed_amount += detail_obj["amount"]
            object_list.append(detail_obj)

        # Load Item choices
        choices = []
        qs = Item.objects.all().order_by("id")
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

def done_drafted_bill(request, bill_obj):
    billed_amount = 0
    now = datetime.datetime.now()
    billdetail_vs = list(bill_obj.billdetail_set.values("rate", "item_count"))
    for detail_obj in billdetail_vs:
        billed_amount += detail_obj["rate"] * detail_obj["item_count"]
    bill_obj.is_draft = False
    bill_obj.billed_amount = billed_amount

    bill_obj.created_time = now
    create_bill_ledger(bill_obj, bill_obj.client.current_balance)
    bill_obj.client.current_balance += billed_amount

    if bill_obj.payment:
        bill_obj.payment.payment_time = now + datetime.timedelta(seconds=1)
        bill_obj.payment.is_draft = False
        description = "Payment received against bill ID bill-%d" % bill_obj.id
        bill_obj.payment.description = description
        create_payment_ledger(bill_obj.payment, bill_obj.client.current_balance)
        bill_obj.client.current_balance -= bill_obj.payment.amount
        bill_obj.payment.save()

    bill_obj.balance = bill_obj.client.current_balance
    bill_obj.client.save()
    bill_obj.save()

def get_print_bill_data(request, bill_obj):
    context = {}
    if bill_obj.payment:
        bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount + bill_obj.payment.amount
    else:
        bill_obj.previous_balance = bill_obj.balance - bill_obj.billed_amount
    bill_obj.after_bill_balance = bill_obj.previous_balance + bill_obj.billed_amount

    context["obj"] = bill_obj
    qs = bill_obj.billdetail_set.all()
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

    return context

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def print_bill(request, bill_id):
    try:
        bill_obj = ClientBill.objects.get(id=int(bill_id), is_draft=False)
    except:
        raise Http404

    context = get_print_bill_data(request, bill_obj)
    return render(request, 'client_bills/print.html', context)

@login_required(login_url='/login/')
@require_http_methods(["POST"])
def done_bill(request, bill_id):
    try:
        bill_obj = ClientBill.objects.get(id=int(bill_id), is_draft=True)
    except:
        raise Http404

    if bill_obj.billdetail_set.count() == 0:
        raise Http404

    action = int(request.POST.get("submit", 0))
    if action == 1:
        done_drafted_bill(request, bill_obj)
        redirect_url = "/client-bills/?"+request.GET.urlencode()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    elif action == 2:
        done_drafted_bill(request, bill_obj)
        context = get_print_bill_data(request, bill_obj)
        return render(request, 'client_bills/print.html', context)
    elif action == 3:
        done_drafted_bill(request, bill_obj)
        redirect_url = "/client-bills/create/?"
        redirect_url += request.GET.urlencode()
        msg = 'Client: [%s] Bill was done succfully.' % bill_obj.client.name
        messages.add_message(request, messages.INFO, msg)
        return HttpResponseRedirect(redirect_url)
    else:
        raise Http404
