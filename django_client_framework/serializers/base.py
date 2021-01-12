from logging import getLogger

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import ForeignKey
from django.utils.functional import cached_property
from django_client_framework.exceptions import ValidationError
from ipromise.overrides import overrides
from rest_framework.serializers import (
    BaseSerializer,
    ModelSerializer,
    PrimaryKeyRelatedField,
)
from rest_framework.utils.model_meta import RelationInfo

LOG = getLogger(__name__)


def get_model_field(model, key, default=None):
    try:
        return model._meta.get_field(key)
    except FieldDoesNotExist:
        return default


def register_serializer_field(for_model_field):
    def make_decorator(serializer_field):
        DCFModelSerializer.additional_serializer_field_mapping[
            for_model_field
        ] = serializer_field
        return serializer_field

    return make_decorator


class DCFModelSerializer(ModelSerializer):
    additional_serializer_field_mapping = {}

    @cached_property
    def serializer_field_mapping(self):
        mapping = super().serializer_field_mapping
        mapping.update(self.additional_serializer_field_mapping)
        return mapping

    @overrides(ModelSerializer)
    def get_default_field_names(self, declared_fields, model_info):
        """
        Return the default list of field names that will be used if the
        `Meta.fields` option is not specified.
        """

        def append_id(field_name: str, relation_info: RelationInfo):
            if isinstance(relation_info.model_field, ForeignKey):
                return field_name + "_id"
            else:
                return field_name

        return (
            [model_info.pk.name]
            + list(declared_fields)
            + list(model_info.fields)
            + [
                append_id(field_name, field)
                for field_name, field in model_info.forward_relations.items()
            ]
        )

    @overrides(ModelSerializer)
    def build_field(self, field_name, info, model_class, nested_depth):
        suffix = "_id"
        if field_name.endswith(suffix):
            # now we checked {field_name} is {old_field_name}_id
            old_field_name = field_name[0 : -len(suffix)]
            if old_field_name in info.relations and isinstance(
                info.relations[old_field_name].model_field, ForeignKey
            ):
                _, ret_kwargs = super().build_field(
                    old_field_name, info, model_class, nested_depth
                )
                ret_kwargs.update({"source": old_field_name})
                return self.serializer_related_field, ret_kwargs
        return super().build_field(field_name, info, model_class, nested_depth)

    @overrides(BaseSerializer)
    def is_valid(self, raise_exception=False):
        return all(
            [
                super().is_valid(raise_exception),
                self.check_undefined_fields(raise_exception),
                self.check_readonly_fields(raise_exception),
            ]
        )

    def check_undefined_fields(self, raise_exception):
        valid_fields = list(self.fields.keys())
        if "id" in valid_fields:
            valid_fields.remove("id")
        if "pk" in valid_fields:
            valid_fields.remove("pk")
        valid_fields.sort()

        input_fields = list(self.initial_data.keys())
        input_fields.sort()

        extra_fields = list(set(input_fields) - set(valid_fields))
        extra_fields.sort()

        if extra_fields:
            if raise_exception:
                raise ValidationError(
                    f"Extra fields are not allowed: {extra_fields}, valid fields are: {valid_fields}"
                )
            else:
                return False
        return True

    def check_readonly_fields(self, raise_exception):
        read_only_fields = set(
            [
                field_name
                for field_name, field_instance in self.fields.items()
                if field_instance.read_only
            ]
        )
        invalid_fields = [key for key in self.initial_data if key in read_only_fields]
        invalid_fields.sort()

        if invalid_fields:
            if raise_exception:
                raise ValidationError(f"These fields are read-only: {invalid_fields}")
            else:
                return False
        return True

    def validate_in(self, field_name, data):
        if field_name not in data:
            raise ValidationError(**{field_name: "This field is required."})


class GenerateJsonSchemaDecorator:
    for_model_read = {}
    for_model_write = {}

    def __call__(self, for_model):
        def decorator(serializer_class):
            self.for_model_read.setdefault(for_model, [])
            self.for_model_read[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def write(self, for_model):
        def decorator(serializer_class):
            self.for_model_write.setdefault(for_model, [])
            self.for_model_write[for_model].append(serializer_class)
            return serializer_class

        return decorator

    def get_models(self):
        return [*self.for_model_read.keys(), *self.for_model_write.keys()]


generate_jsonschema = GenerateJsonSchemaDecorator()


def check_integrity():
    from django_client_framework.api.model_api import BaseModelAPI

    generate_jsonschema_for_models = {
        **generate_jsonschema.for_model_read,
        **generate_jsonschema.for_model_write,
    }
    for model in BaseModelAPI.models:
        if (
            model not in generate_jsonschema_for_models
            or not generate_jsonschema_for_models[model]
        ):
            raise NotImplementedError(
                f"{model} is a registered api model but does not have a generated json schema"
            )

    for model in generate_jsonschema_for_models:
        if model not in BaseModelAPI.models:
            raise NotImplementedError(
                f"{model} has a generated json schema but is not a registered api model"
            )

    for serializer_cls in DCFModelSerializer.__subclasses__():
        model = serializer_cls.Meta.model
        for field_name in getattr(serializer_cls.Meta, "fields", []):
            if field_name not in serializer_cls().fields:
                raise NotImplementedError(
                    f"{field_name} in {serializer_cls.__name__}.Meta.fields is not a field"
                )
            field = serializer_cls().fields[field_name]
            if (
                isinstance(field, PrimaryKeyRelatedField)
                and not field_name.endswith("_id")
                and get_model_field(model, field_name)
            ):
                raise NotImplementedError(
                    f"You must append '_id' to '{field_name}' in {serializer_cls.__name__}.Meta.fields."
                )

        for field_name in getattr(serializer_cls.Meta, "exclude", []):
            if not get_model_field(model, field_name):
                raise NotImplementedError(
                    f"'{field_name}' in {serializer_cls.__name__}.Meta.exclude is not a field."
                )
