from rest_framework import generics, pagination
from rest_framework.permissions import IsAuthenticated

from favorite.serializers import FavoriteSerializer, FavoriteAddSerializer
from favorite.models import Favorite


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 300


class FavoriteList(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
            return Favorite.objects.filter(owner=self.request.user)
        return Favorite.objects.filter(owner=self.request.user, item__published=True)


class FavoriteAdd(generics.ListCreateAPIView):
    serializer_class = FavoriteAddSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Favorite.objects.filter(owner=user)


class FavoriteDelete(generics.RetrieveDestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Favorite.objects.filter(owner=user)
