import json
from itertools import chain

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters, viewsets, pagination
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from dossier.permissions import IsOwner, DossierPermission, ContentPermission, IsSharedOwner
from dossier.models import Dossier, DossierInvitation, Content, DossierSharedUsers, File, ContentNote
from dossier.filters import CustomDateFilter
from dossier.serializers import (
    CreateDossierSerializer,
    DetailDossierSerializer,
    AddContentSerializer,
    SharedDossierUserSerializer,
    FavoriteDossierSerializer,
    DossierOrderingSerializer,
    ListDossierSerializer,
    DossierContentListSerializer)
from rest_framework.decorators import api_view

from django.core.files.storage import default_storage

from generics.models import CombinedItem, Note

from accounts.serializers import MailGun

User = get_user_model()


class LargeResultsSetPagination(pagination.PageNumberPagination):
	page_size = 10
	page_size_query_param = 'page_size'
	max_page_size = 300


class ListPublicDossiers(generics.ListAPIView):
    serializer_class = CreateDossierSerializer
    filter_class = CustomDateFilter
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('title', 'color', 'ordering_id')
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        return Dossier.objects.filter(accessibility="Public", is_verified=True)


class OrderingDossierAPIView(generics.RetrieveUpdateAPIView):
    queryset = Dossier.objects.filter(is_verified=True)
    serializer_class = DossierOrderingSerializer
    permission_classes = (DossierPermission,)


class CreateDossierAPI(generics.CreateAPIView):
    serializer_class = CreateDossierSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Dossier.objects.filter(owner=user)


class ListDossierAPI(generics.ListAPIView):
    serializer_class = ListDossierSerializer
    filter_class = CustomDateFilter
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('title', 'color', 'ordering_id', 'created_at', 'last_modified')
    permission_classes = (DossierPermission,)
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return Dossier.objects.filter(Q(owner=user) | Q(shared_users=self.request.user.id)).distinct()


class DetailDossierAPI(generics.RetrieveAPIView):
    queryset = Dossier.objects.all()
    serializer_class = DetailDossierSerializer
    permission_classes = (DossierPermission,)


class EditDossierAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreateDossierSerializer
    permission_classes = (DossierPermission,)

    def get_queryset(self):
        dossier_id = self.kwargs['pk']
        for item in File.objects.filter(dossier_id=dossier_id):
            if default_storage.exists(item.file):
                default_storage.delete(item.file)
            item.delete()
        return Dossier.objects.all()


class ContentDossierDeleteAPI(generics.RetrieveDestroyAPIView):
    queryset = Content.objects.all()
    serializer_class = AddContentSerializer
    permission_classes = (ContentPermission,)


class UnshareDossierAPI(viewsets.ModelViewSet):
    serializer_class = SharedDossierUserSerializer
    permission_classes = (IsSharedOwner,)

    def get_object(self):
        user = self.request.user
        _dossier = Dossier.objects.get(id=self.kwargs['pk'])
        _shared_dossier = DossierSharedUsers.objects.get(person=user, dossier=_dossier)
        return _shared_dossier


class ShareDossierDeleteAPI(generics.DestroyAPIView):
    queryset = DossierSharedUsers.objects.all()
    serializer_class = CreateDossierSerializer
    permission_classes = (IsOwner,)


class FavoriteDossierAPIView(generics.RetrieveUpdateAPIView):
    ''' Add current dossier to favorite dossiers '''
    queryset = Dossier.objects.all()
    serializer_class = FavoriteDossierSerializer
    permission_classes = (DossierPermission,)


class FavoriteDossierListAPIView(generics.ListAPIView):
    ''' List of all favorite dossier '''
    serializer_class = FavoriteDossierSerializer
    permission_classes = (DossierPermission,)

    def get_queryset(self):
        user = self.request.user
        return Dossier.objects.filter(
            owner=user,
            is_favorite=True
        )


@api_view(['POST'])
def add_content(request):
    if request.user:
        dossier = Dossier.objects.get(id=request.data['dossier'])
        items = request.data['items']
        permission = "view"
        try:
            permission = DossierSharedUsers.objects.get(dossier_id=request.data['dossier'], person_id=request.user.id).permission
        except DossierSharedUsers.DoesNotExist:
            pass
        if request.user == dossier.owner or permission == 'edit' :
            if not Content.objects.filter(dossier_id=dossier.id, items=items[0]):
                content = Content.objects.create(added_by=request.user, dossier=dossier)
                content.items.add(*items)
                return JsonResponse({'response': 'Succesvol toegevoegd'})
            else:
                return JsonResponse({'response': 'Item bestaat al in het bestand'})
        else:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
    else:
        return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})


