from django.core.management.base import BaseCommand
from generics.scripts.module_scraper import ModuleItemsScraper
from django.conf import settings


class Command(BaseCommand):
    help = 'scrapes document modules from Notubiz API'

    def handle(self, *args, **options):
        municipality = settings.RIS_MUNICIPALITY

        if municipality == 'Utrecht' or municipality == 'Zoetermeer':
            print ("{} municipality doesn't have module documents".format(municipality))
        else:
            print "Starting the module scraper"
            scraper = ModuleItemsScraper()
            scraper.start()
print "Scraping ended succesfully"