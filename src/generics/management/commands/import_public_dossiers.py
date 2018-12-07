from django.core.management.base import BaseCommand
from generics.scripts.public_dossiers_scraper import NotubizPublicDossiersScraper
from django.conf import settings

class Command(BaseCommand):
    help = 'scrapes public dossiers from Notubiz'

    def handle(self, *args, **options):
        municipality = settings.RIS_MUNICIPALITY

        print ("Starting the scraper for {}".format(municipality))

        if municipality == 'Almere':
            scraper = NotubizPublicDossiersScraper()
            scraper.start()
        elif municipality == 'Rotterdam':
            scraper = NotubizPublicDossiersScraper()
            scraper.start()
        else:
            print "No dossiers for non-Notubiz municipalities"

        print "Scraping ended succesfully"
