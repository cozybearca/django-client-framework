
from django_client_framework.models import Serializable, AccessControlled
from django_client_framework.serializers import ModelSerializer
from django_client_framework.permissions import default_groups, set_perms_shortcut
from django_client_framework.api import register_api_model
from django.db.models import CharField


@register_api_model
class Product(Serializable, AccessControlled):
    barcode = CharField(max_length=32)

    @classmethod
    def serializer_class(cls):
        return ProductSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, product):
            set_perms_shortcut(default_groups.anyone, product, "r")


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        exclude = []