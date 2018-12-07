from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Q

from dossier.models import Dossier, Content, DossierSharedUsers, File
from generics.models import ReceivedDocument
from generics.models import CouncilAddress
from generics.models import Commitment
from generics.models import WrittenQuestion
from generics.models import Motion
from generics.models import PublicDocument
from generics.models import ManagementDocument
from generics.models import PolicyDocument
from generics.models import Note
from generics.models import Document
from generics.models import Event
from generics.models import CombinedItem

from accounts.serializers import UserProfileSerializer
from generics.serializers import NoteListSerializer
from itertools import chain

User = get_user_model()


class OwnerPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Dossier.objects.filter(Q(owner=user) | Q(shared_users=user)).distinct()
        return queryset


class content_serializer_item(serializers.ModelSerializer):
    content_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

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
    def get_content_id(item):
        if item.dossier_id:
            return Content.objects.get(items__id=item.id, dossier_id=item.dossier_id).id
        else:
            return 0

    @staticmethod
    def get_url(item):
        if item.item_type == 'event' or item.item_type == 'child_event' or item.item_type == 'document':
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
            "public_dossier": None,
        }[item.item_type]

        if doc_type == Motion or doc_type == PublicDocument or doc_type == PolicyDocument or doc_type == ReceivedDocument or doc_type == ManagementDocument:
            return doc_type.objects.get(id=item.item_id).document.url

        if doc_type == CouncilAddress or doc_type == WrittenQuestion:
            return doc_type.objects.get(id=item.item_id).question_document.url

        if doc_type == Commitment:
            return doc_type.objects.get(id=item.item_id).new_question_document.url

        return None

    class Meta:
        model = CombinedItem
        fields = ('id', 'item_id', 'content_id', 'name', 'date', 'url', 'last_modified', 'item_type', 'parent_id')


class content_serializer_event(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'name')


class content_serializer_document(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'text')


class DossierOrderingSerializer(serializers.ModelSerializer):
    new_ordering_id = serializers.IntegerField(label='new_ordering', required=False)

    class Meta:
        model = Dossier
        fields = ('id', 'title', 'accessibility', 'color', 'is_verified', 'ordering_id', 'new_ordering_id')
        read_only_fields = ('title', 'accessibility', 'color', 'is_verified', 'ordering_id')
        write_only_fields = ('new_ordering_id',)

    def update(self, instance, validated_data):
        instance.ordering_id = validated_data.get('new_ordering_id')
        instance.save()
        return instance


class CreateDossierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dossier
        fields = ('id', 'title', 'accessibility', 'color', 'created_at', 'last_modified', 'is_verified', 'ordering_id')
        read_only_fields = ('is_verified', 'ordering_id')

    def create(self, validated_data):
        user = self.context.get('request').user
        dossier = Dossier(
            owner=user,
            **validated_data
        )

        dossier.is_verified = False

        dossier.ordering_id = dossier.id

        dossier.save()
        return dossier

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.accessibility = validated_data.get('accessibility', instance.accessibility)
        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance


class AddContentSerializer(serializers.ModelSerializer):
    dossier = OwnerPrimaryKeyRelatedField()
    added_by = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Content
        fields = ('id', 'dossier', 'items', 'added_by')

    def create(self, validated_data):
        user = self.context.get('request').user
        items = validated_data.pop('items')
        dossier = Dossier.objects.get(id=validated_data['dossier'].id)
        # So we check here if this item has already been added to the folder
        # And if it has already been added then we return an error response
        if user == dossier.owner:
            if not Content.objects.filter(dossier_id=validated_data['dossier'].id, items=items[0]):
                content = Content.objects.create(added_by=user, **validated_data)
                content.items.add(*items)
                return content
            else:
                return Content(**validated_data)
        else:
            return Content(**validated_data)


class ShareDossierSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(many=True)
    class Meta:
        model = Dossier
        fields = ('user',)


class SharedDossierUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='Username', required=False, allow_blank=True)
    email = serializers.EmailField(label='Email Address', required=False, allow_blank=True)
    dossier = OwnerPrimaryKeyRelatedField()

    class Meta:
        model = DossierSharedUsers
        fields = ('id', 'dossier', 'username', 'email', 'person', 'permission')
        read_only_fields = ('person',)

    def validate(self, data):
        email = User.objects.filter(email=data['email'])
        username = User.objects.filter(username=data['username'])

        try:
            already_shared = DossierSharedUsers.objects.get(dossier=data['dossier'])

            if username in already_shared.person.username:
                raise_error = True
        except Exception:
            raise_error = False

        if raise_error:
             raise serializers.ValidationError("You've already shared this dossier with this user. Please try again with another user.")
        if email.exists() or username.exists():
            pass
        else:
            raise serializers.ValidationError("A user with that username or email does not exists, please try again.")
        return data

    def create(self, validated_data):
        _username = User.objects.filter(username=validated_data['username'])
        _email = User.objects.filter(email=validated_data['email'])

        try:
            if _username:
                user = User.objects.get(username=validated_data['username'])
            elif _email:
                user = User.objects.get(email=validated_data['email'])
        except User.DoesNotExist:
            user = None

        dossier = validated_data['dossier']
        permission = validated_data['permission']

        shared_dossier = DossierSharedUsers(
            person=user,
            dossier=dossier,
            permission=permission
        )
        shared_dossier.save()
        return shared_dossier


class EditShareDossierUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierSharedUsers
        fields = ('id', 'permission')

    def update(self, instance, validated_data):
        instance.permission = validated_data.get('permission', instance.permission)
        instance.save()

        return instance


class ContentDetailSerializer(serializers.ModelSerializer):
    added_by = serializers.SlugRelatedField(slug_field='username', read_only=True)
    items = content_serializer_item(many=True, read_only=True)

    class Meta:
        model = Content
        fields = ('id', 'dossier', 'added_by', 'items')


class DetailDossierSerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer('dossier_owner', read_only=True)
    content = serializers.SerializerMethodField()
    shared_users = serializers.SlugRelatedField(slug_field='username', read_only=True, many=True)

    # So what we do here is we add in extra items into the CONTENT array
    # Where those extra items are actually files and made up of a different model
    # than the actual content array is made of
    # BUT it gonna have the same fields so that the front-end part would work the same/similarly
    @staticmethod
    def get_content(item):
        files_queryset = File.objects.filter(dossier_id=item.pk)
        files_serializer = FilesSerializer(files_queryset, many=True, read_only=True).data
        content_queryset = Content.objects.filter(dossier_id=item.pk)
        content_serializer = ContentDetailSerializer(content_queryset, many=True, read_only=True).data
        result_list = list(chain(files_serializer, content_serializer))
        return result_list

    class Meta:
        model = Dossier
        fields = ('id', 'title', 'owner', 'accessibility', 'color', 'created_at', 'last_modified', 'content', 'shared_users', 'is_verified')


class FavoriteDossierSerializer(serializers.ModelSerializer):
    ''' making current dossier favorite '''
    class Meta:
        model = Dossier
        fields = ('id', 'title', 'is_favorite')
        read_only_fields = ('title',)


class FilesSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    absolute = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    @staticmethod
    def get_url(file):
        return file.file.url if 'http' in file.file.url else settings.STATIC_URL[1:] + file.file.url

    @staticmethod
    def get_absolute(file):
        return file.file.file.name

    @staticmethod
    def get_type(whatever):
        return "Geupload document"

    class Meta:
        model = File
        fields = (
            'id',
            'file',
            'name',
            'type',
            'url',
            'dossier_id',
            'date',
            'last_modified',
            'absolute'
        )


class ListDossierSerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer('owner', read_only=True)
    shared_users = UserProfileSerializer('shared_users', many=True, read_only=True)

    class Meta:
        model = Dossier
        fields = ('id', 'title', 'accessibility', 'color', 'created_at', 'last_modified', 'is_verified', 'ordering_id', 'owner', 'shared_users')
        read_only_fields = ('is_verified', 'ordering_id')


class DossierSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    owner = UserProfileSerializer('owner', read_only=True)
    shared_users = UserProfileSerializer('shared_users', many=True, read_only=True)

    # So what we do here is we add in extra items into the CONTENT array
    # Where those extra items are actually files and made up of a different model
    # than the actual content array is made of
    # BUT it gonna have the same fields so that the front-end part would work the same/similarly
    @staticmethod
    def get_content(item):
        files_queryset = File.objects.filter(dossier_id=item.pk)
        files_serializer = FilesSerializer(files_queryset, many=True, read_only=True).data
        content_queryset = Content.objects.filter(dossier_id=item.pk)
        content_serializer = ContentDetailSerializer(content_queryset, many=True, read_only=True).data
        result_list = list(chain(files_serializer, content_serializer))
        return result_list

    class Meta:
        model = Dossier
        fields = ('id', 'title', 'accessibility', 'color', 'created_at', 'last_modified', 'is_verified', 'ordering_id', 'owner', 'shared_users', 'content')
        read_only_fields = ('is_verified', 'ordering_id')


class DossierContentListSerializer(serializers.Serializer):
    content = serializers.SerializerMethodField()

    def get_content(self, item):
        if type(item) is File:
            return FilesSerializer(item, read_only=True).data
        elif type(item) is CombinedItem:
            dossier_id = self.context['request'].parser_context['kwargs']['pk']
            item.dossier_id = dossier_id
            return content_serializer_item(item, read_only=True).data
        elif type(item) is Note:
            return NoteListSerializer(item, read_only=True).data