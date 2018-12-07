from __future__ import unicode_literals
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

from django.contrib.postgres.search import SearchVectorField

User = settings.AUTH_USER_MODEL


class DocumentContent(models.Model):
    content = models.TextField(null=True)
    vector = SearchVectorField(null=True)


class PublicDossier(models.Model):
    title = models.TextField(null=True)
    created_at = models.DateTimeField(null=True)
    last_modified = models.DateTimeField(null=True)
    folder_count = models.IntegerField(null=True)
    document_count = models.IntegerField(null=True)
    notubiz_id = models.IntegerField(null=True)
    published = models.BooleanField(default=True)
    depth = models.IntegerField(default=0)
    parent_dossier = models.ForeignKey("PublicDossier", default=None, null=True, related_name='public_dossier_parent')


class Event(models.Model):
    """
    An event is a meeting that can have multiple sub events
    """
    EVENT_STATUS_CHOICES = (
        ('cancelled', 'Cancelled'),
        ('tentative', 'Tentative'),
        ('confirmed', 'Confirmed'),
        ('passed', 'Passed'),
    )

    notubiz_id = models.IntegerField(null=True, unique=True)
    ibabs_id = models.TextField(null=True)
    name = models.TextField(null=True)
    jurisdiction = models.TextField(null=True)
    description = models.TextField(null=True)
    classification = models.TextField(null=True)
    start_time = models.DateTimeField(null=True)
    timezone = models.TextField(null=True)
    end_time = models.DateTimeField(null=True)
    all_day = models.BooleanField(default=False, blank=True)
    status = models.TextField(null=True)
    location = models.TextField(null=True)
    parent_event = models.ForeignKey("Event", default=None, null=True, related_name='parentevent')
    last_modified = models.DateTimeField(default=None, null=True)
    published = models.BooleanField(default=True)

    original_last_modified = None

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.original_last_modified = self.last_modified

    def __str__(self):
        return self.name


class Document(models.Model):
    ITEM_TYPE_OPTIONS = (
        ('none', 'None'),
        ('event', 'Event'),
        ('child_event', 'Child Event'),
        ('agenda_item', 'Agenda Item'),
        ('public_dossier', 'Public Dossier'),
        ('received_document', 'Received document'),
        ('council_address', 'Council address'),
        ('written_question', 'Written question'),
        ('format', 'Format'),
        ('motion', 'Motion'),
        ('commitment', 'Commitment'),
        ('management_document', 'Management document'),
        ('policy_document', 'Policy document')
    )

    notubiz_id = models.IntegerField(null=True, unique=True)
    file = models.FileField(upload_to='documents', null=True)
    ibabs_id = models.TextField(null=True)
    text = models.TextField()
    url = models.URLField(max_length=2000)
    last_modified = models.DateTimeField(null=True)
    file_path = models.TextField(null=True)
    media_type = models.TextField(null=True)
    event = models.ForeignKey(Event, related_name='documents', null=True, on_delete=models.SET_NULL)
    public_dossier = models.ForeignKey(PublicDossier, related_name='public_dossier_document', null=True, on_delete=models.SET_NULL)
    attached_to = models.CharField(max_length=50, choices=ITEM_TYPE_OPTIONS, default='none')
    date = models.DateTimeField(null=True)
    document_content_scanned = models.BooleanField(default=False)
    doc_content = models.ForeignKey(DocumentContent, on_delete=models.CASCADE, related_name='doc_content', null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='document_author', on_delete=models.CASCADE, null=True)


    def __str__(self):
        return '{doc.text} for event {doc.event}'.format(doc=self)


class EventDocument(models.Model):
    event = models.ForeignKey(Event, related_name='event_document', null=True, on_delete=models.SET_NULL)
    document_id = models.IntegerField(null=True)
    document_type = models.TextField(null=True)


