from .base import DomainObject
from ..models import node, edges
from ..db import collections as db
from typing import Dict, Any, Optional, List, Union
from .code_elements import Function, Class
from arango.exceptions import DocumentInsertError


class VirtualFolder(DomainObject[node.VirtualFolderNode]):
    """
    A domain object representing a virtual folder that can contain other
    virtual folders, each linked to a single code element.
    """
    @property
    def key(self) -> str:
        return self.model.key

    @property
    def name(self) -> str:
        return self.model.name

    @property
    def qname(self) -> str:
        return self.model.qname

    @property
    def description(self) -> str | None:
        return self.model.description
    
    @property
    def node_type(self) -> str:
        return self.model.node_type

    @staticmethod
    def get_by_key(key: str) -> 'VirtualFolder':
        return VirtualFolder(db.nodes.get(key))

    @staticmethod
    def get_folder_linked_to_element(
        element_id: str
    ) -> Optional['VirtualFolder']:
        """Finds the virtual folder that is linked to a given code element."""
        link = db.links_to_edges.find_one({"to_id": element_id})
        if link:
            folder_node = db.nodes.get(link.from_id)
            if folder_node and folder_node.node_type == 'virtual_folder':
                return VirtualFolder(folder_node)
        return None

    def to_dict(self) -> dict:
        """
        Serializes the virtual folder, including info about any linked element,
        and recursively serializes its children.
        """
        link_edge = db.links_to_edges.find_one({"from_id": self.id})
        linked_element_data = None
        
        if link_edge:
            linked_node = db.nodes.get(link_edge.to_id)
            if linked_node:
                linked_element_data = {
                    "id": linked_node.id,
                    "name": linked_node.name,
                    "qname": linked_node.qname,
                    "node_type": linked_node.node_type,
                }

        children = [child.to_dict() for child in self.get_virtual_folders()]

        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "qname": self.qname,
            "description": self.description,
            "node_type": self.node_type,
            "link_to": linked_element_data,
            "children": children,
            "call_order": getattr(self.model, 'call_order', None),
        }

    def delete(self) -> None:
        db.nodes.delete(self.model.key)

    def update(self, update_data: dict) -> 'VirtualFolder':
        updated_model = self.model.model_copy(update=update_data)
        db.nodes.update(updated_model)
        return self.get_by_key(self.key)

    def add_virtual_folder(
        self, folder_name: str, description: Optional[str] = None, call_order: Optional[int] = None
    ) -> 'VirtualFolder':
        virtual_folder = node.VirtualFolderNode(
            qname=f"{self.qname}.{folder_name}", name=folder_name,
            description=description, call_order=call_order
        )
        created_node = db.nodes.create(virtual_folder)
        edge = edges.VirtualContainsEdge(
            _from=self.id, _to=created_node.id
        )
        db.virtual_contains_edges.create(edge)
        return VirtualFolder(created_node)

    def get_virtual_folders(self) -> List['VirtualFolder']:
        return [
            VirtualFolder(f) for f in db.nodes.find_related(
                start_node_id=self.id,
                edge_collection=db.virtual_contains_edges,
                filter_by_type="virtual_folder",
                limit=100
            )
        ]

    def get_descendant_tree(self) -> Dict[str, Any]:
        """
        Builds a recursive JSON tree of the virtual folder and its descendants.
        Includes import information from UsesImportEdge edges.
        """
        cursor = db.virtual_contains_edges.get_descendant_tree_query(self.id)
        
        node_map: Dict[str, Dict[str, Any]] = {}
        
        # Process the root node first
        root_data = self._to_dict_with_imports()
        root_data["children"] = []
        node_map[self.id] = root_data

        # Process descendant nodes
        for item in cursor:
            node_data, parent_id = item['vertex'], item['parent_id']
            node_id = node_data['_id']

            if node_id not in node_map:
                # Create VirtualFolder and serialize to dict
                vf_node_model = node.VirtualFolderNode.model_validate(
                    node_data
                )
                vf = VirtualFolder(vf_node_model)
                serialized_node = vf._to_dict_with_imports()
                serialized_node["children"] = []
                node_map[node_id] = serialized_node

            # Link child to parent
            if parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])

        return node_map.get(self.id, {})

    def _to_dict_with_imports(self) -> dict:
        """
        Helper method to serialize virtual folder with import information from UsesImportEdge.
        """
        link_edge = db.links_to_edges.find_one({"from_id": self.id})
        linked_element_data = None
        imports_data = None
        
        if link_edge:
            linked_node = db.nodes.get(link_edge.to_id)
            if linked_node:
                linked_element_data = {
                    "id": linked_node.id,
                    "name": linked_node.name,
                    "qname": linked_node.qname,
                    "node_type": linked_node.node_type,
                }
                
                # Get imports using UsesImportEdge
                import_edges = db.uses_import_edges.find({"from_id": linked_node.id})
                if import_edges:
                    imports_data = {}
                    for import_edge in import_edges:
                        alias = import_edge.alias or import_edge.target_symbol
                        imports_data[alias] = import_edge.target_qname

        result = {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "qname": self.qname,
            "description": self.description,
            "node_type": self.node_type,
            "link_to": linked_element_data,
            "call_order": getattr(self.model, 'call_order', None),
        }
        
        # Add imports if we found any
        if imports_data:
            result["imports"] = imports_data
            
        return result

    def link_to_code_element(self, code_element_id: str):
        if not db.nodes.get(code_element_id):
            raise ValueError(f"Code element '{code_element_id}' not found.")
        
        edge = edges.LinksToEdge(from_id=self.id, to_id=code_element_id)
        try:
            db.links_to_edges.create(edge)
        except DocumentInsertError as e:
            if e.error_code == 1210:
                raise ValueError(f"Folder '{self.name}' is already linked.")
            raise

    def create_folder_for_element(
        self, element: Union[Function, Class]
    ) -> 'VirtualFolder':
        """
        Creates a new virtual folder under `self`, names it after the element,
        links it to the element, and recursively creates folders for its
        dependencies using the actual call order from CallEdges.
        """
        created_folders = {}  # element_id -> VirtualFolder
        current_path = []  # (caller_id, callee_id) pairs
        return self._create_folder_recursively(element, current_path, created_folders)

    def _create_folder_recursively(
        self,
        element: Union[Function, Class],
        current_path: list[tuple[str, str]],
        created_folders: dict[str, 'VirtualFolder'],
    ) -> "VirtualFolder":
        """
        Creates a virtual folder for an element and recursively creates
        folders for its dependencies in the correct call order.
        Uses caller-callee path tracking and creates edges to existing folders.
        """
        # Create folder for this element if not already created
        if element.id not in created_folders:
            new_folder = self.add_virtual_folder(
                folder_name=element.name,
                description=element.model.description,
            )
            new_folder.link_to_code_element(element.id)
            created_folders[element.id] = new_folder
        else:
            new_folder = created_folders[element.id]
        
        # Get all CallEdges from this element, sorted by order
        if isinstance(element, Class):
            # For classes, only process __init__ method calls
            init_method_id = None
            
            # Find the __init__ method
            for method in element.methods:
                if method.name == "__init__":
                    init_method_id = method.id
                    break
            
            if init_method_id:
                call_edges = db.calls_edges.find({"from_id": init_method_id})
                print(f"Processing {element.name}.__init__ - found {len(call_edges)} call edges:")
            else:
                call_edges = []
                print(f"Processing {element.name} - no __init__ method found, skipping")
        else:
            # For functions, process their direct calls
            call_edges = db.calls_edges.find({"from_id": element.id})
            print(f"Processing {element.name} - found {len(call_edges)} call edges:")
        
        # Sort by order to maintain source code call sequence
        call_edges = sorted(call_edges, key=lambda edge: edge.order)
        
        for edge in call_edges:
            called_node = db.nodes.get(edge.to_id)
            if called_node:
                print(f"  Order {edge.order}: calls {called_node.name} ({called_node.qname})")
        
        # Create folders for called elements in order
        for call_edge in call_edges:
            called_node = db.nodes.get(call_edge.to_id)
            if called_node and called_node.node_type in ['function', 'class']:
                if called_node.node_type == 'function':
                    called_element = Function(called_node)
                else:
                    called_element = Class(called_node)
                
                # Check for infinite recursion using caller-callee pairs
                call_pair = (element.id, called_element.id)
                if call_pair in current_path:
                    print(f"  Skipping {called_element.name} - would create infinite loop")
                    continue
                
                # Add call pair to path for recursion detection
                new_path = current_path + [call_pair]
                
                if called_element.id in created_folders:
                    # Folder already exists, create edge reference
                    existing_child_folder = created_folders[called_element.id]
                    edge = edges.VirtualContainsEdge(
                        _from=new_folder.id, _to=existing_child_folder.id
                    )
                    db.virtual_contains_edges.create(edge)
                    print(f"  Created edge to existing {called_element.name}")
                else:
                    # Create new folder and recurse
                    child_folder_node = node.VirtualFolderNode(
                        qname=f"{new_folder.qname}.{called_element.name}",
                        name=called_element.name,
                        description=called_element.model.description,
                        call_order=call_edge.order
                    )
                    created_child_node = db.nodes.create(child_folder_node)
                    edge = edges.VirtualContainsEdge(
                        _from=new_folder.id, _to=created_child_node.id
                    )
                    db.virtual_contains_edges.create(edge)
                    child_folder = VirtualFolder(created_child_node)
                    child_folder.link_to_code_element(called_element.id)
                    created_folders[called_element.id] = child_folder
                    
                    print(f"  Created new folder for {called_element.name}")
                
                # Always recurse to process dependencies, but only if not in path
                if called_element.id in created_folders:
                    created_folders[called_element.id]._create_folder_recursively(
                        called_element, new_path, created_folders
                    )
        
        return new_folder

