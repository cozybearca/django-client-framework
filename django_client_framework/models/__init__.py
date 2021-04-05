from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.postgres.fields import *
from django.db.models import *

from .abstract import (
    AccessControlled,
    Searchable,
    Serializable,
    delete_searchfeature_on_delete,
    update_searchfeature_on_change,
)
from .fields import PriceField, UniqueForeignKey
from .lookup import *


def check_integrity():
    from . import abstract

    abstract.check_integrity()
