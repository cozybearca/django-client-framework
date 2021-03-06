# from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from rest_framework.exceptions import APIException, ValidationError


def transform_drf_exception(exc, current_field=None):
    if isinstance(exc, APIException):
        return transform_drf_exception(exc.detail, current_field)
    elif isinstance(exc, str):
        return {current_field or "non_field_error": exc}
    elif isinstance(exc, dict):
        collect = {}
        for field, val in exc.items():
            collect.update(transform_drf_exception(val, field))
        return collect
    elif isinstance(exc, list):
        collect = {}
        for val in exc:
            collect.update(transform_drf_exception(val, current_field))
        return collect
    else:
        raise NotImplementedError(f"Unable to handle {exc.__repr__()}")


def dcf_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        flatten = transform_drf_exception(exc)
        return JsonResponse(flatten, status=400)
    else:
        # get default behavior
        from rest_framework.views import exception_handler

        return exception_handler(exc, context)


class ConvertAPIExceptionToJsonResponse:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response

    def process_exception(self, request, expt):
        if isinstance(expt, APIException):
            return JsonResponse(expt.detail, status=expt.status_code, safe=False)
        else:
            return None
