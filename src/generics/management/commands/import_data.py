from django.core.management.base import BaseCommand
from generics.scripts.data_scraper import NotubizDataScraper
from generics.scripts.ibabs_data_scraper import iBabsDataScraper
from django.conf import settings


class Command(BaseCommand):
    help = 'scrapes events from Notubiz, iBabs APIs'

    def handle(self, *args, **options):
        municipality = settings.RIS_MUNICIPALITY

        print ("Starting the scraper for {}".format(municipality))

        if municipality == 'Almere':
            scraper = NotubizDataScraper()
        elif municipality == 'Rotterdam':
            scraper = NotubizDataScraper()
        elif municipality == 'Utrecht':
            scraper = iBabsDataScraper()
        elif municipality == 'Zoetermeer':
            scraper = iBabsDataScraper()
        else:
            scraper = NotubizDataScraper()

        scraper.start()


print "Scraping ended succesfully"