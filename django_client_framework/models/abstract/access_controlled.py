from logging import getLogger

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models as m
from guardian.models import UserObjectPermission


LOG = getLogger(__name__)


class AccessControlled(m.Model):
    class Meta:
        abstract = True

    userobjectpermissions = GenericRelation(
        UserObjectPermission, object_id_field="object_pk"
    )

    class PermissionManager:
        def add_perms(self, instance):
            raise NotImplementedError()

        def reset_perms(self, instance):
            LOG.debug(f"resetting permission for {instance}")
            instance.userobjectpermissions.all().delete()
            self.add_perms(instance)

    @classmethod
    def get_permissionmanager_class(cls):
        """
        Returns an PermissionManager class. The default implementation looks for a class
        named PermissionManager in the current class.
        """
        manager = getattr(cls, "PermissionManager", None)
        if manager is None:
            raise NotImplementedError(
                f"{cls.__name__} does not define a nested class named PermissionManager."
            )
        if not issubclass(manager, AccessControlled.PermissionManager):
            raise NotImplementedError(
                f"{manager} should extend {AccessControlled.PermissionManager}"
            )
        if not hasattr(manager, "add_perms"):
            raise NotImplementedError(
                f"{manager} must implement add_perms(self, instance)"
            )

        return manager

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        self.get_permissionmanager_class()().reset_perms(self)
        return ret


def check_integrity():

    for model in AccessControlled.__subclasses__():
        model.get_permissionmanager_class()
