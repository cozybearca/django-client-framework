from logging import getLogger

from django.db.models.fields import related_descriptors
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.utils.functional import cached_property
from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from ipromise import overrides
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .base_model_api import BaseModelAPI

LOG = getLogger(__name__)


class RelatedModelAPI(BaseModelAPI):
    """ handle requests such as GET/POST/PUT /products/1/images """

    @property
    def allowed_methods(self):
        if isinstance(self.field, ForeignKey):
            return ["GET", "PATCH"]
        else:
            return ["GET", "DELETE", "POST", "PATCH"]

    @cached_property
    def __body_pk_ls(self):
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
                f" but received {type(data)}: {data}"
            )

    def __check_write_perm_on_rel_objects(self, queryset=None):
        filtered = p.filter_queryset_by_perms_shortcut("w", self.user_object, queryset, self.reverse_field_name)
        no_write = queryset.difference(filtered).values_list("pk")

        if no_write:
            has_read = p.filter_queryset_by_perms_shortcut(
                "r", self.user_object, queryset.model.objects.filter(pk__in=no_write)
            )
            if has_read.exists():
                raise e.PermissionDenied(
                    f"You have no write permission on objects {list(has_read.values_list('pk'))}"
                )
            else:
                raise e.NotFound()

    def __return_get_result_if_permitted(self, request, *args, **kwargs):
        if p.has_perms_shortcut(self.user_object, self.model_object, "r"):
            return self.get(request, *args, **kwargs)
        else:
            return Response({"success": True})

    def __check_perm_on_field(self, instance, perm, field_name):
        if not p.has_perms_shortcut(self.user_object, instance, perm, field_name):
            self._deny_permission(perm, instance, field_name)

    def get(self, request, *args, **kwargs):
        self.__check_perm_on_field(self.model_object, "r", self.field_name)
        if isinstance(self.field, ForeignKey):
            if self.field_val:
                self.__check_perm_on_field(
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
        self.__check_perm_on_field(self.model_object, "w", self.field_name)
        self.__check_write_perm_on_rel_objects(
            self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        )
        
        selected = list(self.field_model.objects.filter(id__in=self.__body_pk_ls))
        for selected_product in selected:
            self.field_val.add(selected_product)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        self.__check_perm_on_field(self.model_object, "w", self.field_name)
        self.__check_write_perm_on_rel_objects(
            self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        )
        self.__check_write_perm_on_rel_objects(queryset=self.field_val.all())
        objects = self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        self.field_val.set(objects)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        self.__check_perm_on_field(self.model_object, "w", self.field_name)
        self.__check_write_perm_on_rel_objects(
            self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        )
        if isinstance(self.field, ManyToOneRel):
            self.__check_write_perm_on_rel_objects(queryset=self.field_val.all())
            selected = list(self.field_model.objects.filter(id__in=self.__body_pk_ls))
            self.field_val.set(selected)
        else:
            self.__check_write_perm_on_rel_objects(
                self.field_model.objects.filter(pk__in=[self.field_val.id])
            )
            # assuming there is only one id passed because this is OneToOne not ManyToOne Rel
            new_val = list(self.field_model.objects.filter(pk__in=self.__body_pk_ls))[0]
            setattr(self.model_object, self.field_name, new_val)
            self.model_object.save()
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.__check_perm_on_field(self.model_object, "w", self.field_name)
        self.__check_write_perm_on_rel_objects(
            self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        )
        if not hasattr(self.field_val, "remove"):
            raise e.ValidationError(
                f"Cannot remove {self.field_name} from {self.model.__name__} due to non-null constraints."
                " Did you mean to delete the object directly?"
            )
        selected = list(self.field_model.objects.filter(id__in=self.__body_pk_ls))
        for selected_product in selected:
            try:
                self.field_val.remove(selected_product)
            except:
                continue
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

    @cached_property
    def field_val(self):
        return getattr(self.model_object, self.field_name)

    @cached_property
    def field_model(self):
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
