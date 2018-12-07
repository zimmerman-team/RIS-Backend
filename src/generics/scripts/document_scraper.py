#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import requests
from textract.exceptions import MissingFileError

from generics.models import DocumentContent, Document, CombinedItem, ReceivedDocument, CouncilAddress, WrittenQuestion, PublicDocument, \
    PolicyDocument, ManagementDocument, Motion, Commitment
import os
from django.contrib.postgres.search import SearchVector
from requests.exceptions import SSLError, InvalidURL, ChunkedEncodingError
import fulltext
import nltk
from unidecode import unidecode
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pdf2image import convert_from_path
import textract

from ris import local_settings

nltk.download('punkt')
nltk.download('stopwords')

class NotubizDocumentScraper():
    """

    """

    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.realpath(__name__))
        self.current = os.path.abspath(BASE_DIR)
        self.xls_dir = BASE_DIR + "/generics/"

    def start(self):
        # post get events, get th docs and update the vectors all at once
        self.get_document_content()

    def get_document_content(self):
        file_name = ''
        for event_doc_obj in sorted(Document.objects.filter(document_content_scanned=False), key=lambda x: x.id, reverse=True):
            try:
                file_name = self.downloadFile(event_doc_obj)

                document_content_text = self.getFileContent(file_name, event_doc_obj.id)
                document_content = DocumentContent.objects.create(content=document_content_text)

                event_doc_obj.document_content_scanned = True
                event_doc_obj.file_path = file_name
                event_doc_obj.doc_content = document_content
                event_doc_obj.save()

                self.remove_folder_contents()

                if CombinedItem.objects.filter(item_id=event_doc_obj.id, item_type='document').exists():
                    ci = CombinedItem.objects.get(item_id=event_doc_obj.id, item_type='document')
                    ci.doc_content = document_content
                    ci.save()

                self.add_content_text(ReceivedDocument.objects.filter(document__url=event_doc_obj.url),
                                      'received_document', document_content_text)
                self.add_content_text(CouncilAddress.objects.filter(question_document__url=event_doc_obj.url),
                                      'council_address', document_content_text)
                self.add_content_text(WrittenQuestion.objects.filter(question_document__url=event_doc_obj.url),
                                      'written_question', document_content_text)
                self.add_content_text(PublicDocument.objects.filter(document__url=event_doc_obj.url),
                                      'format', document_content_text)
                self.add_content_text(PolicyDocument.objects.filter(document__url=event_doc_obj.url),
                                      'policy_document', document_content_text)
                self.add_content_text(ManagementDocument.objects.filter(document__url=event_doc_obj.url),
                                      'management_document', document_content_text)
                self.add_content_text(Motion.objects.filter(document__url=event_doc_obj.url),
                                      'motion', document_content_text)
                self.add_content_text(Commitment.objects.filter(new_document__url=event_doc_obj.url),
                                      'commitment', document_content_text)
            except Exception:
                self.remove_folder_contents()

        vector = SearchVector('content', config='dutch')
        DocumentContent.objects.update(vector=vector)


    # Adds document content text to other types of objects where their url points to this document
    def add_content_text(self, query_set, typez, doc_cont_text):
        for typ in query_set:
            ci = CombinedItem.objects.get(item_id=typ.id, item_type=typez)
            ci.document_content_text = doc_cont_text
            ci.save()


    def downloadFile(self, event_doc_obj):

        if local_settings.RIS_MUNICIPALITY != 'Utrecht':
            file_name = str(event_doc_obj.notubiz_id) + '.pdf'
        else:
            file_name = str(event_doc_obj.ibabs_id) + '.pdf'

        path = os.path.abspath(self.current + '/files/' + file_name)

        if os.path.isfile(path):
            return file_name

        # So because utrecht servers are faulty, sometimes we wouldn't get the full document content
        # in the request thus resulting in a ChunkedEncodingError
        # So we redo the download up to 5 times and if there will still be an issue
        # we can investigate it more thouroughly
        times_tried = 0
        while times_tried < 5:
            try:
                try:
                    r = requests.get(event_doc_obj.url, stream=True)
                except SSLError:
                    return None
                except InvalidURL:
                    return None

                if r.status_code == 200 and 'text/html' not in r.headers[
                    'Content-Type'] and 'content-disposition' in r.headers:

                    path = os.path.abspath(self.current + '/files/' + file_name)

                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)

                    return file_name
                else:
                    break
            except ChunkedEncodingError, e:
                times_tried = times_tried + 1
                print(e.message)
                print('File wasnt downloaded succesfully so we redo the download')
                print('File downloaded {number} times'.format(number=times_tried))

        if times_tried >= 5:
            raise ChunkedEncodingError('So redownloading the file 5 times didn\'t work, maybe there\'s some other issue? ')

        return None

    def scanDoc(self, path):
        text = self.remove_non_ascii(fulltext.get(path))

        # Oke so maybe the pdf was actually an image
        if text == "":
            print('Maybe pdf contained only images, trying to get text from image')
            text = self.get_image_content(path)

        tokens = word_tokenize(text)

        punctuations = ['(',')',';',':','[',']',',','.',"'",'@','&']
        stop_words = stopwords.words('dutch')

        keywords = [word for word in tokens if not word in stop_words and not word in punctuations]

        return " ".join(keywords)

    def getFileContent(self, file_name, doc_id, path=False):
        path_to_files = path if path else '/files/'
        path = os.path.abspath(self.current + path_to_files + file_name)
        content = self.scanDoc(path)

        if content == "":
            print "Could not find content for {} with id = {}".format(file_name, doc_id)
        else:
            print "Found content for {} with id = {}".format(file_name, doc_id)

        return content

    def get_image_content(self, path):
        content = ""
        self.convert_pdf_to_jpg(path)
        i = 0
        while True:
            try:
                image_path = self.current + '/files/image-{i}.jpg'.format(i=i)
                # Got the text from image
                content = content + textract.process(image_path,
                                                     encoding='ascii',
                                                     method='tesseract')
                # remove the image
                os.remove(os.path.abspath(image_path))
                i = i + 1
            except MissingFileError:
                break

        return content

    def remove_non_ascii(self, text):
        try:
            return unidecode(unicode(text, encoding = "utf-8"))
        except TypeError:
            return text

    # So because we have some caching/memory issues with big pdf files and converting them to image
    # We are going to create a seperate pdf for each page and then convert it to image
    def convert_pdf_to_jpg(self, path):
        pages = convert_from_path(path)
        i = 0
        for page in pages:
            image_path = self.current + '/files/image-{i}.jpg'.format(i=i)
            page.save(image_path, 'JPEG')
            i = i + 1

    def remove_folder_contents(self):
        folder = self.current + '/files/'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    def test_lol(self, randomvalue):
        return 'I AM FROM THE DOCUMENT SCRAPER' + randomvalue
