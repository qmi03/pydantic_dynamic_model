from typing import Annotated
from pydantic import (
    BaseModel,
    create_model,
)
from .definitions import ModelDefinition
from .utils import get_python_type, create_field_info, create_field_validators


def create_dynamic_model(model_definition: ModelDefinition) -> type[BaseModel]:
    """Creates a Pydantic model from a ModelDefinition"""
    field_definitions = {}
    validators = {}
    for field in model_definition.fields:
        # Create field_definition argument
        if field.enum_values:
            # maybe add a validator here for enum but let's not for now
            field.metadata["possible_values"] = field.enum_values

        field_type = get_python_type(base_type=field.base_type, wrappers=field.wrappers)
        field_info = create_field_info(field)

        field_definitions[field.name] = Annotated[field_type, field_info]
        validators.update(create_field_validators(field))
    # think about this return later
    # return create_model(
    #     model_definition.model_name,
    #     __config__=model_definition.config,
    #     __validators__=validators,
    #     __module__=model_definition.module_name,
    #     __base__= model_definition.base_class
    #     **field_definitions,
    # )
    return create_model(
        model_definition.model_name,
        __validators__=validators,
        __module__=model_definition.module_name,
        **field_definitions,
    )
