import logging
from pathlib import Path
from typing import Optional
import uuid

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.model.nodes import ProjectNode

logger = logging.getLogger(__name__)

class HierarchyBuilder:
    def __init__(self, project_node: ProjectNode, scope_manager: ScopeManager):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.manager = scope_manager

    def build_hierarchy(self, rel_path: Path, checksum: str) -> Optional[ScopeModel]:
        """
        Builds the scope hierarchy for the given relative path.
        Returns the ScopeModel for the file itself.
        """
        parts = rel_path.parts
        current_qname = self.project_node.name
        current_parent_id = None
        
        # Get/Create Root
        root = self.manager.get_scope_by_qname(current_qname)
        if not root:
             # Use manager.create_scope
             root = self.manager.create_scope(
                 name=self.project_node.name,
                 qname=current_qname,
                 scope_type=ScopeType.FOLDER,
                 file_path=str(self.project_path),
                 start_line=0, start_col=0, end_line=0, end_col=0,
                 scope_id=str(uuid.uuid4())
             )
        
        current_parent_id = root.id
        scope = root # Default to root if parts empty (unlikely)

        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            
            name = part
            if is_last:
                name = Path(part).stem
            
            current_qname = f"{current_qname}.{name}"
            
            # Check if exists
            scope = self.manager.get_scope_by_qname(current_qname)
            
            if not scope:
                new_id = str(uuid.uuid4())
                scope_type = ScopeType.FILE if is_last else ScopeType.FOLDER
                
                path_so_far = self.project_path / Path(*parts[:i+1])
                
                # Note: create_scope doesn't support checksum yet in manager signature
                # We need to update manager signature or pass it somehow.
                # For now, let's assume we update manager signature too or use kwargs if flexible?
                # The manager signature is explicit. I should update it.
                # But for now I will omit checksum or update manager first.
                # Wait, I should update manager first to support checksum.
                
                scope = self.manager.create_scope(
                    name=name,
                    qname=current_qname,
                    scope_type=scope_type,
                    file_path=str(path_so_far),
                    start_line=0, start_col=0, end_line=0, end_col=0,
                    scope_id=new_id,
                    checksum=checksum if is_last else None
                )
                # Checksum handling:
                # If I update manager to take checksum, I can pass it.
                # I will update manager in next step.
                
                if current_parent_id:
                    self.manager.link_parent_child(current_parent_id, scope.id)
            
            current_parent_id = scope.id
            
        return scope
