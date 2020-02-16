from django.urls import re_path 

from . import views
urlpatterns = [
    re_path(r'^suppliers/$', views.suppliers_ledger_view, name='suppliers_ledger'),
    re_path(r'^suppliers/print/$', views.suppliers_ledger_print, name='suppliers_ledger_print'),

    re_path(r'^clients/$', views.clients_ledger_view, name='clients_ledger'),
    re_path(r'^clients/print/$', views.clients_ledger_print, name='clients_ledger_print'),
]
