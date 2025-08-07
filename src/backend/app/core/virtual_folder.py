
from arango.exceptions import DocumentInsertError
from typing import Union, Optional

from app.db import collections as db
from app.models import edges, node
from app.models.edges import LinksToEdge
from .base import DomainObject
from .code_elements import Class, Function, to_domain_element


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
    def description(self) -> Optional[str]:
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
                domain_element = to_domain_element(linked_node)
                if domain_element:
                    linked_element_data = domain_element.to_dict()

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
        self, folder_name: str, description: Optional[str] = None,
        call_order: Optional[int] = None
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

    def get_virtual_folders(self) -> list['VirtualFolder']:
        return [
            VirtualFolder(f) for f in db.nodes.find_related(
                start_node_id=self.id,
                edge_collection=db.virtual_contains_edges,
                filter_by_type="virtual_folder",
                limit=100
            )
        ]

    def get_descendant_tree(self) -> dict[str, any]:
        """
        Builds a recursive JSON tree of the virtual folder and its descendants.
        Includes import information from UsesImportEdge edges.
        """
        cursor = db.virtual_contains_edges.get_descendant_tree_query(self.id)

        node_map: dict[str, dict[str, any]] = {}

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
        Helper method to serialize virtual folder with import information.
        """
        link_edge = self.get_linked_element_edge()
        linked_element_data = None
        if link_edge:
            linked_node = db.nodes.get(link_edge.to_id)
            if linked_node:
                domain_element = to_domain_element(linked_node)
                if domain_element:
                    linked_element_data = domain_element.to_dict()

        imports_data = []
        import_edges = self.get_imports()
        if import_edges:
            for import_edge in import_edges:
                from_node = db.nodes.get(import_edge.from_id)
                to_node = db.nodes.get(import_edge.to_id)

                from_vf = self.get_folder_linked_to_element(from_node.id)
                to_vf = self.get_folder_linked_to_element(to_node.id)

                imports_data.append({
                    "_key": import_edge.key,
                    "id": import_edge.id,
                    "from_id": import_edge.from_id,
                    "to_id": import_edge.to_id,
                    "from_parent_virtual_folder_id":
                        from_vf.id if from_vf else None,
                    "to_parent_virtual_folder_id":
                        to_vf.id if to_vf else None,
                    "alias": import_edge.alias or import_edge.target_symbol,
                    "qname": import_edge.target_qname,
                })

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

        if imports_data:
            result["imports"] = imports_data

        return result

    def remove_element_by_id(self, element_id: str) -> bool:
        """
        Removes an element from this virtual folder by its ID.
        This could be a subfolder or a linked code element.
        """
        # Check for subfolders first
        edge = db.virtual_contains_edges.find_one({
            'from_id': self.id,
            'to_id': element_id
        })
        if edge:
            db.virtual_contains_edges.delete(edge.key)
            # Optionally, delete the subfolder if it's not referenced elsewhere
            # For now, just removing the link
            return True

        return False

    def get_linked_element_edge(self) -> Optional[LinksToEdge]:
        """Returns the 'links_to' edge if it exists."""
        return db.links_to_edges.find_one({"from_id": self.id})

    def get_imports(self) -> list[edges.UsesImportEdge]:
        """
        Returns all import edges from the linked code element of this folder.
        """
        link_edge = self.get_linked_element_edge()
        if not link_edge:
            return []
        return db.uses_import_edges.find({"from_id": link_edge.to_id})

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
        self,
        element: Union[Function, Class],
        link_directly: bool = False,
    ) -> "VirtualFolder":
        """
        Creates a new virtual folder under `self`, names it after the element,
        links it to the element, and recursively creates folders for its
        dependencies using the actual call order from CallEdges.
        If `link_directly` is True, it links the element directly to `self`
        and adds its dependencies as children of `self`.
        """
        current_path = []
        created_folders = {}

        if link_directly:
            self.link_to_code_element(element.id)
            created_folders[element.id] = self

        return self._create_folder_recursively(
            element, current_path, created_folders
        )

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
        call_edges = self._get_call_edges_for_element(element)

        # Create folders for called elements in order
        for call_edge in call_edges:
            called_node = db.nodes.get(call_edge.to_id)
            if not (called_node and called_node.node_type in ['function', 'class']):
                continue

            called_element = to_domain_element(called_node)
            if not called_element:
                continue

            # Check for infinite recursion using caller-callee pairs
            call_pair = (element.id, called_element.id)
            if call_pair in current_path:
                continue

            new_path = current_path + [call_pair]

            if called_element.id in created_folders:
                # Folder already exists, create edge reference
                existing_child_folder = created_folders[called_element.id]
                edge = edges.VirtualContainsEdge(
                    _from=new_folder.id, _to=existing_child_folder.id
                )
                db.virtual_contains_edges.create(edge)
            else:
                child_folder = self._create_child_folder(
                    new_folder, called_element, call_edge.order
                )
                created_folders[called_element.id] = child_folder

            # Always recurse to process dependencies
            if called_element.id in created_folders:
                created_folders[called_element.id]._create_folder_recursively(
                    called_element, new_path, created_folders
                )

        return new_folder

    def _get_call_edges_for_element(
        self, element: Union[Function, Class]
    ) -> list[edges.CallEdge]:
        """
        Returns a sorted list of CallEdges for a given code element.
        For classes, it considers calls from the `__init__` method.
        """
        if isinstance(element, Class):
            for method in element.methods:
                if method.name == "__init__":
                    call_edges = db.calls_edges.find({"from_id": method.id})
                    return sorted(call_edges, key=lambda edge: edge.order)
            return []
        else:
            call_edges = db.calls_edges.find({"from_id": element.id})
            return sorted(call_edges, key=lambda edge: edge.order)

    def _create_child_folder(
        self,
        parent_folder: "VirtualFolder",
        element: Union[Function, Class],
        call_order: int,
    ) -> "VirtualFolder":
        """
        Creates, links, and returns a new child virtual folder.
        """
        child_folder_node = node.VirtualFolderNode(
            qname=f"{parent_folder.qname}.{element.name}",
            name=element.name,
            description=element.model.description,
            call_order=call_order
        )
        created_child_node = db.nodes.create(child_folder_node)
        edge = edges.VirtualContainsEdge(
            _from=parent_folder.id, _to=created_child_node.id
        )
        db.virtual_contains_edges.create(edge)
        child_folder = VirtualFolder(created_child_node)
        child_folder.link_to_code_element(element.id)
        return child_folder

