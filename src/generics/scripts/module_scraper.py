# -*- coding: utf-8 -*-
import requests
from lxml import etree
from dateutil import parser
from django.core.exceptions import ValidationError

from generics.models import Event
from generics.models import Document
from generics.models import ReceivedDocument
from generics.models import CouncilAddress
from generics.models import Commitment
from generics.models import WrittenQuestion
from generics.models import Organisation
from generics.models import CombinedItem
from generics.models import Motion
from generics.models import PublicDocument
from generics.models import ManagementDocument
from generics.models import PolicyDocument
from generics.models import Party
from generics.models import Person

from django.conf import settings


module_meta = {
    "1": {
        "model": ReceivedDocument,
        "attribute_mapping": {
            "2": {"field": "document", "datatype": "document"},
            "1": {"field": "subject", "datatype": "varchar"},
            "3": {"field": "description", "datatype": "text"},
            "7": {"field": "publication_date", "datatype": "datetime"},
            "15": {"field": "date", "datatype": "datetime"},
            "47": {"field": "date_created", "datatype": "datetime"},
            "34": {"field": "advice", "datatype": "varchar"},
            "33": {"field": "sender", "datatype": "varchar"},
            "50": {"field": "location", "datatype": "varchar"},
            "45": {"field": "document_type", "datatype": "varchar"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "46": {"field": "category", "datatype": "varchar"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "5":  {"field": "number", "datatype": "varchar"},
            "54": {"field": "linked_event", "datatype": "event"},
            "53": {"field": "heading", "datatype": "varchar"},
            "51": {"field": "comission", "datatype": "integer"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "86": {"field": "RIS_number", "datatype": "integer"},
        },
        "combined_item_mapping": {
            "item_type": "received_document",
            "name": "subject",
            "date": "date_created",
            "classification": "document_type",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "2": {
        "model": CouncilAddress,
        "attribute_mapping": {
            "1":  {"field": "title", "datatype": "varchar"},
            "47": {"field": "publication_date", "datatype": "datetime"},
            "15": {"field": "question_date", "datatype": "datetime"},
            "2":  {"field": "question_document", "datatype": "document"},
            "17": {"field": "answer_date", "datatype": "datetime"},
            "21": {"field": "answer_document", "datatype": "document"},
            "18": {"field": "handled_by", "datatype": "varchar"},
            "50": {"field": "location", "datatype": "varchar"},
            "45": {"field": "address_type", "datatype": "varchar"},
            "16": {"field": "interim_answer_date", "datatype": "datetime"},
            "20": {"field": "interim_answer_document", "datatype": "document"},
            "54": {"field": "linked_event", "datatype": "event"},
            "9":  {"field": "name", "datatype": "varchar"},
            "11": {"field": "address", "datatype": "varchar"},
            "10": {"field": "email", "datatype": "varchar"},
            "14": {"field": "telephone", "datatype": "varchar"},
            "13": {"field": "place", "datatype": "varchar"},
            "12": {"field": "postal_code", "datatype": "varchar"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "86": {"field": "RIS_number", "datatype": "integer"},

        },
        "combined_item_mapping": {
            "item_type": "council_address",
            "name": "title",
            "date": "question_date",
            "classification": "TODO",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "3": {
        "model": Commitment,
        "attribute_mapping": {
            "1": {"field": "title", "datatype": "varchar"},
            "23": {"field": "portfolio_holder", "datatype": "varchar"}, # TODO - change to datatype person
            "48": {"field": "recipient", "datatype": "varchar"},
            "22": {"field": "agenda_item", "datatype": "varchar"},
            "15": {"field": "commitment_date", "datatype": "datetime"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "25": {"field": "text", "datatype": "text"},
            "26": {"field": "involved_comittee", "datatype": "varchar"},
            "28": {"field": "expected_settlement_date", "datatype": "datetime"},
            "35": {"field": "situation", "datatype": "text"},
            "17": {"field": "date_finished", "datatype": "datetime"},
            "21": {"field": "new_document", "datatype": "document"},
            "31": {"field": "dispensation", "datatype": "text"},
            "47": {"field": "item_created", "datatype": "datetime"}
        },
        "combined_item_mapping": {
            "item_type": "commitment",
            "name": "title",
            "date": "commitment_date",
            "classification": "TODO",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "4": {
        "model": WrittenQuestion,
        "attribute_mapping": {
            "1": {"field": "title", "datatype": "varchar"},
            "47": {"field": "publication_date", "datatype": "datetime"},
            "35": {"field": "explanation", "datatype": "text"},
            "37": {"field": "parties", "datatype": "party"},
            "15": {"field": "question_date", "datatype": "datetime"},
            "2":  {"field": "question_document", "datatype": "document"},
            "16": {"field": "interim_answer_date", "datatype": "datetime"},
            "20": {"field": "interim_answer_document", "datatype": "document"},
            "41": {"field": "interim_answer_explanation", "datatype": "text"},
            "17": {"field": "answer_date", "datatype": "datetime"},
            "21": {"field": "answer_document", "datatype": "document"},
            "49": {"field": "answer_explanation", "datatype": "text"},
            "36": {"field": "initiator", "datatype": "person"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "50": {"field": "location", "datatype": "varchar"},
            "26": {"field": "involved_comittee", "datatype": "varchar"},
            "28": {"field": "expected_answer_date", "datatype": "datetime"},
            "23": {"field": "portfolio_holder", "datatype": "varchar"}, # TODO - change to datatype person
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "40": {"field": "progress_state", "datatype": "text"},
            "39": {"field": "evaluation_date", "datatype": "datetime"},
            "54": {"field": "linked_event", "datatype": "event"},
            "38": {"field": "vote_outcome", "datatype": "varchar"},
            "5":  {"field": "number", "datatype": "varchar"},
            "45": {"field": "unknown_type", "datatype": "varchar"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "51": {"field": "meeting_category", "datatype": "integer"},
            "86": {"field": "RIS_number", "datatype": "integer"},
            "87": {"field": "co_signatories", "datatype": "integer"},
        },
        "combined_item_mapping": {
            "item_type": "written_question",
            "name": "title",
            "date": "question_date",
            "classification": "TODO",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "6": {
        "model": Motion,
        "attribute_mapping": {
            "1":  {"field": "title", "datatype": "varchar"},
            "22": {"field": "agenda_item", "datatype": "varchar"},
            "45": {"field": "document_type", "datatype": "varchar"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "2":  {"field": "document", "datatype": "document"},
            "21": {"field": "new_document_settlement", "datatype": "document"},
            "37": {"field": "parties", "datatype": "party"},
            "23": {"field": "portfolio_holder", "datatype": "varchar"}, # TODO - change to datatype person
            "26": {"field": "involved_comittee", "datatype": "varchar"},
            "28": {"field": "expected_settlement_date", "datatype": "datetime"},
            "62": {"field": "outcome", "datatype": "varchar"},
            "15": {"field": "meeting_date", "datatype": "datetime"},
            "17": {"field": "date_finished", "datatype": "datetime"},
            "47": {"field": "date_created", "datatype": "datetime"},
            "49": {"field": "dispensation", "datatype": "text"},
            "35": {"field": "explanation", "datatype": "text"},
            "36": {"field": "council_member", "datatype": "varchar"},
            "61": {"field": "comments", "datatype": "text"},
            "40": {"field": "situation", "datatype": "text"}
        },
        "combined_item_mapping": {
            "item_type": "motion",
            "name": "title",
            "date": "meeting_date",
            "classification": "TODO",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "7": {
        "model": PublicDocument,
        "attribute_mapping": {
            "1":  {"field": "title", "datatype": "varchar"},
            "44": {"field": "document_date", "datatype": "datetime"},
            "7":  {"field": "publication_date", "datatype": "datetime"},
            "47": {"field": "date_created", "datatype": "datetime"},
            "2":  {"field": "document", "datatype": "document"},
            "45": {"field": "document_type", "datatype": "varchar"},
            "5":  {"field": "number", "datatype": "varchar"},
            "51": {"field": "meeting_category", "datatype": "integer"},
            "23": {"field": "portfolio_holder", "datatype": "integer"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "18": {"field": "settlement", "datatype": "varchar"},
            "54": {"field": "linked_event", "datatype": "event"},
            "46": {"field": "category", "datatype": "varchar"},
            "50": {"field": "location", "datatype": "varchar"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "86": {"field": "RIS_number", "datatype": "integer"},
        },
        "combined_item_mapping": {
            "item_type": "format",
            "name": "title",
            "date": "date_created",
            "classification": "document_type",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "8": {
        "model": ManagementDocument,
        "attribute_mapping": {
            "1":  {"field": "title", "datatype": "varchar"},
            "2":  {"field": "document", "datatype": "document"},
            "5":  {"field": "number", "datatype": "varchar"},
            "7":  {"field": "publication_date", "datatype": "datetime"},
            "44": {"field": "document_date", "datatype": "datetime"},
            "45": {"field": "document_type", "datatype": "varchar"},
            "50": {"field": "district", "datatype": "varchar"},
            "47": {"field": "date_created", "datatype": "datetime"},
            "23": {"field": "portfolio_holder", "datatype": "integer"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "51": {"field": "meeting_category", "datatype": "integer"},
            "18": {"field": "settlement", "datatype": "varchar"},
            "54": {"field": "linked_event", "datatype": "event"},
            "46": {"field": "category", "datatype": "varchar"},
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "56": {"field": "operational_from", "datatype": "datetime"},
            "17": {"field": "settlement_date", "datatype": "datetime"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "57": {"field": "valid_until", "datatype": "datetime"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "70": {"field": "operational_from_2", "datatype": "datetime"},
            "71": {"field": "status", "datatype": "varchar"},
            "86": {"field": "RIS_number", "datatype": "integer"},
        },
        "combined_item_mapping": {
            "item_type": "management_document",
            "name": "title",
            "date": "document_date",
            "classification": "document_type",
            "last_modified": "last_modified",
            "document_content": ""
        }
    },
    "9": {
        "model": PolicyDocument,
        "attribute_mapping": {
            "2":  {"field": "document", "datatype": "document"},
            "5":  {"field": "number", "datatype": "varchar"},
            "1":  {"field": "title", "datatype": "varchar"},
            "44": {"field": "document_date", "datatype": "datetime"},
            "52": {"field": "policy_field", "datatype": "varchar"},
            "24": {"field": "dossiercode", "datatype": "varchar"},
            "51": {"field": "meeting_category", "datatype": "integer"},
            "45": {"field": "document_type", "datatype": "varchar"},
            "50": {"field": "location", "datatype": "varchar"},
            "23": {"field": "portfolio_holder", "datatype": "integer"},
            "18": {"field": "settlement", "datatype": "varchar"},
            "47": {"field": "date_created", "datatype": "datetime"},
            "54": {"field": "linked_event", "datatype": "event"},
            "7":  {"field": "publication_date", "datatype": "datetime"},
            "46": {"field": "category", "datatype": "varchar"},
            "60": {"field": "coupled_to_module", "datatype": "integer"},
            "65": {"field": "add_to_LTA", "datatype": "integer"},
            "86": {"field": "RIS_number", "datatype": "integer"},
        },
        "combined_item_mapping": {
            "item_type": "policy_document",
            "name": "title",
            "date": "date_created",
            "classification": "document_type",
            "last_modified": "last_modified",
            "document_content": ""
        }
    }
}


class ModuleItemsScraper():
    """
    This script parses all data bound to Notubiz modules.
    """

    def __init__(self):
        self.organisation = settings.RIS_MUNICIPALITY
        self.api_url = "https://api.notubiz.nl/organisations/{}/modules/{}/items/"


    def start(self):
        """

        """
        organisation = 0
        moduleIds = []

        if self.organisation == 'Almere':
            organisation = 952
            moduleIds = range(1,18)
        elif self.organisation == 'Rotterdam':
            organisation = 726
            moduleIds = [3,4,6]

        for module_id in moduleIds:
            module_id_str = str(module_id)
            response = requests.get(self.api_url.format(str(organisation), module_id_str))
            try:
                root = etree.fromstring(response.content)
            except Exception:
                continue

            if root == None:
                print "no items found for module {}".format(module_id_str)
                continue

            self.parse_module(root, module_id_str)


    def validate_datetime(self, datetime_str):
        """

        """
        if datetime_str == '':
            return None

        try:
            datetime_str = "{} {}".format(datetime_str, "CET")
            datetime = parser.parse(datetime_str)
        except UnicodeEncodeError:
            datetime = None
        except ValueError:
            datetime = None
        except ValidationError:
            datetime = None
        return datetime


    def get_organisation(self, notubiz_id):
        """
        Get or create the organisation
        """
        org = Organisation.objects.filter(notubiz_id=notubiz_id)
        if (len(org) == 0):
            response = requests.get("https://api.notubiz.nl/organisations/{}/".format(str(notubiz_id)))
            root = etree.fromstring(response.content)
            name = root.find("organisation").find("name").text
            org = Organisation.objects.create(notubiz_id=notubiz_id, name=name)
            return org
        return org[0]


    def parse_item_meta(self, item):
        """
        Parse the meta thats added as attributes to the item
        """
        return {
            "notubiz_id": item.get("id"),
            "item_created": self.validate_datetime(item.get("creation_date")),
            "last_modified": self.validate_datetime(item.get("last_modified")),
            "confidential": item.get("confidential"),
            "distribution_group": item.get("distribution_group"),
            "organisation": self.get_organisation(item.get("organisation_id"))
        }


    def parse_item_attachments(self, item, module_id):
        if item.find("attachments"):
            print "Not implemented, module {} with id {} has attachments".format(module_id, item.get("id"))
            #"TODO - implement"
            return {}
        else:
            return {}


    def parse_module_document(self, attribute_xml, item_type):
        document_xml = attribute_xml.find("value")
        document_id = document_xml.get("id")
        document_last_modified = self.validate_datetime(document_xml.get("last_modified"))

        # document_version = document_xml.get("version")
        # document_distribution_group = document_xml.get("distribution_group")
        document_filetype = document_xml.find("filetype").text
        document_title = unicode(document_xml.find("title").text).encode("utf-8")
        document_url = document_xml.find("url").text

        # for doc_type_xml in document_xml.find("types"):
        #     document_type_id = doc_type_xml.get("id")
        #     document_type_name = doc_type_xml.find("name").text

        defaults = {
            'last_modified': document_last_modified,
            'text': document_title,
            'url': document_url,
            'media_type': document_filetype,
            'attached_to': item_type,
            'date': document_last_modified,
            'event': None
        }

        document, created = Document.objects.get_or_create(
            notubiz_id=document_id,
            defaults= defaults
        )

        if document.last_modified != document_last_modified:
            defaults['notubiz_id'] = document_id
            Document.objects.filter(id=document.id).update(**defaults)

        return document

        # save doc and return here


    def parse_module_event(self, attribute_xml):
        """

        """
        event_id = attribute_xml.find("value")
        try:
            event = Event.objects.get(notubiz_id=event_id)
        except:
            event = None

        return event


    def get_or_create_person(self, person_xml):
        """

        """
        person_notubiz_id = person_xml.get("id")
        person_name = person_xml.text

        person, created = Person.objects.get_or_create(
            notubiz_id=person_notubiz_id,
            defaults={
                'name': person_name
            }
        )
        return person


    def get_or_create_party(self, party_xml):
        """

        """
        party_notubiz_id = party_xml.get("id")
        party_name = party_xml.text

        party, created = Party.objects.get_or_create(
            notubiz_id=party_notubiz_id,
            defaults={
                'name': party_name
            }
        )
        return party


    def parse_item_attributes(self, item, attribute_mapping, item_type):
        """

        """
        item_attributes_data = {}

        for attribute_xml in item.find("attributes"):

            attribute_id = str(attribute_xml.get("id"))
            attribute_meta = attribute_mapping[attribute_id]

            datatype = attribute_meta.get("datatype")
            field = attribute_meta.get("field")
            multiple = attribute_xml.get("multiple")

            if datatype == "event":
                # attribute value = a event ID
                field_data = self.parse_module_event(attribute_xml)

            if datatype == "document":
                field_data = self.parse_module_document(attribute_xml, item_type)

            if datatype == "party":

                if multiple != None and int(multiple) > 0:

                    field_data = []
                    for party_xml in attribute_xml.find("values"):
                        party_instance = self.get_or_create_party(party_xml)
                        field_data.append(party_instance)
                else:

                    field_data = []
                    party_xml = attribute_xml.find("value")
                    party_instance = self.get_or_create_party(party_xml)
                    field_data.append(party_instance)

            if datatype == "person":

                if multiple != None and int(multiple) > 0:

                    field_data = []
                    for person_xml in attribute_xml.find("values"):
                        person_instance = self.get_or_create_person(person_xml)
                        field_data.append(person_instance)
                else:

                    field_data = []
                    person_xml = attribute_xml.find("value")
                    person_instance = self.get_or_create_party(person_xml)
                    field_data.append(person_instance)

            if datatype == "varchar" or datatype == "text":

                if multiple != None and int(multiple) > 0:

                    vals = []
                    for val in attribute_xml.find("values"):
                        vals.append(val.text)
                    try:
                        field_data = ", ".join(vals)
                    except:
                        field_data = ""
                else:
                    field_data = unicode(attribute_xml.find("value").text).encode("utf-8")

            if datatype == "integer":

                if attribute_id == "51" or attribute_id == "87":
                    continue

                if multiple != None and int(multiple) > 0:

                    vals = []
                    for val in attribute_xml.find("values"):
                        vals.append(val.text)
                    field_data = ", ".join(vals)
                else:
                    field_data = attribute_xml.find("value").text

            if datatype == "datetime":
                field_data = self.validate_datetime(attribute_xml.find("value").text)

            item_attributes_data[field] = field_data

        return item_attributes_data


    def parse_module(self, items, module_id):
        """

        """
        if module_id not in module_meta:
            return

        model = module_meta[module_id]["model"]
        attribute_mapping = module_meta[module_id]["attribute_mapping"]
        combined_item_mapping = module_meta[module_id]["combined_item_mapping"]

        print "module id {}".format(module_id)

        for item in items:

            if item.tag == 'pagination':
                continue

            item_meta_data = self.parse_item_meta(item)

            item_exists = False
            item_instance = None
            notubiz_id = item_meta_data.get('notubiz_id')

            print notubiz_id

            if model.objects.filter(notubiz_id=notubiz_id).exists():
                item_exists = True
                if model.objects.get(notubiz_id=notubiz_id).last_modified == item_meta_data.get('last_modified'):
                    continue

            item_attributes_data = self.parse_item_attributes(item, attribute_mapping, combined_item_mapping['item_type'])

            # merge it to 1 dict
            model_data = item_meta_data.copy()
            model_data.update(item_attributes_data)

            # prework for many to many relationships
            module_has_parties = False
            if model_data.get("parties") != None:
                module_has_parties = True
                parties = model_data.get("parties")
                model_data.pop('parties', None)

            module_has_initiator = False
            if model_data.get("initiator") != None:
                module_has_initiator = True
                initiator = model_data.get("initiator")
                model_data.pop('initiator', None)


            # save the actual item
            if item_exists:
                # update
                model.objects.filter(notubiz_id=notubiz_id).update(**model_data)
                item_instance = model.objects.get(notubiz_id=notubiz_id)
            else:
                #create
                try:
                    item_instance = model.objects.create(**model_data)
                except UnicodeEncodeError:
                    print "UNICODE ENCODE ERROR"
                    continue

            # post work for many to many relationships
            if module_has_parties:
                item_instance.parties.clear()
                for party in parties:
                    item_instance.parties.add(party)

            if module_has_initiator:
                item_instance.initiator.clear()
                for person in initiator:
                    item_instance.initiator.add(person)

            # add to combined items
            self.add_module_data_to_combined_items(item_instance, combined_item_mapping, item_exists)


    def add_module_data_to_combined_items(self, item_instance, combined_item_mapping, item_exists):
        """
        """

        if combined_item_mapping['classification'] == 'TODO':
            classification = None
        else:
            classification = getattr(item_instance, combined_item_mapping['classification'])

        combined_item_data = {
            'item_id': item_instance.id,
            'notubiz_id': item_instance.notubiz_id,
            'name': getattr(item_instance, combined_item_mapping['name']),
            'date': getattr(item_instance, combined_item_mapping['date']),
            'url': 'n/a',
            'classification': classification,
            'last_modified': getattr(item_instance, combined_item_mapping['last_modified']),
            'item_type': combined_item_mapping['item_type']
        }

        if item_exists:
            # update
            CombinedItem.objects.filter(
                notubiz_id=combined_item_data.get('notubiz_id'),
                item_type=combined_item_data.get('item_type')
            ).update(**combined_item_data)
        else:
            # create
            CombinedItem.objects.create(**combined_item_data)

