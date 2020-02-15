from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth_views


from . import views

urlpatterns = [
    # all list view urls
    re_path(r'^clients/$', views.ClientPaymentListView.as_view(), name='clients_payment_list'),
    re_path(r'^clients/create/$', views.ClientPaymentCreateView.as_view(), name='clients_payment_create'),

    re_path(r'^suppliers/$', views.SupplierPaymentListView.as_view(), name='suppliers_payment_list'),
    re_path(r'^suppliers/create/$', views.SupplierPaymentCreateView.as_view(), name='suppliers_payment_create'),
]
