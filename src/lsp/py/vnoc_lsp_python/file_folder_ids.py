"""FileID / FolderID injection (libcst), mirrored from backend FileTracker / FolderTracker."""

import logging
import uuid
from pathlib import Path

import libcst as cst

from vnoc_lsp_python.id_injector import IDInjector, inject_module_metadata

logger = logging.getLogger(__name__)

FILE_SCHEMA = "FileSchema"
FOLDER_SCHEMA = "FolderSchema"


def read_or_inject_file_id(file_path: Path) -> tuple[str, bool]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Failed to read %s: %s", file_path, e)
        return str(uuid.uuid4()), False

    try:
        module = cst.parse_module(content)
        doc = module.get_docstring(clean=True)
        meta = IDInjector()._extract_metadata(doc)

        existing_id = meta.get("FileID")
        if existing_id:
            file_id = existing_id
            return f"{FILE_SCHEMA}/{file_id}", False

        file_id = str(uuid.uuid4())
        new_content, modified = inject_module_metadata(content, {"FileID": file_id})

        if modified:
            file_path.write_text(new_content, encoding="utf-8")

        return f"{FILE_SCHEMA}/{file_id}", modified

    except Exception as e:
        logger.error("Error processing %s: %s", file_path, e)
        return str(uuid.uuid4()), False


def read_or_inject_folder_id(folder_path: Path) -> tuple[str, bool]:
    init_file = folder_path / "__init__.py"

    if not init_file.exists():
        init_file.write_text("")
        logger.info("Created __init__.py for %s", folder_path)

    try:
        content = init_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Failed to read %s: %s", init_file, e)
        return str(uuid.uuid4()), False

    try:
        module = cst.parse_module(content)
        doc = module.get_docstring(clean=True)
        meta = IDInjector()._extract_metadata(doc)

        existing_id = meta.get("FolderID")
        if existing_id:
            folder_id = existing_id
            return f"{FOLDER_SCHEMA}/{folder_id}", False

        folder_id = str(uuid.uuid4())
        new_content, modified = inject_module_metadata(
            content, {"FolderID": folder_id}
        )

        if modified:
            init_file.write_text(new_content, encoding="utf-8")

        return f"{FOLDER_SCHEMA}/{folder_id}", modified

    except Exception as e:
        logger.error("Error processing %s: %s", init_file, e)
        return str(uuid.uuid4()), False
