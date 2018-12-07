# ris-backend URL Configuration

from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from generics import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^api/', include('accounts.urls')),
    url(r'^admin/queue/', include('django_rq.urls')),
    url(r'^admin/task_queue/', include('task_queue.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('generics.urls')),
    url(r'^api/', include('dossier.urls')),
    url(r'^api/', include('favorite.urls')),
    url(r'^api/', include('query.urls')),
    url(r'^api/subscription/', include('subscriptions.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
