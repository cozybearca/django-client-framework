from logging import getLogger

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models as m
from django.db import transaction
from django.db.models.base import ModelBase
from guardian import models as gm
from guardian import shortcuts as gs
from deprecation import deprecated
from . import default_groups

LOG = getLogger(__name__)


def get_permission_for_model(
    shortcut, model, string=False, app_label=True, field_name=None
):
    """
    Returns permission object for model and field.
    If string is True, then returns the Permission object's full codename as string.
    """
    action_shortcuts = {
        "r": "view",
        "w": "change",
        "c": "add",
        "d": "delete",
    }
    action = action_shortcuts[shortcut]
    c = ContentType.objects.get_for_model(model, for_concrete_model=False)
    if field_name:
        if not model._meta.get_field(field_name):
            raise AttributeError(
                f'field named "{field_name}" not found on model {model}'
            )
        p, _created = Permission.objects.get_or_create(
            content_type=c, codename=f"{action}_{model._meta.model_name}__{field_name}"
        )
    else:
        p, _created = Permission.objects.get_or_create(
            content_type=c, codename=f"{action}_{model._meta.model_name}"
        )
    if string:
        if app_label:
            return f"{c.app_label}.{p.codename}"
        else:
            return p.codename
    else:
        return p


def filter_queryset_by_perms_shortcut(perms, user_or_group, queryset, field_name=None):
    """
    Filters queryset by keeping objects that user_or_group has all permissions
    specified by perms. If field_name is specified, additionally include objects
    that user_or_group has field permission on.

    Warning: Different from has_perms_shortcut(), this function accounts for the
    special "anyone" group. If a permission is set on the "anyone" group, then
    filter_queryset_by_perms_shortcut() views any group or user has that
    permission. On the other hand, has_perms_shortcut() ignores the "anyone"
    group's permission.

    Algorithm:
        perms: rwcd \in {0,1}^4
        with/no field: f \in {0,1}
        normal/anyone user: u \in {0,1}
        A0 = filter with rwcd mask, f=0
        A1 = filter with rwcd mask, f=1
        B0 = A0 union A1, g=0
        B1 = A0 union A1, g=1
        B0 union B1
    """
    union = queryset.model.objects.none()
    for u in set([user_or_group, default_groups.anyone]):  # B
        for f in set([None, field_name]):  # A
            perm_full_strs = [
                get_permission_for_model(s, queryset.model, string=True, field_name=f)
                for s in perms.lower()
            ]
            union |= (
                gs.get_objects_for_group
                if isinstance(u, Group)
                else gs.get_objects_for_user
            )(
                u,
                perms=perm_full_strs,
                accept_global_perms=True,
                any_perm=False,
                klass=queryset,  # filter
            )
    return union


def set_perms_shortcut(
    user_or_group, model_or_instance_or_queryset, perms, field_name=None
):
    """
    Adds model or object permission depending on whether model_or_instance_or_queryset
    is a model.
    """
    LOG.debug(f"{user_or_group=} {model_or_instance_or_queryset=} {perms=}")

    if isinstance(model_or_instance_or_queryset, m.Model):
        instance = model_or_instance_or_queryset
        model = instance.__class__
    elif isinstance(model_or_instance_or_queryset, m.QuerySet):
        instance = model_or_instance_or_queryset
        model = model_or_instance_or_queryset.model
    elif model_or_instance_or_queryset.__class__ is ModelBase:
        instance = None
        model = model_or_instance_or_queryset
    else:
        raise TypeError(
            f"model_or_instance_or_queryset has wrong type: {type(model_or_instance_or_queryset)}"
        )

    for s in perms.lower():
        permstr = get_permission_for_model(s, model, string=True, field_name=field_name)
        gs.assign_perm(permstr, user_or_group, obj=instance)


def has_perms_shortcut(
    user_or_group, model_or_instance, perms, field_name=None, field=None
):
    """
    Check if user has all permissions indicated by perms. If field_name is provided,
    then checks wheather user has permission on that field. model permission implies
    object permission implies field permission. Permission check is permissive. Returns
    True as long as one of model or object permission is permitted.
    """
    User = get_user_model()

    if isinstance(model_or_instance, m.Model):
        instance = model_or_instance
        model = instance._meta.model
    elif model_or_instance.__class__ is ModelBase:
        instance = None
        model = model_or_instance
    else:
        raise TypeError(f"model_or_instance has wrong type: {type(model_or_instance)}")

    if field:
        field_name = field.name

    if isinstance(user_or_group, User) and user_or_group.is_superuser:
        return True

    def disjunction(s):
        for f in [None, field_name]:
            perm = get_permission_for_model(s, model, field_name=f)
            if isinstance(user_or_group, Group):
                # check group model permission
                if user_or_group.permissions.filter(pk=perm.pk).exists():
                    yield True
                # check group object permission
                if (
                    instance
                    and gm.GroupObjectPermission.objects.filter(
                        group=user_or_group,
                        permission=perm,
                        content_type=perm.content_type,
                        object_pk=instance.pk,
                    ).exists()
                ):
                    yield True
            else:
                # check user model permission
                name = f"{perm.content_type.app_label}.{perm.codename}"
                if user_or_group.has_perm(name):
                    yield True
                # check user object permission
                if user_or_group.has_perm(name, instance):
                    yield True
        yield False

    def conjunction():
        for s in perms.lower():
            if any(disjunction(s)):
                yield True
            else:
                yield False

    return all(conjunction())


def clear_permissions():
    LOG.info("clearing permissions...")
    with transaction.atomic():
        Permission.objects.all().delete()
        gm.UserObjectPermission.objects.all().delete()
        gm.GroupObjectPermission.objects.all().delete()
        # We need the logged_in group to survive migration, otherwise users who are using
        # the site when the migration happens would see permission errors after migration.
        Group.objects.exclude(m.Q(name="anyone") | m.Q(name="logged_in")).delete()


def reset_permissions():
    with transaction.atomic():
        LOG.info("resetting permissions...")

        clear_permissions()
        LOG.info("recreating permissions...")

        # reset user permissions
        from .default_groups import default_groups
        from .default_users import default_users

        default_groups.setup()
        default_users.setup()
        # set user self permission
        # must be done after all default users are added
        from django_client_framework.models import AccessControlled

        for model in AccessControlled.__subclasses__():
            permmanager = model.get_permissionmanager_class()()
            for instance in model.objects.all():
                permmanager.reset_perms(instance)


@deprecated(details="use reset_permissions()")
def setup_permissions():
    reset_permissions()