class EventAgendaItem(models.Model):
    description = models.TextField(null=True)
    classification = models.TextField(null=True)
    subjects = ArrayField(base_field=models.TextField(), null=True, default=list)
    notes = models.TextField(null=True)
    order = models.IntegerField(blank=True, null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    event = models.ForeignKey(Event, related_name='agenda')
    griffier = models.ForeignKey(User, related_name='agenda_item_griffier', on_delete=models.CASCADE, null=True)
    medewerker = models.ForeignKey(User, related_name='agenda_item_medewerker', on_delete=models.CASCADE, null=True)


class EventAgendaMedia(models.Model):
    """
    Media attached to Agenda item
    """
    note = models.TextField(null=True)
    date = models.DateTimeField(null=True)
    agenda_item = models.ForeignKey(EventAgendaItem, related_name='media')


class EventAgendaMediaLink(models.Model):
    item_id = models.IntegerField(default=0)
    url = models.URLField(max_length=2000)
    media_type = models.TextField(null=True)
    text = models.TextField(default=None)
    media = models.ForeignKey(EventAgendaMedia, related_name='links')


class EventMedia(models.Model):
    filename = models.CharField(max_length=100, default=None)
    httpstream = models.URLField(max_length=254, null=True)
    rtmpstream = models.URLField(max_length=254, null=True)
    download = models.URLField(max_length=254)
    event = models.ForeignKey(Event, related_name='event_media')


class Organisation(models.Model):
    notubiz_id = models.IntegerField(unique=True, default=0)
    name = models.TextField(null=True)


class Person(models.Model):
    notubiz_id = models.IntegerField(unique=True, default=0)
    name = models.CharField(max_length=254, null=False, blank=False)


class Party(models.Model):
    """
    Political parties.
    """
    notubiz_id = models.IntegerField(unique=True, default=0)
    name = models.TextField(null=True)


class ReceivedDocument(models.Model):
    """
    Maps to module 1 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)

    document = models.ForeignKey(Document, null=True)
    subject = models.TextField(null=True)
    description = models.TextField(null=True)
    publication_date = models.DateTimeField(null=True)
    date = models.DateTimeField(null=True)
    date_created = models.DateTimeField(null=True)
    advice = models.TextField(null=True)
    sender = models.TextField(null=True)
    location = models.TextField(null=True)
    document_type = models.TextField(null=True)
    policy_field = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    category = models.TextField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    number = models.TextField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='received_documents')
    heading = models.TextField(null=True)
    commission = models.IntegerField(null=True)
    add_to_LTA = models.TextField(null=True)
    status = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='received_document_author', on_delete=models.CASCADE, null=True)

    RIS_number = models.IntegerField(null=True)


class CouncilAddress(models.Model):
    """
    Maps to module 2 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)

    title = models.TextField(null=True)
    publication_date = models.DateTimeField(null=True)

    question_date = models.DateTimeField(null=True)
    question_document = models.ForeignKey('Document', null=True, related_name="ca_question_documents")

    interim_answer_date = models.DateTimeField(null=True)
    interim_answer_document = models.ForeignKey('Document', null=True, related_name="ca_interim_answer_documents")

    answer_date = models.DateTimeField(null=True)
    answer_document = models.ForeignKey('Document', null=True, related_name="ca_answer_documents")

    handled_by = models.TextField(null=True)
    location = models.TextField(null=True)
    address_type = models.TextField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='council_adresses')
    name = models.TextField(null=True)
    address = models.TextField(null=True)
    email = models.TextField(null=True)
    telephone = models.TextField(null=True)
    place = models.TextField(null=True)
    postal_code = models.TextField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    add_to_LTA = models.IntegerField(null=True)
    RIS_number = models.IntegerField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='council_address_author', on_delete=models.CASCADE, null=True)


