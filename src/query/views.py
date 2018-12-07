from rest_framework import generics, filters, viewsets, pagination
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated

from query.permissions import IsSharedOwner
from query.models import Query, QuerySharedUsers
from query.serializers import QuerySerializer, CreateQuerySerializer, UpdateQuery, ShareQuerySerializer, UnshareQuerySerializer
from query.permissions import IsOwner
from query.filters import CustomDateFilter


class LargeResultsSetPagination(pagination.PageNumberPagination):
	page_size = 10
	page_size_query_param = 'page_size'
	max_page_size = 300


class ListQueries(generics.ListAPIView):
	serializer_class = QuerySerializer
	filter_class = CustomDateFilter
	filter_backends = (filters.OrderingFilter,)
	ordering_fields = ('title', 'created_at', 'last_modified',)
	permission_classes = (IsOwner,)
	pagination_class = LargeResultsSetPagination

	def get_queryset(self):
		user = self.request.user
		return Query.objects.filter(Q(owner=user) | Q(shared_users=user))


class CreateQuery(generics.CreateAPIView):
	queryset = Query.objects.all()
	serializer_class = CreateQuerySerializer
	permission_classes = (IsOwner,)


class EditQuery(generics.RetrieveUpdateAPIView):
	queryset = Query.objects.all()
	serializer_class = UpdateQuery
	permission_classes = (IsOwner,)


class DetailQuery(generics.RetrieveAPIView):
	queryset = Query.objects.all()
	serializer_class = QuerySerializer
	permission_classes = (IsOwner,)


class DeleteQuery(generics.DestroyAPIView):
	queryset = Query.objects.all()
	serializer_class = QuerySerializer
	permission_classes = (IsOwner,)


class ShareQuery(generics.ListCreateAPIView):
	queryset = QuerySharedUsers.objects.all()
	serializer_class = ShareQuerySerializer
	permission_classes = (IsAuthenticated,)


class DeleteSharedQuery(viewsets.ModelViewSet):
	serializer_class = UnshareQuerySerializer
	permission_classes = (IsSharedOwner,)

	def get_object(self):
		user = self.request.user
		_query = Query.objects.get(id=self.kwargs['pk'])
		_shared_query = QuerySharedUsers.objects.get(person=user, query=_query)
		return _shared_query