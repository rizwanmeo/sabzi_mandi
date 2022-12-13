from django.urls import path, re_path

from . import views

urlpatterns = [
    # clients payment list view urls
    re_path(r'^clients/$', views.ClientPaymentListView.as_view(), name='clients_payment_list'),

    # clients payment list view url
    re_path(r'^clients/print/$', views.clients_payment_print, name='clients_payment_print'),

    # clients payment list view url
    re_path(r'^clients/create/$', views.ClientPaymentCreateView.as_view(), name='clients_payment_create'),

    # clients payment update view url
    re_path(r'^clients/(?P<pk>\d+)/update/$', views.ClientPaymentUpdateView.as_view(), name='clients_payment_update'),

    # clients payment delete view url
    re_path(r'^clients/(?P<pk>\d+)/delete/$', views.ClientPaymentDeleteView.as_view(), name='clients_payment_delete'),

    # suppliers payment list view url
    re_path(r'^suppliers/$', views.SupplierPaymentListView.as_view(), name='suppliers_payment_list'),

    # suppliers payment create view url
    re_path(r'^suppliers/create/$', views.SupplierPaymentCreateView.as_view(), name='suppliers_payment_create'),

    # suppliers payment delete view url
    re_path(r'^suppliers/(?P<pk>\d+)/delete/$', views.SupplierPaymentDeleteView.as_view(), name='suppliers_payment_delete'),
]
