from django.db import models
from django.conf import settings

from generics.models import CombinedItem

User = settings.AUTH_USER_MODEL


class Favorite(models.Model):
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_owner')
	item = models.ForeignKey(CombinedItem)
	created_at = models.DateTimeField(auto_now_add=True)