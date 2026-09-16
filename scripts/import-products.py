#!/usr/bin/env python3
"""Process pending Art Ink Studio XLSX product-import requests without a database."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IMPORTS = ROOT / "content" / "imports"
PRODUCTS = ROOT / "content" / "products"
IMAGES = ROOT / "public" / "images"
LANGUAGES = ("en", "mk", "sq")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_ROWS = 1000
MAX_ZIP_FILES = 2000
MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_TOTAL_BYTES = 300 * 1024 * 1024
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL_NS = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}


class ImportValidationError(Exception):
    def __init__(self, errors: list[str], warnings: list[str] | None = None):
        super().__init__("Import validation failed")
        self.errors = errors
        self.warnings = warnings or []


def column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "")
    if not letters:
        return 0
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_xlsx(file_path: Path) -> dict[str, list[dict[str, str]]]:
    with zipfile.ZipFile(file_path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", NS):
                shared.append("".join(node.text or "" for node in item.findall(".//m:t", NS)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {node.attrib["Id"]: node.attrib["Target"] for node in relationships.findall("p:Relationship", REL_NS)}
        result: dict[str, list[dict[str, str]]] = {}

        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            name = sheet.attrib["name"]
            rel_id = sheet.attrib[f"{{{NS['r']}}}id"]
            target = targets[rel_id].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            xml = ET.fromstring(archive.read(target))
            raw_rows: list[list[str]] = []
            max_cols = 0
            for row in xml.findall("m:sheetData/m:row", NS):
                values: dict[int, str] = {}
                for cell in row.findall("m:c", NS):
                    index = column_index(cell.attrib.get("r", ""))
                    kind = cell.attrib.get("t", "")
                    if kind == "inlineStr":
                        value = "".join(node.text or "" for node in cell.findall(".//m:t", NS))
                    else:
                        value_node = cell.find("m:v", NS)
                        value = value_node.text if value_node is not None and value_node.text is not None else ""
                        if kind == "s" and value:
                            value = shared[int(value)]
                        elif kind == "b":
                            value = "TRUE" if value == "1" else "FALSE"
                    values[index] = value.strip()
                    max_cols = max(max_cols, index + 1)
                raw_rows.append([values.get(i, "") for i in range(max_cols)])

            while raw_rows and not any(raw_rows[0]):
                raw_rows.pop(0)
            if not raw_rows:
                result[name] = []
                continue
            headers = [str(value).strip() for value in raw_rows[0]]
            records: list[dict[str, str]] = []
            for raw in raw_rows[1:]:
                row = {headers[i]: (raw[i].strip() if i < len(raw) else "") for i in range(len(headers)) if headers[i]}
                if any(row.values()):
                    records.append(row)
            result[name] = records
        return result


def bool_value(value: str, field: str, row_number: int, errors: list[str]) -> bool:
    normalized = str(value).strip().upper()
    if normalized in {"TRUE", "1", "YES", "DA", "D"}:
        return True
    if normalized in {"FALSE", "0", "NO", "NE", "N", ""}:
        return False
    errors.append(f"Products row {row_number}: {field} must be TRUE or FALSE.")
    return False


def int_value(value: str, field: str, row_number: int, errors: list[str], default: int = 100) -> int:
    if str(value).strip() == "":
        return default
    try:
        number = int(float(str(value)))
        if number < 0 or str(number) != str(value).strip().removesuffix(".0"):
            raise ValueError
        return number
    except ValueError:
        errors.append(f"Products row {row_number}: {field} must be a whole number of 0 or more.")
        return default


def image_name(value: str, field: str, row_number: int, errors: list[str]) -> str:
    raw = str(value).strip().replace("\\", "/")
    for prefix in ("/images/", "images/", "public/images/"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    if not raw:
        errors.append(f"Products row {row_number}: {field} is required.")
        return ""
    if "/" in raw or not FILE_RE.fullmatch(raw) or Path(raw).suffix.lower() not in IMAGE_EXTENSIONS:
        errors.append(f"Products row {row_number}: unsafe or unsupported image filename '{raw}' in {field}.")
        return ""
    return raw


def optional_images(value: str, row_number: int, errors: list[str]) -> list[str]:
    if not str(value).strip():
        return []
    names: list[str] = []
    for raw in str(value).split("|"):
        name = image_name(raw, "gallery_images", row_number, errors)
        if name and name not in names:
            names.append(name)
    return names


def safe_repo_path(value: str, expected_suffix: str, field: str) -> Path:
    raw = str(value or "").strip().replace("\\", "/").lstrip("/")
    if not raw.lower().endswith(expected_suffix):
        raise ImportValidationError([f"{field} must be a {expected_suffix} file."])
    candidate = (ROOT / raw).resolve()
    if ROOT not in candidate.parents or not candidate.is_file():
        raise ImportValidationError([f"{field} file is missing or unsafe: {raw}"])
    return candidate


def read_image_zip(file_path: Path | None) -> dict[str, bytes]:
    if file_path is None:
        return {}
    files: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(file_path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir() and not entry.filename.startswith("__MACOSX/")]
        if len(entries) > MAX_ZIP_FILES:
            raise ImportValidationError([f"Image ZIP has more than {MAX_ZIP_FILES} files."])
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if len(path.parts) != 1 or path.name != entry.filename or not FILE_RE.fullmatch(path.name):
                raise ImportValidationError([f"Image ZIP must be flat and contains an unsafe path: {entry.filename}"])
            if Path(path.name).suffix.lower() not in IMAGE_EXTENSIONS:
                raise ImportValidationError([f"Unsupported image type in ZIP: {path.name}"])
            if entry.file_size > MAX_FILE_BYTES:
                raise ImportValidationError([f"Image is larger than 12 MB: {path.name}"])
            total += entry.file_size
            if total > MAX_TOTAL_BYTES:
                raise ImportValidationError(["Uncompressed image ZIP is larger than 300 MB."])
            if path.name in files:
                raise ImportValidationError([f"Duplicate filename in image ZIP: {path.name}"])
            files[path.name] = archive.read(entry)
    return files


def file_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_existing() -> tuple[dict[str, dict], dict[str, str]]:
    products: dict[str, dict] = {}
    codes: dict[str, str] = {}
    for path in PRODUCTS.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = str(item.get("slug", path.stem))
        products[slug] = item
        code = str(item.get("code", "")).strip()
        if code:
            codes[code] = slug
    return products, codes


def load_categories() -> set[str]:
    categories: set[str] = set()
    for path in (ROOT / "content" / "categories").glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = str(item.get("slug", path.stem)).strip()
        if SLUG_RE.fullmatch(slug):
            categories.add(slug)
    return categories


def validate_import(workbook_path: Path, images_zip: Path | None, mode: str) -> tuple[list[dict], dict[str, bytes], list[str]]:
    sheets = read_xlsx(workbook_path)
    errors: list[str] = []
    warnings: list[str] = []
    required_headers = {"slug", "code", "category", "main_image", "material", "published", "order"}
    rows = sheets.get("Products")
    if rows is None:
        raise ImportValidationError(["Workbook must contain a sheet named Products."])
    if len(rows) > MAX_ROWS:
        raise ImportValidationError([f"Products sheet has more than {MAX_ROWS} populated rows."])
    if not rows:
        raise ImportValidationError(["Products sheet has no product rows."])
    missing_headers = required_headers - set(rows[0])
    if missing_headers:
        errors.append("Products sheet is missing columns: " + ", ".join(sorted(missing_headers)))

    colour_rows = sheets.get("Colours", [])
    colours: dict[str, list[dict[str, str]]] = defaultdict(list)
    for index, row in enumerate(colour_rows, start=2):
        slug = row.get("product_slug", "").strip()
        if not slug:
            errors.append(f"Colours row {index}: product_slug is required.")
            continue
        hex_value = row.get("hex", "").strip()
        if not HEX_RE.fullmatch(hex_value):
            errors.append(f"Colours row {index}: invalid HEX '{hex_value}'. Use #RRGGBB.")
        names = {language: row.get(language, "").strip() for language in LANGUAGES}
        for language, value in names.items():
            if not value:
                errors.append(f"Colours row {index}: {language} colour name is required.")
        colours[slug].append({**names, "hex": hex_value})

    existing, existing_codes = load_existing()
    available_categories = load_categories()
    if not available_categories:
        errors.append("No catalogue categories are configured.")
    batch_slugs: set[str] = set()
    batch_codes: dict[str, str] = {}
    product_output: list[dict] = []
    referenced_images: set[str] = set()

    for index, row in enumerate(rows, start=2):
        slug = row.get("slug", "").strip()
        code = row.get("code", "").strip()
        category = row.get("category", "").strip().lower()
        if not SLUG_RE.fullmatch(slug):
            errors.append(f"Products row {index}: invalid slug '{slug}'.")
        if slug in batch_slugs:
            errors.append(f"Products row {index}: duplicate slug '{slug}' in workbook.")
        batch_slugs.add(slug)
        if not code:
            errors.append(f"Products row {index}: code is required.")
        elif code in batch_codes:
            errors.append(f"Products row {index}: duplicate code '{code}' also used by '{batch_codes[code]}'.")
        else:
            batch_codes[code] = slug
        if category not in available_categories:
            errors.append(f"Products row {index}: unknown category '{category}'. Add it in Categories first or use an existing category URL ID.")
        if mode == "create" and slug in existing:
            errors.append(f"Products row {index}: slug '{slug}' already exists. Use Create + update only when intentional.")
        if code in existing_codes and existing_codes[code] != slug:
            errors.append(f"Products row {index}: code '{code}' already belongs to '{existing_codes[code]}'.")

        main = image_name(row.get("main_image", ""), "main_image", index, errors)
        gallery = optional_images(row.get("gallery_images", ""), index, errors)
        if main:
            referenced_images.add(main)
        referenced_images.update(gallery)
        material = row.get("material", "").strip()
        if not material:
            errors.append(f"Products row {index}: material is required.")
        published = bool_value(row.get("published", ""), "published", index, errors)
        order = int_value(row.get("order", ""), "order", index, errors)

        product = {
            "slug": slug,
            "code": code,
            "category": category,
            "image": f"/images/{main}" if main else "",
            "gallery": [f"/images/{name}" for name in gallery],
        }
        if colours.get(slug):
            product["colors"] = colours[slug]
        product.update({"material": material, "sizes": row.get("sizes", "").strip(), "published": published, "order": order})
        for language in LANGUAGES:
            translated = {
                "name": row.get(f"{language}_name", "").strip(),
                "subtitle": row.get(f"{language}_subtitle", "").strip(),
                "description": row.get(f"{language}_description", "").strip(),
            }
            translated_material = row.get(f"{language}_material", "").strip()
            if translated_material:
                translated["material"] = translated_material
            for field in ("name", "subtitle", "description"):
                if not translated[field]:
                    errors.append(f"Products row {index}: {language}_{field} is required.")
            product[language] = translated
        product_output.append(product)

    unknown_colour_slugs = set(colours) - batch_slugs
    for slug in sorted(unknown_colour_slugs):
        errors.append(f"Colours sheet references '{slug}', but that slug is not in Products.")

    zip_images = read_image_zip(images_zip)
    for name in sorted(referenced_images):
        if name not in zip_images and not (IMAGES / name).is_file():
            errors.append(f"Referenced image is missing from ZIP and public/images: {name}")
        elif name in zip_images and (IMAGES / name).is_file() and mode == "create":
            if file_digest(zip_images[name]) != file_digest((IMAGES / name).read_bytes()):
                errors.append(f"Image '{name}' already exists with different content. Rename it or use Create + update.")
    unused = sorted(set(zip_images) - referenced_images)
    if unused:
        preview = ", ".join(unused[:10])
        warnings.append(f"ZIP contains {len(unused)} unused image(s): {preview}{'…' if len(unused) > 10 else ''}")
    if errors:
        raise ImportValidationError(errors, warnings)
    return product_output, zip_images, warnings


def update_request(path: Path, request: dict, status: str, report: str) -> None:
    request["status"] = status
    request["report"] = report[:12000]
    request["processed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_request(path: Path) -> str:
    request = json.loads(path.read_text(encoding="utf-8"))
    if str(request.get("status", "pending")).lower() != "pending":
        return "skipped"
    title = str(request.get("title", path.stem)).strip() or path.stem
    mode = str(request.get("mode", "create")).lower()
    if mode not in {"create", "upsert"}:
        update_request(path, request, "failed", "Invalid import mode. Choose create or upsert.")
        return "failed"
    try:
        workbook_path = safe_repo_path(request.get("workbook", ""), ".xlsx", "Workbook")
        zip_value = str(request.get("images_zip", "")).strip()
        images_zip = safe_repo_path(zip_value, ".zip", "Images ZIP") if zip_value else None
        products, images, warnings = validate_import(workbook_path, images_zip, mode)
        with tempfile.TemporaryDirectory(prefix="artink-import-") as temp_dir:
            staging = Path(temp_dir)
            staged_products = staging / "products"
            staged_images = staging / "images"
            staged_products.mkdir()
            staged_images.mkdir()
            for product in products:
                (staged_products / f"{product['slug']}.json").write_text(json.dumps(product, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
            for name, data in images.items():
                (staged_images / name).write_bytes(data)
            for staged in staged_products.iterdir():
                shutil.copy2(staged, PRODUCTS / staged.name)
            for staged in staged_images.iterdir():
                shutil.copy2(staged, IMAGES / staged.name)
        lines = [f"Import completed: {title}", f"Mode: {'Create only' if mode == 'create' else 'Create + update'}", f"Products written: {len(products)}", f"Images supplied: {len(images)}"]
        if warnings:
            lines.extend(["", "Warnings:", *[f"- {warning}" for warning in warnings]])
        lines.extend(["", "Review the products in the normal Products editor. Nothing is live until PUBLISH ALL is increased."])
        update_request(path, request, "completed", "\n".join(lines))
        return "completed"
    except ImportValidationError as exc:
        lines = [f"Import failed: {title}", f"Errors: {len(exc.errors)}", *[f"- {error}" for error in exc.errors]]
        if exc.warnings:
            lines.extend(["", "Warnings:", *[f"- {warning}" for warning in exc.warnings]])
        lines.extend(["", "No products from this batch were written. Correct the files and create a new import request."])
        update_request(path, request, "failed", "\n".join(lines))
        return "failed"
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        update_request(path, request, "failed", f"Import failed because the uploaded files could not be read: {exc}\n\nNo products from this batch were written.")
        return "failed"


def main() -> int:
    IMPORTS.mkdir(parents=True, exist_ok=True)
    results = defaultdict(int)
    for path in sorted(IMPORTS.glob("*.json")):
        results[process_request(path)] += 1
    print(f"Bulk import results: completed={results['completed']} failed={results['failed']} skipped={results['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
