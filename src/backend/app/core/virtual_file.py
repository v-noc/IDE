from .base import DomainObject
from ..models import node, edges
from ..db import collections as db
from typing import Dict, Any, Union
from .code_elements import Function, Class, Package
from .dependency_resolver import DependencyResolver


class VirtualFile(DomainObject[node.VirtualFileNode]):
    """
    A domain object representing a virtual file.
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
    def get_by_key(key: str) -> 'VirtualFile':
        return VirtualFile(db.nodes.get(key))

    @staticmethod
    def get_by_qname(qname: str) -> 'VirtualFile':
        return VirtualFile(db.nodes.find_one(
            {"qname": qname, "node_type": "virtual_file"}
        ))
    
    def delete(self) -> None:
        db.nodes.delete(self.model.key)

    def update(self, update_data: dict) -> 'VirtualFile':
        updated_model = self.model.model_copy(update=update_data)
        db.nodes.update(updated_model)
        return self.get_by_key(self.key)

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


    
    def add_code_element_with_dependencies(
        self, 
        element: Union[Function, Class],
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Adds a code element (function or class) to this virtual file along with
        all its dependencies if requested.
        
        Args:
            element: The Function or Class to add
            include_dependencies: Whether to include all dependencies
            
        Returns:
            Dict containing information about what was added
        """
        resolver = DependencyResolver()
        elements_to_add = {}
        
        if include_dependencies:
            # Get all dependencies
            dependencies = resolver.resolve_dependencies(element)
            elements_to_add = dependencies
        else:
            # Just add the single element
            elements_to_add[element.id] = element
        
        # Create virtual contains edges for all elements
        added_elements = {
            'functions': [],
            'classes': [],
            'packages': [],
            'total_count': 0
        }
        
        for element_id, element_obj in elements_to_add.items():
            # Check if already exists in this virtual file
            existing_edge = db.virtual_contains_edges.find_one({
                'from_id': self.id,
                'to_id': element_id
            })
            
            if existing_edge:
                continue  # Skip if already linked
            
            # Create virtual contains edge
            contains_edge = edges.VirtualContainsEdge(
                _from=self.id,
                _to=element_id
            )
            db.virtual_contains_edges.create(contains_edge)
            
            # Categorize for response
            if isinstance(element_obj, Function):
                added_elements['functions'].append({
                    'id': element_obj.id,
                    'name': element_obj.name,
                    'qname': element_obj.qname
                })
            elif isinstance(element_obj, Class):
                added_elements['classes'].append({
                    'id': element_obj.id,
                    'name': element_obj.name,
                    'qname': element_obj.qname
                })
            elif isinstance(element_obj, Package):
                added_elements['packages'].append({
                    'id': element_obj.id,
                    'name': element_obj.name,
                    'qname': element_obj.qname
                })
            
            added_elements['total_count'] += 1
        
        return added_elements
    
    def remove_code_element(self, element_id: str) -> bool:
        """
        Removes a code element from this virtual file by deleting the 
        virtual contains edge.
        
        Args:
            element_id: The ID of the element to remove
            
        Returns:
            True if removed, False if not found
        """
        edge = db.virtual_contains_edges.find_one({
            'from_id': self.id,
            'to_id': element_id
        })
        
        if edge:
            db.virtual_contains_edges.delete(edge.key)
            return True
        return False
    
    def get_code_elements_summary(self) -> Dict[str, Any]:
        """
        Gets a summary of all code elements in this virtual file.
        
        Returns:
            Dict with categorized code elements
        """
        functions = self.get_functions()
        classes = self.get_classes()
        packages = self.get_packages()
        
        return {
            'functions': [
                {'id': f.id, 'name': f.name, 'qname': f.qname} 
                for f in functions
            ],
            'classes': [
                {'id': c.id, 'name': c.name, 'qname': c.qname} 
                for c in classes
            ],
            'packages': [
                {'id': p.id, 'name': p.name, 'qname': p.qname} 
                for p in packages
            ],
            'total_count': len(functions) + len(classes) + len(packages)
        }

    def get_functions(self) -> list[Function]:
        return [Function(function) for function in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="function"
        )]

    def get_classes(self) -> list[Class]:
        return [Class(class_) for class_ in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="class"
        )]

    def get_packages(self) -> list[Package]:
        return [Package(package) for package in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="package"
        )]

    def link_to_code_element(self, code_element_id: str) -> bool:
        try:
            if not db.nodes.get(code_element_id):
                return False
            
            edge_model = edges.LinksToEdge(
                _from=self.id,
                _to=code_element_id,
            )
            db.links_to_edges.create(edge_model)
            return True
        except Exception as e:
            print(e)    
            return False
    
    def get_descendant_tree(self) -> Dict[str, Any]:
        pass