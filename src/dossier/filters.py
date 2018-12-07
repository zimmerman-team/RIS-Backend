from django_filters.rest_framework import FilterSet
from django_filters import DateFilter
from dossier.models import Dossier


class CustomDateFilter(FilterSet):
    created_at_start_date = DateFilter(name="created_at", lookup_expr='gte')
    created_at_end_date = DateFilter(name="created_at", lookup_expr='lte')
    last_modified_start_date = DateFilter(name="last_modified", lookup_expr='gte')
    last_modified_end_date = DateFilter(name="last_modified", lookup_expr='lte')

    class Meta:
        model = Dossier
        fields = ['created_at', 'last_modified', ]