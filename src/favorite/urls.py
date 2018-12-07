from django.conf.urls import url
from favorite.views import FavoriteList, FavoriteAdd, FavoriteDelete


urlpatterns = [
	url(r'^favorite/list/$', FavoriteList.as_view(), name='list favorites'),
	url(r'^favorite/add/$', FavoriteAdd.as_view(), name='create favorite'),
	url(r'^favorite/delete/(?P<pk>\d+)/$', FavoriteDelete.as_view(), name='delete favorites'),
]