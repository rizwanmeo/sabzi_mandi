from django.urls import re_path

from . import views

urlpatterns = [
    # all list view urls
    re_path(r'^$', views.ClientBillListView.as_view(), name='client_bills'),

    # all client-bills related urls
    re_path(r'^create/$', views.ClientBillCreateView.as_view(), name='client_bills_create'),
    re_path(r'^(?P<bill_id>\d+)/detail-create/$', views.BillDetailCreateView.as_view(), name='client_bills_detail_create'),
    re_path(r'^(?P<bill_id>\d+)/done/$', views.done_bill, name='client_bill_done'),
    re_path(r'^(?P<bill_id>\d+)/print/$', views.print_bill, name='print_bill'),

    # all delete view urls
    re_path(r'^(?P<pk>\d+)/delete/$', views.ClientBillDeleteView.as_view(), name='client_bills_delete'),
    re_path(r'^(?P<pk>\d+)/bill-detail-delete/$', views.ClientBillDetailDeleteView.as_view(), name='client_bills_detail_delete'),

    # all update view urls
    re_path(r'^(?P<pk>\d+)/update/$', views.ClientBillUpdateView.as_view(), name='client_bills_update'),
]
