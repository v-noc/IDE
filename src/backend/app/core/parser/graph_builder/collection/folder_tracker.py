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
            return str(uuid.uuid4())

        # Check for existing ID manually first to avoid unnecessary parsing
        # (Although inject_module_metadata parses too, this is a quick check)
        # We rely on inject_module_metadata to do the heavy lifting

        # We need to know the ID to return it.
        # So we parse first, or just generate one and let injector decide if it needs to update.
        # But to return the *correct* ID (existing one), we must extract it.
        # Since inject_module_metadata is "write-only" mostly, let's use IDInjector's helper if we could.
        # But IDInjector is in the other file. Let's just use regex or the same extraction logic.

        # Actually, let's just generate a potential new ID, pass it to injector.
        # Wait, if ID exists, we want to return THAT, not the new one.
        # And inject_module_metadata preserves existing.
        # So we need to Extract first.

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
