from django.conf.urls import url
from dossier.views import (
    CreateDossierAPI, DetailDossierAPI,
    ContentDossierDeleteAPI, FavoriteDossierAPIView, ListDossierAPI, FavoriteDossierListAPIView, add_content,
    OrderingDossierAPIView,
    ListPublicDossiers, UnshareDossierAPI, email_share, confirm_share_invitation, get_invitation_details, upload_file,
    delete_file, DossierContentList, delete_dossier, edit_folder, add_note_content, delete_note_content)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^dossier/create/$', CreateDossierAPI.as_view(), name='create_new_dossier'),
    url(r'^dossier/list/$', ListDossierAPI.as_view(), name='list of all dossiers'),
    url(r'^dossier/public-list/$', ListPublicDossiers.as_view(), name='list of all public and verified/approved dossiers'),
    url(r'^dossier/(?P<pk>\d+)/$', DetailDossierAPI.as_view(), name='dossier_details'),
    url(r'^dossier/delete/$', delete_dossier, name='delete_dossier'),
    url(r'^dossier/edit/$', edit_folder, name='edit_folder'),
    url(r'^dossier/content/(?P<pk>\d+)/$', DossierContentList.as_view(), name='dossier_contents'),

    url(r'^dossier/content/add/$', add_content, name='add_new_content'),
    url(r'^dossier/content/delete/(?P<pk>\d+)/$', ContentDossierDeleteAPI.as_view(), name='remove-dossier-content'),

    url(r'^dossier/note-content/add/$', add_note_content, name='add_new_note'),
    url(r'^dossier/note-content/delete/$', delete_note_content, name='remove-dossier-note'),

    url(r'^dossier/unshare/(?P<pk>\d+)/$', UnshareDossierAPI.as_view({'delete': 'destroy'}), name='shared-dossier-unshare'),
    url(r'^dossier/favorite/(?P<pk>\d+)$', FavoriteDossierAPIView.as_view()),
    url(r'^dossier/favorite/list/$', FavoriteDossierListAPIView.as_view(), name='list of all favorite dossiers'),

    url(r'^dossier/ordering/(?P<pk>\d+)$', OrderingDossierAPIView.as_view()),

    url(r'^dossier/upload-file/', upload_file, name='upload_file'),
    url(r'^dossier/delete-file/', delete_file, name='delete_file'),

    url(r'^dossier/share/', email_share, name='share_folder'),
    url(r'^dossier/get_invitation/', get_invitation_details, name='get invitation details'),
    url(r'^dossier/confirm_invitation/', confirm_share_invitation, name='confirm share invitation')

] + static(settings.STATIC_URL, document_root=settings.MEDIA_ROOT)
