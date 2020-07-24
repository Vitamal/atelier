from .develop_and_test_settings_common import *

LANGUAGE_CODE = 'en'

INSTALLED_APPS += [
    'atelier.atelier_email.tests.atelier_email_testapp',

]

TIME_ZONE = 'UTC'

STATICFILES_STORAGE = None
