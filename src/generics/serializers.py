from rest_framework import serializers
import datetime

from accounts.serializers import UserProfileSerializer
from generics.models import Event, Note, EventDocument
from generics.models import Document
from generics.models import EventAgendaItem
from generics.models import EventAgendaMedia
from generics.models import EventAgendaMediaLink
from generics.models import EventMedia
from generics.models import CombinedItem
from generics.models import PublicDossier
from generics.models import DocumentContent
from generics.models import PublicDossierContent

from generics.models import ReceivedDocument
from generics.models import CouncilAddress
from generics.models import Commitment
from generics.models import WrittenQuestion
from generics.models import Motion
from generics.models import PublicDocument
from generics.models import ManagementDocument
from generics.models import PolicyDocument

from generics.models import Party
from generics.models import Person
from generics.models import Organisation
from generics.models import Speaker
from generics.models import SpeakerIndex

from django.utils import six
from django.db.models import Q

doc_types = [
    "document",
    "received_document",
    "council_address",
    "written_question",
    "format",
    "policy_document",
    "management_document",
    "motion",
    "commitment",
]

class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = (
            'notubiz_id',
            'person_id',
            'firstname',
            'lastname',
            'sex',
            'function',
            'email',
            'photo_url',
            'last_modified',
        )


class EventMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMedia
        fields = ('id', 'filename', 'httpstream', 'rtmpstream', 'download', 'event')


class EventAgendaMediaLinkSerializer(serializers.ModelSerializer):
    item_id = serializers.SerializerMethodField()

    def get_item_id(self, item):
        try:
            if item.item_id == 0:
                return Document.objects.get(url=item.url).id
            ci = CombinedItem.objects.get(id=item.item_id)
            if item.media_type == 'public_dossier':
                return PublicDossier.objects.get(id=ci.item_id).id
            return Document.objects.get(Q(url=item.url) | Q(id=ci.item_id)).id
        except Exception as e:
            print "LOC 67: {}".format(e)
            return None

    combined_id = serializers.SerializerMethodField()

    def get_combined_id(self, item):
        try:
            if item.item_id == 0:
                return CombinedItem.objects.get(url=item.url).id
            return CombinedItem.objects.get(id=item.item_id).id
        except Exception as e:
            print "LOC 78: {}".format(e)
            return None

    url = serializers.SerializerMethodField()

    def get_url(self, item):
        try:
            if item.url != '':
                return item.url
            else:
                ci = self.get_combined_id(item)
                return CombinedItem.objects.get(id=ci).url
        except Exception as e:
            print "LOC 92: {}".format(e)
            return None

    class Meta:
        model = EventAgendaMediaLink
        fields = (
            'id',
            'combined_id',
            'item_id',
            'url',
            'media_type',
            'text',
            'media'
        )


class EventAgendaMediaSerializer(serializers.ModelSerializer):
    links = EventAgendaMediaLinkSerializer('links', many=True)
    link_item_type = serializers.SerializerMethodField()

    def get_link_item_type(self, obj):
        return obj.links.first().media_type if obj.links.first().media_type else 'document'

    class Meta:
        model = EventAgendaMedia
        fields = ('id', 'note', 'date', 'link_item_type', 'agenda_item', 'links')


class EventAgendaItemSerializer(serializers.ModelSerializer):
    media = EventAgendaMediaSerializer('media', many=True)
    griffier = UserProfileSerializer()
    medewerker = UserProfileSerializer()

    class Meta:
        model = EventAgendaItem
        fields = ('id', 'notes', 'description', 'start_time', 'end_time', 'order', 'classification', 'event', 'media', 'griffier', 'medewerker')


class BasicEventAgendaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAgendaItem
        fields = ('id', 'notes')


