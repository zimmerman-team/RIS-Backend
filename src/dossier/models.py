from django.db import models
from django.conf import settings

from generics.models import CombinedItem, Note

import uuid

User = settings.AUTH_USER_MODEL

COLOUR_CHOICES = (
    ('Blue', 'blue'),
    ('Green', 'green'),
    ('Yellow', 'yellow'),
    ('Red', 'red'),
    ('Orange', 'orange'),
    ('Purple', 'purple'),
    ('White', 'white')
)
ACCESSIBILITY_CHOICE = (
    ('Public', 'public'),
    ('Private', 'private')
)
PERMISSION_CHOICE = (
    ('View', 'view'),
    ('Edit', 'edit')
)


class Dossier(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dossier_owner')
    shared_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='DossierSharedUsers')
    title = models.CharField(max_length=100)
    accessibility = models.CharField(choices=ACCESSIBILITY_CHOICE, max_length=7, default='private')
    is_verified = models.BooleanField(default=False)
    color = models.CharField(max_length=7, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_favorite = models.BooleanField(default=False)
    ordering_id = models.IntegerField(unique=True, null=True)

    def __str__(self):
        return self.title


class DossierInvitation(models.Model):
    dossier = models.ForeignKey(Dossier, related_name='dossier_invitations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dossier_invitations')
    email = models.EmailField(max_length=254)
    permission = models.CharField(choices=PERMISSION_CHOICE, max_length=50, default='view')
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_confirmed = models.BooleanField(default=False)


class Content(models.Model):
    items = models.ManyToManyField(CombinedItem, blank=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='added_by')
    dossier = models.ForeignKey(Dossier, related_name='content')


class ContentNote(models.Model):
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_note_added_by')
    note = models.ForeignKey(Note, related_name='content_note')
    dossier = models.ForeignKey(Dossier, related_name='content_note_dossier')


class DossierSharedUsers(models.Model):
    person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_user')
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='dossier_shared_user')
    permission = models.CharField(choices=PERMISSION_CHOICE, max_length=50, default='view')


class File(models.Model):
    file = models.FileField(upload_to='user_files')
    name = models.TextField(null=True)
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