@api_view(['POST'])
def add_note_content(request):
    if request.user:
        dossier = Dossier.objects.get(id=request.data['dossier'])
        note_id = request.data['note_id']
        permission = "view"
        try:
            note = Note.objects.get(id=note_id, user=request.user)
        except Exception:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
        try:
            permission = DossierSharedUsers.objects.get(dossier_id=request.data['dossier'], person_id=request.user.id).permission
        except DossierSharedUsers.DoesNotExist:
            pass
        if request.user == dossier.owner or permission == 'edit' :
            if not ContentNote.objects.filter(dossier=dossier.id, note=note.id).exists():
                ContentNote.objects.create(added_by=request.user, dossier=dossier, note=note)
                return JsonResponse({'response': 'Succesvol toegevoegd'})
            else:
                return JsonResponse({'response': 'Item bestaat al in het bestand'})
        else:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
    else:
        return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})


@api_view(['POST'])
def delete_note_content(request):
    if request.user:
        note_id = request.data['note_id']
        dossier_id = request.data['dossier_id']
        try:
            ContentNote.objects.get(note=note_id, dossier=dossier_id).delete()
            return JsonResponse({'response': 'Succesvol verwijderd'})
        except:
            return JsonResponse({'response': 'Err is fout gegaan'})
    else:
        return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})


@api_view(['PUT'])
def edit_folder(request):
    if request.user:
        dossier = Dossier.objects.get(id=request.data['dossier_id'])
        permission = "view"
        try:
            permission = DossierSharedUsers.objects.get(dossier_id=dossier.id, person_id=request.user.id).permission
        except DossierSharedUsers.DoesNotExist:
            pass
        if request.user == dossier.owner or permission == 'edit':
            dossier.title = request.data['title']
            dossier.color = request.data['color']
            dossier.accessibility = request.data['accessibility']
            dossier.save()
            return JsonResponse({'response': 'Folder is succesvol bijgewerkt'})
        else:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="U moet ingelogd zijn voor deze optie")


@api_view(['DELETE'])
def delete_dossier(request):
    if request.user:
        params = json.loads(request.body)
        dossier = Dossier.objects.get(id=params['dossier_id'])
        if request.user == dossier.owner:
            for item in File.objects.filter(dossier_id=dossier.id):
                if default_storage.exists(item.file):
                    default_storage.delete(item.file)
                item.delete()
            dossier.delete()
            return JsonResponse({'response': 'Folder verwijderd'})
        else:
            try:
                DossierSharedUsers.objects.get(person=request.user, dossier=dossier).delete()
                return JsonResponse({'response': 'Folder verwijderd'})
            except DossierSharedUsers.DoesNotExist:
                pass
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="U moet ingelogd zijn voor deze optie")


@api_view(['POST'])
def email_share(request):
    if request.user:
        dossier_id = request.data['dossier_id']
        dossier = Dossier.objects.get(pk=dossier_id)
        email_to_share = request.data['email']
        permission = request.data['permission']

        try:
            possible_user = User.objects.get(email=email_to_share)
            try:
                dossier_shared_user = DossierSharedUsers.objects.get(person=possible_user, dossier=dossier_id)
            except DossierSharedUsers.DoesNotExist:
                dossier_shared_user = None
        except User.DoesNotExist:
            dossier_shared_user = None

        try:
            dossier_user_invitations = DossierInvitation.objects.get(dossier=dossier_id, email=email_to_share, user_confirmed=False)
        except DossierInvitation.DoesNotExist:
            dossier_user_invitations = None


        if dossier_shared_user:
            return JsonResponse({'response': 'Folder is al gedeeld met deze e-mail ' + email_to_share})
        if dossier_user_invitations:
            return JsonResponse({'response': 'Er is al een uitnodiging voor deze e-mail in behandeling ' + email_to_share})

        invitation = DossierInvitation.objects.create(dossier=dossier, user=request.user, email=email_to_share, permission=permission)

        email_subject = "RI Studio %s: folder delen" % (settings.RIS_MUNICIPALITY)
        html_content = "<p>Hoi!</p><p>RI Studio-gebruiker %s wil een map met u delen. Volg deze link als u toegang tot deze map wilt hebben</p><p>%sfolder-delen/%s</p><p>Met vriendelijke groet,</p><p>Support Team Raadsinformatie Portaal %s</p>" % (request.user.username, settings.FRONTEND_URL, invitation.uuid, settings.RIS_MUNICIPALITY)

        mail = MailGun()
        mail.send_mail(email_to_share, email_subject, False, html_content)

        return JsonResponse({'response': 'Uitnodiging verzonden naar ' + email_to_share})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="U moet ingelogd zijn voor deze optie")


@api_view(['POST'])
def get_invitation_details(request):
    invitation_uuid = request.data['uuid']
    try:
        dossier_invitation = DossierInvitation.objects.get(uuid=invitation_uuid)
        response = ({
            "folder" : dossier_invitation.dossier.title,
            "user" : dossier_invitation.user.username,
            "permission" : dossier_invitation.permission,
            "confirmed" : dossier_invitation.user_confirmed
        })
        return JsonResponse({'response': response})
    except DossierInvitation.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Folder delen uitnodiging niet gevonden")


