from urllib.parse import urlparse

from atelier.project.default.settings import *

SECRET_KEY = os.environ.get('SECRET_KEY', 'default')

DEBUG = int(os.environ.get('DEBUG', default=0))

# ALLOWED_HOSTS = ['flexitkt.herokuapp.com', 'flexitkt-production.herokuapp.com', 'internt.flexit.xyz']

EMAIL_HOST = 'smtp.mailtrap.io'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = 25
EMAIL_USE_TLS = True

# Redirect all requests to https
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

redis_url = urlparse(os.environ.get('REDIS_URL'))

RQ_QUEUES = {
    'default': {
        'ASYNC': True,
        'HOST': redis_url.hostname,
        'PASSWORD': redis_url.password,
        'PORT': redis_url.port,
        'DB': 0,
        'DEFAULT_TIMEOUT': 60 * 60 * 2  # 2 hours
    },
    'long_running_tasks': {
        'ASYNC': True,
        'HOST': redis_url.hostname,
        'PASSWORD': redis_url.password,
        'PORT': redis_url.port,
        'DB': 0,
        'DEFAULT_TIMEOUT': 60 * 60 * 20  # 20 hours
    }
}

# FLEXIT_MESSAGES_EMAIL_BACKEND = 'MAILGUN_API'
# MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
# MAILGUN_SENDER_DOMAIN = os.environ.get('MAILGUN_SENDER_DOMAIN')
# MAILGUN_API_BASE_URL = f'https://api.eu.mailgun.net/v3/{MAILGUN_SENDER_DOMAIN}'
#
# IEVV_SMS_DEFAULT_BACKEND_ID = 'linkmobility'
# LINKMOBILITY_USERNAME = os.environ.get('LINKMOBILITY_USERNAME')
# LINKMOBILITY_PASSWORD = os.environ.get('LINKMOBILITY_PASSWORD')
# LINKMOBILITY_SENDER = os.environ.get('LINKMOBILITY_SENDER', 'Flexit AS')
# LINKMOBILITY_DEFAULT_COUNTRY_CODE = os.environ.get('LINKMOBILITY_DEFAULT_COUNTRY_CODE', '47')
