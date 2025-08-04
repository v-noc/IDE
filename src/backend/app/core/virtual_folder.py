from .base import DomainObject
from ..models import node, edges
from ..db import collections as db
from typing import Dict, Any, Optional, List, Union
from .virtual_file import VirtualFile
from .code_elements import Function, Class


class VirtualFolder(DomainObject[node.VirtualFolderNode]):
    """
    A domain object representing a virtual folder.
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

    def to_dict(self) -> dict:
        """
        Serializes the virtual folder to a dictionary, including information
        about any linked code element.
        """
        # Find the link originating from this virtual folder
        link_edge = db.links_to_edges.find_one({"from_id": self.id})

        linked_element_data = None
        if link_edge:
            # If a link exists, fetch the linked node
            linked_node = db.nodes.get(link_edge.to_id)
            if linked_node:
                linked_element_data = {
                    "id": linked_node.id,
                    "name": linked_node.name,
                    "qname": linked_node.qname,
                    "node_type": linked_node.node_type
                }

        return {
            "key": self.key,
            "name": self.name,
            "qname": self.qname,
            "description": self.description,
            "node_type": self.node_type,
            "linked_element": linked_element_data,
        }

    def delete(self) -> None:
        db.nodes.delete(self.model.key)

    def update(self, update_data: dict) -> 'VirtualFolder':
        updated_model = self.model.model_copy(update=update_data)
        db.nodes.update(updated_model)
        return self.get_by_key(self.key)
    
    def add_code_element_with_dependencies(
        self,
        element: Union[Function, Class],
        target_virtual_file: Optional[VirtualFile] = None,
        virtual_file_name: Optional[str] = None,
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Adds a code element (function or class) to a virtual file within this
        folder along with all its dependencies if requested.
        
        Args:
            element: The Function or Class to add
            target_virtual_file: Existing virtual file to add to (optional)
            virtual_file_name: Name for new virtual file if not provided
            include_dependencies: Whether to include all dependencies
            
        Returns:
            Dict containing information about what was added
        """
        # Determine target virtual file
        if target_virtual_file is None:
            if virtual_file_name is None:
                virtual_file_name = f"{element.name}_virtual_file"
            
            # Create new virtual file
            target_virtual_file = self.add_virtual_file(
                file_name=virtual_file_name,
                description=f"Virtual file for {element.name} and dependencies"
            )
        
        # Add the element and its dependencies to the virtual file
        result = target_virtual_file.add_code_element_with_dependencies(
            element=element,
            include_dependencies=include_dependencies
        )
        
        # Add virtual file information to result
        result['virtual_file'] = {
            'id': target_virtual_file.id,
            'name': target_virtual_file.name,
            'qname': target_virtual_file.qname
        }
        
        return result
    
    def add_code_elements_to_separate_files(
        self,
        elements: List[Union[Function, Class]],
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Adds multiple code elements to separate virtual files.

        Each element gets its own virtual file with its dependencies.
        
        Args:
            elements: List of Functions or Classes to add
            include_dependencies: Whether to include dependencies
            
        Returns:
            A dict with info about all created elements and files.
        """
        results = {
            'virtual_files_created': [],
            'total_elements_added': 0,
            'elements_by_file': {}
        }
        
        for element in elements:
            result = self.add_code_element_with_dependencies(
                element=element,
                virtual_file_name=f"{element.name}_module",
                include_dependencies=include_dependencies
            )
            
            file_info = result['virtual_file']
            results['virtual_files_created'].append(file_info)
            results['total_elements_added'] += result['total_count']
            results['elements_by_file'][file_info['name']] = {
                'functions': result['functions'],
                'classes': result['classes'],
                'packages': result['packages'],
                'count': result['total_count']
            }
        
        return results
    
    def get_all_code_elements_summary(self) -> Dict[str, Any]:
        """
        Gets a summary of all code elements across all virtual files in this
        folder.
        
        Returns:
            Dict with aggregated code elements information
        """
        virtual_files = self.get_virtual_files()
        
        all_functions = []
        all_classes = []
        all_packages = []
        files_summary = []
        
        for vf in virtual_files:
            file_summary = vf.get_code_elements_summary()
            files_summary.append({
                'file_id': vf.id,
                'file_name': vf.name,
                'file_qname': vf.qname,
                'summary': file_summary
            })
            
            all_functions.extend(file_summary['functions'])
            all_classes.extend(file_summary['classes'])
            all_packages.extend(file_summary['packages'])
        
        return {
            'aggregated': {
                'functions': all_functions,
                'classes': all_classes,
                'packages': all_packages,
                'total_count': (
                    len(all_functions) + len(all_classes) + len(all_packages)
                )
            },
            'by_file': files_summary,
            'virtual_files_count': len(virtual_files)
        }

    def add_virtual_file(
        self, file_name: str,  description: Optional[str] = None
    ) -> VirtualFile:
        virtual_file = node.VirtualFileNode(
            qname=f"{self.qname}.{file_name}",
            name=file_name,
            description=description
        )
        created_virtual_file = db.nodes.create(virtual_file)
        contains_edge_model = edges.VirtualContainsEdge(
            _from=self.id,
            _to=created_virtual_file.id,
        )
        db.virtual_contains_edges.create(contains_edge_model)
        return VirtualFile(created_virtual_file)

    def get_virtual_files(self) -> List[VirtualFile]:
        return [VirtualFile(file) for file in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            filter_by_type="virtual_file"
        )]

    def add_virtual_folder(
        self, folder_name: str, description: Optional[str] = None
    ) -> 'VirtualFolder':
        virtual_folder = node.VirtualFolderNode(
            qname=f"{self.qname}.{folder_name}",
            name=folder_name,
            description=description
        )
        created_virtual_folder = db.nodes.create(virtual_folder)
        contains_edge_model = edges.VirtualContainsEdge(
            _from=self.id,
            _to=created_virtual_folder.id,
        )
        db.virtual_contains_edges.create(contains_edge_model)
        return VirtualFolder(created_virtual_folder)

    def get_virtual_folders(self) -> List['VirtualFolder']:
        return [VirtualFolder(folder) for folder in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            filter_by_type="virtual_folder"
        )]

    def get_descendant_tree(self) -> Dict[str, Any]:
        """
        Retrieves all descendants of this folder and formats them as a tree.
        This implementation uses a single database query for efficiency.
        """
        # This assumes 'virtual_contains_edges' has a 
        # 'get_descendant_tree_query' method, similar to the one used for 
        # real 'contains_edges'.
        cursor = db.virtual_contains_edges.get_descendant_tree_query(self.id)

        node_map = {
            self.id: {
                "node": self.model.model_dump(by_alias=True), "children": []
            }
        }

        for item in cursor:
            node_data = item['vertex']
            parent_id = item['parent_id']

            node_id = node_data['_id']
            if node_id not in node_map:
                node_map[node_id] = {"node": node_data, "children": []}

            if parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])

        def build_tree(node_id):
            node_info = node_map[node_id]
            return {
                **node_info["node"],
                "children": [
                    build_tree(child["node"]["_id"])
                    for child in node_info["children"]
                ]
            }

        return build_tree(self.id)

    def link_to_code_element(self, code_element_id: str) -> bool:
        try:
            if not db.nodes.get(code_element_id):
                return False
            
            edge_model = edges.LinksToEdge(
                _from=self.id,
                _to=code_element_id,
            )
            print(edge_model)
            db.links_to_edges.create(edge_model)
            return True
        except Exception as e:
            print(e)    
            return False
    

