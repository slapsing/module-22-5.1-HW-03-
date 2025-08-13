from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('admin/', admin.site.urls),
    path('news/', include('news.urls')),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('accounts/', include('sign.urls')),
]
