from django.core.management.base import BaseCommand
from generics.scripts.document_scraper import NotubizDocumentScraper


class Command(BaseCommand):
    help = 'scrapes documents from Notubiz/iBabs API'

    def handle(self, *args, **options):

        print "Starting the scraper"

        scraper = NotubizDocumentScraper()
        scraper.start()

print "Scraping ended succesfully"