from django.contrib.auth import get_user_model

from rest_framework import serializers, exceptions
from query.models import Query, QuerySharedUsers
from accounts.serializers import UserProfileSerializer
from django.db.models import Q

User = get_user_model()


class QuerySerializer(serializers.ModelSerializer):
    shared_users = UserProfileSerializer('shared_users', many=True, read_only=True)

    class Meta:
        model = Query
        fields = ('id', 'owner', 'shared_users', 'title', 'filters', 'sort_by', 'page', 'tab', 'created_at',)


class CreateQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ('id', 'title', 'filters', 'sort_by', 'page', 'tab', 'created_at',)

    def create(self, validated_data):
        user = self.context.get('request').user
        query = Query(
            owner=user,
            **validated_data
        )

        query.save()
        return query


class UpdateQuery(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ('id', 'owner', 'shared_users', 'title', 'filters', 'sort_by', 'page', 'tab', 'created_at',)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.query_url = validated_data.get('query_url', instance.query_url)
        instance.save()
        return instance


class OwnerPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user
        queryset = Query.objects.filter(Q(owner=user) | Q(shared_users=user)).distinct()
        return queryset


class AlreadyShared(exceptions.APIException):
    status_code = 401
    default_detail = 'Already shared with this user.'


class UserNotFound(exceptions.APIException):
    status_code = 401
    default_detail = 'User with this username or email niet gevonden.'


class UnshareQuerySerializer(serializers.ModelSerializer):
    query = OwnerPrimaryKeyRelatedField()

    class Meta:
        model = QuerySharedUsers
        fields = ('id', 'query', 'person')
        read_only_fields = ('person',)


class ShareQuerySerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='Username', required=False, allow_blank=True)
    email = serializers.EmailField(label='Email Address', required=False, allow_blank=True)
    query = OwnerPrimaryKeyRelatedField()

    class Meta:
        model = QuerySharedUsers
        fields = ('id', 'query', 'username', 'email', 'person')
        read_only_fields = ('person',)

    def validate(self, data):
        email = User.objects.filter(email=data['email'])
        username = User.objects.filter(username=data['username'])
        try:
            already_shared = QuerySharedUsers.objects.get(query=data['query'])

            if (username in already_shared.person.username or email in already_shared.person.email):
                raise AlreadyShared
        except Exception:
            pass

        if email.exists() or username.exists():
            pass
        else:
            raise UserNotFound
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
            raise UserNotFound

        query = validated_data['query']

        shared_query = QuerySharedUsers(
            person=user,
            query=query,
        )
        shared_query.save()
        return shared_query