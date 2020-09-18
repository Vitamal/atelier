from __future__ import unicode_literals
import uuid
import random
from datetime import timedelta
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models import QuerySet, CASCADE
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


def _get_current_datetime():
    return timezone.now()


def get_time_to_live_minutes(app):
    """
    Get the configured time to live in minutes for tokens for the given ``app``.
    """
    time_to_live_minutes = getattr(
        settings,
        'DJANGO_CRADMIN_SECURE_USER_TOKEN_TIME_TO_LIVE_MINUTES', {
            'default': 60 * 24 * 4  # Default to 4 days
        })
    return time_to_live_minutes.get(app, time_to_live_minutes['default'])


def get_expiration_datetime_for_app(app):
    """
    Get the expiration datetime of tokens for the given ``app``
    relative to ``now``.

    If the given app is configured to with 60 minutes time to live,
    this will return a datetime object representing 60 minutes in the future.
    """
    time_to_live_minutes = get_time_to_live_minutes(app)
    return _get_current_datetime() + timedelta(minutes=time_to_live_minutes)


# noinspection PyUnusedLocal
def generate_token(**kwargs):
    """
    Generate a token for the :obj:`.GenericTokenWithMetadata.token` field.

    Joins an UUID1 (unique uuid) with an UUID4 (random uuid), so the chance
    of this not beeing unique is very low, and guessing this is
    very hard.

    Returns:
        A token that is very unlikely to not be unique.
    """
    return u'{}-{}'.format(uuid.uuid1(), uuid.uuid4())


def generate_letter_digits_token(length):
    sm_letters = 'abcdefghkmopqrstuvwxyz'
    cap_letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    digits = '23456789'
    return ''.join(random.choice(sm_letters + cap_letters + digits) for _ in range(length))


class GenericTokenExpiredError(Exception):
    """
    Raised by :meth:`.GenericTokenWithMetadata.get_and_validate` when
    the token is found, but has expired.
    """


# noinspection PyUnresolvedReferences
class GenericTokenWithMetadataQuerySet(QuerySet):
    """
    QuerySet for :class:`.GenericTokenWithMetadata`.
    """
    def unsafe_pop(self, app, token):
        """
        Get the :class:`.GenericTokenWithMetadata` matching the given
        `token` and `app`. Removes the GenericTokenWithMetadata from the database, and
        returns the `GenericTokenWithMetadata` object.

        You should normally use :meth:`.GenericTokenWithMetadataBaseManager.pop`
        instead of this.

        Raises:
            GenericTokenWithMetadata.DoesNotExist if no matching token is stored for
            the given app.
        """
        token = self.get(token=token, app=app)
        token.delete()
        return token

    def get_and_check_for_single_use(self, *args, **kwargs):
        token = self.get(*args, **kwargs)
        if token.single_use:
            token.delete()
        return token

    def filter_has_expired(self):
        """
        Return a queryset containing only the expired GenericTokenWithMetadata objects in
        the current queryset.
        """
        return self.filter(
            expiration_datetime__isnull=False,
            expiration_datetime__lt=_get_current_datetime())

    def filter_not_expired(self):
        """
        Return a queryset containing only the un-expired GenericTokenWithMetadata objects in
        the current queryset.
        """
        return self.filter(
            models.Q(expiration_datetime=None) |
            models.Q(expiration_datetime__gte=_get_current_datetime()))

    def filter_by_content_object(self, content_object):
        """
        Filter by :obj:`.GenericTokenWithMetadata.content_object`.

        Examples:
            Lets say the content_object is a User object, you
            can find all tokens for that user in the
            ``page_admin_invites`` app like this::

                from django.contrib.auth import get_user_model
                user = get_user_model()
                GenericTokenWithMetadata.objects\
                    .filter(app='page_admin_invites')\
                    .filter_by_content_object(user)
        """
        content_type = ContentType.objects.get_for_model(content_object)
        return self.filter(
            object_id=content_object.pk,
            content_type=content_type)

    def filter_usable_by_content_object_in_app(self, content_object, app):
        """
        Filters only non-expired tokens with the given ``content_object`` and ``app``.
        """
        return self.filter_not_expired()\
            .filter(app=app)\
            .filter_by_content_object(content_object)

    def filter_usable_by_content_type_in_app(self, content_type, app):
        """
        Filters only non-expired tokens with the given ``content_type`` and ``app``.
        """
        return self.filter_not_expired()\
            .filter(app=app)\
            .filter(content_type=content_type)

    def filter_by_content_type_and_id(self, content_type, object_id):
        return self.filter(
            object_id=object_id,
            content_type=content_type)

    def filter_usable_by_content_type_and_id_in_app(self, content_type, object_id, app):
        """
        Filters only non-expired tokens with the given ``content_type``, ``object_id`` and ``app``.
        """
        return self.filter_not_expired()\
            .filter(app=app)\
            .filter_by_content_type_and_id(content_type, object_id)


