from logging import getLogger

from django.conf import settings
from django.core.cache import cache
from django.db import models as m
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

LOG = getLogger(__name__)


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


def check_integrity():
    from ...serializers import Serializer, DelegateSerializer

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
