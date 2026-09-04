#!/usr/bin/env python3
"""Build a Waveform Review Kit project from a CSV table and waveform images."""

from __future__ import annotations

import argparse
import hashlib
import csv
import json
import re
import shutil
from pathlib import Path


DEFAULT_LABELS = [
    {"code": "confirmed", "name": "确认事件", "shortcut": "1", "color": "#248a3d"},
    {"code": "possible", "name": "可能事件", "shortcut": "2", "color": "#c77900"},
    {"code": "rejected", "name": "非事件或噪声", "shortcut": "3", "color": "#d70015"},
    {"code": "uncertain", "name": "无法判断", "shortcut": "4", "color": "#6e6e73"},
]


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create project.json and copy images for Waveform Review Kit."
    )
    parser.add_argument("--csv", required=True, type=Path, help="Input UTF-8 CSV.")
    parser.add_argument("--output", required=True, type=Path, help="New project directory.")
    parser.add_argument(
        "--assets-root",
        type=Path,
        help="Base directory for image paths; defaults to the CSV directory.",
    )
    parser.add_argument("--title", default="我的波形复核项目")
    parser.add_argument("--description", default="")
    parser.add_argument("--project-id", help="Stable ID used for browser storage.")
    parser.add_argument(
        "--reference-sections",
        default="known,candidate",
        help="Comma-separated section IDs that are reference-only.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing project.json and copied files in an existing output directory.",
    )
    return parser.parse_args()


def slug(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-").lower()
    return value or "waveform-review-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV is missing a header row")
        fields = {name.strip() for name in reader.fieldnames if name}
        if "id" not in fields:
            raise ValueError("CSV requires an id column")
        if "image" not in fields and "images" not in fields:
            raise ValueError("CSV requires an image or images column")
        return [
            {(key or "").strip(): (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def main() -> None:
    args = arguments()
    csv_path = args.csv.expanduser().resolve()
    assets_root = (args.assets_root or csv_path.parent).expanduser().resolve()
    output = args.output.expanduser().resolve()
    asset_output = output / "assets"

    if (output / "project.json").exists() and not args.overwrite:
        raise FileExistsError(
            f"{output / 'project.json'} already exists; use --overwrite to replace it"
        )
    output.mkdir(parents=True, exist_ok=True)
    asset_output.mkdir(parents=True, exist_ok=True)

    reference_sections = {
        value.strip() for value in args.reference_sections.split(",") if value.strip()
    }
    rows = read_rows(csv_path)
    items = []
    ids = set()
    section_order = []

    for row_number, row in enumerate(rows, start=2):
        item_id = row.get("id", "")
        if not item_id:
            raise ValueError(f"CSV row {row_number}: id is empty")
        if item_id in ids:
            raise ValueError(f"CSV row {row_number}: duplicate id {item_id!r}")
        ids.add(item_id)

        section = row.get("section") or "review"
        if section not in section_order:
            section_order.append(section)

        image_values = split_pipe(row.get("images") or row.get("image") or "")
        if not image_values:
            raise ValueError(f"CSV row {row_number}: no image path")
        label_values = split_pipe(row.get("page_labels", ""))
        pages = []
        for image_index, image_value in enumerate(image_values):
            source = (assets_root / image_value).resolve()
            try:
                source.relative_to(assets_root)
            except ValueError as error:
                raise ValueError(
                    f"CSV row {row_number}: image escapes assets root: {image_value}"
                ) from error
            if not source.is_file():
                raise FileNotFoundError(
                    f"CSV row {row_number}: image does not exist: {source}"
                )
            item_hash = hashlib.sha1(item_id.encode("utf-8")).hexdigest()[:10]
            destination_name = f"{slug(item_id)}-{item_hash}_{image_index + 1}{source.suffix.lower()}"
            destination = asset_output / destination_name
            if destination.exists() and not args.overwrite:
                raise FileExistsError(
                    f"Destination already exists: {destination}; use --overwrite"
                )
            shutil.copy2(source, destination)
            pages.append(
                {
                    "image": destination_name,
                    "label": label_values[image_index]
                    if image_index < len(label_values)
                    else f"第 {image_index + 1} 页",
                }
            )

        metadata = {
            key.removeprefix("meta_"): value
            for key, value in row.items()
            if key.startswith("meta_") and value
        }
        items.append(
            {
                "id": item_id,
                "section": section,
                "title": row.get("title") or item_id,
                "subtitle": row.get("subtitle", ""),
                "tags": split_pipe(row.get("tags", "")),
                "metadata": metadata,
                "pages": pages,
            }
        )

    sections = [
        {
            "id": section,
            "label": section,
            "reviewable": section not in reference_sections,
            "description": "",
        }
        for section in section_order
    ]
    manifest = {
        "schema_version": 1,
        "project_id": args.project_id or slug(args.title),
        "title": args.title,
        "description": args.description,
        "sections": sections,
        "labels": DEFAULT_LABELS,
        "items": items,
    }
    manifest_path = output / "project.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created {manifest_path}")
    print(f"Items: {len(items)}; sections: {len(sections)}")
    print(f"Copied images: {sum(len(item['pages']) for item in items)}")


if __name__ == "__main__":
    main()
