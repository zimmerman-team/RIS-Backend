from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from generics import views
# from django.views.decorators.cache import cache_page
# from ris.settings import API_CACHE_SECONDS


urlpatterns = [
    # url(r'^events/$', cache_page(API_CACHE_SECONDS)(views.EventList.as_view())),
    url(r'^events/$', views.EventList.as_view()),
    url(r'^events/(?P<pk>\d+)/$', views.EventDetail.as_view()),
    url(r'^get_child_events/(?P<pk>\d+)/$', views.getChildEvents.as_view()),
    url(r'^child_events/(?P<pk>\d+)/$', views.ChildEventList.as_view()),
    url(r'^events/create/$', views.create_new_event, name='create_new_event'),
    url(r'^events/edit/$', views.edit_event, name='edit_event'),
    url(r'^events/create-child/$', views.create_new_child_event, name='create_new_child_event'),
    url(r'^events/edit-child/$', views.edit_child_event, name='edit_child_event'),
    url(r'^check-time-room-allocated/$', views.check_if_time_and_room_allocated, name='check_if_time_and_room_allocated'),
    url(r'^get-next-politieke-markt-number/$', views.get_next_politieke_markt_number, name='get_next_politieke_markt_number'),
    url(r'^change-event-publish-status/$', views.change_event_publish_status, name='change_event_publish_status'),
    url(r'^get-event-publish-status/$', views.get_event_publish_status, name='get_event_publish_status'),
    url(r'^add-documents-to-event/$', views.add_documents_to_event, name='add_documents_to_event'),
    url(r'^remove-document-from-event/$', views.remove_document_from_event, name='remove_document_from_event'),

    url(r'^documents/$', views.DocumentList.as_view()),
    url(r'^documents/(?P<pk>[0-9]+)/$', views.DocumentDetail.as_view()),
    url(r'^upload-documents/$', views.upload_documents, name='upload_documents'),
    url(r'^edit-document/$', views.edit_document, name='edit_document'),
    url(r'^delete-document/$', views.delete_document, name='delete_document'),
    url(r'^change-document-publish-status/$', views.change_document_publish_status, name='change_document_publish_status'),

    url(r'^agenda_items/$', views.EventAgendaItemList.as_view()),
    url(r'^agenda_items/(?P<pk>[0-9]+)/$', views.EventAgendaItemDetail.as_view()),
    url(r'^agenda_items/edit/$', views.edit_event_agenda_item, name='edit_event_agenda_item'),
    url(r'^agenda_media_items/$', views.EventAgendaMediaList.as_view()),
    url(r'^agenda_media_items/(?P<pk>[0-9]+)/$', views.EventAgendaMediaDetail.as_view()),
    url(r'^agenda_media_link_items/$', views.EventAgendaMediaLinkList.as_view()),
    url(r'^agenda_media_link_items/(?P<pk>[0-9]+)/$', views.EventAgendaMediaLinkDetail.as_view()),
    url(r'^event_media/$', views.EventMediaList.as_view()),
    url(r'^event_media/(?P<pk>[0-9]+)/$', views.EventMediaDetail.as_view()),
    url(r'^agenda_items/create/$', views.create_new_event_agenda_item, name='create_new_event_agenda_item'),
    url(r'^agenda_item/add-items/$', views.add_media_to_agenda_item, name='add_media_to_agenda_item'),
    url(r'^get-next-agenda-item-id/$', views.get_next_agenda_item_id, name='get_next_agenda_item_id'),

    url(r'^combined/$', views.CombinedList.as_view()),
    url(r'^combined/(?P<pk>[0-9]+)/$', views.CombinedDetail.as_view()),

    url(r'^public-dossiers/$', views.PublicDossierList.as_view()),
    url(r'^public-dossiers/(?P<pk>[0-9]+)/$', views.PublicDossierDetail.as_view()),
    url(r'^public-dossiers/add-content/$', views.add_content_to_public_dossier, name='add_content_to_public_dossier'),
    url(r'^public-dossiers/remove-content/$', views.remove_public_dossier_content, name='remove_public_dossier_content'),
    url(r'^public-dossiers/(?P<pk>[0-9]+)/edit/$', views.PublicDossierUpdateDestroy.as_view(), name='public_dossier_edit'),
    url(r'^public-dossiers/(?P<pk>[0-9]+)/delete/$', views.PublicDossierUpdateDestroy.as_view(), name='public_dossier_delete'),
    url(r'^public-dossiers/change-publish-status/$', views.change_dossier_publish_status, name='change_dossier_publish_status'),
    url(r'^public-dossiers/child_dossiers/$', views.get_public_dossier_child_dossiers, name='get_public_dossier_child_dossiers'),
    url(r'^public-dossiers/check-title/$', views.check_if_dossier_title_exists, name='check_if_dossier_title_exists'),

    url(r'^received_documents/(?P<pk>[0-9]+)/$', views.ReceivedDocumentDetail.as_view()),
    url(r'^council_addresses/(?P<pk>[0-9]+)/$', views.CouncilAddressDetail.as_view()),
    url(r'^commitments/(?P<pk>[0-9]+)/$', views.CommitmentDetail.as_view()),
    url(r'^written_questions/(?P<pk>[0-9]+)/$', views.WrittenQuestionDetail.as_view()),
    url(r'^motions/(?P<pk>[0-9]+)/$', views.MotionDetail.as_view()),
    url(r'^public_documents/(?P<pk>[0-9]+)/$', views.PublicDocumentDetail.as_view()),
    url(r'^management_documents/(?P<pk>[0-9]+)/$', views.ManagementDocumentDetail.as_view()),
    url(r'^policy_documents/(?P<pk>[0-9]+)/$', views.PolicyDocumentDetail.as_view()),

    url(r'^item_counts/$', views.GetItemCounts.as_view({'get': 'list'})),

    url(r'^my_agenda/list', views.MyAgendaList.as_view(), name='my_agenda_list'),
    url(r'^my_agenda/add', views.add_my_agenda, name='add_to_my_agenda'),
    url(r'^my_agenda/remove', views.remove_my_agenda, name='remove_from_my_agenda'),

    url(r'^note/add', views.add_note, name='add_to_notes'),
    url(r'^note/edit', views.edit_note, name='edit_note'),
    url(r'^note/remove', views.remove_note, name='remove_from_notes'),
    url(r'^note/my_list/$', views.MyNotes.as_view(), name='my_notes_list'),
    url(r'^note/document_list', views.DocNotes.as_view(), name='my_notesz_list'),
    url(r'^note/(?P<pk>[0-9]+)/$', views.get_note, name='get_my_note'),

    url(r'^speakers/$', views.SpeakersList.as_view()),
    url(r'^event_speakers/(?P<event_id>\d+)/$', views.EventAgendasSpeakerList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)

