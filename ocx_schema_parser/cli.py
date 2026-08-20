"""Command line interface: export the OCX schema model as JSON."""
from __future__ import annotations

import argparse
import sys
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
        "--version", action="version", version=f"%(prog)s {ocx_schema_parser.__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export a schema source to JSON")
    export.add_argument(
        "source",
        help="A local .xsd file, a folder of .xsd files, or an http(s) URL",
    )
    export.add_argument("-o", "--output", type=Path, default=None, help="Output JSON file (default: stdout)")
    export.add_argument(
        "--download-folder",
        type=Path,
        default=None,
        help="Folder for downloaded schemas when source is a URL (default: temp folder)",
    )
    export.add_argument("--indent", type=int, default=2, help="JSON indentation (default: 2)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        schemas = load(args.source, download_folder=args.download_folder)
        model = resolve(schemas)
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
