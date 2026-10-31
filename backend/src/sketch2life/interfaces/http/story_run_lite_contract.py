"""Add the pinned synthetic StoryRun contract without altering existing components."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def add_story_run_lite_contract(schema: dict[str, Any]) -> None:
    resource = files("sketch2life.interfaces.http").joinpath("story_run_lite_openapi.json")
    contract = json.loads(resource.read_text(encoding="utf-8"))
    component_groups = contract["components"]

    def namespaced(value: Any) -> Any:
        if isinstance(value, list):
            return [namespaced(item) for item in value]
        if isinstance(value, dict):
            return {key: namespaced(item) for key, item in value.items()}
        if isinstance(value, str) and value.startswith("#/components/"):
            parts = value.split("/")
            if len(parts) != 4 or parts[2] not in component_groups:
                raise ValueError("StoryRun-lite contract has an unsupported component reference")
            return f"#/components/{parts[2]}/StoryRunLite_{parts[3]}"
        return value

    components = schema.setdefault("components", {})
    for group, entries in component_groups.items():
        target = components.setdefault(group, {})
        for name, value in entries.items():
            unique_name = f"StoryRunLite_{name}"
            if unique_name in target:
                raise ValueError("StoryRun-lite contract component conflicts with the main API")
            target[unique_name] = namespaced(value)

    paths = schema["paths"]
    methods = {"get", "put", "post", "delete", "patch", "options", "head"}
    for path, value in contract["paths"].items():
        if path not in paths or set(paths[path]) & methods != set(value) & methods:
            raise ValueError("StoryRun-lite route surface does not match its pinned contract")
        paths[path] = namespaced(value)
