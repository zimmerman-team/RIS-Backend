from django.conf.urls import url
from subscriptions.views import email_demo, get_user_subscriptions, remove, change, subscribe


urlpatterns = [
    url(r'^get/', get_user_subscriptions, name='get_user_subscriptions'),
    url(r'^subscribe/', subscribe, name='subscribe'),
    url(r'^remove/', remove, name='remove'),
    url(r'^change/', change, name='change'),
    url(r'^demo/', email_demo, name='email'),
]
