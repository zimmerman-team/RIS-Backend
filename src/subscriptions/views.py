# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render_to_response
from rest_framework import status
from rest_framework.decorators import api_view

from generics.models import CombinedItem, Event
from subscriptions.models import UserNotifications


def email_demo(request):
    return render_to_response("document_notification.html")


@api_view(['POST'])
def get_user_subscriptions(request):
    if request.user:
        if request.user.is_superuser or request.user.type == 'admin' or request.user.type == 'auteur' or request.user.type == 'raadslid':
            user_subscriptions = UserNotifications.objects.filter(user=request.user)
        else:
            user_subscriptions = UserNotifications.objects.filter(user=request.user, item__published=True)
        response = []
        for subscription in user_subscriptions:
            current_item = CombinedItem.objects.get(id=subscription.item.id)

            name = current_item.name
            parent_id = 0
            if current_item.item_type == 'child_event':
                child_event = Event.objects.get(id=current_item.item_id)
                parent_id = child_event.parent_event.id
                name = child_event.classification

            response.append({
                'item_origin_id': current_item.item_id,
                'id': current_item.id,
                'name': name,
                'date_added': subscription.date_added,
                'date': current_item.date,
                'url': current_item.url,
                'last_modified': current_item.last_modified,
                'item_type': current_item.item_type,
                'active': subscription.active,
                'parent_id': parent_id
            })

        return JsonResponse(response, safe=False)

    else:
        HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def subscribe(request):
    if request.user:
        params = json.loads(request.body)

        try:
            UserNotifications.objects.create(user=request.user,
                                             item=CombinedItem.objects.get(id=params.get('item')))
            return HttpResponse(status=status.HTTP_200_OK,
                                content="user:{} subscribed to item:{} successfully".format(request.user,
                                                                                            params.get('item')))
        except CombinedItem.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Invalid item id!")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['DELETE'])
def remove(request):
    if request.user:
        params = json.loads(request.body)

        try:
            UserNotifications.objects.get(user=request.user,
                                          item=CombinedItem.objects.get(id=params.get('item'))).delete()
            return HttpResponse(status=status.HTTP_200_OK,
                                content="Item:{} removed from user:{}".format(params.get('item'), request.user))
        except UserNotifications.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="No subscription found")

        except CombinedItem.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Invalid item id!")

    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")


@api_view(['POST'])
def change(request):
    if request.user:
        params = json.loads(request.body)

        try:
            item = UserNotifications.objects.get(user=request.user,
                                                 item=CombinedItem.objects.get(id=params.get('item')))

            item.active = bool(params.get('enable'))
            item.save()
            return HttpResponse(status=status.HTTP_200_OK,
                                content="user:{} subscribed to item:{} successfully".format(request.user,
                                                                                            params.get('item')))
        except CombinedItem.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND, content="Invalid item id!")
    else:
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED, content="User not logged in")
