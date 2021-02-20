from logging import getLogger

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.models.fields import related_descriptors
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.http.request import QueryDict
from django.utils.functional import cached_property
from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from django_client_framework.models import Serializable
from django_client_framework.models.abstract import Searchable
from ipromise import overrides
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

LOG = getLogger(__name__)


def register_api_model(model_class):
    BaseModelAPI.models.append(model_class)
    return model_class


# see https://www.django-rest-framework.org/api-guide/pagination/
class ApiPagination(PageNumberPagination):
    page_query_param = "_page"
    page_size_query_param = "_limit"
    page_size = 50
    max_page_size = 1000

    @overrides(PageNumberPagination)
    def get_paginated_response(self, data):
        return Response(
            {
                "page": self.page.number,
                "limit": self.get_page_size(self.request),
                "total": self.page.paginator.count,
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "objects": data,
            }
        )


class BaseModelAPI(GenericAPIView):
    """ base class for requests to /products or /products/1 """

    pagination_class = ApiPagination
    models = []

    @cached_property
    def __name_to_model(self):
        return {model._meta.model_name: model for model in self.models}

    @overrides(APIView)
    def dispatch(self, request, *args, **kwargs):
        if request.method not in self.allowed_methods:
            raise MethodNotAllowed(request.method)
        return super().dispatch(request, *args, **kwargs)

    def get_request_data(self, request):
        if isinstance(request.data, QueryDict) or isinstance(request.data, dict):
            data = request.data.copy()
            excluded_keys = [
                "_limit",
                "_order_by",
                "_page",
                "_fulltext",
                "csrfmiddlewaretoken",
            ]
            for key in excluded_keys:
                data.pop(key, None)
            return data
        else:
            return request.data

    @cached_property
    def request_data(self):
        return self.get_request_data(self.request)

    def _filter_queryset_by_param(self, queryset):
        """
        Support generic filtering, eg: /products?name__in[]=abc&name__in[]=def
        """
        querydict = {}
        for key in self.request.query_params:
            if "[]" in key:
                querydict[key[:-2]] = self.request.query_params.getlist(key, [])
            elif key == "_fulltext" and (
                searchtext := self.request.query_params.get(key)
            ):
                if issubclass(self.model, Searchable):
                    queryset = self.model.filter_by_text_search(
                        searchtext, queryset=queryset
                    )
                else:
                    raise e.ValidationError(
                        f"{self.model.__name__} does not support full text search"
                    )
            elif key and key[0] != "_":  # ignore pagination keys
                val = self.request.query_params.get(key, None)
                if val == "true":
                    val = True
                elif val == "false":
                    val = False
                querydict[key] = val

        try:
            return queryset.filter(**querydict)
        except Exception as exept:
            raise e.ValidationError(exept)

    def _order_queryset_by_param(self, queryset):
        """
        Support generic filtering, eg: /products?_order_by=name
        """
        by = self.request.query_params.getlist("_order_by", ["pk"])
        try:
            return queryset.order_by(*by)
        except Exception as execpt:
            raise e.ValidationError(execpt)

    @overrides(GenericAPIView)
    def filter_queryset(self, queryset):
        return self._order_queryset_by_param(
            self._filter_queryset_by_param(
                p.filter_queryset_by_perms_shortcut("r", self.user_object, queryset)
            )
        )

    @cached_property
    def model(self):
        model_name = self.kwargs["model"]
        if model_name not in self.__name_to_model:
            valid_models = ", ".join(self.__name_to_model.keys())
            raise e.ValidationError(
                f"{model_name} is not a valid model. Valid models are: {valid_models or []}"
            )
        return self.__name_to_model[model_name]

    def get_model_field(self, key, default=None):
        try:
            return self.model._meta.get_field(key)
        except FieldDoesNotExist:
            return default

    @cached_property
    def model_object(self):
        pk = self.kwargs["pk"]
        return get_object_or_404(self.model, pk=pk)

    @overrides(GenericAPIView)
    def get_serializer_class(self):
        return self.model.serializer_class()

    @overrides(GenericAPIView)
    def get_queryset(self, *args, **kwargs):
        return self.model.objects.all()

    def _deny_permission(self, required_perm, object, field_name=None):
        objname = f"{object._meta.model_name} object {object.pk}"
        shortcuts = {
            "r": "read",
            "w": "write",
            "c": "create",
            "d": "delete",
        }
        if p.has_perms_shortcut(self.user_object, object, "r"):
            if field_name:
                raise e.PermissionDenied(
                    f"You have no {shortcuts[required_perm]} permission on {objname}'s {field_name} field."
                )
            else:
                raise e.PermissionDenied(
                    f"You have no {shortcuts[required_perm]} permission on {objname}."
                )
        else:
            raise e.NotFound(f"{objname} cannot be found.")

    @cached_property
    def user_object(self):
        """
        DRF does not know about django-guardian's Anynymous user instance.
        This is a helper method to get the django-guardian version of user
        instances.
        """
        if self.request.user.is_anonymous:
            return get_user_model().get_anonymous()
        else:
            return self.request.user


class ModelCollectionAPI(BaseModelAPI):
    """ handle request such as GET/POST /products """

    allowed_methods = ["GET", "POST"]

    @overrides(APIView)
    def check_permissions(self, request):
        if request.method == "POST":
            if not p.has_perms_shortcut(self.user_object, self.model, "c"):
                raise e.PermissionDenied("You have no permission to perform POST.")

    def get(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginator.paginate_queryset(queryset, self.request, view=self)
        return self.paginator.get_paginated_response([obj.json() for obj in page])

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=self.request_data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        # make sure user write permission to related fields
        for field_name, field_instance in serializer.validated_data.items():
            model_field = self.get_model_field(field_name)
            if model_field and isinstance(model_field, ForeignKey) and field_instance:
                related_name = model_field.related_query_name()
                if not p.has_perms_shortcut(
                    self.user_object, field_instance, "w", field_name=related_name
                ):
                    self._deny_permission("w", field_instance, related_name)

        instance = serializer.save()
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
                    "info": "The object has been created but you have no permission to view it.",
                },
                status=201,
            )


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

        return Response(serializer.data)

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


class ModelFieldAPI(BaseModelAPI):
    """ handle requests such as GET/POST/PUT /products/1/images """

    @property
    def allowed_methods(self):
        if isinstance(self.field, ForeignKey):
            return ["GET"]
        else:
            return ["GET", "DELETE", "POST", "PUT"]

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
        filtered = p.filter_queryset_by_perms_shortcut("w", self.user_object, queryset)
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
        self.field_val.add(*self.__body_pk_ls)
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
        self.field_val.remove(*self.__body_pk_ls)
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


def check_integrity():
    for model in BaseModelAPI.models:
        if not issubclass(model, Serializable):
            raise TypeError(f"model {model} must inherit Serializable")
