from django.db import models as m
from django_client_framework.api import register_api_model
from django_client_framework.models import Serializable
from django_client_framework.serializers import ModelSerializer


@register_api_model
class Brand(Serializable):

    name = m.CharField(max_length=100, unique=True, null=True)

    @classmethod
    def serializer_class(cls):
        return BrandSerializer


class BrandSerializer(ModelSerializer):
    class Meta:
        model = Brand
        exclude = []
