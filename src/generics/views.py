import json
import os

from django.db import IntegrityError
from rest_framework import generics, filters, status, pagination, viewsets
from django.http import Http404, HttpResponse, JsonResponse
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.postgres.search import SearchVector

from accounts.models import User
from generics.scripts.document_scraper import NotubizDocumentScraper
from generics.models import Event, Note, EventDocument
from generics.models import Document
from generics.models import EventAgendaItem
from generics.models import EventAgendaMedia
from generics.models import EventAgendaMediaLink
from generics.models import EventMedia
from generics.models import CombinedItem
from generics.models import ReceivedDocument
from generics.models import CouncilAddress
from generics.models import Commitment
from generics.models import WrittenQuestion
from generics.models import Motion
from generics.models import PublicDocument
from generics.models import ManagementDocument
from generics.models import PolicyDocument
from generics.models import MyAgenda
from generics.models import Speaker
from generics.models import SpeakerIndex
from generics.models import PublicDossier
from generics.models import PublicDossierContent

from filters import EventDateFilter, NotesFilter
from filters import DocDateFilter
from filters import AgendaItemFilter
from filters import CombinedDateFilter

from generics.serializers import EventListSerializer, NoteListSerializer
from generics.serializers import ChildEventsListSerializer
from generics.serializers import EventDetailSerializer, BasicEventDetailSerializer
from generics.serializers import DocumentSerializer
from generics.serializers import BasicEventAgendaItemSerializer
from generics.serializers import EventAgendaItemSerializer
from generics.serializers import EventAgendaMediaSerializer
from generics.serializers import EventAgendaMediaLinkSerializer
from generics.serializers import EventMediaSerializer
from generics.serializers import CombinedSerializer
from generics.serializers import ReceivedDocumentSerializer
from generics.serializers import CouncilAddressSerializer
from generics.serializers import CommitmentSerializer
from generics.serializers import WrittenQuestionSerializer
from generics.serializers import MotionSerializer
from generics.serializers import PublicDocumentSerializer
from generics.serializers import ManagementDocumentSerializer
from generics.serializers import PolicyDocumentSerializer
from generics.serializers import GetItemCountsSerializer
from generics.serializers import SpeakerSerializer
from generics.serializers import SpeakerIndexSerializer
from generics.serializers import DocumentContent
from generics.serializers import PublicDossierListSerializer
from generics.serializers import FullPublicDossierDetail, BasicPublicDossierDetail

from generics.permissions import PublicDossierPermission

from rest_framework.decorators import api_view
from itertools import chain
import datetime
from dateutil import parser
import after_response
from django.shortcuts import render
from django.conf import settings

import django_filters.rest_framework

def index(request):
    context = {
        'municipality': settings.RIS_MUNICIPALITY,
    }
    return render(request, 'index.html', context=context)


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class CombinedList(generics.ListAPIView):
    serializer_class = CombinedSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name', 'classification', 'item_type')
    search_fields = ('name', 'classification', 'date',)
    ordering_fields = ('name', 'date', 'last_modified')
    filter_class = CombinedDateFilter
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = CombinedItem.objects.all().exclude(item_type='child_event')
        if self.request.user.id != None:
            if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
                return queryset
        queryset = queryset.filter(published=True)
        return queryset


class CombinedDetail(generics.RetrieveAPIView):
    queryset = CombinedItem.objects.all()
    serializer_class = CombinedSerializer


@api_view(['GET'])
def get_next_politieke_markt_number(request):
    numbers = []
    queryset = Event.objects.only('name', 'parent_event').filter(parent_event=None).order_by('-start_time')[:50]
    queryset = [q for q in queryset if 'Politieke Markt' in q.name]
    for item in queryset:
        arr = [int(s) for s in item.name.replace('e', '').split() if s.isdigit()]
        if len(arr) > 0:
            numbers.append(arr[0])
    numbers.sort(reverse=True)
    if len(numbers) > 0:
        return JsonResponse({ 'value': str(numbers[0] + 1) + 'e' })
    else:
        return JsonResponse({ 'value': None })


