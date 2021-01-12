from decimal import Decimal

from django.db import models as m


class DecimalField(m.DecimalField):
    class Descriptor:
        def __init__(self, name):
            self.name = name

        def __set_name__(self, cls, name):
            self.name = name

        def __get__(self, instance, cls):
            return instance.__dict__[self.name]

        def __set__(self, instance, value):
            if type(value) is float:
                value = Decimal(str(value))
            elif type(value) is Decimal:
                pass
            elif value is None:
                pass
            else:
                value = Decimal(value)
            instance.__dict__[self.name] = value

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, DecimalField.Descriptor(name))


def PriceField(**kwargs):
    kwargs.setdefault("decimal_places", 2)
    kwargs.setdefault("max_digits", 10)
    return DecimalField(**kwargs)