@api_view(['POST'])
def confirm_share_invitation(request):
    invitation_uuid = request.data['uuid']
    try:
        dossier_invitation = DossierInvitation.objects.get(uuid=invitation_uuid)
    except DossierInvitation.DoesNotExist:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Folder delen uitnodiging niet gevonden")

    try:
        Dossier.objects.get(id=dossier_invitation.dossier.id)
    except Dossier.DoesNotExist:
        dossier_invitation.delete()
        return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Folder is verwijderd")

    try:
        email_user = User.objects.get(email=dossier_invitation.email)
    except User.DoesNotExist:
        email_user = None

    if email_user:
        if dossier_invitation.user_confirmed:
            return JsonResponse({'response': 'Deze uitnodiging voor het delen van folders is al bevestigd'})
        else:
            dossier_invitation.user_confirmed = True
            dossier_invitation.save()
            DossierSharedUsers.objects.create(dossier=dossier_invitation.dossier, person=email_user, permission=dossier_invitation.permission)
            return JsonResponse({'response': 'Folder delen succesvol!'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="U moet zich registreren voor deze optie")


@api_view(['POST'])
def upload_file(request):
    if request.user:
        filez = request.FILES['file']
        dossier_id = request.POST['dossier_id']
        file_name = filez.name
        increment = 1
        permission = "view"
        try:
            permission = DossierSharedUsers.objects.get(dossier_id=dossier_id, person_id=request.user.id).permission
        except DossierSharedUsers.DoesNotExist:
            pass
        if request.user == Dossier.objects.get(id=dossier_id).owner or permission == 'edit':
            while File.objects.filter(name=file_name, dossier_id=dossier_id):
                try:
                    file_name = file_name[:file_name.index('(')] + '(' + `increment` + ')'
                except:
                    file_name = file_name + '(' + `increment` + ')'
                increment = increment + 1

            try:
                dossier = Dossier.objects.get(pk=dossier_id)
                File.objects.create(file=filez, name=file_name, dossier=dossier)
            except Dossier.DoesNotExist:
                return JsonResponse({'response': 'Folder niet gevonden'})
            return JsonResponse({'response': 'Bestand geupload'})
        else:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
    else:
        return JsonResponse({'response': 'U moet zich registreren voor deze optie'})


@api_view(['DELETE'])
def delete_file(request):
    if request.user:
        params = json.loads(request.body)
        file_id = params['file_id']
        dossier_id = params['dossier_id']
        permission = "view"
        try:
            permission = DossierSharedUsers.objects.get(dossier_id=dossier_id, person_id=request.user.id).permission
        except DossierSharedUsers.DoesNotExist:
            pass
        if request.user == Dossier.objects.get(id=dossier_id).owner or permission == 'edit':
            try:
                filez = File.objects.get(pk=file_id)
                if default_storage.exists(filez.file):
                    default_storage.delete(filez.file)
                filez.delete()
            except File.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="File Not Found")
            return JsonResponse({'response': 'deleted'})
        else:
            return JsonResponse({'response': 'U hebt geen toestemming voor deze actie'})
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User Not Logged In")


class DossierContentList(generics.ListAPIView):
    serializer_class = DossierContentListSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        notes = []
        files_queryset = File.objects.filter(dossier_id=self.kwargs['pk'])
        combined_items = Content.objects.filter(dossier_id=self.kwargs['pk']).values_list('items')
        if self.request.user.is_superuser or self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.type == 'raadslid':
            combined_item_queryset = CombinedItem.objects.filter(id__in=combined_items)
        else:
            combined_item_queryset = CombinedItem.objects.filter(id__in=combined_items, published=True)

        try:
            queries = self.request.query_params['q'].split(',')
            file_type = "geupload document"
            for query in queries:
                # So this happens if the search word is not included in files type which is declared above
                # Because if the file type does contain the searched word, then all files should be returned
                # Otherwise we do a normal search
                if query.lower() not in file_type:
                    files_queryset = files_queryset.filter(name__icontains=query)
                combined_item_queryset = combined_item_queryset.filter(Q(name__icontains=query) | Q(item_type__icontains=query))
        except MultiValueDictKeyError:
            print('Queries')

        try:
            content_notes = ContentNote.objects.filter(dossier_id=self.kwargs['pk'], added_by=self.request.user)
            for cn in content_notes:
                cn.note.name = cn.note.title
                cn.note.date = cn.note.created_at
                notes.append(cn.note)
        except:
            pass

        result_list = list(chain(files_queryset, combined_item_queryset, notes))

        try:
            ordering = self.request.query_params['ordering']
            result_list = {
                'name':  sorted(result_list, key=lambda result: result.name),
                '-name': sorted(result_list, key=lambda result: result.name, reverse=True),
                'date': sorted(result_list, key=lambda result: result.date),
                '-date': sorted(result_list, key=lambda result: result.date, reverse=True),
                'last_modified': sorted(result_list, key=lambda result: result.last_modified),
                '-last_modified': sorted(result_list, key=lambda result: result.last_modified, reverse=True),
            }[ordering]
        except MultiValueDictKeyError:
            print('No ordering required')
        return result_list
