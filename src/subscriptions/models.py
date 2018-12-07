# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from accounts.models import User
from generics.models import CombinedItem

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.shortcuts import render_to_response

from accounts.serializers import MailGun
from generics.serializers import getItemURL, getItemType


class UserNotifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=0)
    item = models.ForeignKey(CombinedItem, on_delete=models.CASCADE, null=True)
    active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)


class PreferredNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=0)
    is_email = models.BooleanField(default=False)
    is_push = models.BooleanField(default=False)


@receiver(post_save, sender=CombinedItem)
def send_email_notification(sender, **kwargs):
    item = kwargs.get('instance', None)
    notifications = UserNotifications.objects.filter(item=item.id, active=True)
    for n in notifications:
        if n.item.published == False and not n.user.is_superuser and not n.user.type == 'admin' and not n.user.type == 'auteur' or n.user.type == 'raadslid':
            continue
        if n.date_added < item.last_modified:
            n.save()

            url = settings.FRONTEND_URL + getItemURL(str(item.item_id), item.item_type)

            context = {
                'url': url,
                'item': item,
                'type': getItemType(item.item_type),
                'type_upper': getItemType(item.item_type).upper(),
                'username': n.user.username,
                'municipality': settings.RIS_MUNICIPALITY,
                'portal_url': settings.FRONTEND_URL,
                'bcolor': settings.COLOR[settings.RIS_MUNICIPALITY]
            }

            if item.item_type == "event" or item.item_type == "child_event":
                html_content = render_to_response('event_notification.html', context)
            else:
                html_content = render_to_response('document_notification.html', context)

            email_subject = "RI Studio %s: Notificatie" % (settings.RIS_MUNICIPALITY)

            mail = MailGun()
            mail.send_mail(n.user.email, email_subject, False, html_content)