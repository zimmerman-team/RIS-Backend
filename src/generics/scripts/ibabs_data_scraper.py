#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import zeep
from datetime import datetime as dt
from generics.models import Event, Document, EventAgendaItem, EventAgendaMediaLink, CombinedItem
import datetime
from django.core.exceptions import ObjectDoesNotExist
from dateutil import parser
from django.conf import settings
import re

utrecht_modules = [
    {'code': '0', 'name': 'Raadsinformatiebijeenkomst'},
    {'code': '2', 'name': 'Gemeenteraad'},
    {'code': '4', 'name': 'Commissie Stad en Ruimte'},
    {'code': '5', 'name': 'Commissie Mens en Samenleving'},
    {'code': '6', 'name': 'Subcommissie Controle en Financien'},
    {'code': '15', 'name': 'Raadsvoorstellen weekoverzicht'},
    {'code': '17', 'name': 'Vragenuur'},
    {'code': '18', 'name': 'Raadsactiviteiten'},
    {'code': '19', 'name': 'Gast van de raad'}
]
zoetermeer_modules = [
    {'code': '100000003', 'name': 'Raadsvergadering'},
    {'code': '100000056', 'name': 'Commissie Samenleving en commissie Stad PLENAIR'},
    {'code': '100000057', 'name': 'Commissie Samenleving'},
    {'code': '100000058', 'name': 'Commissie Stad'}
]


