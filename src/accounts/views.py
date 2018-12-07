from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q

import json
import tweepy
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_auth.registration.views import SocialLoginView
from rest_auth.views import LoginView
from rest_auth.social_serializers import TwitterLoginSerializer

from rest_framework.permissions import IsAuthenticated

from dossier.models import Dossier
from favorite.models import Favorite
from query.models import Query

from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.account.adapter import DefaultAccountAdapter

from .serializers import RegistrationSerializer, UserProfileSerializer, UserProfileUpdateSerializer, DeleteProfileSerializer, GetUserItemCountsSerializer, MailGun

from generics.filters import reduce_comma
from itertools import chain
from django.conf import settings
from django.shortcuts import render_to_response
from rest_framework.decorators import api_view

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        print "HAAA"


class RegistrationView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer


class ActivateViews(APIView):
    queryset = User.objects.all()

    def get(self, request, pk, format='json'):
        """
		receives the validation key, checks if it exists.

		If it does, return succes message
		Else return error (invalid validation key or expired key)

        """
        return_message = ''

        # use pk to validate the user
        found_users = self.queryset.filter(activation_key=pk)

        if len(found_users) == 0:
        	return_message = 'Invalid activation key'

        elif len(found_users) > 1:
        	return_message = 'Multiple users with this activation key'
        else:
        	user = found_users[0]
        	user.is_active = True
        	user.activation_key = ''
        	user.save()
        	return_message = 'Account activated'

		# give response
        content = {'message': return_message}
        return Response(content)


class UserProfileView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UpdateProfileView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        try:
            if self.request.data['id'] and (self.request.user.type == 'admin' or
                                         self.request.user.is_superuser):
                return User.objects.get(pk=self.request.data['id'])
        except MultiValueDictKeyError:
            pass
        return self.request.user