class Commitment(models.Model):
    """
    Maps to module 3 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)

    title = models.TextField(null=True)

    expected_settlement_date = models.DateTimeField(null=True)
    commitment_date = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)

    portfolio_holder = models.TextField(null=True)
    recipient = models.TextField(null=True)
    agenda_item = models.TextField(null=True)
    policy_field = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    text = models.TextField(null=True)
    situation = models.TextField(null=True)
    involved_comittee = models.TextField(null=True)
    dispensation = models.TextField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='commitment_author', on_delete=models.CASCADE, null=True)

    new_document = models.ForeignKey(
        'Document',
        null=True,
        related_name="commitment_new_document")


class WrittenQuestion(models.Model):
    """
    Maps to module 4 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)
    title = models.TextField(null=True)
    publication_date = models.DateTimeField(null=True)
    explanation = models.IntegerField(null=True)
    parties = models.ManyToManyField(Party)
    question_date = models.DateTimeField(null=True)
    question_document = models.ForeignKey(
        'Document',
        null=True,
        related_name="wq_question_documents")
    interim_answer_date = models.DateTimeField(null=True)
    interim_answer_document = models.ForeignKey(
        'Document',
        null=True,
        related_name="wq_interim_answer_documents")
    interim_answer_explanation = models.TextField(null=True)
    answer_date = models.DateTimeField(null=True)
    answer_document = models.ForeignKey(
        'Document',
        null=True,
        related_name="wq_answer_documents")
    answer_explanation = models.TextField(null=True)
    expected_answer_date = models.DateTimeField(null=True)
    initiator = models.ManyToManyField(Person)
    policy_field = models.TextField(null=True)
    location = models.TextField(null=True)
    involved_comittee = models.TextField(null=True)
    portfolio_holder = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    progress_state = models.TextField(null=True)
    evaluation_date = models.DateTimeField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='written_questions')

    vote_outcome = models.TextField(null=True)
    number = models.TextField(null=True)
    unknown_type = models.TextField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    add_to_LTA = models.IntegerField(null=True)
    meeting_category = models.IntegerField(null=True)
    RIS_number = models.IntegerField(null=True)
    co_signatories = models.IntegerField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='written_question_author', on_delete=models.CASCADE, null=True)


class Motion(models.Model):
    """
    Maps to module 6 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)

    title = models.TextField(null=True)
    agenda_item = models.TextField(null=True)
    document_type = models.TextField(null=True)
    policy_field = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    document = models.ForeignKey('Document', related_name="motion_document", null=True)
    new_document_settlement = models.ForeignKey('Document', related_name="new_document_settlement_document", null=True)
    parties = models.ManyToManyField(Party)
    portfolio_holder = models.TextField(null=True)
    involved_comittee = models.TextField(null=True)
    expected_settlement_date = models.DateTimeField(null=True, default=None)
    outcome = models.TextField(null=True)
    meeting_date = models.DateTimeField(null=True)
    date_created = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)
    dispensation = models.TextField(null=False)
    explanation = models.TextField(null=True)
    council_member = models.TextField(null=True)
    comments = models.TextField(null=True)
    situation = models.TextField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='motion_author', on_delete=models.CASCADE, null=True)


class PublicDocument(models.Model):
    """
    Maps to module 7 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)

    title = models.TextField(null=True)
    document_date = models.DateTimeField(null=True)
    publication_date = models.DateTimeField(null=True)
    date_created = models.DateTimeField(null=True)
    document = models.ForeignKey('Document', related_name="public_documents")
    document_type = models.TextField(null=True)
    number = models.TextField(null=True)
    meeting_category = models.IntegerField(null=True)
    portfolio_holder = models.IntegerField(null=True)
    policy_field = models.TextField(null=True)
    settlement = models.TextField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='public_documents')
    category = models.TextField(null=True)
    location = models.TextField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    add_to_LTA = models.IntegerField(null=True)
    RIS_number = models.IntegerField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='public_document_author', on_delete=models.CASCADE, null=True)


