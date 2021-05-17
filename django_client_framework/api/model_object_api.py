from logging import getLogger

from django.db.models.deletion import ProtectedError
from django.db.models.fields.related import ForeignKey
from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from ipromise import overrides
from rest_framework.response import Response
from rest_framework.views import APIView
from .base_model_api import BaseModelAPI

LOG = getLogger(__name__)


class ModelObjectAPI(BaseModelAPI):
    """ handle requests such as GET/DELETE/PATCH /products/1 """

    allowed_methods = ["GET", "DELETE", "PATCH"]

    @overrides(APIView)
    def check_permissions(self, request):
        pass

    @overrides(APIView)
    def check_object_permissions(self, request, obj):
        pass

    def get(self, request, *args, **kwargs):
        if not p.has_perms_shortcut(self.user_object, self.model_object, "r"):
            self._deny_permission("r", self.model_object)
        serializer = self.get_serializer(
            self.model_object,
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        # permission check deferred to .perform_update()
        instance = self.model_object
        has_read_permissions = False
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            has_read_permissions = True

        serializer = self.get_serializer(instance, data=self.request_data, partial=True)
        if not serializer.is_valid(raise_exception=True):
            raise e.ValidationError("Validation Error")
        # User can have either write permission to model, object, or to a field
        # check permission for related objects
        for field_name, field_val in serializer.validated_data.items():
            field = self.get_model_field(field_name, None)
            if not field:
                continue
            if not p.has_perms_shortcut(
                self.user_object, self.model_object, "w", field_name
            ):
                self._deny_permission("w", self.model_object, field_name)
            if isinstance(field, ForeignKey):
                old_related_obj = getattr(self.model_object, field_name, None)
                new_related_obj = field_val
                for related_obj in filter(
                    bool, [old_related_obj, new_related_obj]
                ):  # remove None
                    if not p.has_perms_shortcut(
                        self.user_object,
                        related_obj,
                        "w",
                        field_name=field.related_query_name(),
                    ):
                        if p.has_perms_shortcut(
                            self.user_object,
                            related_obj,
                            "r",
                            field_name=field.related_query_name(),
                        ):
                            raise e.PermissionDenied(
                                f"To change related field {field_name},"
                                f" you need write permission on object {related_obj.pk}.",
                            )
                        else:
                            raise e.NotFound(
                                f"Related object {related_obj.pk} does not exist."
                            )
        # when permited
        serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # return Response(serializer.data)
        if has_read_permissions:
            p.add_perms_shortcut(self.user_object, instance, "r")
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            return Response(
                self.get_serializer(
                    instance=instance,
                    context={"request": request},
                ).data,
                status=201,
            )
        else:
            return Response(
                {
                    "success": True,
                    "info": "The object has been updated but you have no permission to view it.",
                },
                status=201,
            )

    def delete(self, request, *args, **kwargs):
        if not p.has_perms_shortcut(self.user_object, self.model_object, "d"):
            self._deny_permission("d", self.model_object)
        try:
            if hasattr(self.get_serializer_class(), "delete"):
                serializer = self.get_serializer(
                    data=self.request_data,
                    instance=self.model_object,
                    context={"request": request},
                )
                serializer.is_valid(raise_exception=True)
                serializer.delete()
            else:
                self.model_object.delete()
        except ProtectedError as excpt:
            raise e.ValidationError(excpt)
        else:
            return Response(status=204)
