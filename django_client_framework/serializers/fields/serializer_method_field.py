from deps.drf_jsonschema.convert import field_to_jsonschema
from deps.drf_jsonschema.converters import converter
from rest_framework import serializers as s


class TypedSerializerMethodField(s.SerializerMethodField):
    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop("type")
        super().__init__(*args, **kwargs)


@converter
class TypedSerializerMethodFieldFieldConverter:
    field_class = TypedSerializerMethodField

    def convert(self, field):
        return field_to_jsonschema(field.type)
