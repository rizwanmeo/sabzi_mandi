from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth_views


from dukan import views

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(template_name='login.html'), name='logout'),
    re_path(r'^get_earn_data/$', views.get_earn_data, name='get_earn_data'),
    re_path(r'^get_top_client/$', views.get_top_client, name='get_top_client'),
    re_path(r'^suppliers/$', views.get_suppliers, name='suppliers'),
    re_path(r'^clients/$', views.get_clients, name='clients'),
    re_path(r'^shops/$', views.ShopListView.as_view(), name='shops_list'),
    re_path(r'^shops/create/$', views.ShopCreateView.as_view(), name='shops_create'),
    re_path(r'^shops/(?P<pk>\d+)/update/$', views.ShopUpdateView.as_view(), name='^shops_update$'),
    #path('admin/', admin.site.urls),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
