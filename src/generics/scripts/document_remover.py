#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import requests
from requests.exceptions import SSLError, InvalidURL
from generics.models import Document, CombinedItem, Motion, PublicDocument, Commitment, CouncilAddress, PolicyDocument, \
    WrittenQuestion, ReceivedDocument, ManagementDocument, EventAgendaMediaLink
from django.db.models import Q

class DocumentRemover():
    """

    """

    def start(self):
        # post get events, get th docs and update the vectors all at once
        self.check_remove_docs()

    def check_remove_docs(self):
        for document in Document.objects.filter(~Q(notubiz_id=None)):
            url = document.url
            try:
                r = requests.get(url, stream=True)
                if r.status_code == 404:
                    self.delete_doc(document)
            except SSLError:
                return None
            except InvalidURL:
                return None

    def delete_doc(self, doc):
        other_docs = None
        try:
            comb = CombinedItem.objects.get(item_id=doc.id, item_type='document')
            comb.delete()
        except CombinedItem.DoesNotExist:
            # So the combined item might be of another type of document
            # So we gonna go through all the types of docs check if this document
            # is attached to them and delete there CombinedItem equivalent
            # We dont need to delete the other type documents themselves
            # Cause they gonna be deleted when we delete the original doc
            doc_type = {
                    "motion": Motion,
                    "format": PublicDocument,
                    "commitment": Commitment,
                    "council_address": CouncilAddress,
                    "policy_document": PolicyDocument,
                    "written_question": WrittenQuestion,
                    "received_document": ReceivedDocument,
                    "management_document": ManagementDocument,
            } [doc.attached_to]

            if doc_type == Motion:
                other_docs = Motion.objects.filter(document=doc)
            if doc_type == PublicDocument:
                other_docs = PublicDocument.objects.filter(document=doc)
            if doc_type == Commitment:
                other_docs = Commitment.objects.filter(new_document=doc)
            if doc_type == CouncilAddress:
                other_docs = CouncilAddress.objects.filter(question_document=doc)
                if not other_docs:
                    other_docs = CouncilAddress.objects.filter(interim_answer_document=doc)
                if not other_docs:
                    other_docs = CouncilAddress.objects.filter(answer_document=doc)
            if doc_type == PolicyDocument:
                other_docs = PolicyDocument.objects.filter(document=doc)
            if doc_type == WrittenQuestion:
                other_docs = WrittenQuestion.objects.filter(question_document=doc)
                if not other_docs:
                    other_docs = WrittenQuestion.objects.filter(interim_answer_document=doc)
                if not other_docs:
                    other_docs = WrittenQuestion.objects.filter(answer_document=doc)
            if doc_type == ReceivedDocument:
                other_docs = ReceivedDocument.objects.filter(document=doc)
            if doc_type == ManagementDocument:
                other_docs = ManagementDocument.objects.filter(document=doc)

            if not other_docs and other_docs is not None:
                for other_doc in other_docs:
                    try:
                        comb = CombinedItem.objects.get(item_id=other_doc.id, item_type=doc.attached_to)
                        comb.delete()
                    except CombinedItem.DoesNotExist:
                        # combined item for these docs dont even exist at all
                        pass

        # We have to delete the agenda media for events, cause it doesn't delete automatically with the doc :/
        links = EventAgendaMediaLink.objects.filter(item_id=doc.id)

        if links:
            for link in links:
                # so here we delete the media object attached to the link
                link.media.delete()
                # and here we delete the link itself
                link.delete()
        else:
            # Could be a document of other type in media
            if other_docs:
                for other_doc in other_docs:
                    links = EventAgendaMediaLink.objects.filter(item_id=other_doc.id)
                    if links:
                        for link in links:
                            # so here we delete the media object attached to the link
                            link.media.delete()
                            # and here we delete the link itself
                            link.delete()

        # And finally we delete the document itself
        doc.delete()