@api_view(['POST'])
def get_event_publish_status(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['event_id']
            _event = Event.objects.get(id=event_id)
            return JsonResponse({ "value": _event.published })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def change_event_publish_status(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['event_id']
            published = params['published']
            _event = Event.objects.get(id=event_id)
            _event.published = published
            _event.save()
            ci = CombinedItem.objects.get(item_id=event_id, item_type='event')
            ci.published = published
            ci.save()
            return JsonResponse({ "response": "success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@after_response.enable
def update_vector():
    vector = SearchVector('content', config='dutch')
    DocumentContent.objects.update(vector=vector)


@api_view(['POST'])
def add_documents_to_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['event_id']
            docs = params['docs']
            event = Event.objects.get(id=event_id)
            for d in docs:
                if not EventDocument.objects.filter(event=event, document_id=d['id'], document_type=d['type']).exists():
                    EventDocument.objects.create(event=event, document_id=d['id'], document_type=d['type'])
            return JsonResponse({ "response": "Success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def remove_document_from_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['event_id']
            document = params['document']
            event = Event.objects.get(id=event_id)
            if document['attachment_type'] == 0:
                EventDocument.objects.get(event=event, document_id=document['id'], document_type=document['type']).delete()
            if document['attachment_type'] == 1:
                try:
                    actual_doc = Document.objects.get(id=document['id'])
                    actual_doc.event = None
                    actual_doc.attached_to = 'none'
                    actual_doc.save()
                except Exception:
                    print 'LOC 200: {}'.format(e)
            return JsonResponse({ "response": "Success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def create_new_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            name = params['name']
            description = params['description']
            location = params['location']
            start_time = parser.parse(params['start_time'])
            try:
                end_time = parser.parse(params['end_time'])
                if start_time > end_time:
                    return JsonResponse({ "response": "start_time must be smaller that end_time" })
            except:
                end_time = None
            published = params['published']
            if Event.objects.only("name", "start_time").filter(name=name, start_time=start_time).exists():
                return JsonResponse({ "response": "Event with same name and start_time exists" })
            event = Event.objects.create(
                name=name,
                description=description,
                last_modified=datetime.datetime.now(),
                start_time=start_time,
                end_time=end_time,
                published=published,
                location=location
            )
            content = DocumentContent.objects.create(
                content=description
            )
            CombinedItem.objects.create(
                name=name,
                doc_content=content,
                date=start_time,
                last_modified=datetime.datetime.now(),
                item_type='event',
                item_id=event.id,
                published=published
            )
            update_vector.after_response()
            return JsonResponse({ "id": event.id })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def edit_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['id']
            name = params['name']
            description = params['description']
            location = params['location']
            start_time = parser.parse(params['start_time'])
            try:
                end_time = parser.parse(params['end_time'])
                if start_time > end_time:
                    return JsonResponse({ "response": "start_time must be smaller that end_time" })
            except:
                end_time = None
            # published = params['published']
            if Event.objects.only("name", "start_time").filter(name=name, start_time=start_time).exclude(id=event_id).exists():
                return JsonResponse({ "response": "Event with same name and start_time exists" })
            Event.objects.filter(id=event_id).update(
                name=name,
                description=description,
                last_modified=datetime.datetime.now(),
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
            content = DocumentContent.objects.create(
                content=description
            )
            CombinedItem.objects.filter(item_id=event_id, item_type='event').update(
                name=name,
                doc_content=content,
                date=start_time,
                last_modified=datetime.datetime.now(),
            )
            update_vector.after_response()
            return JsonResponse({ "id": event_id })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


class EventList(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventListSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name', 'classification',)
    search_fields = ('name', 'description', 'classification', 'start_time',)
    ordering_fields = ('name', 'start_time', 'last_modified')
    filter_class = EventDateFilter
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        try:
            if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
                return Event.objects.all()
            else:
                return Event.objects.filter(published=True)
        except:
            return Event.objects.filter(published=True)


class PublicDossierList(generics.ListCreateAPIView):
    serializer_class = PublicDossierListSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ('title',)
    search_fields = ('title',)
    ordering_fields = ('title', 'created_at', 'last_modified')
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        try:
            dossier = self.request.query_params['dossier']
        except:
            dossier = None
        try:
            if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
                if dossier:
                    return PublicDossier.objects.filter(depth=0).exclude(id=dossier)
                return PublicDossier.objects.filter(depth=0)
            else:
                if dossier:
                    return PublicDossier.objects.filter(published=True, depth=0, parent_dossier=None).exclude(id=dossier)
                return PublicDossier.objects.filter(published=True, depth=0, parent_dossier=None)
        except:
            if dossier:
                return PublicDossier.objects.filter(published=True, depth=0, parent_dossier=None).exclude(id=dossier)
            return PublicDossier.objects.filter(published=True, depth=0, parent_dossier=None)


class PublicDossierDetail(generics.RetrieveAPIView):
    queryset = PublicDossier.objects.all()

    def get_serializer_class(self):
        try:
            if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
                return FullPublicDossierDetail
            return BasicPublicDossierDetail
        except:
            return BasicPublicDossierDetail


class PublicDossierUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = PublicDossier.objects.all()
    serializer_class = FullPublicDossierDetail
    permission_classes = (PublicDossierPermission,)

    def delete(self, request, *args, **kwargs):
        dossier = self.get_object()
        try:
            CombinedItem.objects.get(item_id=dossier.id, item_type='public_dossier').delete()
            content = PublicDossierContent.objects.filter(dossier=dossier)
            for c in content:
                if c.item_type == 'public_dossier':
                    pd = PublicDossier.objects.get(id=c.item.item_id)
                    pd.published = True
                    pd.depth = 0
                    pd.last_modified = datetime.datetime.now()
                    pd.save()
                    ci = CombinedItem.objects.get(id=c.item.id)
                    ci.published = True
                    ci.save()
        except Exception as e:
            print 'LOC 140: {}'.format(e)
        return self.destroy(request, *args, **kwargs)


@api_view(['POST'])
def check_if_dossier_title_exists(request):
    params = json.loads(request.body)
    title = params['title']
    if PublicDossier.objects.filter(title=title).exists():
        return JsonResponse({ "exists": True })
    else:
        return JsonResponse({ "exists": False })


@api_view(['POST'])
def change_dossier_publish_status(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            dossier_id = params['id']
            value = params['value']
            try:
                dossier = PublicDossier.objects.get(id=dossier_id)
                dossier.published = value
                dossier.last_modified = datetime.datetime.now()
                dossier.save()
                dci = CombinedItem.objects.get(item_id=dossier_id, item_type='public_dossier')
                dci.published = value
                dci.save()
                content = PublicDossierContent.objects.filter(dossier=dossier)
                for c in content:
                    if c.item_type == 'public_dossier':
                        pd = PublicDossier.objects.get(id=c.item.item_id)
                        pd.published = value
                        pd.last_modified = datetime.datetime.now()
                        pd.save()
                        ci = CombinedItem.objects.get(id=c.item.id)
                        ci.published = value
                        ci.save()
                return JsonResponse({'response': 'Success'})
            except Exception as e:
                print 'LOC 167: {}'.format(e)
                return JsonResponse({'response': 'Failure'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['POST'])
def get_public_dossier_child_dossiers(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            dossier_id = params['id']
            result = []
            if PublicDossier.objects.filter(parent_dossier=dossier_id).exists():
                for d1 in PublicDossier.objects.filter(parent_dossier=dossier_id):
                    CombinedItem.objects.get(item_id=d1.id, item_type='public_dossier')
                    has_dossiers = False
                    if PublicDossierContent.objects.filter(dossier=d1.id).exists() or PublicDossier.objects.filter(parent_dossier=d1.id).exists():
                        has_dossiers = True
                    result.append({
                        'id': d1.id,
                        'name': d1.title,
                        'combined_id': CombinedItem.objects.get(item_id=d1.id, item_type='public_dossier').id,
                        'has_dossiers': has_dossiers,
                    })
            if PublicDossierContent.objects.filter(dossier=dossier_id, item_type='public_dossier').exists():
                for d2 in PublicDossierContent.objects.filter(dossier=dossier_id, item_type='public_dossier'):
                    has_dossiers = False
                    if PublicDossierContent.objects.filter(dossier=d2.item.item_id, item_type='public_dossier').exists() or PublicDossier.objects.filter(parent_dossier=d2.item.item_id).exists():
                        has_dossiers = True
                    result.append({
                        'id': d2.item.item_id,
                        'name': d2.item.name,
                        'combined_id': d2.item.id,
                        'has_dossiers': has_dossiers,
                    })
            return JsonResponse(result, safe=False)
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['POST'])
def add_content_to_public_dossier(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            items = params['items']
            dossier_id = params['dossier']
            for item in items:
                item_id = item['id']
                item_type = item['type']
                try:
                    dossier = PublicDossier.objects.get(id=dossier_id)
                    dossier.last_modified = datetime.datetime.now()
                    dossier.save()
                    ci = CombinedItem.objects.get(id=item_id)
                    PublicDossierContent.objects.create(dossier=dossier, item=ci, item_type=item_type)
                    if item_type == 'public_dossier':
                        dossier_item = PublicDossier.objects.get(id=ci.item_id)
                        dossier_item.depth = 1
                        dossier_item.last_modified = datetime.datetime.now()
                        dossier_item.save()
                except Exception as e:
                    print 'LOC 159: {}'.format(e)
                    return JsonResponse({'response': 'Failure'})
            return JsonResponse({'response': 'Success'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['POST'])
def remove_public_dossier_content(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            items = params['items']
            dossier_id = params['dossier']
            dossier_item = PublicDossier.objects.get(id=dossier_id)
            for item in items:
                item_id = item['id']
                item_type = item['type']
                try:
                    if item_type == 'public_dossier':
                        ci = CombinedItem.objects.get(id=item_id, item_type=item_type)
                        PublicDossierContent.objects.get(dossier=dossier_id, item=ci, item_type=item_type).delete()
                        if not PublicDossierContent.objects.filter(item=ci, item_type=item_type).exists() and not dossier_item.parent_dossier:
                            dossier_item.depth = 0
                    else:
                        dossier = PublicDossier.objects.get(id=dossier_id)
                        dossier.last_modified = datetime.datetime.now()
                        dossier.save()
                        ci = CombinedItem.objects.get(id=item_id, item_type=item_type)
                        PublicDossierContent.objects.get(dossier=dossier, item=ci, item_type=item_type).delete()
                except Exception as e:
                    print 'LOC 219: {}'.format(e)
                    return JsonResponse({'response': 'Failure'})
            dossier_item.last_modified = datetime.datetime.now()
            dossier_item.save()
            return JsonResponse({'response': 'Success'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['POST'])
def create_new_child_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            name = params['name']
            parent_id = params['parent_id']
            try:
                start_time = parser.parse(params['start_time'])
            except:
                start_time = None
            try:
                end_time = parser.parse(params['end_time'])
            except:
                end_time = None
            # published = params['published']
            if Event.objects.filter(id=parent_id).exists():
                parent_event = Event.objects.get(id=parent_id)
            else:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Parent event not found")
            if end_time:
                if start_time > end_time:
                    return JsonResponse({ "response": "start_time must be smaller that end_time" })

            event = Event.objects.create(
                name=name,
                last_modified=datetime.datetime.now(),
                start_time=start_time,
                end_time=end_time,
                published=parent_event.published,
                parent_event=parent_event,
                classification=name,
                location=name,
            )
            CombinedItem.objects.create(
                name=name,
                date=start_time,
                last_modified=datetime.datetime.now(),
                item_type='child_event',
                item_id=event.id,
                published=parent_event.published
            )
            return JsonResponse({ "response": "success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def edit_child_event(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event_id = params['event_id']
            try:
                start_time = parser.parse(params['start_time'])
            except:
                start_time = None
            try:
                end_time = parser.parse(params['end_time'])
            except:
                end_time = None

            if end_time:
                if start_time > end_time:
                    return JsonResponse({ "response": "start_time must be smaller that end_time" })

            Event.objects.filter(id=event_id).update(
                last_modified=datetime.datetime.now(),
                start_time=start_time,
                end_time=end_time,
            )

            CombinedItem.objects.filter(item_id=event_id, item_type='child_event').update(
                date=start_time,
                last_modified=datetime.datetime.now(),
            )
            return JsonResponse({ "response": "success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


class ChildEventList(generics.ListAPIView):
    serializer_class = ChildEventsListSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        pk = self.kwargs.get(self.lookup_field)
        events = Event.objects.filter(parent_event=pk)
        return events.order_by("start_time")


class getChildEvents(APIView):

    def get_objects(self, pk):
        try:
            return Event.objects.filter(parent_event=pk)
        except:
            raise Http404

    def get(self, request, pk, format=None):
        events = self.get_objects(pk)
        serializer = ChildEventsListSerializer(events, many=True)
        return Response(serializer.data)


class EventDetail(APIView):

    def get_user_object(self):
        return self.request.user

    def get_object(self, pk):
        try:
            return Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        event = self.get_object(pk)
        serializer = self.get_serializer_class(event)
        return Response(serializer.data)

    def get_serializer_class(self, event):
        if self.request.GET.get('basicData'):
            return BasicEventDetailSerializer(event)
        return EventDetailSerializer(event)

    def put(self, request, pk, format=None):
        event = self.get_object(pk)
        serializer = EventDetailSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        event = self.get_object(pk)
        event.delete()
        item_type = request.query_params['type']
        try:
            CombinedItem.objects.get(item_id=pk, item_type=item_type).delete()
            if Event.objects.filter(parent_event=pk):
                for e in Event.objects.filter(parent_event=pk):
                    CombinedItem.objects.get(item_id=e.id, item_type='child_event').delete()
        except Exception as e:
            print "LOC 519: {}".format(e)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def check_if_time_and_room_allocated(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            room = params['room']
            start_time = params['start_time']
            end_time = params['end_time']
            try:
                start_time = parser.parse(params['start_time'])
            except:
                start_time = None
            try:
                start_time = parser.parse(params['start_time'])
            except:
                end_time = None
            try:
                event_id = params['event_id']
            except:
                event_id = None
            if not start_time and not end_time:
                return JsonResponse({ "allocated": False })
            if end_time:
                if Event.objects.filter(name=room, start_time__lt=end_time, end_time__gt=start_time).exists():
                    if event_id:
                        if Event.objects.filter(name=room, start_time__lt=end_time, end_time__gt=start_time).exclude(id=int(event_id)).exists():
                            return JsonResponse({ "allocated": True })
                        else:
                            return JsonResponse({ "allocated": False })
                    return JsonResponse({ "allocated": True })
                else:
                    return JsonResponse({ "allocated": False })
            else:
                if Event.objects.filter(name=room, start_time=start_time).exists():
                    if event_id:
                        if Event.objects.filter(name=room, start_time=start_time).exclude(id=int(event_id)).exists():
                            return JsonResponse({ "allocated": True })
                        else:
                            return JsonResponse({ "allocated": False })
                    return JsonResponse({ "allocated": True })
                else:
                    return JsonResponse({ "allocated": False })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


class DocumentList(generics.ListCreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('text')
    ordering_fields = ('text', 'date', 'last_modified')
    filter_class = DocDateFilter
    pagination_class = LargeResultsSetPagination


class DocumentDetail(APIView):
    def get_object(self, pk):
        try:
            return Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        document = self.get_object(pk)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        document = self.get_object(pk)
        serializer = DocumentSerializer(document, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        document = self.get_object(pk)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def edit_document(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            def _get_actual_doc(doc, doc_typ):
                if doc_typ == Document:
                    real_doc = doc
                elif doc_typ == Commitment:
                    real_doc = doc.new_document
                elif doc_typ == CouncilAddress or doc_typ == WrittenQuestion:
                    real_doc = doc.question_document
                    if not doc:
                        real_doc = doc.interim_answer_document
                    if not doc:
                        real_doc = doc.answer_document
                else:
                    real_doc = doc.document
                return real_doc

            type_choice = {
                    "motion": Motion,
                    "document": Document,
                    "format": PublicDocument,
                    "commitment": Commitment,
                    "council_address": CouncilAddress,
                    "policy_document": PolicyDocument,
                    "written_question": WrittenQuestion,
                    "received_document": ReceivedDocument,
                    "management_document": ManagementDocument,
                }
            data = request.data
            subject = data['subject']
            typez = data['type']
            portfolio = data['portfolio']
            stats = data['status']
            doc_id = data['doc_id']
            prev_type = data['prev_type']
            published = data['published']

            try:
                author_id = data['author_id']
                author = User.objects.get(pk=author_id)
            except:
                author = None

            try:
                stats = data['status']
            except KeyError:
                stats = None

            try:
                dossier_id = data['dossier_id']
            except KeyError:
                dossier_id=False

            public_dossier = None

            if dossier_id and dossier_id is not None and not dossier_id == 'null':
                public_dossier = PublicDossier.objects.get(pk=dossier_id)

            doc_type = type_choice[typez]
            prev_doc_type = type_choice[prev_type]

            ci = CombinedItem.objects.get(item_id=doc_id, item_type=prev_type)

            if doc_type == prev_doc_type:
                document = doc_type.objects.get(pk=doc_id)
                # This is the actual Document object
                actual_doc = _get_actual_doc(document, doc_type)
            else:
                prev_doc = prev_doc_type.objects.get(pk=doc_id)
                # This is the actual Document object
                actual_doc = _get_actual_doc(prev_doc, prev_doc_type)
                #And now because the document type has changed we need to create a new
                #Document of that type and delete the old one lol!
                # And we gonna create this document here with only the fields
                # That are necesesarry to be transfered from the previous doc
                file_name=ci.name
                date = ci.date

                if doc_type == ReceivedDocument:
                    document = ReceivedDocument.objects.create(
                        date=date,
                        document=actual_doc,
                        description=file_name,
                        publication_date=date,
                        date_created=date,
                        document_type=typez,
                        organisation=None,
                        last_modified = datetime.datetime.now(),
                    )
                elif doc_type == Motion:
                    document = Motion.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        document=actual_doc,
                        date_created=date,
                        document_type=typez,
                        comments=file_name,
                        organisation=None
                    )
                elif doc_type == PublicDocument:
                    document = PublicDocument.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        document=actual_doc,
                        date_created=date,
                        document_type=typez,
                        document_date=date,
                        publication_date=date,
                        organisation=None
                    )
                elif doc_type == Commitment:
                    document = Commitment.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        item_created=date,
                        new_document=actual_doc,
                        text=file_name,
                        organisation=None
                    )
                elif doc_type == CouncilAddress:
                    document = CouncilAddress.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        item_created=date,
                        publication_date=date,
                        question_date=date,
                        question_document=actual_doc,
                        interim_answer_date=date,
                        interim_answer_document=actual_doc,
                        answer_date=date,
                        answer_document=actual_doc,
                        name=file_name,
                        organisation=None
                    )
                elif doc_type == PolicyDocument:
                    document = PolicyDocument.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        item_created=date,
                        document=actual_doc,
                        document_type=typez,
                        document_date=date,
                        publication_date=date,
                        organisation=None
                    )
                elif doc_type == WrittenQuestion:
                    document = WrittenQuestion.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        item_created=date,
                        publication_date=date,
                        question_date=date,
                        question_document=actual_doc,
                        interim_answer_date=date,
                        interim_answer_document=actual_doc,
                        answer_date=date,
                        answer_document=actual_doc,
                        organisation=None
                    )
                elif doc_type == ManagementDocument:
                    document = ManagementDocument.objects.create(
                        title=file_name,
                        last_modified=datetime.datetime.now(),
                        item_created=date,
                        document=actual_doc,
                        document_type=typez,
                        document_date=date,
                        publication_date=date,
                        date_created=date,
                        organisation=None
                    )
                elif doc_type == Document:
                    document = actual_doc
                else:
                    document = Document.objects.none()

                # And now we delete the previous doc
                if prev_doc_type != Document:
                    prev_doc.delete()

            try:
                # We also have to adjust the PublicDossierContent
                content = PublicDossierContent.objects.get(dossier=actual_doc.public_dossier, item=ci, item_type=ci.item_type)
            except PublicDossierContent.DoesNotExist:
                content = PublicDossierContent.objects.none()

            # And now after all that bs, we can actually modify the objects we need to modify, yay!

            # So We first modify the actual Document object
            actual_doc.subject = subject
            actual_doc.portfolio = portfolio
            actual_doc.status = stats
            if public_dossier:
                actual_doc.public_dossier = public_dossier
            actual_doc.author = author
            actual_doc.last_modified = datetime.datetime.now()
            actual_doc.save()
            # Now we change the document if its of another type
            # Because we already saved the Document object instance
            if not document == Document:
                document.subject = subject
                document.portfolio = portfolio
                document.status = stats
                document.author = author
                document.save()

            # And Finally we update the combined item object
            ci.subject = subject
            ci.portfolio = portfolio
            ci.status = stats
            ci.author = author
            ci.item_id = document.id
            ci.item_type = typez
            ci.published = published
            ci.last_modified = datetime.datetime.now()
            ci.save()

            # Update the content with new shit
            if content:
                content.dossier = public_dossier
                content.item = ci
                content.item_type = ci.item_type
                content.save()
            elif public_dossier:
                PublicDossierContent.objects.create(dossier=public_dossier, item=ci, item_type=ci.item_type)

            return JsonResponse({'response': 'succesvol geupdatet'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Unauthorized")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def delete_document(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':

            data = request.data
            typez = data['doc_type']
            doc_id = data['doc_id']

            doc_type = {
                "motion": Motion,
                "document": Document,
                "format": PublicDocument,
                "commitment": Commitment,
                "council_address": CouncilAddress,
                "policy_document": PolicyDocument,
                "written_question": WrittenQuestion,
                "received_document": ReceivedDocument,
                "management_document": ManagementDocument,
            }[typez]

            ci = CombinedItem.objects.get(item_id=doc_id, item_type=typez)

            doc = doc_type.objects.get(pk=doc_id)

            # We delete the attached doc == the 'Document' object if it exists
            if typez != "document":
                try:
                    actual_doc = _get_actual_doc(doc, doc_type)
                    actual_doc.delete()
                except:
                    # Seems like no document has been attached to other docs
                    pass

            # We delete the doc of the specified type
            doc.delete()

            # We delete public dossier content
            for content in PublicDossierContent.objects.filter(item=ci):
                content.delete()

            # We have to delete the agenda media for events, cause it doesn't delete automatically with the doc :/
            links = EventAgendaMediaLink.objects.filter(item_id=doc_id, media_type=typez)

            if links:
                for link in links:
                    # so here we delete the media object attached to the link
                    link.media.delete()
                    # and here we delete the link itself
                    link.delete()

            # And we delete the combined item
            ci.delete()

            return JsonResponse({'response': 'succesvol vervwijden'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Unauthorized")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def upload_documents(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            files = request.FILES.getlist('files')
            subject = request.POST['subject']
            typez = request.POST['type']
            portfolio = request.POST['portfolio']

            if request.POST['published'] == 'true':
                published = True
            else:
                published = False

            try:
                author_id = request.POST['author_id']
                author = User.objects.get(pk=author_id)
            except KeyError:
                author = None

            try:
                status = request.POST['status']
            except KeyError:
                status = None

            try:
                dossier_id = request.POST['dossier_id']
            except KeyError:
                dossier_id = False

            public_dossier = PublicDossier.objects.none()
            file_names = []
            doc_ids = []
            actual_docs_ids = []
            types = []

            if dossier_id and dossier_id is not None and not dossier_id == 'null':
                public_dossier = PublicDossier.objects.get(pk=dossier_id)

            backend_url = request.build_absolute_uri('/') + 'api/'
            # Ofcourse yall need to add the filename here for it to work
            backend_download_url = backend_url + 'media/documents/'
            for filez in files:
                file_name = filez.name
                try:
                    dot_index = file_name.index('.')
                    file_name = file_name[:dot_index]
                except Exception:
                    pass

                doc_type = {
                    "motion": Motion,
                    "document": Document,
                    "format": PublicDocument,
                    "commitment": Commitment,
                    "council_address": CouncilAddress,
                    "policy_document": PolicyDocument,
                    "written_question": WrittenQuestion,
                    "received_document": ReceivedDocument,
                    "management_document": ManagementDocument,
                } [typez]

                # So for all documents we create a Document object,
                # And after that associate it with an appropriate type of document
                increment = 1
                # Here we give an incrementation to the file, if it already exists in the document
                while Document.objects.filter(text=file_name):
                    try:
                        file_name = file_name[:file_name.index(' (')] + '(' + `increment` + ')'
                    except:
                        file_name = file_name + ' (' + `increment` + ')'
                    increment = increment + 1

                # Here we save the Document
                doc_item = Document.objects.create(
                    file=filez,
                    text=file_name,
                    date=datetime.datetime.now(),
                    status=status,
                    subject=subject,
                    portfolio=portfolio,
                    public_dossier=public_dossier if public_dossier else None,
                    attached_to='none' if typez == "document" else typez,
                    author=author,
                    last_modified=datetime.datetime.now(),
                )

                # This is the actual file name as saved in our folders
                # because when there are two files uploaded with the same naem
                # we give them the pretty name wich is file_name
                # but django stores them with a random generated ending
                # and this is how we get the actually stored files name
                actual_file_name = os.path.basename(doc_item.file.name)

                download_url = backend_download_url + actual_file_name

                # And now that we have the actual name and the download url of the file
                # we save it properly
                doc_item.url = download_url
                doc_item.file_path = download_url
                doc_item.save()

                # Here we attach the document to an appropriate type if the type is any other than
                # Document itself

                if doc_type == ReceivedDocument:
                    other_doc_item = ReceivedDocument.objects.create(
                        date=datetime.datetime.now(),
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        document=doc_item,
                        description=file_name,
                        publication_date=datetime.datetime.now(),
                        date_created=datetime.datetime.now(),
                        document_type=typez,
                        organisation=None
                    )
                elif doc_type == Motion:
                    other_doc_item = Motion.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        document=doc_item,
                        date_created=datetime.datetime.now(),
                        document_type=typez,
                        comments=file_name,
                        organisation=None
                    )
                elif doc_type == PublicDocument:
                    other_doc_item = PublicDocument.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        document=doc_item,
                        date_created=datetime.datetime.now(),
                        document_type=typez,
                        document_date=datetime.datetime.now(),
                        publication_date=datetime.datetime.now(),
                        organisation=None
                    )
                elif doc_type == Commitment:
                    other_doc_item = Commitment.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        item_created=datetime.datetime.now(),
                        new_document=doc_item,
                        text=file_name,
                        organisation=None
                    )
                elif doc_type == CouncilAddress:
                    other_doc_item = CouncilAddress.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        item_created=datetime.datetime.now(),
                        publication_date=datetime.datetime.now(),
                        question_date=datetime.datetime.now(),
                        question_document=doc_item,
                        interim_answer_date=datetime.datetime.now(),
                        interim_answer_document=doc_item,
                        answer_date=datetime.datetime.now(),
                        answer_document=doc_item,
                        name=file_name,
                        organisation=None
                    )
                elif doc_type == PolicyDocument:
                    other_doc_item = PolicyDocument.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        item_created=datetime.datetime.now(),
                        document=doc_item,
                        document_type=typez,
                        document_date=datetime.datetime.now(),
                        publication_date=datetime.datetime.now(),
                        organisation=None
                    )
                elif doc_type == WrittenQuestion:
                    other_doc_item = WrittenQuestion.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        item_created=datetime.datetime.now(),
                        publication_date=datetime.datetime.now(),
                        question_date=datetime.datetime.now(),
                        question_document=doc_item,
                        interim_answer_date=datetime.datetime.now(),
                        interim_answer_document=doc_item,
                        answer_date=datetime.datetime.now(),
                        answer_document=doc_item,
                        organisation=None
                    )
                elif doc_type == ManagementDocument:
                    other_doc_item = ManagementDocument.objects.create(
                        title=file_name,
                        status=status,
                        subject=subject,
                        portfolio=portfolio,
                        author=author,
                        last_modified=datetime.datetime.now(),
                        item_created=datetime.datetime.now(),
                        document=doc_item,
                        document_type=typez,
                        document_date=datetime.datetime.now(),
                        publication_date=datetime.datetime.now(),
                        date_created=datetime.datetime.now(),
                        organisation=None
                    )
                else:
                    other_doc_item = Document.objects.none()

                saved_doc = doc_item
                if other_doc_item:
                    other_doc_item.save()
                    saved_doc = other_doc_item

                # And here we create the combined item and attach the document to it
                ci = CombinedItem.objects.create(
                    item_id=saved_doc.id,
                    name=file_name,
                    date=datetime.datetime.now(),
                    url=download_url,
                    last_modified=datetime.datetime.now(),
                    item_type=typez,
                    status=status,
                    subject=subject,
                    portfolio=portfolio,
                    author=author,
                    published=published
                )
                ci.save()

                # Here we add the combined item to the public dossier, if one was selected
                if public_dossier:
                    PublicDossierContent.objects.create(dossier=public_dossier, item=ci, item_type=typez)

                # Here we add the filenames, its gonna be used for the scanner
                file_names.append(actual_file_name)
                # These are the DIFIRENT TYPE DOCUMENT IDS
                doc_ids.append(saved_doc.id)
                # These are their types
                types.append(typez)
                # These are the actual DOCUMENT OBJECT IDS
                actual_docs_ids.append(doc_item.id)

            scan_uploaded_docs.after_response(file_names, doc_ids, actual_docs_ids, types)
            return JsonResponse({'response': 'Bestand geupload'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Unauthorized")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def change_document_publish_status(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            doc_id = params['doc_id']
            doc_type = params['doc_type']
            value = params['value']
            try:
                ci = CombinedItem.objects.get(item_id=doc_id, item_type=doc_type)
                ci.published = value
                ci.save()
                return JsonResponse({'response': 'Success'})
            except Exception as e:
                print 'LOC 1301: {}'.format(e)
                return JsonResponse({'response': 'Failure'})
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Unauthorized")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@after_response.enable
def scan_uploaded_docs(file_names, doc_ids, actual_docs_ids, types):
    scraper = NotubizDocumentScraper()

    for index, file_name in enumerate(file_names):
        document_content_text = scraper.getFileContent(file_name, actual_docs_ids[index], '/media/documents/')

        document_content = DocumentContent.objects.create(content=document_content_text)

        # Here we save the scanned status and the document_content for
        # the actual Document object
        doc = Document.objects.get(pk=actual_docs_ids[index])
        doc.document_content_scanned = True
        doc.file_path = file_name
        doc.doc_content = document_content
        doc.save()

        # Here we save the document content to the appropriate TYPE of Document
        ci = CombinedItem.objects.get(item_id=doc_ids[index], item_type=types[index])
        ci.doc_content = document_content
        ci.save()


class EventAgendaItemList(generics.ListCreateAPIView):
    queryset = EventAgendaItem.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('id', 'notes', 'description')
    filter_fields = ('classification', 'id')
    ordering_fields = ('id')
    filter_class = AgendaItemFilter
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        try:
            if self.request.query_params['basic']:
                return BasicEventAgendaItemSerializer
            else:
                return EventAgendaItemSerializer
        except:
            return EventAgendaItemSerializer


class EventAgendaItemDetail(APIView):
    def get_object(self, pk):
        try:
            return EventAgendaItem.objects.get(pk=pk)
        except EventAgendaItem.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        agenda_item = self.get_object(pk)
        serializer = EventAgendaItemSerializer(agenda_item)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        agenda_item = self.get_object(pk)
        serializer = EventAgendaItemSerializer(agenda_item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        agenda_item = self.get_object(pk)
        event = agenda_item.event
        order = agenda_item.order
        agenda_item.delete()
        if order:
            for ai in EventAgendaItem.objects.filter(event=event, order__gte=order):
                ai.order -= 1
                ai.save()
        if EventAgendaMedia.objects.filter(agenda_item=agenda_item).exists():
            eam = EventAgendaMedia.objects.filter(agenda_item=agenda_item).delete()
            for e in eam:
                if EventAgendaMediaLink.objects.filter(media=e).exists():
                    EventAgendaMediaLink.objects.filter(media=e).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def create_new_event_agenda_item(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            event = Event.objects.get(id=params['event_id'])
            name = params['name']
            description = params['description']

            try:
                order = params['order']
                same_order_agenda = EventAgendaItem.objects.filter(event=event, order=order)
                while same_order_agenda:
                    same_order_agenda = same_order_agenda.get()
                    same_order_agenda.order += 1
                    same_order_agenda.save()
                    same_order_agenda = EventAgendaItem.objects.\
                        filter(event=event, order=same_order_agenda.order).exclude(id=same_order_agenda.id)
            except KeyError:
                order = None

            try:
                griffier = User.objects.get(id=params['griffier'])
            except:
                griffier = None
            try:
                medewerker = User.objects.get(id=params['medewerker'])
            except:
                medewerker = None

            try:
                start_time = parser.parse(params['start_time'])
            except:
                start_time = None
            try:
                end_time = parser.parse(params['end_time'])
            except:
                end_time = None

            if start_time and end_time:
                if start_time > end_time:
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Start tijd moet kleiner zijn dan eind_tijd")
                if EventAgendaItem.objects.filter(event=event, start_time__lte=start_time, end_time__gte=end_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                if EventAgendaItem.objects.filter(event=event, start_time=start_time, end_time=end_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
            if start_time:
                if EventAgendaItem.objects.filter(event=event, start_time=start_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                if EventAgendaItem.objects.filter(event=event, start_time__lte=start_time, end_time__gt=start_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
            if end_time:
                if EventAgendaItem.objects.filter(event=event, end_time=end_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                if EventAgendaItem.objects.filter(event=event, start_time__lt=end_time, end_time__gte=end_time).exists():
                    return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")

            agenda_item = EventAgendaItem.objects.create(
                notes=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                event=event,
                griffier=griffier,
                medewerker=medewerker,
                order=order
            )
            return JsonResponse({ "id": agenda_item.id })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


def reduce_items_infront(event, curr_order):
    order_infront = curr_order + 1
    agenda_infront = EventAgendaItem.objects.filter(event=event, order=order_infront)
    while agenda_infront:
        agenda_infront = agenda_infront.get()
        agenda_infront.order -= 1
        agenda_infront.save()
        order_infront += 1
        agenda_infront = EventAgendaItem.objects.filter(event=event, order=order_infront)


@api_view(['POST'])
def edit_event_agenda_item(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            agenda_id = params['agenda_id']
            name = params['title']
            description = params['description']
            agenda_item = EventAgendaItem.objects.get(id=agenda_id)
            event = agenda_item.event

            try:
                order = params['order']
                curr_order = agenda_item.order

                if order > curr_order and curr_order is not None:
                    reduce_items_infront(event, curr_order)

                if order != curr_order:
                    same_order_agenda = EventAgendaItem.objects.filter(event=event, order=order)
                    while same_order_agenda:
                        same_order_agenda = same_order_agenda.get()
                        same_order_agenda.order += 1
                        same_order_agenda.save()
                        same_order_agenda = EventAgendaItem.objects. \
                            filter(event=event, order=same_order_agenda.order).exclude(id=same_order_agenda.id)

            except:
                order = None
                curr_order = agenda_item.order
                if curr_order:
                    reduce_items_infront(event, curr_order)
            try:
                griffier = User.objects.get(id=params['griffier'])
            except:
                griffier = None
            try:
                medewerker = User.objects.get(id=params['medewerker'])
            except:
                medewerker = None

            try:
                clear_times = params['clear_times']
                start_time = None
                end_time = None
            except:
                try:
                    start_time = parser.parse(params['start_time'])
                except:
                    start_time = None
                try:
                    end_time = parser.parse(params['end_time'])
                except:
                    end_time = None

                if start_time and end_time:
                    if start_time > end_time:
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Start tijd moet kleiner zijn dan eind_tijd")
                    if EventAgendaItem.objects.filter(event=event, start_time=start_time, end_time=end_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                    if EventAgendaItem.objects.filter(event=event, start_time__lte=start_time, end_time__gte=end_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                if start_time:
                    if EventAgendaItem.objects.filter(event=event, start_time=start_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                    if EventAgendaItem.objects.filter(event=event, start_time__lte=start_time, end_time__gt=start_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                if end_time:
                    if EventAgendaItem.objects.filter(event=event, end_time=end_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")
                    if EventAgendaItem.objects.filter(event=event, start_time__lt=end_time, end_time__gte=end_time).exclude(id=agenda_id).exists():
                        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Het agenda-item van het evenement met dezelfde naam of start tijd / eind_tijd bestaat")

            agenda_item = EventAgendaItem.objects.filter(id=agenda_id).update(
                notes=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                griffier=griffier,
                medewerker=medewerker,
                order=order
            )
            return JsonResponse({ "response": "success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def add_media_to_agenda_item(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
            params = json.loads(request.body)
            agenda_item_id = params['agenda_item_id']
            agenda_item = EventAgendaItem.objects.get(id=agenda_item_id)
            docs = params['documents']
            dossiers = params['dossiers']
            for d in docs:
                doc_ci = CombinedItem.objects.get(id=d["id"], item_type=d["type"])
                eam = EventAgendaMedia.objects.create(
                    note=doc_ci.name,
                    date=agenda_item.event.start_time,
                    agenda_item=agenda_item
                )
                EventAgendaMediaLink.objects.create(
                    text=doc_ci.name,
                    url='',
                    item_id=d["id"],
                    media_type=d["type"],
                    media=eam
                )
            for d in dossiers:
                dossier_ci = CombinedItem.objects.get(item_id=d, item_type='public_dossier')
                eam = EventAgendaMedia.objects.create(
                    note=dossier_ci.name,
                    date=agenda_item.event.start_time,
                    agenda_item=agenda_item
                )
                EventAgendaMediaLink.objects.create(
                    text=dossier_ci.name,
                    url='',
                    item_id=dossier_ci.id,
                    media_type='public_dossier',
                    media=eam
                )
            return JsonResponse({ "response": "success" })
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['GET'])
def get_next_agenda_item_id(request):
    queryset = EventAgendaItem.objects.only('id').all().order_by('-id')
    return JsonResponse({ 'value': queryset[0].id + 1 })


class EventAgendaMediaList(generics.ListCreateAPIView):
    queryset = EventAgendaMedia.objects.all()
    serializer_class = EventAgendaMediaSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('note', 'date')


class EventAgendaMediaDetail(APIView):
    def get_object(self, pk):
        try:
            return EventAgendaMedia.objects.get(pk=pk)
        except EventAgendaMedia.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        agenda_media = self.get_object(pk)
        serializer = EventAgendaMediaSerializer(agenda_media)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        agenda_media = self.get_object(pk)
        serializer = EventAgendaMediaSerializer(agenda_media, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        agenda_media = self.get_object(pk)
        agenda_media.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventAgendaMediaLinkList(generics.ListCreateAPIView):
    queryset = EventAgendaMediaLink.objects.all()
    serializer_class = EventAgendaMediaLinkSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('note', 'date')


class EventAgendaMediaLinkDetail(APIView):
    def get_object(self, pk):
        try:
            return EventAgendaMediaLink.objects.get(pk=pk)
        except EventAgendaMediaLink.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        agenda_media_link = self.get_object(pk)
        serializer = EventAgendaMediaLinkSerializer(agenda_media_link)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        agenda_media_link = self.get_object(pk)
        serializer = EventAgendaMediaLinkSerializer(agenda_media_link, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        if request.user:
            if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur':
                agenda_media_link = self.get_object(pk)
                agenda_media_link.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not Admin")
        else:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


class EventMediaList(generics.ListCreateAPIView):
    queryset = EventMedia.objects.all()
    serializer_class = EventMediaSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('filename')


class EventMediaDetail(APIView):
    def get_object(self, pk):
        try:
            return EventMedia.objects.get(pk=pk)
        except EventMediaSerializer.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        agenda_media_link = self.get_object(pk)
        serializer = EventMediaSerializer(agenda_media_link)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        agenda_media_link = self.get_object(pk)
        serializer = EventMediaSerializer(agenda_media_link, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        agenda_media_link = self.get_object(pk)
        agenda_media_link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReceivedDocumentDetail(APIView):
    def get_object(self, pk):
        try:
            return ReceivedDocument.objects.get(id=pk)
        except ReceivedDocument.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = ReceivedDocumentSerializer(obj)
        return Response(serializer.data)


class CouncilAddressDetail(APIView):
    def get_object(self, pk):
        try:
            return CouncilAddress.objects.get(pk=pk)
        except CouncilAddress.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = CouncilAddressSerializer(obj)
        return Response(serializer.data)


class CommitmentDetail(APIView):
    def get_object(self, pk):
        try:
            return Commitment.objects.get(pk=pk)
        except Commitment.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = CommitmentSerializer(obj)
        return Response(serializer.data)


class WrittenQuestionDetail(APIView):
    def get_object(self, pk):
        try:
            return WrittenQuestion.objects.get(pk=pk)
        except WrittenQuestion.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = WrittenQuestionSerializer(obj)
        return Response(serializer.data)


class MotionDetail(APIView):
    def get_object(self, pk):
        try:
            return Motion.objects.get(pk=pk)
        except Motion.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = MotionSerializer(obj)
        return Response(serializer.data)


class PublicDocumentDetail(APIView):
    def get_object(self, pk):
        try:
            return PublicDocument.objects.get(pk=pk)
        except PublicDocument.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = PublicDocumentSerializer(obj)
        return Response(serializer.data)


class ManagementDocumentDetail(APIView):
    def get_object(self, pk):
        try:
            return ManagementDocument.objects.get(pk=pk)
        except ManagementDocument.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = ManagementDocumentSerializer(obj)
        return Response(serializer.data)


class PolicyDocumentDetail(APIView):
    def get_object(self, pk):
        try:
            return PolicyDocument.objects.get(pk=pk)
        except PolicyDocument.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        obj = self.get_object(pk)
        serializer = PolicyDocumentSerializer(obj)
        return Response(serializer.data)


class ItemsCounts(object):
    def __init__(self, **kwargs):
        for field in (
                'total_count', 'events_count', 'documents_count', 'received_documents_count', 'council_adress_count',
                'written_questions_count', 'public_documents_count', 'management_documents_count',
                'policy_documents_count',
                'commitments_count', 'motions_count'):
            setattr(self, field, kwargs.get(field, None))


class GetItemCounts(viewsets.ViewSet):
    serializer_class = GetItemCountsSerializer

    def list(self, request):
        dt = datetime.datetime.now()
        total = CombinedItem.objects.all().exclude(item_type='child_event')
        events = Event.objects.filter(start_time__lte=dt).exclude(~Q(parent_event=None))
        documents = Document.objects.all()
        received_documents = ReceivedDocument.objects.all()
        council_adress = CouncilAddress.objects.all()
        written_questions = WrittenQuestion.objects.all()
        public_documents = PublicDocument.objects.all()
        management_documents = ManagementDocument.objects.all()
        policy_documents = PolicyDocument.objects.all()
        commitments = Commitment.objects.all()
        motions = Motion.objects.all()

        obj = {
            1: ItemsCounts(
                total_count=total.count(),
                events_count=events.count(),
                documents_count=documents.count(),
                received_documents_count=received_documents.count(),
                council_adress_count=council_adress.count(),
                written_questions_count=written_questions.count(),
                public_documents_count=public_documents.count(),
                management_documents_count=management_documents.count(),
                policy_documents_count=policy_documents.count(),
                commitments_count=commitments.count(),
                motions_count=motions.count(),
            )
        }

        serializer = GetItemCountsSerializer(
            instance=obj.values(), many=True
        )

        return Response(serializer.data)


class MyAgendaList(generics.ListAPIView):
    serializer_class = EventListSerializer

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
            my_agenda_id_list = MyAgenda.objects.filter(user=self.request.user).values_list('agenda_id', flat=True)
        else:
            my_agenda_id_list = MyAgenda.objects.filter(user=self.request.user, agenda__published=True).values_list('agenda_id', flat=True)
        return Event.objects.filter(pk__in=my_agenda_id_list)


@api_view(['POST'])
def add_my_agenda(request):
    params = json.loads(request.body)
    try:
        return JsonResponse({'response': 'added'}) if MyAgenda.objects.create(
            agenda=Event.objects.get(pk=params['agenda_id']),
            user=User.objects.get(pk=params['user_id'])) else JsonResponse({'response': 'something wrong'})
    except User.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="User Not Found")
    except Event.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Event Not Found")
    except IntegrityError:
        return HttpResponse(status=status.HTTP_406_NOT_ACCEPTABLE, content="Agenda Already Added")
    except Exception:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Don't know what happened")


@api_view(['DELETE'])
def remove_my_agenda(request):
    params = json.loads(request.body)
    try:
        return JsonResponse({'response': 'deleted'}) if [item.delete() for item in MyAgenda.objects.filter(
            agenda=Event.objects.get(pk=params['agenda_id']),
            user=User.objects.get(pk=params['user_id']))] else JsonResponse({'response': 'something wrong'})
    except User.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="User Not Found")
    except Event.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Event Not Found")
    except Exception:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Don't know what happened")


class DocNotes(generics.ListAPIView):
    serializer_class = NoteListSerializer

    def get_queryset(self):
        params = self.request.query_params
        document_id = params['document_id']
        doc_type = params['type']
        my_note_list = Note.objects.filter(document_id=document_id).filter(type=doc_type)
        return my_note_list


class MyNotes(generics.ListAPIView):
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('title', 'created_at', 'last_modified')
    serializer_class = NoteListSerializer
    pagination_class = LargeResultsSetPagination
    filter_class = NotesFilter

    def get_queryset(self):
        user = self.request.user
        my_note_list = Note.objects.filter(user=user)
        return my_note_list


class MyNote(generics.RetrieveAPIView):
    serializer_class = NoteListSerializer

    def get_queryset(self):
        user = self.request.user
        my_note_list = Note.objects.filter(user=user)
        return my_note_list


@api_view(['GET'])
def get_note(request, pk):
    note = Note.objects.get(pk=pk)
    return JsonResponse(note)


@api_view(['POST'])
def add_note(request):
    if request.user:
        params = json.loads(request.body)
        document_id = params['document_id']
        title = params['title']
        desc = params['description']
        type = params['type']
        doc_title = params['doc_title']
        user = request.user
        Note.objects.create(document_id=document_id, user=user, title=title, doc_title=doc_title, type=type, description=desc)
        return JsonResponse({'response': 'created'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['POST'])
def edit_note(request):
    if request.user:
        params = json.loads(request.body)
        note_id = params['note_id']
        title = params['title']
        desc = params['description']
        try:
            note = Note.objects.get(pk=note_id)
        except Document.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Note Not Found")
        note.title = title
        note.description = desc
        note.save()
        return JsonResponse({'response': 'edited'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


@api_view(['DELETE'])
def remove_note(request):
    if request.user:
        params = json.loads(request.body)
        note_id = params['note_id']
        try:
            Note.objects.get(pk=note_id).delete()
        except Document.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Note Not Found")
        return JsonResponse({'response': 'deleted'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


class SpeakersList(generics.ListAPIView):
    queryset = Speaker.objects.all()
    serializer_class = SpeakerSerializer
    pagination_class = LargeResultsSetPagination


class EventAgendasSpeakerList(generics.ListAPIView):
    serializer_class = SpeakerIndexSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        speakers = []
        agendas = EventAgendaItem.objects.filter(event=self.kwargs['event_id'])
        for a in agendas:
            speakers = list(chain(speakers, SpeakerIndex.objects.filter(agenda_item=a)))

        return speakers


def _get_actual_doc(doc, doc_typ):
    if doc_typ == Document:
        real_doc = doc
    elif doc_typ == Commitment:
        real_doc = doc.new_document
    elif doc_typ == CouncilAddress or doc_typ == WrittenQuestion:
        real_doc = doc.question_document
        if not doc:
            real_doc = doc.interim_answer_document
        if not doc:
            real_doc = doc.answer_document
    else:
        real_doc = doc.document
    return real_doc
