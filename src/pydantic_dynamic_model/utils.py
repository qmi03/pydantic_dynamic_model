from .definitions import (
    SimpleType,
    ModelDefinition,
    WrapperType,
    FieldDefinition,
    FieldValidatorDef,
    ValidatorType,
)
from typing import Union, List, Any, Optional, Dict, Callable
from pydantic import field_validator, Field
from pydantic.types import date, datetime
from .core import create_dynamic_model
import ast
import inspect


def get_python_type(
    base_type: Union[SimpleType, ModelDefinition],
    wrappers: Union[List[WrapperType], None] = None,
) -> Any:
    """Convert FieldType to actual Python type"""

    simple_type_mapping = {
        SimpleType.STRING: str,
        SimpleType.INTEGER: int,
        SimpleType.FLOAT: float,
        SimpleType.BOOLEAN: bool,
        SimpleType.DATETIME: datetime,
        SimpleType.DATE: date,
    }

    result_type = (
        create_dynamic_model(base_type)
        if isinstance(base_type, ModelDefinition)
        else simple_type_mapping.get(base_type, Any)
    )

    if wrappers:
        for wrapper in reversed(wrappers):
            if wrapper == WrapperType.LIST:
                result_type = List[result_type]
            elif wrapper == WrapperType.OPTIONAL:
                result_type = Optional[result_type]
            elif wrapper == WrapperType.DICT:
                result_type == Dict[str, result_type]

    return result_type


def create_field_info(field: FieldDefinition) -> Any:
    """Creates a Field object with the appropriate parameters"""
    params = {}
    if not field.required:
        params["default"] = field.default
    else:
        params["default"] = ...

    if field.description:
        params["description"] = field.description

    # Add all metadata to field params
    params.update(field.metadata)

    return Field(**params)


def create_field_validators(field: FieldDefinition):
    def create_validator_function(validator_def: FieldValidatorDef) -> Callable:
        """Creates a validation function from a FieldValidator definition"""
        if validator_def.validator_type == ValidatorType.LAMBDA:
            try:
                # Safe lambda creation from string
                lambda_str = validator_def.params.get("lambdaExpr", "lambda x: x")
                tree = ast.parse(lambda_str, mode="eval")
                if not isinstance(tree.body, ast.Lambda):
                    raise ValueError("Expression must be a lambda function")
                return eval(compile(tree, "<lambda>", "eval"))
            except Exception as e:
                raise ValueError(f"Invalid lambda expression: {str(e)}")

        elif validator_def.validator_type == ValidatorType.CUSTOM:
            try:
                custom_function_code = validator_def.params.get("customFunctionDef")
                if custom_function_code:
                    safe_globals = {
                        "datetime": datetime,
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                        "list": list,
                        "dict": dict,
                        "Exception": Exception,
                        "ValueError": ValueError,
                    }

                    local_namespace = {}

                    # Compile and execute in restricted environment
                    compiled_code = compile(custom_function_code, "<string>", "exec")
                    exec(compiled_code, safe_globals, local_namespace)

                    if "validate" not in local_namespace:
                        raise ValueError("Custom function must be named 'validate'")

                    validator_func = local_namespace["validate"]

                    # Verify it's a proper function with correct signature
                    sig = inspect.signature(validator_func)
                    if len(sig.parameters) != 2:
                        raise ValueError(
                            "Validator must accept exactly 2 parameters (cls, v)"
                        )

                    return validator_func
            except Exception as e:
                raise ValueError(f"Invalid custom validator: {str(e)}")

        elif validator_def.validator_type == ValidatorType.RANGE:

            def range_validator(cls, v):
                min_val = validator_def.params.get("min")
                max_val = validator_def.params.get("max")
                if min_val is not None and v < min_val:
                    raise ValueError(
                        validator_def.error_message or f"Value must be >= {min_val}"
                    )
                if max_val is not None and v > max_val:
                    raise ValueError(
                        validator_def.error_message or f"Value must be <= {max_val}"
                    )
                return v

            return range_validator

        # Return default function that does nothing
        return lambda cls, x: x

    return {
        f"validate_{field.name}_{idx}": field_validator(field.name)(
            create_validator_function(validator_def)
        )
        for idx, validator_def in enumerate(field.validator_defs)
    }
