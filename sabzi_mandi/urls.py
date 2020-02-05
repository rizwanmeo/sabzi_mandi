from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth_views


from dukan import views

urlpatterns = [
    # Dashboard urls
    re_path(r'^$', views.index, name='index'),

    # login and logout urls
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(template_name='login.html'), name='logout'),

    # all other urls
    re_path(r'^get_earn_data/$', views.get_earn_data, name='get_earn_data'),
    re_path(r'^get_top_client/$', views.get_top_client, name='get_top_client'),
    re_path(r'^shops/make-default/$', views.make_default_shop, name='^make-default$'),

    # all list view urls
    re_path(r'^shops/$', views.ShopListView.as_view(), name='shops_list'),
    re_path(r'^suppliers/$', views.SupplierListView.as_view(), name='suppliers_list'),
    re_path(r'^clients/$', views.ClientListView.as_view(), name='clients_list'),
    re_path(r'^client-bills/$', views.ClientBillListView.as_view(), name='client_bills'),
    re_path(r'^ledger/$', views.ledger_view, name='ledger'),
    re_path(r'^ledger/ledger-print/$', views.ledger_print, name='ledger_print'),

    # all create view urls
    re_path(r'^shops/create/$', views.ShopCreateView.as_view(), name='shops_create'),
    re_path(r'^suppliers/create/$', views.SupplierCreateView.as_view(), name='suppliers_create'),
    re_path(r'^clients/create/$', views.ClientCreateView.as_view(), name='clients_create'),
    re_path(r'^client-bills/create/$', views.ClientBillCreateView.as_view(), name='client_bills_create'),
    re_path(r'^client-bills/(?P<client_id>\d+)/client-detail/$', views.get_drafted_bill, name='get_drafted_bill'),
    re_path(r'^client-bills/(?P<bill_id>\d+)/print/$', views.print_bill, name='print_bill'),
    re_path(r'^client-bills/(?P<client_id>\d+)/(?P<bill_id>\d+)/bill-detail/$', views.client_bill_detail, name='client_bill_detail'),
    re_path(r'^client-bills/(?P<client_id>\d+)/(?P<bill_id>\d+)/done/$', views.done_drafted_bill, name='client_bill_detail_done'),

    # all delete view urls
    re_path(r'^client-bills/(?P<pk>\d+)/delete/$', views.ClientBillDeleteView.as_view(), name='^client_bills_delete$'),
    re_path(r'^client-bills-detail/(?P<pk>\d+)/delete/$', views.delete_client_bill_detail, name='delete_client_bill_detail'),

    # all update view urls
    re_path(r'^shops/(?P<pk>\d+)/update/$', views.ShopUpdateView.as_view(), name='^shops_update$'),
    re_path(r'^suppliers/(?P<pk>\d+)/update/$', views.SupplierUpdateView.as_view(), name='^suppliers_update$'),
    re_path(r'^clients/(?P<pk>\d+)/update/$', views.ClientUpdateView.as_view(), name='^clients_update$'),
    re_path(r'^client-bills/(?P<pk>\d+)/update/$', views.ClientBillUpdateView.as_view(), name='^client_bills_update$'),

    # Admin urls
    path('admin/', admin.site.urls),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
