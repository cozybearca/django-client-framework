from logging import getLogger

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery
from django.db import models as m
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from ..search_feature import SearchFeature

LOG = getLogger(__name__)


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
