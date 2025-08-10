from __future__ import annotations
from arango.exceptions import DocumentInsertError
from typing import Union, Optional, TYPE_CHECKING
from app.db import collections as db
from app.models import edges, node
from app.models.edges import LinksToEdge
from .base import DomainObject
from .code_elements import Class, Function, to_domain_element
if TYPE_CHECKING:
    from .folder import Folder
    from .file import File


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

    def to_dict(self, with_dependency_tree: bool = False) -> dict:
        """
        Serializes the virtual folder, including info about any linked element,
        and recursively serializes its children.
        """
        link_edge = db.links_to_edges.find_one({"from_id": self.id})
        linked_element_data = None

        if link_edge:
            linked_node = db.nodes.get(link_edge.to_id)
            if linked_node:
                # Lazy resolve to domain object; fall back for file/folder
                domain_element = to_domain_element(linked_node)
                if (
                    not domain_element and
                    linked_node.node_type in {"file", "folder"}
                ):
                    if linked_node.node_type == "file":
                        from .file import File  # local import
                        domain_element = File(linked_node)
                    else:
                        from .folder import Folder  # local import
                        domain_element = Folder(linked_node)
                if domain_element:
                    linked_element_data = domain_element.to_dict(
                        with_dependency_tree=False
                    )

        children = [child.to_dict() for child in self.get_virtual_folders()]

        theme = None
        if self.model.properties:
            theme = (
                self.model.properties.metaData.model_dump()
                if self.model.properties.metaData
                else None
            )

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
            "theme": theme,
            "icon": self.model.icon,
        }

    def delete(self) -> None:
        """
        Deletes a virtual folder and all its descendants using a bottom-up
        approach. This method is non-recursive and ensures that child folders
        and their associated edges are removed before their parents to maintain
        data integrity.
        """
        # _collect_all_descendants performs a post-order traversal, so children
        # appear before parents. The folder itself will be the last element.
        all_folders_to_delete = self._collect_all_descendants()

        for folder in all_folders_to_delete:
            # Delete edges associated with the folder.
            db.links_to_edges.delete({"from_id": folder.id})
            db.virtual_contains_edges.delete({"from_id": folder.id})
            db.virtual_contains_edges.delete({"to_id": folder.id})

            # Delete the folder node itself.
            db.nodes.delete(folder.model.key)

    def _collect_all_descendants(self) -> list['VirtualFolder']:
        """
        Collects all descendants of this folder in a way that ensures children
        come before their parents in the list (post-order traversal).
        """
        descendants_post_order = []
        # Stack stores tuples of (folder, children_iterator)
        stack = [(self, iter(self.get_virtual_folders()))]
        visited = {self.id}

        while stack:
            parent, children_iter = stack[-1]
            try:
                child = next(children_iter)
                if child.id not in visited:
                    visited.add(child.id)
                    stack.append((child, iter(child.get_virtual_folders())))
            except StopIteration:
                # All children visited, process the parent
                folder, _ = stack.pop()
                descendants_post_order.append(folder)

        return descendants_post_order

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
        children = [
            VirtualFolder(f) for f in db.nodes.find_related(
                start_node_id=self.id,
                edge_collection=db.virtual_contains_edges,
                filter_by_type="virtual_folder",
                limit=1  # depth of traversal: direct children only
            )
        ]
        # Sort by call_order if present, then by name for stable ordering
        children.sort(
            key=lambda vf: (
                vf.model.call_order is None,
                vf.model.call_order if vf.model.call_order is not None else 0,
                vf.name.lower(),
            )
        )
        return children

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
                # Lazy resolve to domain object; fall back for file/folder
                domain_element = to_domain_element(linked_node)
                if (
                    not domain_element and
                    linked_node.node_type in {"file", "folder"}
                ):
                    if linked_node.node_type == "file":
                        from .file import File  # local import
                        domain_element = File(linked_node)
                    else:
                        from .folder import Folder  # local import
                        domain_element = Folder(linked_node)
                if domain_element:
                    linked_element_data = domain_element.to_dict(
                        with_dependency_tree=False
                    )

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
                    "from_parent_virtual_folder_id": (
                        from_vf.id if from_vf else None
                    ),
                    "to_parent_virtual_folder_id": (
                        to_vf.id if to_vf else None
                    ),
                    "alias": (
                        import_edge.alias or import_edge.target_symbol
                    ),
                    "qname": import_edge.target_qname,
                })
        theme = None
        if self.model.properties:
            theme = (
                self.model.properties.metaData.model_dump()
                if self.model.properties.metaData
                else None
            )

        result = {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "qname": self.qname,
            "description": self.description,
            "node_type": self.node_type,
            "link_to": linked_element_data,
            "call_order": getattr(self.model, 'call_order', None),
            "icon": self.model.icon,
            "theme": theme,
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
        element: Union["Folder", "File", Function, Class],
        link_directly: bool = False
    ) -> "VirtualFolder":
        """
        Creates a virtual folder structure from a code element's dependency
        tree.
        If `link_directly` is True, this folder is linked to the element;
        otherwise, a new child folder is created for it.
        """
        dependency_tree = element.to_dict(with_dependency_tree=True)
        children_data = dependency_tree.get("children", [])

        if link_directly:
            # Link this folder to the element and build the tree underneath.
            self.link_to_code_element(dependency_tree["id"])

            if children_data:
                self._create_from_dict(children_data)
            return self
        else:
            # Create a new child folder to house the tree.
            root_vf = self.add_virtual_folder(
                folder_name=dependency_tree["name"],
                description=dependency_tree.get("description"),
            )
            root_vf.link_to_code_element(dependency_tree["id"])
            if children_data:
                root_vf._create_from_dict(children_data)
            return root_vf

    def _create_from_dict(self, children_data: list[dict]):
        """
        Recursively creates virtual folders from a list of child dictionaries.
        """
        for child_dict in children_data:
            # Create the virtual folder for the current child.
            child_vf = self.add_virtual_folder(
                folder_name=child_dict["name"],
                description=child_dict.get("description"),
                call_order=child_dict.get("call_order"),
            )
            # Link it to the corresponding code element.
            child_vf.link_to_code_element(child_dict["id"])

            # If this child has its own children, recurse.
            if "children" in child_dict and child_dict["children"]:
                child_vf._create_from_dict(child_dict["children"])

    def _create_child_folder(
        self,
        parent_folder: "VirtualFolder",
        element: Union[Function, Class],
        call_order: Optional[int],
    ) -> "VirtualFolder":
        """
        Creates, links, and returns a new child virtual folder.
        """
        child_folder_node = node.VirtualFolderNode(
            qname=f"{parent_folder.qname}.{element.name}",
            name=element.name,
            description=element.model.description,
            call_order=call_order,
        )
        created_child_node = db.nodes.create(child_folder_node)
        edge = edges.VirtualContainsEdge(
            _from=parent_folder.id, _to=created_child_node.id
        )
        db.virtual_contains_edges.create(edge)
        child_folder = VirtualFolder(created_child_node)
        child_folder.link_to_code_element(element.id)
        return child_folder
