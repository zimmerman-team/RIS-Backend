#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import requests
from lxml import etree
from generics.models import Document, CombinedItem, PublicDossier
from django.core.exceptions import ObjectDoesNotExist
from dateutil import parser
from django.conf import settings


class NotubizPublicDossiersScraper:
    """
    Scrapes all public dossiers
    """

    def __init__(self):
        self.org_id_name_mapping = {}
        self.api_url = "http://api.notubiz.nl/"
        self.organisation = settings.RIS_MUNICIPALITY

    def start(self):
        self.get_dossiers()

    def get_dossiers(self):
        organisation = 0
        if self.organisation == 'Rotterdam':
            organisation = 726
        elif self.organisation == 'Almere':
            organisation = 952

        params = {'version': '1.10.3', 'format': 'xml'}
        response = requests.get(self.api_url + "organisations/{}/folders/".format(organisation), params)
        root = etree.fromstring(response.content)
        dossiers = root.find("folders")

        if dossiers != None:
            self.parse_dossiers(dossiers)

        print 'Done'

    def parse_dossiers(self, dossiers, parent=None):
        for d in dossiers:
            dossier_id = int(d.get('id'))
            last_modified = parser.parse(d.get('last_modified'))
            skip = False

            params = {'version': '1.10.3', 'format': 'xml'}
            response = requests.get(self.api_url + "folder/{}/".format(dossier_id), params)
            root = etree.fromstring(response.content)

            try:
                _dossier = PublicDossier.objects.get(notubiz_id=dossier_id)
                if _dossier.last_modified == last_modified:
                    # up to date
                    skip = True
            except ObjectDoesNotExist:
                pass

            if skip is False:
                print 'Did not skip {}'.format(dossier_id)
                self.create_dossier(root.find('folder'), parent)

    def create_dossier(self, data, parent):
        info = self.get_dossier_info(data.find('attributes'))
        dossier_id = int(data.get('id'))
        _dossier, created = PublicDossier.objects.update_or_create(
            notubiz_id=dossier_id,
            defaults={
                'title': info['name'],
                'created_at': parser.parse(info['created_at']),
                'last_modified': parser.parse(info['last_modified']),
                'folder_count': int(data.get('folder_count')),
                'document_count': int(data.get('document_count')),
                'parent_dossier': parent
            }
        )
        _dossier.save()

        _combined_item, created = CombinedItem.objects.update_or_create(
            notubiz_id=_dossier.notubiz_id,
            item_type= 'public_dossier',
            defaults= {
                'item_id': _dossier.id,
                'name': _dossier.title.strip(),
                'date': _dossier.created_at,
                'last_modified': _dossier.last_modified,
                'item_type': 'public_dossier'
            }
        )
        _combined_item.save()

        if _dossier.document_count > 0:
            documents = data.find("documents")
            self.parse_documents(documents, _dossier)
        if _dossier.folder_count > 0:
            dossiers = data.find("folders")
            self.parse_dossiers(dossiers, _dossier)

    def get_dossier_info(self, info):
        name = None
        created_at = None
        last_modified = None
        for a in info:
            if int(a.get('id')) == 1:
                name = a.text
            if int(a.get('id')) == 47:
                created_at = a.text
            if int(a.get('id')) == 89:
                last_modified = a.text
        return {
            'name': name,
            'created_at': created_at,
            'last_modified': last_modified
        }

    def parse_documents(self, data, dossier):
        for d in data:
            doc_info = self.get_document_info(d, dossier)

            _document, created = Document.objects.update_or_create(
                notubiz_id=doc_info['notubiz_id'],
                defaults= {
                    'text': doc_info['text'],
                    'url': doc_info['url'],
                    'media_type': doc_info['media_type'],
                    'date': parser.parse(doc_info['date']),
                    'attached_to': doc_info['attached_to'],
                    'public_dossier': doc_info['public_dossier'],
                    'last_modified': parser.parse(doc_info['last_modified']),
                }
            )
            _document.save()

            _combined_item, created = CombinedItem.objects.update_or_create(
                notubiz_id=_document.notubiz_id,
                item_type= 'document',
                defaults= {
                    'item_id': _document.id,
                    'name': _document.text.strip(),
                    'date': _document.date,
                    'url': _document.url,
                    'classification': _document.media_type,
                    'last_modified': _document.last_modified,
                }
            )
            _combined_item.save()

    def get_document_info(self, doc, dossier):
        name = doc.find('types/type').text
        for a in doc.find('attributes'):
            if int(a.get('id')) == 1:
                name = a.text
        return {
            'notubiz_id': int(doc.get('id')),
            'text': name,
            'url': doc.find('url').text,
            'media_type': doc.find('types/type').text,
            'date': doc.get('publication_date'),
            'attached_to': 'public_dossier',
            'public_dossier': dossier,
            'last_modified': doc.get('last_modified'),
        }