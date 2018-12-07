from django.conf import settings
import requests
import django.contrib.auth.validators
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import AnonymousUser
from django.core.files.storage import default_storage
# from django.core.mail import EmailMessage
from django.core.signing import dumps

from rest_framework import serializers, exceptions

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_auth.serializers import LoginSerializer
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class CustomPassResetForm(PasswordResetForm):
    def save(self, email, domain_override=None, use_https=False, token_generator=default_token_generator,
        from_email=None, request=None, html_email_template_name=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        current_site = get_current_site(request)
        user = User.objects.get(email=email)
        context = {
            'email': user.email,
            'domain': current_site.domain,
            'site_name': current_site.name,
            'municipality': settings.RIS_MUNICIPALITY,
            'portal_url': settings.FRONTEND_URL,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'username': user.username,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http'
        }

        return context


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    password_reset_form_class = CustomPassResetForm

    def send_mail(self, context):
        email_subject = "RI Studio %s: Reset wachtwoord" % (settings.RIS_MUNICIPALITY)
        context['bcolor'] = settings.COLOR[settings.RIS_MUNICIPALITY]
        html_content = render_to_response('password_reset_email.html', context)
        mail = MailGun()
        mail.send_mail(context['email'], email_subject, False, html_content)

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        if not User.objects.filter(email=value):
            raise EmailNotFound

        return value

    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'request': request,
            'html_email_template_name': 'password_reset_email.html',
            'email': request.data['email']
        }
        context = self.reset_form.save(**opts)
        self.send_mail(context)


class ExistingEmailFound(exceptions.APIException):
    status_code = 401
    default_detail = 'Deze e-mail wordt gebruikt in een ander account.'


class ExistingUsernameFound(exceptions.APIException):
    status_code = 401
    default_detail = 'Deze username wordt gebruikt in een ander account.'


class RegistrationSerializer(serializers.ModelSerializer):
    """
    A class for user registration included account verification by activation email.
    """
    username = serializers.CharField(label='Username', max_length=30)
    first_name = serializers.CharField(label='First name', max_length=30)
    last_name = serializers.CharField(label='Last name', max_length=30)
    mobile_number = serializers.CharField(label='Mobile', max_length=30,
                                          required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(min_length=8, label='Password')
    password2 = serializers.CharField(min_length=8, label='Confirm Password',
                                      help_text="Enter the same password as above, for verification.")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password', 'password2', 'mobile_number', 'type')
        write_only_fields = ('password', 'is_active')

    def validate_username(self, value):
        data = self.get_initial()
        username = data.get("username")
        if User.objects.filter(username=username).exists():
            raise ExistingUsernameFound
        return value

    def validate_email(self, value):
        data = self.get_initial()
        email = data.get("email")
        if User.objects.filter(email=email).exists():
            raise ExistingEmailFound
        return value

    def validate_password(self, value):
        """
        Password Validation, the two given password must match
        """
        data = self.get_initial()
        password1 = data.get("password2")
        password2 = value
        if password1 != password2:
            raise serializers.ValidationError("Passwords must match.")
        return value

    def validate_password2(self, value):
        data = self.get_initial()
        password1 = data.get("password")
        password2 = value
        if password1 != password2:
            raise serializers.ValidationError("Passwords must match.")
        return value

    def create(self, validated_data):
        """
        Saving given information into the user model.
        Sending a verification email with an activation link.
        """

        try:
            is_admin = self.context['request'].user is not AnonymousUser and self.context['request'].user.is_superuser or self.context['request'].user.type == 'admin'
        except AttributeError:
            is_admin = False

        first_name = validated_data ['first_name']
        last_name = validated_data['last_name']
        username = validated_data['username']
        try:
            mobile_number = validated_data['mobile_number']
        except KeyError:
            mobile_number = ''
        try:
            typez = validated_data['type']
        except KeyError:
            typez = 'regular'

        email = validated_data['email']
        password = validated_data['password']

        user_obj = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username = username,
            mobile_number=mobile_number,
            type=typez,
         )
        user_obj.set_password(password)
        user_obj.is_active = False
        user_obj.save()

        if user_obj.is_active == False:
            activation_key = str(dumps(username))

            email_subject = "RI Studio %s: activeer je email binnen 2 dagen" % (settings.RIS_MUNICIPALITY)
            # from_email = settings.EMAIL_HOST_USER
            context = {
                'username': username,
                'password': password if is_admin else False,
                'portal_url': settings.FRONTEND_URL,
                'municipality': settings.RIS_MUNICIPALITY,
                'link': "%sactiveer-account/%s" % (settings.FRONTEND_URL, activation_key),
                'bcolor': settings.COLOR[settings.RIS_MUNICIPALITY]
            }

            html_content = render_to_response('activation_email.html', context)

            user_obj.activation_key = activation_key
            user_obj.save()

            # _email = EmailMessage(email_subject, html_content, from_email, [email])
            # _email.content_subtype = "html"
            # _email.send()

            mail = MailGun()
            mail.send_mail(email, email_subject, False, html_content)

        return validated_data


class MailGun:
    def __init__(self):
        self.key = settings.MAILGUN_KEY
        self.host = 'https://api.mailgun.net/v3/{}/messages'.format(settings.MAILGUN_ACCOUNT)

    def send_mail(self, recipients, subject, message=False, html=False, attachment=False, bcc=False, form=settings.MAILGUN_MAIL):
        data = {"from": form, "to": recipients, "subject": subject}

        if message and not html:
            data.update({"text": message})
        elif html and not message:
            data.update({"html": html})
        else:
            return False
        if bcc:
            data.update({'bcc': bcc})

        r = requests.post(self.host, auth=("api", self.key), data=data)

        print 'Status: {0}'.format(r.status_code)
        print 'Body:   {0}'.format(r.text)

        return True if r.status_code == 200 else False


class UserProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    @staticmethod
    def get_profile_pic(user):
        return settings.STATIC_URL[1:] + user.profile_pic.url

    @staticmethod
    def get_is_admin(user):
        return user.is_superuser or user.type == 'admin'

    @staticmethod
    def get_type(user):
        if user.is_superuser:
            return 'admin'
        return user.type

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile_pic',
            'email',
            'first_name',
            'last_name',
            'is_admin',
            'type',
            'mobile_number',
            'date_joined'
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Update/ Change user information
    """
    username = serializers.CharField(help_text='150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, label='Username' , required=False, allow_blank=True)
    first_name = serializers.CharField(label='First name', max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(label='Last name', max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False, label='Email Address')
    profile_pic = serializers.FileField(required=False)
    old_password = serializers.CharField(label='old_password', max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(label='new_password', max_length=30, required=False, allow_blank=True)
    mobile_number = serializers.CharField(label='mobile_number', max_length=30,
                                          required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'profile_pic', 'old_password', 'password', 'mobile_number', 'type')
        write_only_fields = ('username', 'email', 'first_name', 'last_name', 'profile_pic')

    def validate(self, data):
        try:
            user = User.objects.get(pk=self.context['request'].data['id'])
            username = user.username
        except KeyError:
            user = User.objects.get(pk=self.context['request'].user.id)
            username = data['username']

        if User.objects.filter(email=data['email']).exclude(pk=user.id).exists():
            raise serializers.ValidationError("Er bestaat al een gebruiker met dat e-mailadres.")
        if User.objects.filter(username=username).exclude(pk=user.id).exists():
            raise serializers.ValidationError("Een gebruiker met die gebruikersnaam bestaat al.")

        try:
            if data['old_password'] is not None and not user.check_password(data['old_password']):
                raise serializers.ValidationError("Oud wachtwoord onjuist")
        except KeyError:
            pass

        return data

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Checks if user input isn't empty and then update the user information
        """
        if len(validated_data.get('email', instance.email)) > 0:
            instance.email = validated_data.get('email', instance.email)
        if len(validated_data.get('mobile_number', instance.mobile_number)) > 0:
            instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        if len(validated_data.get('type', instance.type)) > 0:
            instance.type = validated_data.get('type', instance.type)
        if len(validated_data.get('first_name', instance.first_name)) > 0:
            instance.first_name = validated_data.get('first_name', instance.first_name)
        if len(validated_data.get('last_name', instance.last_name)) > 0:
            instance.last_name = validated_data.get('last_name', instance.last_name)
        if len(validated_data.get('username', instance.username)) > 0:
            instance.username = validated_data.get('username', instance.username)
        if validated_data.get('password') is not None:
            instance.set_password(validated_data.get('password'))
        if len(validated_data.get('profile_pic', instance.profile_pic)) > 0:
            current_prof_pic = User.objects.get(pk=instance.id).profile_pic
            if validated_data.get('profile_pic') is not None:
                instance.profile_pic = validated_data.get('profile_pic', instance.profile_pic)
                if not current_prof_pic.url.endswith('profile_pictures/default_pic.png'):
                    default_storage.delete(current_prof_pic)
        instance.save()
        return instance


class DeleteProfileSerializer(serializers.ModelSerializer):
    """
    Delete user profile
    """
    class Meta:
        model = User
        fields = ('password',)
        write_only_fields = ('password',)

    def validate(self, data):
        password = data["password"]

        if not check_password(password):
            raise serializers.ValidationError("Onjuist wachtwoord, probeer het opnieuw.")

        return data


class PasswordIncorrect(exceptions.APIException):
    status_code = 401
    default_detail = 'Het wachtwoord is onjuist.'


class UsernameNotFound(exceptions.APIException):
    status_code = 401
    default_detail = 'Gebruikersnaam niet gevonden.'


class UserNotActivated(exceptions.APIException):
    status_code = 401
    default_detail = 'Gebruikersaccount is uitgeschakeld.'


class EmailNotFound(exceptions.APIException):
    status_code = 401
    default_detail = 'E-mail niet gevonden.'


class CustomLoginSerializer(LoginSerializer):
    def _validate_email(self, email, password):
        user = None

        if email and password:
            user = authenticate(email=email, password=password)
        else:
            msg = _('Moet "email" en "wachtwoord" bevatten.')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        user = None

        if username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Moet "email" en "wachtwoord" bevatten.')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        user = None

        if email and password:
            user = authenticate(email=email, password=password)
        elif username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Moet ook "gebruikersnaam" of "email" en "wachtwoord" bevatten.')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if username != '':
            if not User.objects.filter(username=username):
                raise UsernameNotFound

        if email != '':
            if not User.objects.filter(email=email):
                raise EmailNotFound

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                raise UserNotActivated
        else:
            raise PasswordIncorrect


        # If required, is the email verified?
        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_('E-mail is niet geverifieerd.'))

        attrs['user'] = user
        return attrs


class GetUserItemCountsSerializer(serializers.Serializer):
    notifications_count = serializers.IntegerField()
    dossiers_count = serializers.IntegerField()
    queries_count = serializers.IntegerField()
    favorites_count = serializers.IntegerField()