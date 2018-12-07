from django.core.management.base import BaseCommand

from generics.models import CombinedItem, PolicyDocument, Event, Document, ReceivedDocument, CouncilAddress, Commitment, \
    WrittenQuestion, Motion, PublicDocument, ManagementDocument


class Command(BaseCommand):
    help = 'Just a simple script that removes spaces from ' \
           'the start and end of the municipality document objects and combined items names'

    def handle(self, *args, **options):

        print ("Starting the strip")
        Strip()


class Strip:

    def __init__(self):
        self.strip_the_model(CombinedItem.objects.filter(name__startswith=' '))
        self.strip_the_model(PolicyDocument.objects.filter(title__startswith=' '))
        self.strip_the_model(Event.objects.filter(name__startswith=' '))
        self.strip_the_model(Document.objects.filter(text__startswith=' '))
        self.strip_the_model(ReceivedDocument.objects.filter(subject__startswith=' '))
        self.strip_the_model(CouncilAddress.objects.filter(title__startswith=' '))
        self.strip_the_model(Commitment.objects.filter(title__startswith=' '))
        self.strip_the_model(WrittenQuestion.objects.filter(title__startswith=' '))
        self.strip_the_model(Motion.objects.filter(title__startswith=' '))
        self.strip_the_model(PublicDocument.objects.filter(title__startswith=' '))
        self.strip_the_model(ManagementDocument.objects.filter(title__startswith=' '))
        print "Stripping ended succesfully"

    @staticmethod
    def strip_the_model(items_with_space):
        for item in items_with_space:
            if type(item) is CombinedItem or type(item) is Event:
                item.name = item.name.strip()
            elif type(item) is Document:
                item.text = item.text.strip()
            elif type(item) is ReceivedDocument:
                item.subject = item.subject.strip()
            else:
                item.title = item.title.strip()
            item.save()