class SpeakerIndexSerializer(serializers.ModelSerializer):
    speaker = SpeakerSerializer()
    agenda_id = serializers.SerializerMethodField()

    class Meta:
        model = SpeakerIndex
        fields = (
            'speaker',
            'agenda_id',
            'start_time'
        )

    @staticmethod
    def get_agenda_id(obj):
        return obj.agenda_item.id


class DocumentSerializer(serializers.ModelSerializer):
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.only("id", "document_id", "type").filter(document_id=doc.id, type=0)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, ibabs_id=doc.ibabs_id).exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, ibabs_id=doc.ibabs_id).id
        else:
            return None

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, ibabs_id=doc.ibabs_id, item_type='document').published
        except Exception:
            return None

    class Meta:
        model = Document
        fields = (
            'id',
            'notubiz_id',
            'ibabs_id',
            'combined_id',
            'text',
            'attached_to',
            'url',
            'media_type',
            'notes',
            'event',
            'date',
            'published'
        )


class ChildEventsListSerializer(serializers.ModelSerializer):
    event_media = EventMediaSerializer('event_media', many=True, required=False)
    documents = serializers.SerializerMethodField()
    agenda = serializers.SerializerMethodField()
    combined_id = serializers.SerializerMethodField()

    @staticmethod
    def get_combined_id(obj):
        item = CombinedItem.objects.only("id", "item_id", "item_type").get(item_id=obj.id, item_type='child_event')
        if item:
            return item.id
        else:
            return None

    @staticmethod
    def get_agenda(obj):
        ordered_agenda = obj.agenda.order_by('order', 'start_time')
        return EventAgendaItemSerializer(ordered_agenda, many=True).data

    @staticmethod
    def get_documents(obj):
        documents = []
        for d in obj.documents.all():
            ci = CombinedItem.objects.get(item_id=d.id, item_type='document')
            documents.append({
                'id': ci.item_id,
                'combined_id': ci.id,
                'text': ci.name,
                'url': ci.url,
                'media_type': ci.item_type,
                'attachment_type': 1
            })
        if EventDocument.objects.filter(event=obj.id).exists():
            for ed in EventDocument.objects.filter(event=obj.id):
                ci = CombinedItem.objects.get(item_id=ed.document_id, item_type=ed.document_type)
                documents.append({
                    'id': ci.item_id,
                    'combined_id': ci.id,
                    'text': ci.name,
                    'url': ci.url,
                    'media_type': ci.item_type,
                    'attachment_type': 0
                })
        return documents

    class Meta:
        model = Event
        fields = (
            'id',
            'notubiz_id',
            'name',
            'description',
            'jurisdiction',
            'start_time',
            'end_time',
            'classification',
            'location',
            'parent_event',
            'last_modified',
            'documents',
            'event_media',
            'agenda',
            'combined_id',
            'published'
        )


class EventListSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()
    agenda_count = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    combined_id = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'start_time',
            'document_count',
            'agenda_count',
            'media_count',
            'combined_id',
            'published',
            'location'
        )

    @staticmethod
    def get_document_count(obj):
        return obj.documents.count()

    @staticmethod
    def get_agenda_count(obj):
        return obj.agenda.count()

    @staticmethod
    def get_media_count(obj):
        return obj.event_media.count()

    @staticmethod
    def get_combined_id(obj):
        item = CombinedItem.objects.only("id", "item_id", "item_type").filter(item_id=obj.id, item_type='event')
        if item.exists():
            return item[0].id
        else:
            return None


class NoteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = (
            'id',
            'document_id',
            'type',  # The associated document type
            'doc_title',
            'user_id',
            'title',
            'description',
            'created_at',
            'last_modified',
        )


