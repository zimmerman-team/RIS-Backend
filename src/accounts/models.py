from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    activation_key = models.CharField(max_length=255, default='', null=True, blank=True)
    profile_pic = models.FileField(upload_to='profile_pictures', default='profile_pictures/default_pic.png')
    # types of users
    # 1) 'regular'
    # 2) 'admin'
    # 3) 'auteur'
    # 4) 'raadslid'
    type = models.CharField(max_length=100, default='regular')
    mobile_number = models.CharField(max_length=100, default='')
