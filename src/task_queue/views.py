import django_rq
import urllib
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from rq import requeue_job, get_failed_queue, Worker
from rq_scheduler import Scheduler
from rq.registry import FinishedJobRegistry
from task_queue import tasks
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq import get_current_job as gcj
from rq import Queue


# PARSE TASKS
@staff_member_required
def add_task(request):
    task = request.GET.get('task')
    parameters = request.GET.get('parameters')
    queue_to_be_added_to = request.GET.get('queue')
    queue = django_rq.get_queue(queue_to_be_added_to)
    func = getattr(tasks, task)

    if parameters:
        print 'here 1'
        queue.enqueue(func, args=(parameters,), timeout=14400)
    else:
        queue.enqueue(func)
    return HttpResponse(json.dumps(True), content_type='application/json')


# TASK QUEUE MANAGEMENT
@staff_member_required
def get_workers(request):
    workers = Worker.all(connection=tasks.redis_conn)
    workerdata = list()
    # serialize workers
    for w in workers:
        cj = w.get_current_job()

        if cj:
            cjinfo = {
                'id': cj.id,
                'args': cj.args,
                'enqueued_at': cj.enqueued_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
                'description': cj.description}
        else:
            cjinfo = None

        worker_dict = {
            'pid': w.pid,
            'name': w.name,
            'state': w.get_state(),
            'current_job': cjinfo}

        workerdata.append(worker_dict)
    data = json.dumps(workerdata)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def delete_task_from_queue(request):
    job_id = request.GET.get('job_id')
    tasks.delete_task_from_queue(job_id)
    return HttpResponse('Success')


@staff_member_required
def delete_all_tasks_from_queue(request):
    queue_name = request.GET.get('queue_name')
    tasks.delete_all_tasks_from_queue(queue_name)
    return HttpResponse('Success')


@staff_member_required
def get_current_job(request):
    q = Queue(connection=tasks.redis_conn)
    job = gcj(q)
    data = json.dumps(job)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def add_scheduled_task(request):
    task = request.GET.get('task')
    cron_string = request.GET.get('cron_string')
    cron_string = urllib.unquote(cron_string)

    print cron_string

    queue = request.GET.get('queue')
    parameters = request.GET.get('parameters')
    scheduler = Scheduler(queue_name=queue, connection=tasks.redis_conn)

    if parameters:
        args = (parameters,)
    else:
        args = None

    print tasks

    scheduler.cron(
        cron_string=cron_string,   # Time for first execution
        func=getattr(tasks, task),       # Function to be queued
        args=args,
        repeat=None,                      # Repeat this number of times (None means repeat forever),
        timeout=14400,
        queue_name=queue,
    )

    return HttpResponse('Success')


@staff_member_required
def get_queue(request):
    current_queue = request.GET.get('queue')
    queue = django_rq.get_queue(current_queue)
    jobdata = list()

    count_jobs = 0
    for job in queue.jobs:
        count_jobs += 1
        if count_jobs == 6:
            break

        job_dict = {
            'job_id': job._id,
            'created_at': job.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'enqueued_at': job.enqueued_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'status': job.get_status(),
            'function': job.func_name,
            'args': job.args}

        jobdata.append(job_dict)
    data = json.dumps(jobdata)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def get_scheduled_tasks(request):
    # Use RQ's default Redis connection
    # use_connection()
    # Get a scheduler for the "default" queue
    scheduler = Scheduler(connection=tasks.redis_conn)
    list_of_job_instances = scheduler.get_jobs()

    jobdata = list()
    for job in list_of_job_instances:
        if "interval" in job.meta:
            interval = job.meta["interval"]
        else:
            interval = 0

        job_dict = {
            'job_id': job._id,
            'task': job.description,
            'period': interval,
            'args': job.args,
            'queue': job.origin,
            'timeout': job.timeout}

        jobdata.append(job_dict)

    data = json.dumps(jobdata)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def cancel_scheduled_task(request):
    job_id = request.GET.get('job_id')

    scheduler = Scheduler('default', connection=tasks.redis_conn)
    scheduler.cancel(job_id)
    return HttpResponse('Success')


@staff_member_required
def get_failed_tasks(request):
    queue = django_rq.get_failed_queue()
    jobdata = list()
    for job in queue.jobs:

        job_dict = {
            'job_id': job.id,
            'func_name': job.description,
            'error_message': job.exc_info,
            'ended_at': job.ended_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'enqueued_at': job.enqueued_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'args': job.args
        }

        jobdata.append(job_dict)

    data = json.dumps(jobdata)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def get_finished_tasks(request):
    current_queue = request.GET.get('queue')
    queue = django_rq.get_queue(current_queue)
    registry = FinishedJobRegistry(queue.name, queue.connection)

    items_per_page = 10
    num_jobs = len(registry)
    jobs = []

    if num_jobs > 0:
        offset = 0
        job_ids = registry.get_job_ids(offset, items_per_page)

        for job_id in job_ids:
            try:
                jobs.append(Job.fetch(job_id, connection=queue.connection))
            except NoSuchJobError:
                pass

    jobdata = list()
    for job in jobs:

        job_dict = {
            'job_id': job.id,
            'func_name': job.func_name,
            'ended_at': job.ended_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'enqueued_at': job.enqueued_at.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'args': job.args}

        jobdata.append(job_dict)

    data = json.dumps(jobdata)
    return HttpResponse(data, content_type='application/json')


@staff_member_required
def reschedule_all_failed(request):
    queue = get_failed_queue(django_rq.get_connection())

    for job in queue.jobs:
        requeue_job(job.id, connection=queue.connection)

    return HttpResponse('Success')
