from django.urls import re_path

from . import views
from ledger import views as ledger_views

urlpatterns = [
    # all list view urls
    re_path(r'^client/$', views.ClientBillListView.as_view(), name='client_bills'),

    # all client-bills related urls
    re_path(r'^client/create/$', views.ClientBillCreateView.as_view(), name='client_bills_create'),
    re_path(r'^client/print/$', ledger_views.ClientLedgerListView.as_view(), name='client_bills_print'),
    re_path(r'^client/(?P<bill_id>\d+)/detail-create/$', views.BillDetailCreateView.as_view(), name='client_bills_detail_create'),
    re_path(r'^client/(?P<bill_id>\d+)/done/$', views.done_bill, name='client_bill_done'),
    re_path(r'^client/(?P<client_id>\d+)/print/$', views.print_bill, name='print_bill'),

    # all delete view urls
    re_path(r'^client/(?P<pk>\d+)/delete/$', views.ClientBillDeleteView.as_view(), name='client_bills_delete'),
    re_path(r'^client/(?P<pk>\d+)/bill-detail-delete/$', views.ClientBillDetailDeleteView.as_view(), name='client_bills_detail_delete'),

    # supplier create view url
    re_path(r'^supplier/$', views.SupplierBillListView.as_view(), name='supplier_bills'),

    # supplier create view url
    re_path(r'^supplier/create/$', views.SupplierBillCreateView.as_view(), name='create_supplier_bill'),

    # supplier daily detail view url
    re_path(r'^supplier/daily-detail/$', views.SupplierDailyBillReport.as_view(), name='daily_suppliers_bill_detail'),
    re_path(r'^supplier/daily-detail-print/$', views.SupplierDailyBillReportPrint.as_view(), name='suppliers_daily_bill_detail_print'),
    # supplier cash form view url
    re_path(r'^supplier/daily-detail/(?P<pk>\d+)/cash/$', views.SupplierBillCashUpdateView.as_view(), name='suppliers_bill_cash'),

    # supplier update view url
    re_path(r'^supplier/(?P<bill_id>\d+)/$', views.add_supplier_bill_detail, name='add_supplier_bill_detail$'),

    # supplier update view url
    re_path(r'^supplier/(?P<pk>\d+)/delete-bill/$', views.SupplierBillDeleteView.as_view(), name='supplier_bill_delete'),

    # supplier update view url
    re_path(r'^supplier/(?P<pk>\d+)/delete-bill-detail/$', views.SupplierBillDetailDeleteView.as_view(), name='supplier_bill_detail_delete'),

    # supplier update view url
    re_path(r'^supplier/(?P<pk>\d+)/done/$', views.done_supplier_bill, name='done_supplier_bill'),

    # supplier update view url
    re_path(r'^supplier/(?P<pk>\d+)/print/$', views.print_supplier_bill, name='print_supplier_bill'),
]
