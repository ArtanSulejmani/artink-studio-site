#!/usr/bin/env python3
"""Integration tests for the dependency-free XLSX product importer."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def column_name(index: int) -> str:
    value = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value


def sheet_xml(rows: list[list[str]]) -> str:
    output = []
    for row_index, row in enumerate(rows, 1):
        cells = []
        for column_index, value in enumerate(row, 1):
            ref = f"{column_name(column_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        output.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(output) + "</sheetData></worksheet>"


def make_workbook(path: Path, category: str = "textiles", name: str = "Test Shirt") -> None:
    headers = ["slug", "code", "category", "main_image", "gallery_images", "material", "sizes", "published", "order", "en_name", "en_subtitle", "en_material", "en_description", "mk_name", "mk_subtitle", "mk_material", "mk_description", "sq_name", "sq_subtitle", "sq_material", "sq_description"]
    product = ["test-shirt", "TEST-001", category, "test-shirt.png", "", "Cotton", "S-XXL", "FALSE", "50", name, "Personalised shirt", "Cotton", "English description", "Тест маица", "Персонализирана маица", "Памук", "Опис на македонски", "Bluzë test", "Bluzë e personalizuar", "Pambuk", "Përshkrim në shqip"]
    colours = [["product_slug", "hex", "en", "mk", "sq"], ["test-shirt", "#112233", "Navy", "Темно сина", "Blu e errët"]]
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    package_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook = '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Products" sheetId="1" r:id="rId1"/><sheet name="Colours" sheetId="2" r:id="rId2"/></sheets></workbook>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml([headers, product]))
        archive.writestr("xl/worksheets/sheet2.xml", sheet_xml(colours))


def main() -> None:
    source = Path(__file__).with_name("import-products.py")
    spec = importlib.util.spec_from_file_location("artink_importer", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="artink-import-test-") as directory:
        root = Path(directory)
        module.ROOT = root
        module.IMPORTS = root / "content/imports"
        module.PRODUCTS = root / "content/products"
        module.IMAGES = root / "public/images"
        for folder in [module.IMPORTS / "files", module.PRODUCTS, module.IMAGES, root / "content/categories"]:
            folder.mkdir(parents=True, exist_ok=True)
        (root / "content/categories/textiles.json").write_text('{"slug":"textiles"}', encoding="utf-8")
        workbook = module.IMPORTS / "files/products.xlsx"
        images = module.IMPORTS / "files/images.zip"
        make_workbook(workbook)
        with zipfile.ZipFile(images, "w") as archive:
            archive.writestr("test-shirt.png", b"safe-image-fixture")
        request = {"title": "First batch", "mode": "create", "workbook": "/content/imports/files/products.xlsx", "images_zip": "/content/imports/files/images.zip", "status": "pending"}
        request_path = module.IMPORTS / "first.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        assert module.process_request(request_path) == "completed"
        product = json.loads((module.PRODUCTS / "test-shirt.json").read_text(encoding="utf-8"))
        assert product["en"]["name"] == "Test Shirt" and product["colors"][0]["hex"] == "#112233"
        assert (module.IMAGES / "test-shirt.png").read_bytes() == b"safe-image-fixture"

        duplicate = module.IMPORTS / "duplicate.json"
        duplicate.write_text(json.dumps({**request, "title": "Duplicate", "status": "pending"}), encoding="utf-8")
        assert module.process_request(duplicate) == "failed"
        assert "already exists" in json.loads(duplicate.read_text(encoding="utf-8"))["report"]

        make_workbook(workbook, name="Updated Shirt")
        update = module.IMPORTS / "update.json"
        update.write_text(json.dumps({**request, "title": "Update", "mode": "upsert", "status": "pending"}), encoding="utf-8")
        assert module.process_request(update) == "completed"
        assert json.loads((module.PRODUCTS / "test-shirt.json").read_text(encoding="utf-8"))["en"]["name"] == "Updated Shirt"

        make_workbook(workbook, category="unknown")
        invalid = module.IMPORTS / "invalid.json"
        invalid.write_text(json.dumps({**request, "title": "Invalid", "mode": "upsert", "status": "pending"}), encoding="utf-8")
        assert module.process_request(invalid) == "failed"
        assert "unknown category" in json.loads(invalid.read_text(encoding="utf-8"))["report"]
    print("PASS: XLSX create, duplicate protection, update, colours, images and category validation.")


if __name__ == "__main__":
    main()
