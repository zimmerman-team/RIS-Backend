from django.core.management.base import BaseCommand
from generics.scripts.speakers_scraper import NotubizSpeakersDataScraper
from django.conf import settings


class Command(BaseCommand):
    help = 'scrapes speakers from Notubiz API'

    def handle(self, *args, **options):
        municipality = settings.RIS_MUNICIPALITY

        print ("Starting the scraper for {}".format(municipality))

        if municipality == 'Almere' or municipality == 'Rotterdam':
            scraper = NotubizSpeakersDataScraper()
            scraper.start()

print "Scraping ended succesfully"