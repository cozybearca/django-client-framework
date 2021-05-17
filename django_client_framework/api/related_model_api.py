from logging import getLogger
from typing import List, Optional
from django.db.models import Model

from django.db.models.fields import related_descriptors
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.db.models.query import QuerySet
from django.http.response import JsonResponse
from django.utils.functional import cached_property
from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from ipromise import overrides
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .base_model_api import APIPermissionDenied, BaseModelAPI

LOG = getLogger(__name__)


class RelatedModelAPI(BaseModelAPI):
    """handle requests such as GET/POST/PUT /products/1/images"""

    @property
    def allowed_methods(self):
        if self.is_related_object_api:
            return ["GET", "PATCH"]
        else:
            return ["GET", "DELETE", "POST", "PATCH"]

    @cached_property
    def __body_pk_ls(self) -> List[int]:
        data = self.request_data
        if isinstance(data, list):
            if len(data) > 0:
                for item in data:
                    if type(item) is not int:
                        raise e.ValidationError(
                            "Expected a list of model pk in the request body,"
                            f" but one of the list item received is {type(item)}: {item}"
                        )
            return data
        else:
            raise e.ValidationError(
                "Expected a list of object pk in the request body,"
                f" but received {type(data).__name__}: {data}"
            )

    @cached_property
    def __body_pk(self) -> Optional[int]:
        data = self.request_data
        if data is None or isinstance(data, int):
            return data
        else:
            raise e.ValidationError(
                "Expected an object pk in the request body,"
                f" but received {type(data).__name__}: {data}"
            )

    @cached_property
    def __body_pk_queryset(self):
        """Returns the QuerySet from pks in the request body."""
        if self.is_related_object_api:
            if self.__body_pk is None:
                queryset = QuerySet(self.field_model)
            else:
                queryset = self.field_model.objects.filter(pk=self.__body_pk)
        else:
            queryset = self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        return queryset

    @cached_property
    def __field_val_queryset(self):
        if self.is_related_object_api:
            if self.field_val is None:
                return QuerySet(model=self.field_model)
            else:
                return self.field_model.objects.filter(pk=self.field_val.pk)
        else:
            return self.field_val.all()

    def __assert_write_perm_for_rel_objects(self, queryset=None):
        find_has_write = p.filter_queryset_by_perms_shortcut(
            "w", self.user_object, queryset, self.reverse_field_name
        )
        find_no_write = queryset.difference(find_has_write).first()
        if find_no_write:
            raise APIPermissionDenied(find_no_write, "w")

    def __return_get_result_if_permitted(self, request, *args, **kwargs):
        if p.has_perms_shortcut(
            self.user_object, self.model_object, "r", field_name=self.field_name
        ):
            return self.get(request, *args, **kwargs)
        else:
            return JsonResponse(
                {
                    "detail": "Action was successful but you have no permission to view the result."
                },
            )

    def __assert_object_field_perm(self, instance: Model, perm: str, field_name: str):
        if not p.has_perms_shortcut(
            self.user_object, instance, perm, field_name=field_name
        ):
            raise APIPermissionDenied(instance, perm, field_name)

    def get(self, request, *args, **kwargs):
        self.__assert_object_field_perm(self.model_object, "r", self.field_name)
        if self.is_related_object_api:
            if self.field_val:
                self.__assert_object_field_perm(
                    self.field_val, "r", self.field.related_query_name()
                )
                serializer = self.get_serializer(
                    self.field_val,
                    context={"request": self.request},
                )
                return Response(serializer.data)
            else:
                raise e.NotFound()
        else:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginator.paginate_queryset(queryset, self.request, view=self)
            return self.paginator.get_paginated_response(
                [obj.cached_serialized_data for obj in page]
            )

    def post(self, request, *args, **kwargs):
        self.assert_pks_exist_or_raise_404(self.field_model, self.__body_pk_ls)
        self.__assert_object_field_perm(self.model_object, "w", self.field_name)
        self.__assert_write_perm_for_rel_objects(self.__body_pk_queryset)
        self.field_val.add(*self.__body_pk_queryset)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch_related_object(self, request, *args, **kwargs):
        if self.__body_pk is not None:
            self.assert_pks_exist_or_raise_404(self.field_model, [self.__body_pk])
        self.__assert_write_perm_for_rel_objects(self.__body_pk_queryset)
        self.__assert_write_perm_for_rel_objects(self.__field_val_queryset)
        setattr(self.model_object, self.field_name, self.__body_pk_queryset.first())
        self.field_val.save()
        self.model_object.save()
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch_related_collection(self, request, *args, **kwargs):
        self.assert_pks_exist_or_raise_404(self.field_model, self.__body_pk_ls)
        diff_remove = self.__field_val_queryset.difference(self.__body_pk_queryset)
        diff_add = self.__body_pk_queryset.difference(self.__field_val_queryset)
        # Django doesn't support calling .filter() after .union() and
        # .difference()
        symmetric_diff = diff_add.union(diff_remove).values_list("pk")
        queryset = self.field_model.objects.filter(pk__in=symmetric_diff)
        self.__assert_write_perm_for_rel_objects(queryset)
        self.field_val.set(self.__body_pk_queryset)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.__assert_object_field_perm(self.model_object, "w", self.field_name)
        if self.is_related_object_api:
            return self.patch_related_object(request, *args, **kwargs)
        else:
            return self.patch_related_collection(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.__assert_object_field_perm(self.model_object, "w", self.field_name)
        self.__assert_write_perm_for_rel_objects(self.__body_pk_queryset)
        if not hasattr(self.field_val, "remove"):
            raise e.ValidationError(
                f"Cannot remove {self.field_name} from {self.model.__name__} due to non-null constraints."
            )
        # silently ignore invalid pks
        selected_products = self.field_model.objects.filter(
            id__in=self.__body_pk_ls
        ).intersection(self.field_val.all())
        self.field_val.remove(*selected_products)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    @cached_property
    def field_name(self):
        field_name = self.kwargs["target_field"]
        self.check_field_name(field_name)
        return field_name

    def check_field_name(self, field_name):
        # only when related_name is set on field, the field becomes a key on
        # model, otherwise it becomes fieldname_set
        if not hasattr(self.model, field_name):
            raise e.ValidationError(
                f'"{field_name}" is not a property name on {self.model.__name__}'
            )
        target_field = self.get_model_field(field_name, None)
        if (
            target_field
            and any(
                [
                    isinstance(target_field, valid_rel)
                    for valid_rel in [
                        ManyToManyRel,
                        ManyToManyField,
                        ManyToOneRel,
                        ForeignKey,
                    ]
                ]
            )
            and any(
                [
                    isinstance(getattr(self.model, field_name, None), valid_rel)
                    for valid_rel in [
                        related_descriptors.ForwardManyToOneDescriptor,
                        related_descriptors.ForwardOneToOneDescriptor,
                        related_descriptors.ReverseOneToOneDescriptor,
                        related_descriptors.ReverseManyToOneDescriptor,
                        related_descriptors.ManyToManyDescriptor,
                    ]
                ]
            )
        ):
            return field_name
        else:
            raise e.ValidationError(
                f"Property {field_name} on {self.model.__name__} is not a valid relation."
            )

    @cached_property
    def field(self):
        return self.model._meta.get_field(self.field_name)

    @property
    def field_val(self):
        return getattr(self.model_object, self.field_name)

    @cached_property
    def field_model(self) -> Model:
        return self.field.related_model

    @cached_property
    def reverse_field_name(self):
        if isinstance(self.field, ManyToOneRel):
            temp = getattr(self.model, self.field_name)
            return temp.rel.remote_field.name
        else:
            temp = getattr(self.model, self.field_name)
            return temp.field.related_query_name()

    @overrides(GenericAPIView)
    def get_serializer_class(self):
        return self.field_model.serializer_class()

    @overrides(GenericAPIView)
    def get_queryset(self, *args, **kwargs):
        return self.field_val.all()

    @overrides(GenericAPIView)
    def get_object(self, *args, **kwargs):
        raise NotImplementedError()

    @overrides(APIView)
    def check_permissions(self, request):
        return True

    @overrides(APIView)
    def check_object_permissions(self, request, obj):
        raise NotImplementedError()

    @cached_property
    def is_related_object_api(self):
        return isinstance(self.field, ForeignKey)

    @cached_property
    def is_related_collection_api(self):
        return not isinstance(self.field, ForeignKey)
