#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import requests
from lxml import etree
from generics.models import Speaker
from django.core.exceptions import ObjectDoesNotExist
from dateutil import parser
from django.conf import settings

class NotubizSpeakersDataScraper():
    """
    Scrapes all Notubiz speakers
    """

    def __init__(self):
        self.api_url = "http://api.notubiz.nl/"
        self.organisation = settings.RIS_MUNICIPALITY


    def start(self):
        """
        """
        self.get_speakers()

    def get_speakers(self):
        if self.organisation == 'Rotterdam':
            organisation = 726
        elif self.organisation == 'Almere':
            organisation = 952

        params = {'organisation': organisation}
        response = requests.get(self.api_url + "speakers/", params)
        root = etree.fromstring(response.content)
        speakers = root.find("speakers")

        for speaker in speakers:
            speaker_id = int(speaker.get("id"))
            last_modified = parser.parse(speaker.get('last_modified'))

            try:
                _speaker = Speaker.objects.get(notubiz_id=speaker_id)
                if _speaker.last_modified == last_modified:
                    continue
            except ObjectDoesNotExist:
                pass

            print 'did not skip {}'.format(speaker_id)

            data = self.parse_speaker(speaker)
            self.update_or_create_speaker(data)


    def parse_speaker(self, speaker):
        notubiz_id = int(speaker.get("id"))
        person_id = int(speaker.get("person_id"))
        firstname = speaker.find("firstname").text or ""
        lastname = speaker.find("lastname").text or ""
        sex = speaker.find("sex").text or ""
        function = speaker.find("function").text or ""
        email = speaker.find("email").text or ""
        photo_url = speaker.find("photo").text or ""
        last_modified = parser.parse(speaker.get('last_modified'))

        return {
            "notubiz_id": notubiz_id,
            "person_id": person_id,
            "firstname": firstname,
            "lastname": lastname,
            "sex": sex,
            "function": function,
            "email": email,
            "photo_url": photo_url,
            "last_modified": last_modified
        }


    def update_or_create_speaker(self, parsed_data):
        _speaker, created = Speaker.objects.update_or_create(
            notubiz_id=parsed_data["notubiz_id"],
            defaults={
                'notubiz_id': parsed_data["notubiz_id"],
                'person_id': parsed_data["person_id"],
                'firstname': parsed_data["firstname"],
                'lastname': parsed_data["lastname"],
                'sex': parsed_data["sex"],
                'function': parsed_data["function"],
                'email': parsed_data["email"],
                'photo_url': parsed_data["photo_url"],
                'last_modified': parsed_data["last_modified"]
            }
        )