import pytest
from os import environ
import json
from pydantic_dynamic_model import create_dynamic_model, ModelDefinition
from pathlib import Path


def load_test_data(file_name):
    root_path = Path(environ.get("ROOT_PATH", "."))
    file_path = root_path / "tests" / file_name
    with open(file_path, mode="r", encoding="utf-8") as read_file:
        return json.load(read_file)


def test_dynamic_model_creation():
    model_def_raw_json = load_test_data("test_schema.json")
    dynamic_model = create_dynamic_model(
        ModelDefinition.model_validate(model_def_raw_json)
    )
    # with open("lmao.json", mode="w", encoding="utf-8") as file:
    #     file.write(dynamic_model.schema_json(indent=2))

    assert dynamic_model is not None, "Model creation failed"


def test_dynamic_model_parsing():
    model_def_raw_json = load_test_data("test_schema.json")
    dynamic_model = create_dynamic_model(
        ModelDefinition.model_validate(model_def_raw_json)
    )
    example_raw_json = load_test_data("test_case.json")
    instance = dynamic_model.model_validate(example_raw_json)
    assert instance is not None, "Parsing failed"


if __name__ == "__main__":
    pytest.main()
