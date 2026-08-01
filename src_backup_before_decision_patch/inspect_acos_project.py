"""
Inspect the ACOS source tree and report existing classes, functions,
constructors, and public methods.

Run from the ACOS_Project root:

    python -u src/inspect_acos_project.py
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"

RELEVANT_KEYWORDS = (
    "agent",
    "environment",
    "simulator",
    "scenario",
    "metric",
    "experiment",
    "execution",
    "outcome",
    "learning",
    "knowledge",
    "decision",
    "negotiation",
    "mocra",
    "analytics",
    "explain",
)


def annotation_to_text(
    annotation: Optional[ast.expr],
) -> str:
    if annotation is None:
        return ""

    try:
        return ast.unparse(annotation)
    except Exception:
        return "unknown"


def default_to_text(
    default: Optional[ast.expr],
) -> str:
    if default is None:
        return ""

    try:
        return ast.unparse(default)
    except Exception:
        return "unknown"


def format_arguments(
    arguments: ast.arguments,
) -> str:
    parameters: List[str] = []

    positional_arguments = (
        list(arguments.posonlyargs)
        + list(arguments.args)
    )

    defaults_offset = (
        len(positional_arguments)
        - len(arguments.defaults)
    )

    for index, argument in enumerate(
        positional_arguments
    ):
        if argument.arg in {"self", "cls"}:
            continue

        parameter = argument.arg

        annotation = annotation_to_text(
            argument.annotation
        )

        if annotation:
            parameter += f": {annotation}"

        default_index = index - defaults_offset

        if default_index >= 0:
            default_value = default_to_text(
                arguments.defaults[default_index]
            )
            parameter += f" = {default_value}"

        parameters.append(parameter)

    if arguments.vararg is not None:
        parameter = f"*{arguments.vararg.arg}"

        annotation = annotation_to_text(
            arguments.vararg.annotation
        )

        if annotation:
            parameter += f": {annotation}"

        parameters.append(parameter)

    for argument, default in zip(
        arguments.kwonlyargs,
        arguments.kw_defaults,
    ):
        parameter = argument.arg

        annotation = annotation_to_text(
            argument.annotation
        )

        if annotation:
            parameter += f": {annotation}"

        if default is not None:
            parameter += (
                f" = {default_to_text(default)}"
            )

        parameters.append(parameter)

    if arguments.kwarg is not None:
        parameter = f"**{arguments.kwarg.arg}"

        annotation = annotation_to_text(
            arguments.kwarg.annotation
        )

        if annotation:
            parameter += f": {annotation}"

        parameters.append(parameter)

    return ", ".join(parameters)


def format_function_signature(
    function_node: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> str:
    parameters = format_arguments(
        function_node.args
    )

    return_annotation = annotation_to_text(
        function_node.returns
    )

    signature = (
        f"{function_node.name}({parameters})"
    )

    if return_annotation:
        signature += f" -> {return_annotation}"

    return signature


def is_relevant_file(
    file_path: Path,
) -> bool:
    relative_path = str(
        file_path.relative_to(SOURCE_ROOT)
    ).lower()

    return any(
        keyword in relative_path
        for keyword in RELEVANT_KEYWORDS
    )


def inspect_python_file(
    file_path: Path,
) -> None:
    relative_path = file_path.relative_to(
        PROJECT_ROOT
    )

    try:
        source_code = file_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        source_code = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    try:
        syntax_tree = ast.parse(
            source_code,
            filename=str(file_path),
        )
    except SyntaxError as error:
        print("\n" + "=" * 90)
        print(relative_path)
        print("=" * 90)
        print(
            f"SYNTAX ERROR: line "
            f"{error.lineno}: {error.msg}"
        )
        return

    classes = [
        node
        for node in syntax_tree.body
        if isinstance(node, ast.ClassDef)
    ]

    functions = [
        node
        for node in syntax_tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    ]

    if not classes and not functions:
        return

    print("\n" + "=" * 90)
    print(relative_path)
    print("=" * 90)

    for class_node in classes:
        print(f"\nCLASS: {class_node.name}")

        constructor = None

        for member in class_node.body:
            if (
                isinstance(
                    member,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                )
                and member.name == "__init__"
            ):
                constructor = member
                break

        if constructor is not None:
            constructor_parameters = (
                format_arguments(
                    constructor.args
                )
            )

            print(
                f"  Constructor: "
                f"{class_node.name}"
                f"({constructor_parameters})"
            )
        else:
            print(
                f"  Constructor: "
                f"{class_node.name}()"
            )

        public_methods = [
            member
            for member in class_node.body
            if (
                isinstance(
                    member,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                )
                and not member.name.startswith("_")
            )
        ]

        if not public_methods:
            print("  Public methods: None")
            continue

        print("  Public methods:")

        for method in public_methods:
            print(
                "   - "
                + format_function_signature(method)
            )

    if functions:
        print("\nMODULE FUNCTIONS:")

        for function_node in functions:
            if function_node.name.startswith("_"):
                continue

            print(
                "  - "
                + format_function_signature(
                    function_node
                )
            )


def main() -> None:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(
            f"Source directory not found: "
            f"{SOURCE_ROOT}"
        )

    python_files = sorted(
        SOURCE_ROOT.rglob("*.py")
    )

    relevant_files = [
        file_path
        for file_path in python_files
        if (
            is_relevant_file(file_path)
            and not file_path.name.startswith(
                "tempCodeRunnerFile"
            )
        )
    ]

    print("\nACOS PROJECT COMPONENT AUDIT")
    print("=" * 90)
    print(f"Project root: {PROJECT_ROOT}")
    print(
        f"Python files found: "
        f"{len(python_files)}"
    )
    print(
        f"Relevant files inspected: "
        f"{len(relevant_files)}"
    )

    for file_path in relevant_files:
        inspect_python_file(file_path)

    print("\n" + "=" * 90)
    print("ACOS project inspection completed.")
    print("=" * 90)


if __name__ == "__main__":
    main()