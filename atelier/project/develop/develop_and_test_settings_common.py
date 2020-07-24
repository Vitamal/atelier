"""
Common development settings.
"""
from atelier.project.default.settings import *  # noqa

THIS_DIR = os.path.dirname(__file__)

DEBUG = True

ALLOWED_HOSTS = ['*']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s %(asctime)s %(name)s %(pathname)s:%(lineno)s] %(message)s'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'stderr': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['stderr'],
            'level': 'DEBUG',
            'propagate': False
        },
        'boto': {
            'handlers': ['stderr'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.db': {
            'handlers': ['stderr'],
            'level': 'INFO',  # Do not set to debug - logs all queries
            'propagate': False
        },
        'sh': {
            'handlers': ['stderr'],
            'level': 'INFO',  # Do not set to debug - logs everything
            'propagate': False

        },
        'urllib3': {
            'handlers': ['stderr'],
            'level': 'WARNING',
            'propagate': False
        },
        '': {
            'handlers': ['stderr'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

ROOT_URLCONF = 'atelier.project.develop.develop_urls'

REDIS_HOST = 'atelier_redis_1'
REDIS_PORT = 6379

RQ_QUEUES = {
    'default': {
        'ASYNC': False,
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0
    }
}
