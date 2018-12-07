from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField

User = settings.AUTH_USER_MODEL

ORDERING = (
    ('', 'No ordering'),
    ('ordering=name', 'Name ascending'),
    ('ordering=-name', 'Name descending'),
    ('ordering=date', 'Date ascending'),
    ('ordering=-date', 'Date descending'),
    ('ordering=last_modified', 'Last modified ascending'),
    ('ordering=-last_modified', 'Last modified descending')
)

class Query(models.Model):
    title = models.CharField(max_length=100, default='New Query')
    filters = JSONField(default=list)
    sort_by = models.CharField(choices=ORDERING, max_length=50, default='No ordering')
    page = models.IntegerField(null=True)
    tab = models.CharField(max_length=50, default='list')

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    shared_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='QuerySharedUsers')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='query_owner')

    def __str__(self):
        return self.title

class QuerySharedUsers(models.Model):
    person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='query_shared_user')
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='query_shared_user')