from rest_framework import serializers as s


class TypedSerializerMethodField(s.SerializerMethodField):
    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop("type")
        super().__init__(*args, **kwargs)
