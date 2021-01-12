from logging import getLogger

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery
from django.core.cache import cache
from django.db import models as m
from django.db.backends.signals import connection_created
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils.functional import cached_property
from guardian.models import UserObjectPermission

from .search_feature import SearchFeature

LOG = getLogger(__name__)


# install jieba extension
@receiver(connection_created)
def install_jieba_extension(sender, connection, **kwargs):
    cursor = connection.cursor()
    cursor.execute("create extension if not exists pg_jieba")


class Serializable(m.Model):
    class Meta:
        abstract = True

    @classmethod
    def serializer_class(cls):
        raise NotImplementedError(f"{cls} must implement .serializer_class()")

    @property
    def serializer(self):
        return self.serializer_class()(instance=self)

    @property
    def cached_serialized_data(self):
        return self.get_or_create_cached_serialization()

    def json(self):
        return self.serializer_class()(instance=self).data

    def __repr__(self):
        if settings.DEBUG:
            return f"<<{self.__class__.__name__}:{self.serializer_class()(instance=self).data}>>"
        else:
            return f"<{self.__class__.__name__}:{self.pk}>"

    def __str__(self):
        return f"<{self.__class__.__name__}:{self.pk}>"

    def get_serialization_cache_timeout(self):
        return 3600 * 24 * 7

    def get_or_create_cached_serialization(self):
        result = cache.get(self.cache_key_for_serialization, None)
        if result:
            return result
        else:
            ser = self.serializer_class()(instance=self)
            cache.add(
                self.cache_key_for_serialization,
                ser.data,
                timeout=self.get_serialization_cache_timeout(),
            )
            return ser.data

    @cached_property
    def cache_key_for_serialization(self):
        return f"serialization_{self._meta.model_name}_{self.pk}"

    def invalidate_serialization_cache(self):
        cache.delete(self.cache_key_for_serialization)


@receiver(post_save)
def auto_invalidate_cached_serialization_post_save(sender, instance, created, **kwargs):
    if not created and isinstance(instance, Serializable):
        LOG.debug(f"invalidate cache for {instance}")
        instance.invalidate_serialization_cache()


@receiver(post_delete)
def auto_invalidate_cached_serialization_post_delete(sender, instance, **kwargs):
    if isinstance(instance, Serializable):
        LOG.debug(f"delete cache for {instance}")
        instance.invalidate_serialization_cache()


class Searchable(m.Model):
    class Meta:
        abstract = True

    def get_text_feature(self):
        raise NotImplementedError()

    def __get_text_feature(self):
        # Need to reset @cached_property otherwise auto-update won't work
        new_self = self.__class__.objects.get(pk=self.pk)
        text = new_self.get_text_feature()
        if type(text) is not str:
            raise TypeError(
                f".get_text_feature() must return a str, instead of {type(text)}"
            )
        return text

    search_feature = GenericRelation(SearchFeature)

    @classmethod
    def filter_by_text_search(cls, search_text, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()

        search_text = search_text.strip()

        if not search_text:
            raise ValueError(
                "search_text cannot be empty string or only contain spaces."
            )

        pk_set = set(
            SearchFeature.objects.filter(
                content_type=ContentType.objects.get_for_model(cls)
            )
            .filter(
                m.Q(search_vector=SearchQuery(search_text, config="jiebacfg"))
                | m.Q(text_feature__icontains=search_text)
            )
            .values_list("object_id", flat=True)
        )
        return queryset.filter(pk__in=pk_set)

    def get_or_create_searchfeature(self):
        return SearchFeature.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            defaults={"text_feature": self.__get_text_feature()},
        )

    def update_or_create_searchfeature(self):
        return SearchFeature.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            defaults={"text_feature": self.__get_text_feature()},
        )

    @classmethod
    def update_all_search_feature(cls):
        for instance in cls.objects.all():
            instance.update_or_create_searchfeature()


@receiver(post_save)
def update_searchfeature_on_change(sender, instance, **kwargs):
    """
    When a Searchable object is created or updated, we need to update its related
    SearchFeature in order to update the search index.
    """
    if isinstance(instance, Searchable):
        LOG.debug(f"{sender=} {instance=}")
        instance.update_or_create_searchfeature()


@receiver(post_delete)
def delete_searchfeature_on_delete(sender, instance, **kwargs):
    if isinstance(instance, Searchable):
        LOG.debug(f"{sender=} {instance=}")
        instance.search_feature.all().delete()


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
    from django_client_framework.serializers import DelegateSerializer, Serializer

    for model in AccessControlled.__subclasses__():
        model.get_permissionmanager_class()

    for model in Serializable.__subclasses__():
        if model.__module__ == "__fake__":
            break
        if Serializable not in model.__bases__:
            break
        if m.Model not in model.__bases__:
            break
        i = model.__bases__.index(Serializable)
        j = model.__bases__.index(m.Model)
        if i > j:
            raise AssertionError(
                f"{model} must extend {Serializable} before {m.Model}, current order: {model.__bases__}"
            )

    for model in Serializable.__subclasses__():
        sercls = model.serializer_class()
        if not (
            issubclass(sercls, Serializer) or issubclass(sercls, DelegateSerializer)
        ):
            raise NotImplementedError(
                f"{model}.serializer_class() does not return a Serialzer class "
            )
