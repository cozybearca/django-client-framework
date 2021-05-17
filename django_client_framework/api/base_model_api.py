from logging import getLogger

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.http.request import QueryDict
from django.utils.functional import cached_property
from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from django_client_framework.models.abstract import Searchable
from ipromise import overrides
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

LOG = getLogger(__name__)


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
    """base class for requests to /products or /products/1"""

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
        by_arr = by[0].split(",")
        try:
            return queryset.order_by(*by_arr)
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