class GenericTokenWithMetadataBaseManager(models.Manager):
    """
    Manager for :class:`.GenericTokenWithMetadata`.

    Inherits all methods from :class:`.GenericTokenWithMetadataQuerySet`.
    """
    def generate(self, app, expiration_datetime, content_object, single_use=True, metadata=None,
                 method=generate_token, method_params=None):
        """
        Generate and save a token for the given user and app.

        Returns:
            A :class:`.GenericTokenWithMetadata` object with a token
            that is guaranteed to be unique.
        """
        if method_params is None:
            method_params = dict()
        token = method(**method_params)
        generic_token_with_metadata = GenericTokenWithMetadata(
            content_object=content_object, app=app, token=token,
            created_datetime=_get_current_datetime(), single_use=single_use,
            expiration_datetime=expiration_datetime)
        if metadata:
            generic_token_with_metadata.metadata = metadata

        try:
            generic_token_with_metadata.full_clean()
        except ValidationError as e:
            if 'token' in e.error_dict and e.error_dict['token'][0].code == 'unique':
                return self.generate(
                    app=app, content_object=content_object, expiration_datetime=expiration_datetime, metadata=metadata,
                    single_use=single_use, method=method, method_params=method_params
                )
            else:
                raise

        try:
            generic_token_with_metadata.save()
        except IntegrityError:
            return self.generate(
                app=app, content_object=content_object, expiration_datetime=expiration_datetime, metadata=metadata,
                single_use=single_use, method=method, method_params=method_params
            )
        else:
            return generic_token_with_metadata

    def generate_short_living_token(self, app, content_object, minutes=10, metadata=None, single_use=True, length=8):
        """
        Generate and save a short living token for the given object and app.

        Returns:
            A :class:`.GenericTokenWithMetadata` object with a token
            that is guaranteed to be unique.
        """
        return self.generate(app, timezone.now() + timedelta(minutes=minutes), content_object,
                             metadata=metadata, single_use=single_use,
                             method=generate_letter_digits_token, method_params=dict(length=length))

    def prolong_or_generate(self, app, delta_dict, content_object, single_use=True, metadata=None,
                            method=generate_token, method_params=None):
        """
        Prolong of generate and save a token for the given object and app.

        Returns:
            A :class:`.GenericTokenWithMetadata` object with a token
            that is guaranteed to be unique.
        """
        expiration_datetime = timezone.now() + timedelta(**delta_dict)
        token = self.filter_usable_by_content_object_in_app(content_object, app).first()
        if token:
            token.expiration_datetime = expiration_datetime
            token.save()
            return token

        return self.generate(app, expiration_datetime, content_object, single_use, metadata, method, method_params)

    def pop(self, app, token):
        """
        Get the :class:`.GenericTokenWithMetadata` matching the given
        `token` and `app`. Removes the GenericTokenWithMetadata from the database, and
        returns the `GenericTokenWithMetadata` object.

        Does not return expired tokens.

        Raises:
            GenericTokenWithMetadata.DoesNotExist: If no matching token is stored for the
                given app, or if the token is expired.
        """
        return self.filter_not_expired().unsafe_pop(app=app, token=token)

    def delete_expired(self):
        """
        Delete all expired tokens.
        """
        self.filter_has_expired().delete()

    @staticmethod
    def get_and_validate(app, token):
        """
        Get the given ``token`` for the given ``app``.

        Raises:
            GenericTokenWithMetadata.DoesNotExist: If the token does not exist.
            GenericTokenExpiredError: If the token has expired.
        """
        token = GenericTokenWithMetadata.objects.get(app=app, token=token)
        if token.is_expired():
            raise GenericTokenExpiredError('The token has expired.')
        return token


class GenericTokenWithMetadata(models.Model):
    """
    Provides a secure token with attached metadata suitable for
    email and sharing workflows like password reset, public share urls, etc.
    """
    objects = GenericTokenWithMetadataBaseManager.from_queryset(GenericTokenWithMetadataQuerySet)()

    #: The app that generated the token.
    #: You should set this to the name of the app the
    #: generated the token.
    app = models.CharField(db_index=True, max_length=255)

    #: A unique and random token, set it using :func:`.generate_token`.
    token = models.CharField(max_length=100, unique=True)

    #: Datetime when the token was created.
    created_datetime = models.DateTimeField(
        verbose_name=_('Created'))

    #: Datetime when the token expires.
    #: This can be `None`, which means that the token does not expire.
    expiration_datetime = models.DateTimeField(
        null=True, default=None, blank=True,
        verbose_name=_('Expires'))

    #: Single use?
    #: If this is `False`, the token can be used an unlimited number of
    #: times.
    single_use = models.BooleanField(default=True)

    #: JSON encoded metadata
    metadata = JSONField(null=False, blank=True, default=dict)

    #: The content-type of the :obj:`~.GenericTokenWithMetadata.content_object`.
    #: Together with :obj:`~.GenericTokenWithMetadata.object_id` this creates a
    #: generic foreign key to any Django model.
    content_type = models.ForeignKey(ContentType, on_delete=CASCADE)

    #: The object ID of the :obj:`~.GenericTokenWithMetadata.content_object`.
    #: Together with :obj:`~.GenericTokenWithMetadata.content_type` this creates a
    #: generic foreign key to any Django model.
    object_id = models.PositiveIntegerField()

    #: A :class:`django.contrib.contenttypes.fields.GenericForeignKey` to
    #: the object this token is for.
    #:
    #: This generic relationship is used to associate the token
    #: with a specific object.
    #:
    #: Use cases:
    #:
    #: - Password reset: Use the content_object to link to a User object when you
    #:   create password reset tokens.
    #: - Invites: Use the content_object to link to the object that you
    #:   are inviting users to. This enables you to filter on the
    #:   content object to show pending shares.
    content_object = GenericForeignKey('content_type', 'object_id')

    def is_expired(self):
        """
        Returns `True` if :obj:`.GenericTokenWithMetadata.expiration_datetime` is in the past,
        and `False` if it is in the future or now.
        """
        return self.expiration_datetime is not None and self.expiration_datetime < _get_current_datetime()
