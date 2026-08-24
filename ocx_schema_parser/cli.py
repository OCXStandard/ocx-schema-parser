"""Command line interface: export the OCX schema model as JSON or list its entities."""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Optional

import ocx_schema_parser
from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.loader import load
from ocx_schema_parser.resolver import resolve


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocx-schema-parser",
        description="Parse the OCX schema and export it as a typed JSON model.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {ocx_schema_parser.__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export a schema source to JSON")
    export.add_argument(
        "source",
        help="A local .xsd file, a folder of .xsd files, or an http(s) URL",
    )
    export.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (default: stdout)",
    )
    export.add_argument(
        "--download-folder",
        type=Path,
        default=None,
        help="Folder for downloaded schemas when source is a URL (default: temp folder)",
    )
    export.add_argument(
        "--indent", type=int, default=2, help="JSON indentation (default: 2)"
    )

    lister = subparsers.add_parser(
        "list", help="List schema entities as 'prefix:name', one per line"
    )
    lister.add_argument(
        "kind",
        choices=["elements", "complex-types", "simple-types", "enumerations"],
        help="Which entities to list",
    )
    lister.add_argument(
        "source",
        help="A local .xsd file, a folder of .xsd files, or an http(s) URL",
    )
    lister.add_argument(
        "--name",
        default=None,
        help="Print details for one entity given as 'prefix:name' (case-insensitive)",
    )
    lister.add_argument(
        "--download-folder",
        type=Path,
        default=None,
        help="Folder for downloaded schemas when source is a URL (default: temp folder)",
    )

    summary = subparsers.add_parser(
        "summary", help="Print entity counts grouped by target namespace"
    )
    summary.add_argument(
        "source",
        help="A local .xsd file, a folder of .xsd files, or an http(s) URL",
    )
    summary.add_argument(
        "--download-folder",
        type=Path,
        default=None,
        help="Folder for downloaded schemas when source is a URL (default: temp folder)",
    )
    return parser


_SUMMARY_KINDS = (
    ("elements", "elements"),
    ("complex-types", "complex_types"),
    ("simple-types", "simple_types"),
    ("attributes", "attributes"),
    ("attribute-groups", "attribute_groups"),
)


def _print_summary(schemas) -> None:
    """Print named-entity counts per target namespace as an aligned table."""
    counts: dict[str, list[int]] = {}
    for schema in schemas:
        ns = schema.target_namespace or "(no namespace)"
        row = counts.setdefault(ns, [0] * len(_SUMMARY_KINDS))
        for i, (_, attr) in enumerate(_SUMMARY_KINDS):
            row[i] += sum(1 for item in getattr(schema, attr) if item.name)
    total = [sum(row[i] for row in counts.values()) for i in range(len(_SUMMARY_KINDS))]
    rows = [*sorted(counts.items()), ("TOTAL", total)]
    headers = ["namespace", *(label for label, _ in _SUMMARY_KINDS)]
    ns_width = max(len(headers[0]), *(len(ns) for ns, _ in rows))
    print(f"{headers[0]:<{ns_width}}  " + "  ".join(headers[1:]))
    for ns, row in rows:
        cells = "  ".join(f"{n:>{len(h)}}" for n, h in zip(row, headers[1:]))
        print(f"{ns:<{ns_width}}  {cells}")


def _print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    """Print a titled table with aligned columns; the last column wraps."""
    print(f"\n{title}")
    desc_width = 80
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows))
        for i in range(len(headers) - 1)
    ]
    lines = [headers, *rows]
    rules = ["-" * w for w in widths] + ["-" * desc_width]
    lines.insert(1, rules)
    lines.insert(0, rules)
    lines.append(rules)
    for row in lines:
        wrapped = textwrap.wrap(row[-1], desc_width) or [""]
        cells = "  ".join(f"{cell:<{w}}" for cell, w in zip(row, widths))
        print(f"{cells}  {wrapped[0]}")
        indent = " " * (sum(widths) + 2 * len(widths))
        for extra in wrapped[1:]:
            print(f"{indent}{extra}")


def _print_entity(entity) -> None:
    """Print an entity's documentation plus attribute and child tables."""
    print(f"{entity.prefix}:{entity.name}")
    if entity.description:
        print(
            textwrap.fill(
                entity.description, 100, initial_indent="  ", subsequent_indent="  "
            )
        )
    attributes = getattr(entity, "attributes", [])
    if attributes:
        rows = [[a.name, a.type, a.use, a.description] for a in attributes]
        _print_table("Attributes:", ["name", "type", "use", "description"], rows)
    children = getattr(entity, "children", [])
    if children:
        rows = [[c.name, c.type, str(c.cardinality), c.description] for c in children]
        _print_table("Children:", ["name", "type", "cardinality", "description"], rows)


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        schemas = load(args.source, download_folder=args.download_folder)
        if args.command == "summary":
            _print_summary(schemas)
            return 0
        model = resolve(schemas)
        if args.command == "list":
            collections = {
                "elements": model.elements,
                "complex-types": model.complex_types,
                "simple-types": model.simple_types,
                "enumerations": model.enumerations,
            }
            entities = collections[args.kind]
            if args.name:
                prefix, _, local = args.name.rpartition(":")
                match = next(
                    (
                        e
                        for e in entities
                        if e.name.lower() == local.lower()
                        and e.prefix.lower() == prefix.lower()
                    ),
                    None,
                )
                if match is None:
                    print(
                        f"error: {args.name} not found in {args.kind}", file=sys.stderr
                    )
                    return 1
                _print_entity(match)
                return 0
            for entity in entities:
                print(f"{entity.prefix}:{entity.name}")
            return 0
        payload = model.model_dump_json(indent=args.indent)
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        print(
            f"Resolved schema {model.schema_version}: "
            f"{len(model.elements)} elements, "
            f"{len(model.complex_types)} complex types, "
            f"{len(model.enumerations)} enumerations",
            file=sys.stderr,
        )
        return 0
    except OcxParserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
