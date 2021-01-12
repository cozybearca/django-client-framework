from django.db import models as m
from django.db.models.fields.related import ReverseOneToOneDescriptor


class UniqueForeignKey(m.OneToOneField):
    """
    This class fix django's OneToOneField's historical problem, where accessing
    through the reverse relation when the object does not exist would raise an
    ObjectDoesNotExist exception, instead of simply returning None.
    """

    class FixReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
        def __get__(self, *args, **kwargs):
            try:
                return super().__get__(*args, **kwargs)
            except m.ObjectDoesNotExist:
                return None

    related_accessor_class = FixReverseOneToOneDescriptor
