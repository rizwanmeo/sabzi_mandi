from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path 
from django.contrib.auth import views as auth_views

from mandi import views as mandi_views
from mandi import urls as mandi_urls
from shops import urls as shop_urls
from suppliers import urls as supplier_urls
from clients import urls as client_urls
from client_bills import urls as client_bill_urls
from ledger import urls as ledger_urls
from payments import urls as payment_urls

urlpatterns = [
    # Dashboard urls
    re_path(r'^$', mandi_views.index, name='index'),

    # login and logout urls
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(template_name='login.html'), name='logout'),

    # Admin urls
    #path('admin/', admin.site.urls),
    path('', include(mandi_urls)),
    path('shops/', include(shop_urls)),
    path('suppliers/', include(supplier_urls)),
    path('clients/', include(client_urls)),
    path('client-bills/', include(client_bill_urls)),
    path('ledger/', include(ledger_urls)),
    path('payment/', include(payment_urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