class ManagementDocument(models.Model):
    """
    Maps to module 8 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)
    title = models.TextField(null=True)
    number = models.TextField(null=True)
    publication_date = models.DateTimeField(null=True)
    document = models.ForeignKey('Document', related_name="management_documents")
    document_date = models.DateTimeField(null=True)
    document_type = models.TextField(null=True)
    district = models.TextField(null=True)
    date_created = models.DateTimeField(null=True)
    portfolio_holder = models.IntegerField(null=True)
    policy_field = models.TextField(null=True)
    meeting_category = models.IntegerField(null=True)
    settlement = models.TextField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='management_documents')
    category = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    operational_from = models.DateTimeField(null=True)
    settlement_date = models.DateTimeField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    valid_until = models.DateTimeField(null=True)
    add_to_LTA = models.IntegerField(null=True)
    operational_from_2 = models.DateTimeField(null=True) # there's 2 attribute id's in notubiz for this
    status = models.TextField(null=True)
    RIS_number = models.IntegerField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='management_document_author', on_delete=models.CASCADE, null=True)


class PolicyDocument(models.Model):
    """
    Maps to module 9 @ Notubiz
    """
    organisation = models.ForeignKey(Organisation, null=True, default=0)
    notubiz_id = models.IntegerField(null=True)
    item_created = models.DateTimeField(null=True, default=None)
    last_modified = models.DateTimeField(null=True, default=None)
    confidential = models.IntegerField(default=0)
    distribution_group = models.IntegerField(default=0)
    title = models.TextField(null=True)
    document = models.ForeignKey('Document', related_name="policy_documents")
    document_type = models.TextField(null=True)
    document_date = models.DateTimeField(null=True)
    number = models.TextField(null=True)
    policy_field = models.TextField(null=True)
    dossiercode = models.TextField(null=True)
    meeting_category = models.IntegerField(null=True)
    location = models.TextField(null=True)
    portfolio_holder = models.IntegerField(null=True)
    settlement = models.TextField(null=True)
    date_created = models.DateTimeField(null=True)
    linked_event = models.ForeignKey(
        "Event",
        default=None,
        null=True,
        related_name='policy_documents')
    publication_date = models.DateTimeField(null=True)
    category = models.TextField(null=True)
    coupled_to_module = models.IntegerField(null=True)
    add_to_LTA = models.IntegerField(null=True)
    RIS_number = models.IntegerField(null=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='policy_document_author', on_delete=models.CASCADE, null=True)


class CombinedItem(models.Model):
    """
    TODO replace this todo with a short summary of what this CombinedItem is - 2017-06-21
    """

    ITEM_TYPE_OPTIONS = (
        ('document', 'Document'),
        ('event', 'Event'),
        ('child_event', 'Child Event'),
        ('public_dossier', 'Public Dossier'),
        ('received_document', 'Received document'),
        ('council_address', 'Council address'),
        ('written_question', 'Written question'),
        ('format', 'Format'),
        ('motion', 'Motion'),
        ('commitment', 'Commitment'),
        ('management_document', 'Management document'),
        ('policy_document', 'Policy document')
    )

    item_id = models.IntegerField(null=True)
    notubiz_id = models.IntegerField(null=True)
    ibabs_id = models.TextField(null=True)
    name = models.TextField(null=True)
    date = models.DateTimeField(null=True)
    url = models.TextField(null=True)
    classification = models.TextField(null=True)
    last_modified = models.DateTimeField(null=True, default=None)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPE_OPTIONS, default='event')
    doc_content = models.ForeignKey(DocumentContent, on_delete=models.CASCADE, related_name='com_content', null=True)
    published = models.BooleanField(default=True)
    status = models.TextField(null=True)
    subject = models.TextField(null=True)
    portfolio = models.TextField(null=True)
    author = models.ForeignKey(User, related_name='combined_item_author', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class MyAgenda(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=0)
    agenda = models.ForeignKey(Event, on_delete=models.CASCADE, unique=True,)


class Note(models.Model):
    doc_title = models.TextField(null=True)
    document_id = models.IntegerField(null=True)
    type = models.IntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=0)
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class Speaker(models.Model):
    notubiz_id = models.IntegerField(null=False, unique=True)
    person_id = models.IntegerField(null=True)
    firstname = models.TextField(null=True)
    lastname = models.TextField(null=True)
    sex = models.TextField(null=True)
    function = models.TextField(null=True)
    email = models.TextField(null=True)
    photo_url = models.TextField(null=True)
    last_modified = models.DateTimeField(null=True, default=None)


class SpeakerIndex(models.Model):
    speaker = models.ForeignKey(Speaker, related_name='speaker')
    agenda_item = models.ForeignKey(EventAgendaItem, related_name='agenda_item')
    start_time = models.IntegerField(null=True)


class PublicDossierContent(models.Model):
    dossier = models.ForeignKey(PublicDossier, related_name='content_dossier')
    item = models.ForeignKey(CombinedItem, related_name='content_item')
    item_type = models.TextField(null=True)


def send_notification_email(subject, message, to_email):
    send_mail(
        subject,
        message,
        to_email,
        fail_silently = True)