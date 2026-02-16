import uuid
import logging
from pathlib import Path
from app.core.parser.ast.id_injector import inject_module_metadata
from app.core.model.schemas import FolderSchema
logger = logging.getLogger(__name__)


class FolderTracker:
    def __init__(self):
        self.folder_changes = []

    def ensure_tracking(self, folder_path: Path) -> str:
        """
        Ensure that the folder is tracked by creating a __init__.py file if it doesn't exist.
        Injects a 'FolderID' into the file's docstring.
        Returns the FolderID.
        """
        init_file = folder_path / "__init__.py"

        if not init_file.exists():
            init_file.write_text('')
            logger.info(f"Created __init__.py for {folder_path}")

        try:
            content = init_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {init_file}: {e}")
            # Fallback to a new ID if we can't read file, but this is bad
            return None

        from app.core.parser.ast.id_injector import IDInjector
        import libcst as cst

        try:
            module = cst.parse_module(content)
            doc = module.get_docstring(clean=True)
            meta = IDInjector()._extract_metadata(doc)

            existing_id = meta.get("FolderID")
            if existing_id:
                folder_id = existing_id
            else:
                folder_id = str(uuid.uuid4())

                # Now ensure it is written
                new_content, modified = inject_module_metadata(
                    content, {"FolderID": folder_id})

                if modified:

                    init_file.write_text(new_content, encoding="utf-8")

            return f"{FolderSchema.__name__}/{folder_id}"

        except Exception as e:
            logger.error(f"Error processing {init_file}: {e}")
            return str(uuid.uuid4())
