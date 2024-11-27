from typing import Annotated
from pydantic import (
    BaseModel,
    create_model,
    ConfigDict,
)
from .definitions import ModelDefinition, WrapperType
from .utils import get_python_type, create_field_info, create_field_validators


def create_dynamic_model(model_definition: ModelDefinition) -> type[BaseModel]:
    """Creates a Pydantic model from a ModelDefinition"""
    field_definitions = {}
    validators = {}
    config = {}
    for field in model_definition.fields:
        # Create field_definition argument
        if (
            not config.get("use_enum_values", False)
            and WrapperType.ENUM in field.wrappers
        ):
            config["use_enum_values"] = True

        field_type = get_python_type(base_type=field.base_type, wrappers=field.wrappers)
        field_info = create_field_info(field)

        field_definitions[field.name] = Annotated[field_type, field_info]
        validators.update(create_field_validators(field))
    return create_model(
        model_definition.model_name,
        __config__=ConfigDict(**config),
        __validators__=validators,
        __module__=model_definition.module_name,
        **field_definitions,
    )
