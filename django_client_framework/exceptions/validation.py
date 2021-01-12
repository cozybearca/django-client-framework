from rest_framework import exceptions as e


def validation_failed(non_field_errors=None, **field_msgs):
    if non_field_errors:
        if type(non_field_errors) is not str:
            non_field_errors = str(non_field_errors)
        field_msgs.update({"non_field_errors": non_field_errors})
    raise e.ValidationError(detail=field_msgs)
