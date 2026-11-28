"""Offline signature binding for calls from the seed package into product code."""

from __future__ import annotations

import ast
import importlib
import inspect
from functools import cache
from pathlib import Path
from typing import Any

SEED_ROOT = Path(__file__).resolve().parents[2] / "tools" / "seed"


@cache
def _imported_symbol(module_name: str, symbol_name: str) -> Any:
    module = importlib.import_module(module_name)
    if hasattr(module, symbol_name):
        return getattr(module, symbol_name)
    return importlib.import_module(f"{module_name}.{symbol_name}")


def _product_imports(tree: ast.Module) -> dict[str, Any]:
    symbols: dict[str, Any] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if not node.module.startswith("sketch2life"):
                continue
            for alias in node.names:
                if alias.name != "*":
                    symbols[alias.asname or alias.name] = _imported_symbol(
                        node.module, alias.name
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("sketch2life"):
                    module_name = alias.name
                    local_name = alias.asname or module_name.split(".")[0]
                    symbols[local_name] = importlib.import_module(module_name)
    return symbols


def _function_definitions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _local_product_protocol_aliases(tree: ast.Module, symbols: dict[str, Any]) -> dict[str, Any]:
    """Map a local service Protocol to its single imported product implementation."""

    aliases: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not any(
            (isinstance(base, ast.Name) and base.id == "Protocol")
            or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
            for base in node.bases
        ):
            continue
        methods = [
            method
            for method in node.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        candidates = {
            id(value): value
            for value in symbols.values()
            if inspect.isclass(value)
            and methods
            and all(
                _protocol_method_matches(method, getattr(value, method.name, None))
                for method in methods
            )
        }
        if len(candidates) == 1:
            aliases[node.name] = next(iter(candidates.values()))
    return aliases


def _protocol_method_matches(method: ast.FunctionDef | ast.AsyncFunctionDef, target: Any) -> bool:
    if not callable(target):
        return False
    expected = [
        *(
            (argument.arg, inspect.Parameter.POSITIONAL_ONLY)
            for argument in method.args.posonlyargs
            if argument.arg not in {"self", "cls"}
        ),
        *(
            (argument.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            for argument in method.args.args
            if argument.arg not in {"self", "cls"}
        ),
        *(
            (argument.arg, inspect.Parameter.KEYWORD_ONLY)
            for argument in method.args.kwonlyargs
        ),
    ]
    actual_parameters = list(inspect.signature(target).parameters.values())
    if actual_parameters and actual_parameters[0].name in {"self", "cls"}:
        actual_parameters = actual_parameters[1:]
    actual = [(parameter.name, parameter.kind) for parameter in actual_parameters]
    protocol_parameters_match = actual[: len(expected)] == expected
    extra_parameters_are_optional = all(
        parameter.default is not inspect.Parameter.empty
        for parameter in actual_parameters[len(expected) :]
    )
    return protocol_parameters_match and extra_parameters_are_optional


def _looks_like_product_receiver(call: ast.Call) -> bool:
    callee = call.func
    if not isinstance(callee, ast.Attribute) or not isinstance(callee.value, ast.Name):
        return False
    name = callee.value.id.lower()
    return (
        name in {"service", "repository", "repo"}
        or name.endswith(("_service", "_repository", "_repo"))
    )


def _class_for_annotation(annotation: ast.expr | None, symbols: dict[str, Any]) -> type[Any] | None:
    if isinstance(annotation, ast.Name):
        value = symbols.get(annotation.id)
        return value if inspect.isclass(value) else None
    if isinstance(annotation, ast.Attribute) and isinstance(annotation.value, ast.Name):
        value = symbols.get(annotation.value.id)
        member = getattr(value, annotation.attr, None) if value is not None else None
        return member if inspect.isclass(member) else None
    return None


def _walk_scope(root: ast.AST):
    scope_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            if isinstance(child, scope_nodes) and child is not root:
                continue
            stack.append(child)


def _return_class(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    symbols: dict[str, Any],
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    seen: frozenset[str] = frozenset(),
) -> type[Any] | None:
    if function.name in seen:
        return None
    annotated = _class_for_annotation(function.returns, symbols)
    if annotated is not None:
        return annotated
    next_seen = seen | {function.name}
    for node in _walk_scope(function):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Call):
            continue
        callee = node.value.func
        if isinstance(callee, ast.Name):
            value = symbols.get(callee.id)
            if inspect.isclass(value):
                return value
            helper = functions.get(callee.id)
            if helper is not None:
                result = _return_class(helper, symbols, functions, next_seen)
                if result is not None:
                    return result
    return None


def _parameter_defaults(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, ast.expr]:
    positional = [*function.args.posonlyargs, *function.args.args]
    defaults = dict(
        zip(
            (arg.arg for arg in positional[-len(function.args.defaults) :]),
            function.args.defaults,
            strict=True,
        )
    ) if function.args.defaults else {}
    defaults.update(
        {
            arg.arg: value
            for arg, value in zip(
                function.args.kwonlyargs, function.args.kw_defaults, strict=True
            )
            if value is not None
        }
    )
    return defaults


def _scope_types(
    scope: ast.AST,
    symbols: dict[str, Any],
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> tuple[dict[str, type[Any]], dict[str, type[Any]]]:
    """Return instance types and product-class factory parameters for one seed scope."""

    local_types: dict[str, type[Any]] = {}
    factory_classes: dict[str, type[Any]] = {}
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return local_types, factory_classes

    defaults = _parameter_defaults(scope)
    arguments = [
        *scope.args.posonlyargs,
        *scope.args.args,
        *scope.args.kwonlyargs,
    ]
    factory_outputs: dict[str, type[Any]] = {}
    for argument in arguments:
        annotated = _class_for_annotation(argument.annotation, symbols)
        if annotated is not None:
            local_types[argument.arg] = annotated
        default = defaults.get(argument.arg)
        if not isinstance(default, ast.Name):
            continue
        value = symbols.get(default.id)
        if inspect.isclass(value):
            factory_classes[argument.arg] = value
            factory_outputs[argument.arg] = value
            continue
        helper = functions.get(default.id)
        if helper is not None:
            output_type = _return_class(helper, symbols, functions)
            if output_type is not None:
                factory_outputs[argument.arg] = output_type

    for node in _walk_scope(scope):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            annotated = _class_for_annotation(node.annotation, symbols)
            if annotated is not None:
                local_types[node.target.id] = annotated
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            callee = node.value.func
            result_type = None
            if isinstance(callee, ast.Name):
                value = symbols.get(callee.id)
                if inspect.isclass(value):
                    result_type = value
                elif callee.id in factory_outputs:
                    result_type = factory_outputs[callee.id]
                else:
                    helper = functions.get(callee.id)
                    if helper is not None:
                        result_type = _return_class(helper, symbols, functions)
            if result_type is not None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_types[target.id] = result_type

    return local_types, factory_classes


def _resolve_object(
    expression: ast.expr,
    symbols: dict[str, Any],
    local_types: dict[str, type[Any]],
) -> Any | None:
    if isinstance(expression, ast.Name):
        return symbols.get(expression.id, local_types.get(expression.id))
    if isinstance(expression, ast.Attribute):
        owner = _resolve_object(expression.value, symbols, local_types)
        return getattr(owner, expression.attr, None) if owner is not None else None
    return None


def _call_result_class(
    expression: ast.Call,
    symbols: dict[str, Any],
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    factory_classes: dict[str, type[Any]],
) -> type[Any] | None:
    callee = expression.func
    if isinstance(callee, ast.Name):
        value = symbols.get(callee.id, factory_classes.get(callee.id))
        if inspect.isclass(value):
            return value
        helper = functions.get(callee.id)
        if helper is not None:
            return _return_class(helper, symbols, functions)
    return None


def _target_for_call(
    call: ast.Call,
    symbols: dict[str, Any],
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    local_types: dict[str, type[Any]],
    factory_classes: dict[str, type[Any]],
) -> tuple[Any, bool] | None:
    callee = call.func
    if isinstance(callee, ast.Name):
        value = symbols.get(callee.id, factory_classes.get(callee.id))
        return (value, False) if callable(value) else None
    if not isinstance(callee, ast.Attribute):
        return None

    owner_expression = callee.value
    bound_instance = False
    if isinstance(owner_expression, ast.Name) and owner_expression.id in local_types:
        owner = local_types[owner_expression.id]
        bound_instance = True
    elif isinstance(owner_expression, ast.Call):
        owner = _call_result_class(owner_expression, symbols, functions, factory_classes)
        bound_instance = owner is not None
    else:
        owner = _resolve_object(owner_expression, symbols, local_types)
    target = getattr(owner, callee.attr, None) if owner is not None else None
    return (target, bound_instance) if callable(target) else None


def _call_shape(call: ast.Call) -> tuple[int, dict[str, object]]:
    positional_count = 0
    for argument in call.args:
        if isinstance(argument, ast.Starred):
            if isinstance(argument.value, (ast.List, ast.Tuple)):
                positional_count += len(argument.value.elts)
            else:
                raise ValueError("dynamic *args cannot be signature-bound statically")
        else:
            positional_count += 1

    keyword_values: dict[str, object] = {}
    for keyword in call.keywords:
        if keyword.arg is not None:
            keyword_values[keyword.arg] = object()
            continue
        if not isinstance(keyword.value, ast.Dict):
            raise ValueError("dynamic **kwargs cannot be signature-bound statically")
        for key in keyword.value.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                raise ValueError("non-literal **kwargs cannot be signature-bound statically")
            keyword_values[key.value] = object()
    return positional_count, keyword_values


def test_seed_calls_bind_to_current_product_signatures() -> None:
    failures: list[str] = []
    checked_calls = 0

    for source_path in sorted(SEED_ROOT.rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        symbols = _product_imports(tree)
        symbols.update(_local_product_protocol_aliases(tree, symbols))
        functions = _function_definitions(tree)
        scopes: list[ast.AST] = [tree]
        scopes.extend(functions.values())
        scopes.extend(
            node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        )

        for scope in scopes:
            local_types, factory_classes = _scope_types(scope, symbols, functions)
            for node in _walk_scope(scope):
                if not isinstance(node, ast.Call):
                    continue
                resolved = _target_for_call(
                    node, symbols, functions, local_types, factory_classes
                )
                if resolved is None:
                    if _looks_like_product_receiver(node):
                        label = f"{source_path.relative_to(SEED_ROOT)}:{node.lineno}"
                        failures.append(f"{label} unresolved product receiver for {node.func!r}")
                    continue
                target, bound_instance = resolved
                checked_calls += 1
                label = f"{source_path.relative_to(SEED_ROOT)}:{node.lineno}"
                try:
                    signature = inspect.signature(target)
                    positional_count, keyword_values = _call_shape(node)
                    positional = [object()] * positional_count
                    parameters = list(signature.parameters.values())
                    if (
                        bound_instance
                        and inspect.isfunction(target)
                        and parameters
                        and parameters[0].name in {"self", "cls"}
                    ):
                        positional.insert(0, object())
                    signature.bind(*positional, **keyword_values)
                except (TypeError, ValueError) as exc:
                    failures.append(f"{label} {target!r}: {exc}")

    assert checked_calls > 0, "the seed signature scan found no product calls"
    assert not failures, "seed calls do not match current product signatures:\n" + "\n".join(
        failures
    )


def test_s7b_story_reservation_uses_the_parent_router_account_id() -> None:
    source_path = SEED_ROOT / "s7b_story_states.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_ensure_story_revision"
    )
    reservation = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reserve_story_revision"
    )
    account_id = next(
        keyword.value for keyword in reservation.keywords if keyword.arg == "account_id"
    )
    assert ast.unparse(account_id) == "identity.account_id"
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "identity" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_require_parent"
        for node in ast.walk(function)
    )
