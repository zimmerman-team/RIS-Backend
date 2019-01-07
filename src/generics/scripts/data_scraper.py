#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import requests
from lxml import etree
from generics.models import Event, Document, EventAgendaItem, EventAgendaMedia, EventAgendaMediaLink, EventMedia, CombinedItem, Speaker, SpeakerIndex
import datetime
from django.core.exceptions import ObjectDoesNotExist
from dateutil import parser
from django.conf import settings


class NotubizDataScraper():
    """
    Scrapes all events and related data.
    Does not get document files nor indexes them,
    there are scripts in the same folder for that.

    """

    def __init__(self):
        self.org_id_name_mapping = {}
        self.api_url = "http://api.notubiz.nl/"
        self.organisation = settings.RIS_MUNICIPALITY


    def start(self):
        """
        """
        self.get_ids_and_update_per_month(start_year=2001)


    def get_ids_and_update_per_month(self, start_year):
        """
        """
        # this is an function to get event_ids from Notubiz XML file
        CURRENT = datetime.datetime.now()
        end_year = CURRENT.year + 1
        end_month = CURRENT.month + 1
        start_month = 1
        organisation = 0

        if self.organisation == 'Rotterdam':
            organisation = 726
        elif self.organisation == 'Almere':
            organisation = 952

        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month - 1

        for ym in range(ym_start, ym_end):
            year, month = divmod(ym, 12)
            new_month = month + 1
            params = {'organisation': organisation, 'year': year, 'month': new_month}
            response = requests.get(self.api_url + "events/", params)
            root = etree.fromstring(response.content)
            events = root.find("events")

            print 'checking year {} month {}'.format(str(year), str(new_month))

            if events != None:
                self.update_events_by_month(events)

        print 'Done'


    def update_events_by_month(self, events):
        """
        check if events need to be added/updated, and if so start the create/update process
        """
        for event in events:
            event_id = int(event.get("id"))
            last_modified = parser.parse(event.get('last_modified'))
            skip = False

            try:
                _event = Event.objects.get(notubiz_id=event_id)
                if _event.last_modified == last_modified:
                    # up to date
                    skip = True
            except ObjectDoesNotExist:
                pass

            if skip is False:
                print 'did not skip {}'.format(event_id)
                shallIBreak = self.parse_event(event_id, None, "event")
                if shallIBreak:
                    continue


    def parse_event(self, event_id, parent, item_type, room_name=None):
        """
        Creates and

        Parameters:
        -

        Returns:
        -
        -
        """
        event_xml = self.fetch_event(event_id)
        if event_xml == None:
            return True
        parsed_data = self.get_event_data(event_xml)
        _event = self.update_or_create_event(parsed_data, parent, item_type, room_name)

        self.parse_documents(event_xml, _event, parent)
        self.get_event_media(event_xml, _event)
        self.parse_agenda_items(event_xml, _event)

        # Done
        self.parse_child_events(event_xml, _event, parsed_data["child_event_count"])
        return False


    def parse_child_events(self, event_xml, parent_event, child_event_count):
        """
        Some events have "child" Events, so Get them and import them in the DB
        """

        # for each child event call create event again with item_type = child_event
        if child_event_count == 0:
            return

        rooms = event_xml.find("rooms")
        if rooms is None:
            return

        for room in rooms:
            events = room.find("events")
            if events is None:
                continue
            for event in events:

                event_id = int(event.get("id"))
                last_modified = parser.parse("{} {}".format(event.get('last_modified'), "CET"))

                skip = False

                try:
                    _event = Event.objects.get(notubiz_id=event_id)
                    if _event.last_modified == last_modified:
                        # up to date
                        skip = True
                except ObjectDoesNotExist:
                    pass

                if skip is False:
                    print 'did not skip {}'.format(event_id)
                    self.parse_event(event_id, parent_event, "child_event", room.find("name").text)


    def fetch_event(self, event_id):
        """
        This function sends a get request to the notubiz API to
        """

        url = self.api_url + "events/" + str(event_id)
        try:
            response = requests.get(url)

            if int(response.headers['content-length']) == 0:
                # no detail page, use the data from the list call
                event = obj.get('event')

            if int(response.headers['content-length']) > 0:
                root = etree.fromstring(response.content)
                event = root.find("event")

            return event
        except Exception as e:
            print e
            return None


    def get_event_data(self, event):
        """
        This function takes the fetched event and reformats it to all the data we need from it

        // TODO
        store description
        store category as FK

        """
        event_id = int(event.get("id"))
        child_event_count = int(event.get("child_event_count", 0))

        title = event.find("title").text or "n/a"
        description = event.find("description").text or "n/a"
        classification = event.find("category/title").text or "n/a"

        location = event.find("location").text or "n/a"
        organisation_id = event.find("organisation").text or "n/a"
        jurisdiction = self.get_organisation_name(organisation_id)

        content = ' '.join([title, classification, description])

        timezone = "CET"

        updated_at_str = event.get("last_modified", "1970-01-01 00:00")
        updated_at = parser.parse("{} {}".format(updated_at_str, timezone))

        date = event.get("date", "1970-01-01")
        time = event.get("time", "00:00")
        datetime_str = "{} {} {}".format(date, time, timezone)
        event_datetime = parser.parse(datetime_str)

        return {
            "notubiz_id": event_id,
            "child_event_count": child_event_count,
            "updated_at": updated_at,
            "title": title,
            "description": description,
            "classification": classification,
            "location": location,
            "organisation_id": organisation_id,
            "jurisdiction": jurisdiction,
            "content": content,
            "event_datetime": event_datetime
        }


    def update_or_create_event(self, parsed_data, parent=None, item_type='event', room_name=None):
        """
        create the actual models and save them. Then return them
        """

        if room_name != None:
            event_name = room_name.strip()
        else:
            event_name = parsed_data["title"].strip()

        _event, created = Event.objects.update_or_create(
            notubiz_id=parsed_data["notubiz_id"],
            defaults={
                'name': event_name,
                'jurisdiction': parsed_data["jurisdiction"],
                'description': parsed_data["description"],
                'classification': parsed_data["classification"],
                'start_time': parsed_data["event_datetime"],
                'location': parsed_data["location"],
                'parent_event': parent,
                'all_day': False,
                'last_modified': parsed_data["updated_at"]
            }
        )

        _combined_item, created = CombinedItem.objects.update_or_create(
            notubiz_id=_event.notubiz_id,
            item_type=item_type,
            defaults= {
                'item_id': _event.id,
                'name': _event.name.strip(),
                'date': _event.start_time,
                'classification': _event.classification,
                'last_modified': _event.last_modified
            }
        )

        return _event


    def get_organisation_name(self, org_id):
        """
        Get organisation/municipality name given the ID

        It caches the org id's it already got from Notubiz
        """
        if self.org_id_name_mapping.has_key(org_id):
            return self.org_id_name_mapping[org_id]

        url = "https://api.notubiz.nl/organisations/" + org_id
        try:
            response = requests.get(url)
            if int(response.headers['content-length']) > 0:
                root = etree.fromstring(response.content)
                # organisation = root.find("organisation")
                name_value = root.find("organisation/name").text
                self.org_id_name_mapping[org_id] = name_value

                return name_value
            else:
                return "N/A"
        except Exception as e:
            print e
            return "N/A"


    def get_event_media(self, event_xml, _event):
        """
        TODO - this def assumes there's a maximum of 1 video attached.
        Also needs to check for audio, multiples, etc.
        """
        root = event_xml.find("media")
        if root is None:
            return

        video = root.find("video")
        if video is None:
            return

        filename = video.find("filename").text

        if video.find("httpstreamer") is not None and video.find("httpstreamname") is not None:
            httpstream = video.find("httpstreamer").text + "/" + video.find("httpstreamname").text
            httpstream = httpstream.replace(" ", "%20")
        else:
            httpstream = None


        if video.find("streamer") is not None and video.find("streamname") is not None:
            rtmpstream = video.find("streamer").text + "/" + video.find("streamname").text
            rtmpstream = rtmpstream.replace(" ", "%20")
        else:
            rtmpstream = None

        download = video.find("download").text[2:]

        try:
            event_media, created = EventMedia.objects.update_or_create(
                filename = filename.strip(),
                event = _event,
                defaults={
                    'httpstream': httpstream,
                    'rtmpstream': rtmpstream,
                    'download': download,
                }
            )
        except Exception:
            event_media = EventMedia.objects.filter(filename=filename.strip(), event=_event).first()
            event_media.httpstream = httpstream
            event_media.rtmpstream = rtmpstream
            event_media.download = download
            event_media.save()


    def parse_agenda_items(self, event_xml, _event):
        """
        Get Agenda Items and import in the DB
        """

        agenda = event_xml.find("agenda")
        if agenda is None:
            return

        for agenda_item in agenda:

            item_name = agenda_item.find("title").text
            item_description = agenda_item.find("description").text
            # item_url = agenda_item.find("url").text
            item_order = agenda_item.get("order", None)
            item_start_time = agenda_item.get("start_time", None)
            item_end_time = agenda_item.get("end_time", None)

            if item_start_time == "":
                item_start_time = None

            if item_end_time == "":
                item_end_time = None

            try:
                _agenda_item, created = EventAgendaItem.objects.update_or_create(
                    notes=item_name.strip(),
                    start_time=item_start_time,
                    event=_event,
                    defaults= {
                        'description': item_description,
                        'order': item_order if item_order != '' else 0,
                        'end_time': item_end_time,
                    }
                )
            except:
                _agenda_item = EventAgendaItem.objects.filter(notes=item_name.strip(), start_time=item_start_time, event=_event).first()
                _agenda_item.description = item_description
                _agenda_item.order = item_order if item_order != '' else 0
                _agenda_item.end_time = item_end_time
                _agenda_item.save()

            self.parse_agenda_docs(agenda_item, _agenda_item, _event)
            self.parse_agenda_speakers(agenda_item, _agenda_item)


    def parse_agenda_speakers(self, agenda_item_xml, agenda_item):
        """
        """
        speaker_indexation = agenda_item_xml.find("speaker_indexation")

        if speaker_indexation is None:
            return

        for si in speaker_indexation:
            speaker_id = si.get("speaker_id")
            start_time = int(si.get("start_time"))

            try:
                speaker = Speaker.objects.get(notubiz_id=speaker_id)
            except ObjectDoesNotExist:
                continue

            if not SpeakerIndex.objects.filter(speaker=speaker, start_time=start_time, agenda_item=agenda_item).exists():
                _speaker_index = SpeakerIndex.objects.create(
                    speaker=speaker,
                    start_time=start_time,
                    agenda_item=agenda_item
                )


    def parse_agenda_docs(self, agenda_item_xml, _agenda_item, _event):
        """
        Get Agenda Item docs and import in the DB (Document, EventAgendaMedia, EventAgendaMediaLink)
        """
        documents = agenda_item_xml.find("documents")
        if documents is None:
            return

        for document_xml in documents:

            parsed_data = self.get_document_data(document_xml)

            try:
                # extra's for agenda docs
                _agenda_media_item, created = EventAgendaMedia.objects.update_or_create(
                    note=parsed_data["doc_title"],
                    agenda_item=_agenda_item,
                    defaults= {
                        'date': _event.start_time # TODO - not sure why, but setting this to the event start time!
                    }
                )
                _agenda_media_item.save()
            except:
                _agenda_media_item = EventAgendaMedia.objects.filter(note=parsed_data["doc_title"], agenda_item=_agenda_item).first()
                _agenda_media_item.date = _event.start_time
                _agenda_media_item.save()


            _agenda_media_link_item, created = EventAgendaMediaLink.objects.update_or_create(
                text=parsed_data["doc_title"],
                media=_agenda_media_item,
                defaults= {
                    'url': parsed_data["doc_url"],
                    'media_type': parsed_data["doc_type"],
                }
            )

            _agenda_media_link_item.save()
            # end of extra's

            _document = self.update_or_create_document(parsed_data, _event, _agenda_item)


    def get_document_data(self, document):
        """
        This function takes the fetched document and reformats it to all the data we need from it
        """
        last_modified = document.get('last_modified').strip(' \t\n\r')
        if last_modified == "":
            last_modified = "1970-01-01T00:00:00"

        last_modified = parser.parse("{} {}".format(last_modified, "CET"))

        doc_type_xml = document.find("types/type/name")
        if doc_type_xml:
            doc_type = doc_type_xml.text
        else:
            doc_type = ""

        return {
            "notubiz_id": document.get('id'),
            "last_modified": last_modified,
            "doc_title": document.find("title").text,
            "doc_url": document.find("url").text,
            "doc_type": doc_type,
            "content": ''
        }


    def update_or_create_document(self, parsed_data, _event, parent):
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
            notubiz_id=parsed_data["notubiz_id"],
            defaults= {
                'last_modified': parsed_data["last_modified"],
                'text': parsed_data["doc_title"].strip(),
                'url': parsed_data["doc_url"],
                'media_type': parsed_data["doc_type"],
                'date': parsed_data["last_modified"],
                'attached_to': attached_to,
                'event': _event,
            }
        )

        _combined_item, created = CombinedItem.objects.update_or_create(
            notubiz_id=_document.notubiz_id,
            item_type= 'document',
            defaults= {
                'item_id': _document.id,
                'notubiz_id': _document.notubiz_id,
                'name': _document.text.strip(),
                'date': _document.date,
                'url': _document.url,
                'classification': _document.media_type,
                'last_modified': _document.last_modified,
            }
        )
        _combined_item.save()
        return _document


    def parse_documents(self, event_xml, event, parent):
        """
        Get Event Documents and import them in the DB
        """
        documents = event_xml.find("documents")

        if documents is None:
            return

        for document_xml in documents:
            parsed_data = self.get_document_data(document_xml)
            _document = self.update_or_create_document(parsed_data, event, parent)

