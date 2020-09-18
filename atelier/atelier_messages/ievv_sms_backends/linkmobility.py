import requests
from django.conf import settings

from ievv_opensource.ievv_sms import sms_registry


class Backend(sms_registry.AbstractSmsBackend):
    """
    A linkmobility (https://linkmobility.com) backend.

    To use this backend, you should set the following Django settings:

    - ``LINKMOBILITY_USERNAME``: The linkmobility username (USER).
    - ``LINKMOBILITY_PASSWORD``: The linkmobility password (PWD).
    - ``LINKMOBILITY_SENDER``: The linkmobility sender (SND).
    - ``LINKMOBILITY_DEFAULT_COUNTRY_CODE``: The country code to use if received
      phone numbers do not start with ``+<code>`` or ``00<code>``.
      E.g.: 47 for norway.

    If you do not set these settings, you must include
    them as kwargs each time you send a message, and this
    makes it hard to switch SMS sending provider.

    Optionally you can set :

    - ``LINKMOBILITY_BASE_URL``: The linkmobility base api url (URL).

    If this is not set, it defaults to 'https://wsx.sp247.net/sms'

    The backend_id for this backend is ``linkmobility``.
    """
    CHARACTER_REPLACE_MAP = {
        '–': '-'
    }

    @classmethod
    def get_backend_id(cls):
        return 'linkmobility'

    def __init__(self, phone_number, message,
                 linkmobility_sender=None,
                 linkmobility_username=None,
                 linkmobility_password=None,
                 linkmobility_default_country_code=None,
                 **kwargs):
        self._linkmobility_sender = linkmobility_sender
        self._linkmobility_username = linkmobility_username
        self._linkmobility_password = linkmobility_password
        self._linkmobility_default_country_code = linkmobility_default_country_code
        super().__init__(phone_number=phone_number, message=message, **kwargs)

    @property
    def linkmobility_base_url(self):
        return getattr(settings, 'LINKMOBILITY_BASE_URL', 'https://wsx.sp247.net/sms')

    @property
    def linkmobility_username(self):
        return self._linkmobility_username or settings.LINKMOBILITY_USERNAME

    @property
    def linkmobility_password(self):
        return self._linkmobility_password or settings.LINKMOBILITY_PASSWORD

    @property
    def linkmobility_sender(self):
        return self._linkmobility_sender or self.send_as or settings.LINKMOBILITY_SENDER

    @property
    def default_country_code(self):
        return self._linkmobility_default_country_code or settings.LINKMOBILITY_DEFAULT_COUNTRY_CODE

    def replace_message_characters(self, message):
        for from_char, to_char in self.CHARACTER_REPLACE_MAP.items():
            message = message.replace(from_char, to_char)
        return message

    def clean_message(self, message):
        message = self.replace_message_characters(message)
        message = message.encode('latin-1', errors='ignore').decode('latin-1')
        return message

    def clean_phone_number(self, phone_number):
        phone_number = self.STRIP_WHITESPACE_PATTERN.sub('', phone_number)
        if phone_number.startswith('+'):
            return phone_number
        elif phone_number.startswith('00'):
            phone_number = f'+{phone_number[2:]}'
        else:
            phone_number = '+{}{}'.format(self.default_country_code, phone_number)
        return phone_number

    @property
    def linkmobility_postdata(self):
        return {
            'source': self.linkmobility_sender,
            'destination': self.cleaned_phone_number,
            'userData': self.cleaned_message,
            "platformId": "COMMON_API",
            "platformPartnerId": "18500",
            "useDeliveryReport": False
        }

    def send(self):
        """
        Send the message using linkmobility.
        """
        requests.post(
            f'{self.linkmobility_base_url}/send',
            json=self.linkmobility_postdata,
            auth=(self.linkmobility_username, self.linkmobility_password)
        )
