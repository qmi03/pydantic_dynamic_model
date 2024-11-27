from enum import Enum
import ast
from typing import Self, Any, Optional, Dict, Union, List
from pydantic import BaseModel, Field, model_validator


class SimpleType(str, Enum):
    """Supported field types"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"


class WrapperType(str, Enum):
    OPTIONAL = "optional"
    LIST = "list"
    DICT = "dict"
    ENUM = "enum"


class ValidatorType(str, Enum):
    """Types of validator"""

    LAMBDA = "lambda"
    RANGE = "range"
    REGEX = "regex"
    CUSTOM = "custom"
    EMAIL = "email"
    URL = "url"


class FieldValidatorDef(BaseModel):
    """
    Represents a definition for a field validator.

    Attributes:
    validator_type (ValidatorType): The type of validator
    params (Dict[str, Any]): Parameters for the validator, with a default empty dictionary.
    error_message (Optional[str]): An optional error message for validation failures.
    """

    validator_type: ValidatorType
    params: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    @model_validator(mode="after")
    def validate_custom_function(self) -> Self:
        if self.validator_type == ValidatorType.CUSTOM:
            if "customFunctionDef" in self.params:
                code = self.params["customFunctionDef"]
                # Basic security checks
                if any(
                    keyword in code
                    for keyword in ["import", "eval", "exec", "__"]
                ):
                    raise ValueError("Prohibited keywords in custom function")
                # Validate it's a proper function
                try:
                    tree = ast.parse(code)
                    if not any(
                        isinstance(node, ast.FunctionDef) for node in ast.walk(tree)
                    ):
                        raise ValueError("Must define a function")
                except SyntaxError:
                    raise ValueError("Invalid Python syntax")
        elif self.validator_type == ValidatorType.RANGE:
            if not {"max", "min"}.issubset(self.params.keys()):
                raise ValueError("Must define max and min value to use this validator")
        elif self.validator_type == ValidatorType.LAMBDA:
            if "lambdaExpr" not in self.params:
                raise ValueError("Must define a lambda expression")

        return self


class FieldDefinition(BaseModel):
    """Definition of a single field in model"""

    name: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    base_type: Union[SimpleType, "ModelDefinition"]
    wrappers: List[WrapperType] = Field(default_factory=list)
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None
    validator_defs: List[FieldValidatorDef] = Field(default_factory=list)
    enum_values: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelDefinition(BaseModel):
    model_name: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    fields: List[FieldDefinition]
    base_class: Optional[str] = None
    module_name: Optional[str] = None

    class Config:
        protected_namespaces = ()

