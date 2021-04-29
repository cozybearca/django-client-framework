# convert a serializer to a JSON Schema.
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey
from django.db.models.fields.reverse_related import (
    ManyToManyRel,
    ManyToOneRel,
    OneToOneRel,
)
from django_client_framework.serializers import generate_jsonschema
from rest_framework import serializers
from rest_framework.utils.field_mapping import ClassLookupDict

field_to_converter = ClassLookupDict({})


def converter(converter_class):
    """Decorator to register a converter class"""
    if isinstance(converter_class.field_class, list):
        field_classes = converter_class.field_class
    else:
        field_classes = [converter_class.field_class]
    for field_class in field_classes:
        field_to_converter[field_class] = converter_class()
    return converter_class


def field_to_jsonschema(field):
    if isinstance(field, serializers.Serializer):
        result = to_jsonschema(field)
    else:
        converter = field_to_converter[field]
        result = converter.convert(field)
    # if field.label:
    # result["title"] = str(field.label)
    if field.help_text:
        result["description"] = str(field.help_text)
    return result


def is_rel_field(field):
    check_rel = [ForeignKey, OneToOneRel, ManyToOneRel, ManyToManyRel]
    return any([isinstance(field, rel) for rel in check_rel])


def get_field(model, field_name, default=None):
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return default


def to_jsonschema(serializer):
    try:
        properties = {}
        required_fields = []
        for name, field in serializer.fields.items():
            properties[name] = field_to_jsonschema(field)
            if not field.allow_null and not getattr(field, "allow_blank", False):
                required_fields.append(name)

        relational_properties = {}

        if isinstance(serializer, serializers.ModelSerializer):
            model = serializer.Meta.model
            fields = model._meta.get_fields()
            for field in fields:
                if (
                    is_rel_field(field)
                    and hasattr(model, field.name)
                    and field.related_model in generate_jsonschema.get_models()
                ):
                    # only when related_name is set on field, the field becomes a key on
                    # model, otherwise it becomes fieldname_set
                    relational_properties[field.name] = {
                        "type": field.__class__.__name__,
                        "to": field.related_model.__name__,
                    }

        result = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
            "relationalProperties": relational_properties,
            "required": required_fields,
        }
        return result
    except Exception as expt:
        raise RuntimeError(f"Failed to convert {serializer}:\n{expt}")


def model_to_jsonschema(model):
    result = {
        "type": "object",
        "title": model.__name__,
        "properties": {},
        "additionalProperties": False,
        "relationalProperties": {},
        "required": [],
    }
    for serializer in generate_jsonschema.for_model_read.get(model, []):
        schema = to_jsonschema(serializer())
        result["properties"] = {
            **result["properties"],
            **schema["properties"],
        }
        result["relationalProperties"] = {
            **result["relationalProperties"],
            **schema["relationalProperties"],
        }
        result["required"] += schema["required"]

    for serializer in generate_jsonschema.for_model_write.get(model, []):
        schema = to_jsonschema(serializer())
        result["properties"] = {
            **result["properties"],
            **schema["properties"],
        }
        result["relationalProperties"] = {
            **result["relationalProperties"],
            **schema["relationalProperties"],
        }

    result["required"] = list(set(result["required"]))
    return result