class DeleteProfileView(DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = DeleteProfileSerializer

    def get_object(self, queryset=None):
        try:
            pk = self.kwargs['pk']
            if self.request.user.type == 'admin' or self.request.user.is_superuser:
                user = User.objects.get(pk=pk)
                if user:
                    current_prof_pic = User.objects.get(pk=user.id).profile_pic
                    if not current_prof_pic.url.endswith('profile_pictures/default_pic.png'):
                        default_storage.delete(current_prof_pic)
                return user
        except KeyError:
            user = self.request.user
            if user:
                current_prof_pic = User.objects.get(pk=user.id).profile_pic
                if not current_prof_pic.url.endswith('profile_pictures/default_pic.png'):
                    default_storage.delete(current_prof_pic)
            return user


class GetUsersView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        try:
            if self.request.query_params['exclude_me']:
                me_flag = True
            else:
                me_flag = False
        except Exception:
            me_flag = False
        queryset = []
        types = self.request.query_params.get('type', None)
        search = self.request.query_params.get('search', '')
        sort = self.request.query_params.get('sort', 'first_name')
        if self.request.user.type == 'admin' or self.request.user.type == 'auteur' or self.request.user.is_superuser or self.request.user.is_admin:
            if types:
                value = types.split(',')
                typesArr = reduce(reduce_comma, value, [])
                for t in typesArr:
                    if me_flag:
                        queryset = list(chain(
                                queryset,
                                User.objects.filter(
                                    Q(first_name__icontains=search) |
                                    Q(last_name__icontains=search) |
                                    Q(email__icontains=search),
                                    type=t,
                                ).exclude(pk=self.request.user.id)))
                        if t == 'admin':
                            queryset = list(
                            chain(
                                queryset,
                                User.objects.filter(
                                    Q(first_name__icontains=search) |
                                    Q(last_name__icontains=search) |
                                    Q(email__icontains=search),
                                    is_superuser=True,
                                ).exclude(pk=self.request.user.id)))
                    else:
                        queryset = list(
                            chain(
                                queryset,
                                User.objects.filter(
                                    Q(first_name__icontains=search) |
                                    Q(last_name__icontains=search) |
                                    Q(email__icontains=search),
                                    type=t,
                                )))
                        if t == 'admin':
                            queryset = list(
                            chain(
                                queryset,
                                User.objects.filter(
                                    Q(first_name__icontains=search) |
                                    Q(last_name__icontains=search) |
                                    Q(email__icontains=search),
                                    is_superuser=True,
                                )))
            else:
                if me_flag:
                    queryset = User.objects.exclude(pk=self.request.user.id).order_by(sort)
                else:
                    queryset = User.objects.all().order_by(sort)
            return queryset
        else:
            return User.objects.none()


class UserItemsCounts(object):
    def __init__(self, **kwargs):
        for field in ('notifications_count', 'dossiers_count', 'queries_count', 'favorites_count'):
            setattr(self, field, kwargs.get(field, None))


class GetUserItemCounts(viewsets.ViewSet):
    serializer_class = GetUserItemCountsSerializer

    def list(self, request):
        user = request.user
        dossiers = Dossier.objects.filter(Q(owner=user) | Q(shared_users=self.request.user.id)).distinct()
        queries = Query.objects.filter(Q(owner=user) | Q(shared_users=self.request.user.id)).distinct()
        favorites = Favorite.objects.filter(owner=user).distinct('item')

        obj = {
            1: UserItemsCounts(
                notifications_count=notifications.count(),
                dossiers_count=dossiers.count(),
                queries_count=queries.count(),
                favorites_count=favorites.count()
            )
        }

        serializer = GetUserItemCountsSerializer(
            instance=obj.values(), many=True
        )

        return Response(serializer.data)


@api_view(['POST'])
def resend_activation_link(request):
    params = json.loads(request.body)
    email = params['email']
    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            email_subject = "RI Studio %s: activeer je email binnen 2 dagen" % (settings.RIS_MUNICIPALITY)
            context = {
                'username': user.username,
                'portal_url': settings.FRONTEND_URL,
                'municipality': settings.RIS_MUNICIPALITY,
                'link': "%sactiveer-account/%s" % (settings.FRONTEND_URL, user.activation_key),
                'bcolor': settings.COLOR[settings.RIS_MUNICIPALITY]
            }
            html_content = render_to_response('activation_email.html', context)
            mail = MailGun()
            mail.send_mail(email, email_subject, False, html_content)
            return JsonResponse({'response': 'Activation email sent'})
        else:
            return JsonResponse({'response': 'Already activated'})
    except Exception:
        return JsonResponse({'response': 'Geen account met deze e-mail gevonden'})


def test_template(request):
    context = {
        'username': 'username',
        'password': False,
        'portal_url': settings.FRONTEND_URL,
        'municipality': settings.RIS_MUNICIPALITY,
        'link': "%sactiveer-account" % (settings.FRONTEND_URL),
        'bcolor': settings.COLOR[settings.RIS_MUNICIPALITY],
        'uid': 'uid',
        'token': 'token',
        'item': {
            'name': 'Name',
            'date': '2016-12-28T17:54:38',
            'last_modified': '2016-12-28T17:54:38'
        },
        'type': 'document',
        'url': 'url'
    }
    return render_to_response('password_reset_email.html', context)


# Social media Serializers
# Using Django Rest Auth library


class getTwitterReqToken(APIView):
    def get(self, request, format=None):
        auth = tweepy.OAuthHandler('2IfVgQFoVaLfHHFT1QkWtUfkH', 'JOSAzAPs1Dt4tTUUijj6kBQV0GN3zhWPBFpDBi3EqMgE2AnNXh')

        try:
            response = {
                'msg': auth.get_authorization_url(),
                'request_token': auth.request_token
            }
        except tweepy.TweepError:
            response = {
                msg: 'Error! Failed to get request token.'
            }

        return Response(response)


class getTwitterAccToken(APIView):
    def post(self, request, format=None):
        auth = tweepy.OAuthHandler('2IfVgQFoVaLfHHFT1QkWtUfkH', 'JOSAzAPs1Dt4tTUUijj6kBQV0GN3zhWPBFpDBi3EqMgE2AnNXh')
        auth.request_token = request.data.get('request_token')

        try:
            response = auth.get_access_token(request.data.get('oauth_verifier'))
        except tweepy.TweepError:
            response = 'Error! Failed to get access token.'

        return Response(response)


class TwitterLogin(LoginView):
    serializer_class = TwitterLoginSerializer
    adapter_class = TwitterOAuthAdapter


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
	adapter_class = GoogleOAuth2Adapter