from django.conf import settings


def get_rq_queue_name():
    return getattr(settings, 'ATELIER_MESSAGES_RQ_QUEUE_NAME', None) or 'default'
