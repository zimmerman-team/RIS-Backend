import django_rq
from django.core import management
from redis import Redis
from django_rq import job
from django.conf import settings
from rq.job import Job

redis_conn = Redis.from_url(settings.RQ_REDIS_URL)


@job
def do_all():
    """
    Functionalities:
    - All
    """
    management.call_command('import_speakers', verbosity=0, interactive=False)
    management.call_command('import_data', verbosity=0, interactive=False)
    management.call_command('import_notubiz_modules', verbosity=0, interactive=False)
    management.call_command('import_document_files', verbosity=0, interactive=False)


@job
def do_all_except_scan():
    """
    Functionalities:
    - All
    """
    management.call_command('import_speakers', verbosity=0, interactive=False)
    management.call_command('import_data', verbosity=0, interactive=False)
    management.call_command('import_notubiz_modules', verbosity=0, interactive=False)


@job
def import_speakers():
    """
    Functionalities:
    - Imports events from notubiz
    - Imports underlying agenda items, documents, media.
    """
    management.call_command('import_speakers', verbosity=0, interactive=False)


@job
def import_public_dossiers():
    """
    Functionalities:
    - Imports dossiers from notubiz
    """
    management.call_command('import_public_dossiers', verbosity=0, interactive=False)


@job
def import_data():
    """
    Functionalities:
    - Imports events from notubiz
    - Imports underlying agenda items, documents, media.
    """
    management.call_command('import_data', verbosity=0, interactive=False)


@job
def import_notubiz_modules():
    """
    Functionalities:
    - Imports notubiz modules (special documents)
    """
    management.call_command('import_notubiz_modules', verbosity=0, interactive=False)


@job
def import_document_files():
    """
    Functionalities:
    - Downloads documents
    - Extracts text from all documents that are unscanned
    - Updates the search indexes based upon the content of the documents.
    """
    management.call_command('import_document_files', verbosity=0, interactive=False)


def delete_task_from_queue(job_id):
    Job.fetch(job_id, connection=redis_conn).delete()


def delete_all_tasks_from_queue(queue_name):
    if queue_name == "failed":
        q = django_rq.get_failed_queue()
    elif queue_name == "parser":
        q = django_rq.get_queue("parser")
    else:
        q = django_rq.get_queue("default")

    while True:
        current_job = q.dequeue()
        if not current_job:
            break
        current_job.delete()