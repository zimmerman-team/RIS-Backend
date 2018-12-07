from django.conf.urls import url
from query.views import ListQueries, CreateQuery, EditQuery, DetailQuery, DeleteQuery, ShareQuery, DeleteSharedQuery


urlpatterns = [
	url(r'^query/list/$', ListQueries.as_view(), name='list all queries'),
	url(r'^query/create/$', CreateQuery.as_view(), name='create query'),
	url(r'^query/edit/(?P<pk>\d+)/$', EditQuery.as_view(), name='edit query'),
	url(r'^query/get/(?P<pk>\d+)/$', DetailQuery.as_view(), name='get query info'),
	url(r'^query/delete/(?P<pk>\d+)/$', DeleteQuery.as_view(), name='delete query'),
	url(r'^query/share/$', ShareQuery.as_view(), name='share query'),
	url(r'^query/unshare/(?P<pk>\d+)/$', DeleteSharedQuery.as_view({'delete': 'destroy'}), name='unshare query'),
]