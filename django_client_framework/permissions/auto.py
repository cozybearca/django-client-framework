from logging import getLogger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.signals import request_finished
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_currentuser.middleware import _set_current_user

from .default_groups import default_groups

LOGGER = getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def auto_add_user_to_anyone_group(sender, instance, created, **kwargs):
    if created and instance != get_user_model().get_anonymous():
        default_groups.anyone.user_set.add(instance)


@receiver(request_finished)
def auto_clear_current_user_middleware_after_request(*args, **kwargs):
    _set_current_user(None)


@receiver(user_logged_in)
def auto_add_user_to_logged_in_group(user, **kwargs):
    LOGGER.debug(f"user {user} logged in")
    user.groups.add(default_groups.logged_in)


@receiver(user_logged_out)
def auto_remove_user_from_logged_in_group(user, **kwargs):
    if user:
        LOGGER.debug(f"user {user} logged out")
        user.groups.remove(default_groups.logged_in)