class iBabsDataScraper():

    def __init__(self):
        self.wsdl = 'https://www.mijnbabs.nl/iBabsWCFService/Public.svc?wsdl'
        self.site = 'Utrecht'
        if self.site == settings.RIS_MUNICIPALITY:
            self.meetingIds = utrecht_modules
        else:
            self.meetingIds = zoetermeer_modules

    def start(self):
        """
        """
        self.get_meetings_by_meetingtype()

    def get_meetings_by_meetingtype(self):
        """
        """
        client = zeep.Client(wsdl=self.wsdl)

        for i in self.meetingIds:  # these are the meeting type IDs
            self.currMeetingType = i['name']
            response = client.service.GetMeetingsByMeetingtype(self.site, i['code'])
            meetings = response['Meetings']['iBabsMeeting']

            self.update_events_by_meetingtype(meetings, response)

    def update_events_by_meetingtype(self, events, response):
        """
        check if events need to be added/updated, and if so start the create/update process
        """
        for event in events:
            event_id = event['Id']
            # last_modified = parser.parse(event['PublishDate'])
            # How the fuk is this last_modified?
            last_modified = event['PublishDate']
            skip = False
            print(event_id)

            try:
                _event = Event.objects.get(ibabs_id=event_id)
                if _event.last_modified == last_modified:
                    # up to date
                    skip = True
            except ObjectDoesNotExist:
                pass

            if skip is False:
                print 'did not skip {}'.format(event_id)
                self.parse_event(event_id, None, "event", event)

    def parse_event(self, event_id, parent, item_type, event_content, order=-1):
        if event_content is None:
            return
        parsed_data = self.get_event_data(event_content, parent)
        res = self.update_or_create_event(parsed_data, order, parent, item_type)

        if item_type == 'event':
            _event = res
            agenda_item = None
        else:
            _event = parent
            agenda_item = res

        self.parse_documents(event_content, _event, parent, agenda_item)
        self.parse_child_events(event_content, parent, _event)

    # TODO parse_child_events and add parent in get_event_data (if parent != None then location, child_event_count updated_at are special case)
    # At the end, parse child should call parse_event for each child
    # But why? I dont think agenda items have other agenda items in them...
    def parse_child_events(self, event, parent, _event):
        if parent != None:
            return
        if event['MeetingItems']:
            child_events = event['MeetingItems']['iBabsMeetingItem']
            for index, child_event in enumerate(child_events):
                event_id = child_event['Id']
                self.parse_event(event_id, _event, "child_event", child_event, order=index)

    def get_event_data(self, event, parent):
        """
        This function takes the fetched event and reformats it to all the data we need from it
        """
        event_id = event['Id']
        timezone = "CET"
        if parent == None:
            if event['MeetingItems']:
                child_event_count = len(event['MeetingItems']['iBabsMeetingItem'])
            else:
                child_event_count = 0
            title = self.get_meeting_title_by_meeting_id(event['MeetingtypeId'])
            location = event['Location'] or "n/a"
            updated_at_str = event['PublishDate']
            date = event['MeetingDate'] or dt.datetime(1970, 1, 1, 0, 0)
            datetime_str = "{} {}".format(date, timezone)
            event_datetime = parser.parse(datetime_str)
            event_enddatetime = None
            try:
                end_time = event['EndTime']
                if end_time is not None and re.search(r'\d', end_time):
                    hours = int(end_time[:end_time.index(':')])
                    minutes = int(end_time[end_time.index(':') + 1:])
                    event_enddatetime = event_datetime.replace(hour=hours, minute=minutes)
                    end_time = datetime.datetime.strptime(end_time, '%H:%M').time()
            except Exception:
                end_time = None
            try:
                if event['StartTime'] is not None and re.search(r'\d', event['StartTime']):
                    start_time = datetime.datetime.strptime(event['StartTime'], '%H:%M').time()
                else:
                    start_time = None
            except Exception:
                start_time = None
        else:
            child_event_count = 0
            title = event['Title']
            location = parent.location or "n/a"
            updated_at_str = parent.last_modified
            times = self.extract_times(event['Explanation'])
            end_time = times[1]
            start_time = times[0]
            event_datetime = parent.start_time
            event_enddatetime = parent.end_time

        description = event['Explanation'] or "n/a"
        classification = self.currMeetingType

        organisation_id = "n/a"
        jurisdiction = self.site

        content = ' '.join([title, classification, description])

        updated_at = parser.parse("{} {}".format(updated_at_str, timezone))

        return {
            "ibabs_id": event_id,
            "child_event_count": child_event_count,
            "updated_at": updated_at,
            "title": title,
            "description": description,
            "classification": classification,
            "location": location,
            "organisation_id": organisation_id,
            "jurisdiction": jurisdiction,
            "content": content,
            # As DateTimeFields
            "event_datetime": event_datetime,
            "event_enddatetime": event_enddatetime,
            # As TimeFields
            "start_time": start_time,
            "end_time": end_time

        }

    def extract_times(self, expl):
        start_time = None
        end_time = None
        if expl is not None:
            try:
                hour_index = expl.index("Tijd en locatie:\r\n") + 20
                minute_index = expl.index(".", hour_index) + 3
                start_time = datetime.datetime.strptime(expl[hour_index:minute_index], '%H.%M').time()
                hour_index = expl.rfind("uur:", minute_index) - 18
                minute_index = expl.index(".", hour_index) + 3
                end_time = datetime.datetime.strptime(expl[hour_index:minute_index], '%H.%M').time()
            except ValueError:
                try:
                    hour_index = expl.index("Tijd: ") + 6
                    minute_index = expl.index(".", hour_index) + 3
                    start_time = datetime.datetime.strptime(expl[hour_index:minute_index], '%H.%M').time()
                    hour_index = expl.index("- ", minute_index) + 2
                    minute_index = expl.index(".", hour_index) + 3
                    end_time = datetime.datetime.strptime(expl[hour_index:minute_index], '%H.%M').time()
                except ValueError:
                    try:
                        hour = re.search("\d", expl)
                        hour_index = hour.start()
                        minute_index = expl.index(".", hour_index) + 3
                        start_time = datetime.datetime.strptime(expl[hour_index:minute_index], '%H.%M').time()
                        new_expl = expl[minute_index:]
                        hour = re.search("\d", new_expl)
                        hour_index = hour.start()
                        minute_index = new_expl.index(".", hour_index) + 3
                        end_time = datetime.datetime.strptime(new_expl[hour_index:minute_index], '%H.%M').time()
                    except:
                        pass
                except:
                    pass
            except:
                pass
        return start_time, end_time

    def update_or_create_event(self, parsed_data, order, parent=None, item_type='event'):
        """
        create the actual models and save them. Then return them
        """
        if item_type == 'event':
            _event, created = Event.objects.update_or_create(
                ibabs_id=parsed_data["ibabs_id"],
                defaults={
                    'name': parsed_data["title"].strip(),
                    'jurisdiction': parsed_data["jurisdiction"],
                    'description': parsed_data["description"],
                    'classification': parsed_data["classification"],
                    'start_time': parsed_data["event_datetime"],
                    'end_time': parsed_data["event_enddatetime"],
                    'location': parsed_data["location"],
                    'parent_event': parent,
                    'all_day': False,
                    'last_modified': parsed_data["updated_at"]
                }
            )
            _combined_item, created = CombinedItem.objects.update_or_create(
                ibabs_id=_event.ibabs_id,
                item_type=item_type,
                defaults={
                    'item_id': _event.id,
                    'name': _event.name.strip(),
                    'date': _event.start_time,
                    'classification': _event.classification,
                    'last_modified': _event.last_modified
                }
            )
            return _event
        else:
            agenda_item = None
            if order == -1:
                raise Exception('Pls fix code, order cannot be -1')
            agenda_item, created = EventAgendaItem.objects.update_or_create(
                event=parent,
                notes=parsed_data["title"].strip(),
                defaults= {
                    'description': parsed_data["description"],
                    'order': order,
                    'start_time': parsed_data["start_time"],
                    'end_time': parsed_data["end_time"],
                }
            )
            return agenda_item

    def get_document_data(self, document, _event):
        """
        This function takes the fetched document and reformats it to all the data we need from it
        """
        return {
            "ibabs_id": document['Id'],
            "last_modified": _event.last_modified,
            "doc_title": document['DisplayName'].strip(),
            "doc_url": document['PublicDownloadURL'],
            "doc_type": "",
            "content": "n/a"
        }

    def parse_documents(self, event_content, _event, parent, _agenda_item):
        """
        Get Event Documents and import them in the DB
        check if parent is None (2 ways of getting all documents from event_content)
        """
        publish_date = None
        try:
            if event_content['PublishDate'] is not None:
                publish_date = event_content['PublishDate']
        except KeyError:
            pass

        documents = event_content["Documents"] and event_content["Documents"][
            "iBabsDocument"]  # documents in the json response

        if documents is None:
            return

        for document in documents:
            parsed_data = self.get_document_data(document, _event)
            _document = self.update_or_create_document(parsed_data, _event, parent, _agenda_item, pub_date=publish_date)

    def update_or_create_document(self, parsed_data, _event, parent, _agenda_item, pub_date=None):
        """
        create the actual models and save them. Then return them
        """

        attached_to = 'event'
        if parent is not None:
            if parent.__class__.__name__ == 'Event':
                attached_to = 'child_event'
            if parent.__class__.__name__ == 'EventAgendaItem':
                attached_to = 'agenda_item'

        _document, created = Document.objects.update_or_create(
            ibabs_id=parsed_data["ibabs_id"],
            defaults={
                'last_modified': parsed_data["last_modified"],
                'text': parsed_data["doc_title"].strip(),
                'url': parsed_data["doc_url"],
                'media_type': parsed_data["doc_type"],
                'date': pub_date if pub_date is not None else parsed_data["last_modified"],
                'attached_to': attached_to,
                'event': _event
            }
        )

        if _agenda_item:
            _agenda_item_media, created = EventAgendaMedia.objects.update_or_create(
                note=parsed_data["doc_title"].strip(),
                agenda_item=_agenda_item,
                defaults= {
                    'date': pub_date if pub_date is not None else parsed_data["last_modified"],
                }
            )
            _agenda_media_link_item, created = EventAgendaMediaLink.objects.update_or_create(
                text=parsed_data["doc_title"].strip(),
                media=_agenda_item_media,
                defaults= {
                    'url': parsed_data["doc_url"],
                    'media_type': parsed_data["doc_type"],
                }
            )

        _combined_item, created = CombinedItem.objects.update_or_create(
            ibabs_id=_document.ibabs_id,
            item_type='document',
            defaults={
                'item_id': _document.id,
                'ibabs_id': _document.ibabs_id,
                'name': _document.text.strip(),
                'date': _document.date,
                'url': _document.url,
                'classification': self.currMeetingType,
                'last_modified': _document.last_modified
            }
        )
        _combined_item.save()
        return _document

    def get_meeting_title_by_meeting_id(self, meeting_id):
        return {
            '2': 'Gemeenteraad',
            '5': 'Commissie Mens en Samenleving',
            '4': 'Commissie Stad en Ruimte',
            '6': 'Subcommissie Controle en Financien',
            '0': 'Raadsinformatiebijeenkomst',
            '17': 'Vragenuur',
            '18': 'Raadsactiviteiten',
            '19': 'Gast van de raad',
            '15': 'Raadsvoorstellen weekoverzicht',
            '100081947': 'Aangeleverde raadsvoorstellen',
            '100000057': 'Commissie Samenleving',
            '100000058': 'Commissie Stad',
            '100000056': 'Commissie Samenleving en commissie Stad PLENAIR',
            '100000003': 'Raadsvergadering'
        }[meeting_id]