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
        """
        Ensures the file has a 'FileID' in its module docstring.
        Returns the FileID.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return str(uuid.uuid4())

        try:
            # Extract existing ID to return it
            module = cst.parse_module(content)
            doc = module.get_docstring(clean=True)
            meta = IDInjector()._extract_metadata(doc)

            existing_id = meta.get("FileID")
            if existing_id:
                file_id = existing_id
            else:
                file_id = str(uuid.uuid4())

                # Inject if missing
                new_content, modified = inject_module_metadata(
                    content, {"FileID": file_id})

                if modified:
                    file_path.write_text(new_content, encoding="utf-8")

            return f"{FileSchema.__name__}/{file_id}"

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return str(uuid.uuid4())
