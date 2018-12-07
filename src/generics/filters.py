from django_filters.rest_framework import FilterSet
from django_filters import DateFilter, BooleanFilter, Filter, CharFilter
from django.db.models import Q
from generics.models import Event, Document, EventAgendaItem, CombinedItem, Note
from django.contrib.postgres.search import SearchQuery


def reduce_comma(arr, value):
    if value[:1] == ' ' and len(arr):
        arr[len(arr) - 1] = arr[len(arr) - 1] + "," + value
    else:
        arr.append(value)
    return arr


class CommaSeparatedCharFilter(CharFilter):

    def filter(self, qs, value):

        if value:
            value = value.split(',')
            value = reduce(reduce_comma, value, [])

        self.lookup_expr = 'in'

        return super(CommaSeparatedCharFilter, self).filter(qs, value)


class EventFilter(FilterSet):
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'jurisdiction', 'start_time', 'classification', 'location',
                  'parent_event', 'documents', 'agenda']


class EventDateFilter(FilterSet):
    start_date = DateFilter(name="start_time", lookup_expr='gte')
    end_date = DateFilter(name="start_time", lookup_expr='lte')
    no_parent = BooleanFilter(name='parent_event', lookup_expr='isnull')

    class Meta:
        model = Event
        fields = ['id', 'classification', 'start_time', 'parent_event__id', 'no_parent', 'notubiz_id']


class SearchQueryFilter(Filter):

    def filter(self, qs, values):
        if values:
            value_list = values.split(',')
            for value in value_list:
                if value:
                    qs = qs.filter(Q(doc_content__vector=SearchQuery(value, config='dutch')) |
                                   Q(name__icontains=value) |
                                   Q(item_type__icontains=value))

        return qs


class DocDateFilter(FilterSet):
    start_date = DateFilter(name="date", lookup_expr='gte')
    end_date = DateFilter(name="date", lookup_expr='lte')
    q = SearchQueryFilter()

    class Meta:
        model = Document
        fields = ['id', 'date', 'media_type', 'q']


class CombinedDateFilter(FilterSet):
    start_date = DateFilter(name="date", lookup_expr='gte')
    end_date = DateFilter(name="date", lookup_expr='lte')
    q = SearchQueryFilter()
    item_type = CommaSeparatedCharFilter(name='item_type', lookup_expr='in')

    class Meta:
        model = CombinedItem
        fields = {
            'id': ['exact'],
            'date': ['exact'],
            'item_type': ['exact'],
            'q': ['exact'],
            'classification': ['exact'],
            'name': ['exact', 'icontains']
        }


class SearchDocuments(Filter):
    def filter(self, qs, value):
        if value:
            documents_id = qs.values_list('document_id', flat=True)
            documents = Document.objects.filter(pk__in=documents_id)
            filtered_docs_id = documents.filter(
                Q(text__icontains=value) | Q(doc_content__content__icontains=value)).values_list('id', flat=True)
            return qs.filter(document_id__in=filtered_docs_id)
        return qs


class NotesFilter(FilterSet):
    associated_doc = SearchDocuments()

    class Meta:
        model = Note
        fields = {
            'title': ['exact', 'contains'],
            'description': ['exact', 'contains'],
            'created_at': ['exact', 'contains'],
            'last_modified': ['exact', 'contains'],
            'associated_doc': ['exact']
        }


class AgendaItemFilter(FilterSet):
    class Meta:
        model = EventAgendaItem
        fields = ['id','event__id']
