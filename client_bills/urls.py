from django.urls import re_path

from . import views

urlpatterns = [
    # all list view urls
    re_path(r'^$', views.ClientBillListView.as_view(), name='client_bills'),

    # all client-bills related urls
    re_path(r'^create/$', views.ClientBillCreateView.as_view(), name='client_bills_create'),
    re_path(r'^(?P<client_id>\d+)/client-detail/$', views.get_drafted_bill, name='get_drafted_bill'),
    re_path(r'^(?P<bill_id>\d+)/print/$', views.print_bill, name='print_bill'),
    re_path(r'^(?P<client_id>\d+)/(?P<bill_id>\d+)/bill-detail/$', views.client_bill_detail, name='client_bill_detail'),
    re_path(r'^(?P<client_id>\d+)/(?P<bill_id>\d+)/done/$', views.done_drafted_bill, name='client_bill_detail_done'),

    # all delete view urls
    re_path(r'^(?P<pk>\d+)/delete/$', views.ClientBillDeleteView.as_view(), name='^client_bills_delete$'),
    re_path(r'^client-bills-detail/(?P<pk>\d+)/delete/$', views.delete_client_bill_detail, name='delete_client_bill_detail'),

    # all update view urls
    re_path(r'^(?P<pk>\d+)/update/$', views.ClientBillUpdateView.as_view(), name='^client_bills_update$'),
]
