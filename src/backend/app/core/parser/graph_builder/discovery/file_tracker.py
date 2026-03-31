import uuid
import logging
from pathlib import Path
from app.core.parser.ast.id_injector import inject_module_metadata, IDInjector
import libcst as cst

from app.core.model.schemas import FileSchema

logger = logging.getLogger(__name__)


class FileTracker:
    def __init__(self):
        pass

    def process_file(self, file_path: Path) -> str:
        fid, _ = self.process_file_detailed(file_path)
        return fid

    def process_file_detailed(self, file_path: Path) -> tuple[str, bool]:
        """
        Ensures the file has a 'FileID' in its module docstring.
        Returns (FileSchema/<uuid>, modified).
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return str(uuid.uuid4()), False

        try:
            module = cst.parse_module(content)
            doc = module.get_docstring(clean=True)
            meta = IDInjector()._extract_metadata(doc)

            existing_id = meta.get("FileID")
            if existing_id:
                file_id = existing_id
                return f"{FileSchema.__name__}/{file_id}", False

            file_id = str(uuid.uuid4())
            new_content, modified = inject_module_metadata(
                content, {"FileID": file_id})

            if modified:
                file_path.write_text(new_content, encoding="utf-8")

            return f"{FileSchema.__name__}/{file_id}", modified

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return str(uuid.uuid4()), False
