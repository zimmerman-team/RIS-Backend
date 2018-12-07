from django.core.management.base import BaseCommand
from generics.scripts.document_remover import DocumentRemover
from django.conf import settings


# This script basically checks if documents have been removed from
# Notubiz and removes it from our system
class Command(BaseCommand):
    help = 'Removes documents the documents removed from notubiz from our system'

    def handle(self, *args, **options):
        municipality = settings.RIS_MUNICIPALITY
        print "Starting the remover"

        if not municipality == 'Utrecht':
            remover = DocumentRemover()
            remover.start()
        else:
            print ('Utrecht is all good, no need to remove docs')

        print "Remover ended succesfully"
