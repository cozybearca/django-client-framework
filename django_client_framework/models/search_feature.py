from logging import getLogger

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres import search as s
from django.contrib.postgres.indexes import GinIndex
from django.db import models as m
from django.dispatch import receiver

LOG = getLogger(__name__)


class SearchFeature(m.Model):
    content_type = m.ForeignKey(ContentType, on_delete=m.CASCADE, null=True)
    object_id = m.PositiveIntegerField(null=True, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    text_feature = m.TextField()
    search_vector = s.SearchVectorField()

    class Meta:
        unique_together = index_together = ["object_id", "content_type"]
        indexes = [GinIndex(fields=["search_vector"])]


@receiver(m.signals.post_save, sender=SearchFeature)
def auto_update_search_vector(sender, instance, *args, **kwargs):
    """Keep the index up-to-date automatically"""
    LOG.debug(f"{sender=} {instance=}")
    sender.objects.filter(pk=instance.pk).update(
        # use jiebaqry to maximize number of terms
        search_vector=s.SearchVector("text_feature", config="jiebaqry")
    )