class EventDetailSerializer(serializers.ModelSerializer):
    event_media = EventMediaSerializer('event_media', many=True, required=False)

    documents = serializers.SerializerMethodField()
    agenda = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()
    agenda_count = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    combined_id = serializers.SerializerMethodField()
    parent_event_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id',
            'notubiz_id',
            'name',
            'description',
            'jurisdiction',
            'start_time',
            'end_time',
            'classification',
            'location',
            'parent_event',
            'parent_event_name',
            'last_modified',
            'documents',
            'event_media',
            'agenda',
            'document_count',
            'agenda_count',
            'media_count',
            'combined_id',
            'published',
        )

    @staticmethod
    def get_document_count(obj):
        return obj.documents.count()

    @staticmethod
    def get_agenda_count(obj):
        return obj.agenda.count()

    @staticmethod
    def get_media_count(obj):
        return obj.event_media.count()

    @staticmethod
    def get_parent_event_name(obj):
        try:
            return obj.parent_event.name
        except:
            return obj.name

    @staticmethod
    def get_combined_id(obj):
        item = CombinedItem.objects.filter(item_id=obj.id, item_type='event')
        if item.exists():
            return item[0].id
        else:
            return None

    @staticmethod
    def get_documents(obj):
        documents = []
        for d in obj.documents.all():
            ci = CombinedItem.objects.get(item_id=d.id, item_type='document')
            documents.append({
                'id': ci.item_id,
                'combined_id': ci.id,
                'text': ci.name,
                'url': ci.url,
                'media_type': ci.item_type,
                'attachment_type': 1
            })
        if EventDocument.objects.filter(event=obj.id).exists():
            for ed in EventDocument.objects.filter(event=obj.id):
                ci = CombinedItem.objects.get(item_id=ed.document_id, item_type=ed.document_type)
                documents.append({
                    'id': ci.item_id,
                    'combined_id': ci.id,
                    'text': ci.name,
                    'url': ci.url,
                    'media_type': ci.item_type,
                    'attachment_type': 0
                })
        return documents

    @staticmethod
    def get_agenda(obj):
        ordered_agenda = EventAgendaItem.objects.filter(event=obj).order_by('order', 'start_time')
        return EventAgendaItemSerializer(ordered_agenda, many=True).data


class BasicEventDetailSerializer(serializers.ModelSerializer):
    parent_event_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'start_time',
            'end_time',
            'location',
            'parent_event_name',
        )

    @staticmethod
    def get_parent_event_name(obj):
        try:
            return obj.parent_event.name
        except:
            return obj.name


class LimitedCharField(serializers.CharField):

    def to_representation(self, value):
        return six.text_type(value[0:150])


class PartySerializer(serializers.ModelSerializer):

    class Meta:
        model = Party
        fields = ('id', 'name')


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'name')


class OrganisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organisation
        fields = ('id', 'name')


class DocumentContentSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            request = kwargs['context']['request']
            self.q_arg = request.GET.get('q')

    def get_content(self, item):
        q_arg = None
        more_dots = ''
        try:
            q_arg = self.q_arg
        except:
            q_arg = None

        if item is None:
            return ''
        if item.content is None:
            return ''
        if len(item.content) > 600:
            more_dots = ' ... '
        if q_arg:
            content = item.content.lower()
            if len(q_arg.split(',')) == 1:
                index = content.find(q_arg.lower())
                low = index - 300
                high = index + 300
                if low > 0 and high < len(item.content):
                    return six.text_type(item.content[low:high]) + more_dots
                elif low > 0 and high == len(item.content):
                    return item.content + more_dots
                elif low > 0 and high > len(item.content):
                    return six.text_type(item.content[low - high + len(item.content):len(item.content)]) + more_dots
                elif low < 0 and high < len(item.content):
                    return six.text_type(item.content[0:high + 300 - low]) + more_dots
                else:
                    return six.text_type(item.content[0:100]) + more_dots
            else:
                excerpt = ''
                for arg in q_arg.split(','):
                    index = content.find(arg.lower())
                    low = index - 150
                    high = index + 150
                    if low > 0 and high < len(item.content):
                        excerpt += six.text_type(item.content[low:high]) + more_dots
                    elif low > 0 and high == len(item.content):
                        excerpt += item.content + more_dots
                    elif low > 0 and high > len(item.content):
                        excerpt += six.text_type(item.content[low - high + len(item.content):len(item.content)]) + more_dots
                    elif low < 0 and high < len(item.content):
                        excerpt += six.text_type(item.content[0:high + 100 - low]) + more_dots
                return excerpt
        else:
            return six.text_type(item.content[0:600]) + more_dots

    class Meta:
        model = DocumentContent
        fields = ('content',)


class CombinedSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    doc_content = DocumentContentSerializer('doc_content')
    has_content = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    public_dossier = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            self.fields['doc_content'] = DocumentContentSerializer(context=None)

    @staticmethod
    def get_parent_id(item):
        if item.item_type == 'child_event':
            child_event = Event.objects.get(id=item.item_id)
            return child_event.parent_event.id
        else:
            return 0

    @staticmethod
    def get_name(item):
        if item.item_type == 'child_event':
            child_event = Event.objects.get(id=item.item_id)
            return child_event.classification
        else:
            return item.name

    @staticmethod
    def get_has_content(item):
        if item.item_type == 'event':
            if Event.objects.filter(id=item.item_id).exists():
                event = Event.objects.get(id=item.item_id)
                event_docs = event.documents
                event_agenda = event.agenda
                event_media = event.event_media
                if event_docs.count() == 0 and event_agenda.count() == 0 and event_media.count() == 0:
                    return False
                else:
                    return True
            else:
                return None
        else:
            return None

    def get_public_dossier(self, item):
        try:
            no_public_dossier = self.context.get('no_public_dossier')
            if no_public_dossier:
                return None
        except:
            pass

        try:
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
            }[item.item_type]

            if doc_type == Document:
                doc = doc_type.objects.get(pk=item.item_id)
            elif doc_type == Commitment:
                other_doc = Commitment.objects.get(pk=item.item_id)
                doc = other_doc.new_document
            elif doc_type == CouncilAddress or doc_type == WrittenQuestion:
                other_doc = doc_type.objects.get(pk=item.item_id)
                doc = other_doc.question_document
                if not doc:
                    doc = other_doc.interim_answer_document
                if not doc:
                    doc = other_doc.answer_document
            else:
                other_doc = doc_type.objects.get(pk=item.item_id)
                doc = other_doc.document

            if doc and doc.public_dossier:
                return BasicPublicDossierDetail(doc.public_dossier).data
            else:
                return None
        except:
            return None

    @staticmethod
    def get_url(item):
        if item.item_type == 'event' or item.item_type == 'document' or item.item_type == 'public_dossier':
            return item.url

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
        }[item.item_type]

        if doc_type == Motion or doc_type == PublicDocument or doc_type == PolicyDocument or doc_type == ReceivedDocument or doc_type == ManagementDocument:
            try:
                return doc_type.objects.get(id=item.item_id).document.url
            except:
                return None

        if doc_type == CouncilAddress or doc_type == WrittenQuestion:
            try:
                return doc_type.objects.get(id=item.item_id).question_document.url
            except:
                return None

        if doc_type == Commitment:
            try:
                return doc_type.objects.get(id=item.item_id).new_question_document.url
            except:
                return None

        return None

    class Meta:
        model = CombinedItem
        fields = (
            'id',
            'item_id',
            'notubiz_id',
            'name',
            'date',
            'url',
            'classification',
            'last_modified',
            'item_type',
            'has_content',
            'doc_content',
            'parent_id',
            'published',
            'status',
            'subject',
            'portfolio',
            'author',
            'public_dossier',
        )


class ReceivedDocumentSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=1)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='received_document').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='received_document').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='received_document').published
        except:
            return None

    class Meta:
        model = ReceivedDocument
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'document',
            'subject',
            'description',
            'publication_date',
            'date',
            'date_created',
            'advice',
            'sender',
            'notes',
            'location',
            'document_type',
            'policy_field',
            'dossiercode',
            'category',
            'linked_event',
            'heading',
            'published'
        )


class CouncilAddressSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    question_document = DocumentSerializer()
    interim_answer_document = DocumentSerializer()
    answer_document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=2)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='council_address').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='council_address').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='council_address').published
        except:
            return None

    class Meta:
        model = CouncilAddress
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'publication_date',
            'question_date',
            'question_document',
            'interim_answer_date',
            'interim_answer_document',
            'answer_date',
            'answer_document',
            'handled_by',
            'notes',
            'location',
            'address_type',
            'linked_event',
            'name',
            'address',
            'email',
            'telephone',
            'place',
            'postal_code',
            'published'
        )


class CommitmentSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    new_document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=8)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='commitment').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='commitment').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='commitment').published
        except:
            return None

    class Meta:
        model = Commitment
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'expected_settlement_date',
            'commitment_date',
            'date_finished',
            'notes',
            'portfolio_holder',
            'recipient',
            'agenda_item',
            'policy_field',
            'dossiercode',
            'text',
            'situation',
            'involved_comittee',
            'dispensation',
            'new_document',
            'published'
        )


class WrittenQuestionSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    parties = PartySerializer(many=True)
    initiator = PersonSerializer()

    question_document = DocumentSerializer()
    interim_answer_document = DocumentSerializer()
    answer_document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=3)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='written_question').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='written_question').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='written_question').published
        except:
            return None

    class Meta:
        model = WrittenQuestion
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'publication_date',
            'explanation',
            'parties',
            'question_date',
            'question_document',
            'interim_answer_document',
            'interim_answer_explanation',
            'answer_date',
            'notes',
            'answer_document',
            'answer_explanation',
            'expected_answer_date',
            'initiator',
            'policy_field',
            'location',
            'involved_comittee',
            'portfolio_holder',
            'dossiercode',
            'progress_state',
            'evaluation_date',
            'linked_event',
            'vote_outcome',
            'number',
            'unknown_type',
            'meeting_category',
            'co_signatories',
            'published'
        )


class MotionSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    document = DocumentSerializer()
    new_document_settlement = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=7)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='motion').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='motion').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='motion').published
        except:
            return None

    class Meta:
        model = Motion
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'agenda_item',
            'document_type',
            'policy_field',
            'dossiercode',
            'notes',
            'document',
            'new_document_settlement',
            'parties',
            'portfolio_holder',
            'involved_comittee',
            'expected_settlement_date',
            'outcome',
            'meeting_date',
            'date_created',
            'date_finished',
            'dispensation',
            'explanation',
            'council_member',
            'comments',
            'situation',
            'published'
        )


class PublicDocumentSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=4)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='public_document').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='public_document').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='public_document').published
        except:
            return None

    class Meta:
        model = PublicDocument
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'notes',
            'document_date',
            'publication_date',
            'date_created',
            'document',
            'document_type',
            'number',
            'meeting_category',
            'portfolio_holder',
            'policy_field',
            'settlement',
            'linked_event',
            'category',
            'location',
            'published'
        )


class ManagementDocumentSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=6)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='management_document').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='management_document').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='management_document').published
        except:
            return None

    class Meta:
        model = ManagementDocument
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'title',
            'number',
            'notes',
            'publication_date',
            'document',
            'document_date',
            'document_type',
            'district',
            'date_created',
            'portfolio_holder',
            'policy_field',
            'meeting_category',
            'settlement',
            'linked_event',
            'category',
            'dossiercode',
            'operational_from',
            'settlement_date',
            'valid_until',
            'operational_from_2',
            'status',
            'published'
        )


class PolicyDocumentSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    document = DocumentSerializer()
    combined_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    @staticmethod
    def get_notes(doc):
        notes_queryset = Note.objects.filter(document_id=doc.id).filter(type=5)
        return NoteListSerializer(notes_queryset, many=True).data

    @staticmethod
    def get_combined_id(doc):
        if CombinedItem.objects.filter(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='policy_document').exists():
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='policy_document').id
        else:
            return 0

    @staticmethod
    def get_published(doc):
        try:
            return CombinedItem.objects.get(item_id=doc.id, notubiz_id=doc.notubiz_id, item_type='policy_document').published
        except:
            return None

    class Meta:
        model = PolicyDocument
        fields = (
            'organisation',
            'notubiz_id',
            'combined_id',
            'item_created',
            'last_modified',
            'notes',
            'title',
            'document',
            'document_type',
            'document_date',
            'number',
            'policy_field',
            'dossiercode',
            'meeting_category',
            'location',
            'portfolio_holder',
            'settlement',
            'date_created',
            'linked_event',
            'publication_date',
            'category',
            'published'
        )


class PublicDossierListSerializer(serializers.ModelSerializer):
    combined_id = serializers.SerializerMethodField()
    has_dossiers = serializers.SerializerMethodField()
    child_dossiers_count = serializers.SerializerMethodField()

    @staticmethod
    def get_combined_id(dossier):
        if CombinedItem.objects.filter(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").exists():
            return CombinedItem.objects.get(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").id
        else:
            return 0

    @staticmethod
    def get_has_dossiers(dossier):
        if PublicDossierContent.objects.filter(dossier=dossier.id, item_type='public_dossier').exists() or PublicDossier.objects.filter(parent_dossier=dossier.id).exists():
            return True
        else:
            return False

    @staticmethod
    def get_child_dossiers_count(dossier):
        if PublicDossierContent.objects.filter(dossier=dossier.id, item_type='public_dossier').exists():
            res = PublicDossierContent.objects.filter(dossier=dossier.id, item_type='public_dossier').count()
            if PublicDossier.objects.filter(parent_dossier=dossier.id).exists():
                res = res + 1
            return res
        else:
            return 0

    class Meta:
        model = PublicDossier
        fields = (
            'id',
            'combined_id',
            'title',
            'created_at',
            'last_modified',
            'published',
            'has_dossiers',
            'depth',
            'child_dossiers_count'
        )

    def create(self, validated_data):
        dossier = PublicDossier(
            created_at=datetime.datetime.now(),
            last_modified=datetime.datetime.now(),
            **validated_data
        )
        dossier.save()
        CombinedItem.objects.create(
            item_id=dossier.id,
            name=dossier.title,
            date=dossier.created_at,
            last_modified=dossier.last_modified,
            item_type='public_dossier',
            published=dossier.published
        )
        return dossier


class FullPublicDossierDetail(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()
    folder_count = serializers.SerializerMethodField()
    combined_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    dossiers = serializers.SerializerMethodField()
    parent_dossiers = serializers.SerializerMethodField()

    @staticmethod
    def get_combined_id(dossier):
        if CombinedItem.objects.filter(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").exists():
            return CombinedItem.objects.get(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").id
        else:
            return 0

    @staticmethod
    def get_documents(dossier):
        qs = []
        if Document.objects.only('id').filter(public_dossier=dossier).exists():
            qs1 = []
            for doc in Document.objects.only('id', 'public_dossier').filter(public_dossier=dossier):
                try:
                    ci = CombinedItem.objects.get(item_id=doc.id, item_type='document')
                    qs1.append(CombinedSerializer(ci, context={'no_public_dossier': True}).data)
                except CombinedItem.DoesNotExist:
                    pass
            if qs:
                qs = qs + qs1
        for doc_type in doc_types:
            if PublicDossierContent.objects.filter(dossier=dossier, item_type=doc_type).exists():
                content = PublicDossierContent.objects.filter(dossier=dossier, item_type=doc_type)
                qs2 = []
                for c in content:
                    qs2.append(CombinedSerializer(c.item, context={'no_public_dossier': True}).data)
                qs = qs + qs2
        return qs

    @staticmethod
    def get_dossiers(dossier):
        qs = []
        if PublicDossier.objects.filter(parent_dossier=dossier).exists():
            qs1 = []
            for dos in PublicDossier.objects.filter(parent_dossier=dossier):
                ci = CombinedItem.objects.get(item_id=dos.id, item_type='public_dossier')
                qs1.append(CombinedSerializer(ci, context={'no_public_dossier': True}).data)
            qs = qs + qs1
        if PublicDossierContent.objects.filter(dossier=dossier, item_type='public_dossier').exists():
            content = PublicDossierContent.objects.filter(dossier=dossier, item_type='public_dossier')
            qs2 = []
            for c in content:
                qs2.append(CombinedSerializer(c.item, context={'no_public_dossier': True}).data)
            qs = qs + qs2
        return qs

    @staticmethod
    def get_document_count(dossier):
        return len(FullPublicDossierDetail.get_documents(dossier))

    @staticmethod
    def get_folder_count(dossier):
        return len(FullPublicDossierDetail.get_dossiers(dossier))

    @staticmethod
    def get_parent_dossiers(dossier):
        combined_id = CombinedItem.objects.get(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").id
        qs = []
        if PublicDossierContent.objects.filter(item=combined_id, item_type='public_dossier').exists():
            for d in PublicDossierContent.objects.filter(item=combined_id, item_type='public_dossier'):
                qs.append(BasicPublicDossierDetail(d.dossier).data)
        return qs

    class Meta:
        model = PublicDossier
        fields = (
            'id',
            'combined_id',
            'title',
            'created_at',
            'last_modified',
            'document_count',
            'folder_count',
            'parent_dossier',
            'documents',
            'dossiers',
            'published',
            'parent_dossiers',
        )
        depth=1

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.last_modified = datetime.datetime.now()
        instance.published = validated_data.get('published', instance.published)
        instance.save()

        ci = CombinedItem.objects.get(item_id=instance.id, item_type='public_dossier')
        ci.name = instance.title
        ci.last_modified = instance.last_modified
        ci.published = instance.published
        ci.save()

        content = PublicDossierContent.objects.filter(dossier=instance)
        for c in content:
            if c.item_type == 'public_dossier':
                pd = PublicDossier.objects.get(id=c.item.item_id)
                pd.published = instance.published
                pd.save()
                ci = CombinedItem.objects.get(id=c.item.id)
                ci.published = instance.published
                ci.save()

        return instance


class BasicPublicDossierDetail(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()
    folder_count = serializers.SerializerMethodField()
    combined_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    dossiers = serializers.SerializerMethodField()

    @staticmethod
    def get_combined_id(dossier):
        if CombinedItem.objects.filter(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").exists():
            return CombinedItem.objects.get(item_id=dossier.id, notubiz_id=dossier.notubiz_id, item_type="public_dossier").id
        else:
            return 0

    @staticmethod
    def get_documents(dossier):
        qs = []
        if Document.objects.only('id').filter(public_dossier=dossier,).exists():
            qs1 = []
            for doc in Document.objects.only('id', 'public_dossier').filter(public_dossier=dossier):
                try:
                    ci = CombinedItem.objects.get(item_id=doc.id, item_type='document')
                    if not ci.published:
                        continue
                    qs1.append(CombinedSerializer(ci, context={'no_public_dossier': True}).data)
                except CombinedItem.DoesNotExist:
                    pass
            qs = qs + qs1
        for doc_type in doc_types:
            if PublicDossierContent.objects.filter(dossier=dossier, item__published=True, item_type=doc_type).exists():
                content = PublicDossierContent.objects.filter(dossier=dossier, item__published=True, item_type=doc_type)
                qs2 = []
                for c in content:
                    qs2.append(CombinedSerializer(c.item, context={'no_public_dossier': True}).data)
                qs = qs + qs2
        return qs

    @staticmethod
    def get_dossiers(dossier):
        qs = []
        if PublicDossier.objects.only('id', 'parent_dossier', 'published').filter(parent_dossier=dossier, published=True).exists():
            qs1 = []
            for dos in PublicDossier.objects.only('id', 'parent_dossier', 'published').filter(parent_dossier=dossier, published=True):
                ci = CombinedItem.objects.get(item_id=dos.id, item_type='public_dossier')
                qs1.append(CombinedSerializer(ci, context={'no_public_dossier': True}).data)
            qs = qs + qs1
        if PublicDossierContent.objects.filter(dossier=dossier, item__published=True, item_type='public_dossier').exists():
            content = PublicDossierContent.objects.filter(dossier=dossier, item__published=True, item_type='public_dossier')
            qs2 = []
            for c in content:
                qs2.append(CombinedSerializer(c.item, context={'no_public_dossier': True}).data)
            qs = qs + qs2
        return qs

    @staticmethod
    def get_document_count(dossier):
        return len(BasicPublicDossierDetail.get_documents(dossier))

    @staticmethod
    def get_folder_count(dossier):
        return len(BasicPublicDossierDetail.get_dossiers(dossier))

    class Meta:
        model = PublicDossier
        fields = (
            'id',
            'combined_id',
            'title',
            'created_at',
            'last_modified',
            'document_count',
            'folder_count',
            'parent_dossier',
            'documents',
            'dossiers',
            'published'
        )
        depth=1


class GetItemCountsSerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    events_count = serializers.IntegerField()
    documents_count = serializers.IntegerField()
    received_documents_count = serializers.IntegerField()
    council_adress_count = serializers.IntegerField()
    written_questions_count = serializers.IntegerField()
    public_documents_count = serializers.IntegerField()
    management_documents_count = serializers.IntegerField()
    policy_documents_count = serializers.IntegerField()
    commitments_count = serializers.IntegerField()
    motions_count = serializers.IntegerField()


def getItemURL(id, item_type):
    return {
        "event": "evenement/" + id,
        "child_event": "evenement" + id,
        "document": "document/0/" + id,
        "received_document": "document/1/" + id,
        "council_address": "document/2/" + id,
        "written_question": "document/3/" + id,
        "format": "document/4/" + id,
        "policy_document": "document/5/" + id,
        "management_document": "document/6/" + id,
        "motion": "document/7/" + id,
        "commitment": "document/8/" + id,
        "public_dossier": "publieke-dossiers/" + id
    } [item_type]


def getItemType(item_type):
    return {
        "event": "Agenda punten",
        "child_event": "Agenda punten",
        "document": "Documenten",
        "received_document": "P&C Cyclus",
        "council_address": "Brief aan de raad",
        "written_question": "Schriftelijke vragen",
        "format": "Format",
        "policy_document": "Presidium besluitenlijsten",
        "management_document": "Raadsbrieven",
        "motion": "Motie",
        "commitment": "Toezeggingen",
        "public_dossier": "Publieke dossier"
    } [item_type]

def getDocModel(item_type):
    return {
        "document": Document,
        "received_document": ReceivedDocument,
        "council_address": CouncilAddress,
        "written_question": WrittenQuestion,
        "format": PublicDocument,
        "policy_document": PolicyDocument,
        "management_document": ManagementDocument,
        "motion": Motion,
        "commitment": Commitment,
    } [item_type]


def getDocModelSerializer(item_type):
    return {
        "document": DocumentSerializer,
        "received_document": ReceivedDocumentSerializer,
        "council_address": CouncilAddressSerializer,
        "written_question": WrittenQuestionSerializer,
        "format": PublicDocumentSerializer,
        "policy_document": PolicyDocumentSerializer,
        "management_document": ManagementDocumentSerializer,
        "motion": MotionSerializer,
        "commitment": CommitmentSerializer,
    } [item_type]