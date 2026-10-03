from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for every request/response schema: camelCase JSON, snake_case Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,  # allows Read.model_validate(orm_obj)
        # Defaulted response fields are always present in output; mark them required so
        # TS discriminated unions (e.g. SSE events keyed on `type`) narrow correctly.
        json_schema_serialization_defaults_required=True,
    )
