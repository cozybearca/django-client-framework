import logging

from django_client_framework import models as m
from django_client_framework.api import register_api_model
from django_client_framework.models import AccessControlled, Serializable
from django_client_framework.permissions import set_perms_shortcut, default_groups
from django_client_framework.serializers import ModelSerializer

from .brand import Brand

LOG = logging.getLogger(__name__)


@register_api_model
class Product(Serializable, AccessControlled):

    barcode = m.CharField(max_length=255, blank=True, default="")
    brand = m.ForeignKey(
        Brand, null=True, on_delete=m.SET_NULL, related_name="products"
    )

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, product):
            set_perms_shortcut(default_groups.anyone, product, "r")

    @classmethod
    def serializer_class(cls):
        return ProductSerializer


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        exclude = []
