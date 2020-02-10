from django.urls import re_path 

from . import views
urlpatterns = [
    re_path(r'^$', views.ledger_view, name='ledger'),
    re_path(r'^ledger/ledger-print/$', views.ledger_print, name='ledger_print'),
]
