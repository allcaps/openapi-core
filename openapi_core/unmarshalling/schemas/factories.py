from copy import deepcopy
import warnings

from openapi_core.schema.schemas.enums import SchemaType, SchemaFormat
from openapi_core.schema_validator import OAS30Validator
from openapi_core.schema_validator import oas30_format_checker
from openapi_core.unmarshalling.schemas.exceptions import (
    FormatterNotFoundError,
)
from openapi_core.unmarshalling.schemas.unmarshallers import (
    StringUnmarshaller, IntegerUnmarshaller, NumberUnmarshaller,
    BooleanUnmarshaller, ArrayUnmarshaller, ObjectUnmarshaller,
    AnyUnmarshaller,
)


class SchemaUnmarshallersFactory(object):

    PRIMITIVE_UNMARSHALLERS = {
        SchemaType.STRING: StringUnmarshaller,
        SchemaType.INTEGER: IntegerUnmarshaller,
        SchemaType.NUMBER: NumberUnmarshaller,
        SchemaType.BOOLEAN: BooleanUnmarshaller,
    }
    COMPLEX_UNMARSHALLERS = {
        SchemaType.ARRAY: ArrayUnmarshaller,
        SchemaType.OBJECT: ObjectUnmarshaller,
        SchemaType.ANY: AnyUnmarshaller,
    }

    def __init__(self, resolver=None, custom_formatters=None):
        self.resolver = resolver
        if custom_formatters is None:
            custom_formatters = {}
        self.custom_formatters = custom_formatters

    def create(self, schema, type_override=None):
        """Create unmarshaller from the schema."""
        if schema.deprecated:
            warnings.warn("The schema is deprecated", DeprecationWarning)

        schema_type = type_override or schema.type
        if schema_type in self.PRIMITIVE_UNMARSHALLERS:
            klass = self.PRIMITIVE_UNMARSHALLERS[schema_type]
            kwargs = dict(schema=schema)

        elif schema_type in self.COMPLEX_UNMARSHALLERS:
            klass = self.COMPLEX_UNMARSHALLERS[schema_type]
            kwargs = dict(
                schema=schema, unmarshallers_factory=self)

        formatter = self.get_formatter(klass.FORMATTERS, schema.format)

        if formatter is None:
            raise FormatterNotFoundError(schema.format)

        validator = self.get_validator(schema)

        return klass(formatter, validator, **kwargs)

    def get_formatter(self, default_formatters, type_format=SchemaFormat.NONE):
        try:
            schema_format = SchemaFormat(type_format)
        except ValueError:
            return self.custom_formatters.get(type_format)
        else:
            return default_formatters.get(schema_format)

    def get_validator(self, schema):
        format_checker = deepcopy(oas30_format_checker)
        for name, formatter in self.custom_formatters.items():
            format_checker.checks(name)(formatter.validate)
        return OAS30Validator(
            schema.__dict__,
            resolver=self.resolver, format_checker=format_checker,
        )
