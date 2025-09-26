from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

class NodeType(str, Enum):
    # Core tracking nodes
    NAME = "name"
    ATTRIBUTE = "attribute"
    
    # Definition nodes
    FUNCTION = "function"
    CLASS = "class"
    
    # Import nodes
    IMPORT = "import"
    IMPORT_FROM = "import_from"
    IMPORT_ALIAS = "import_alias"
    
    # Usage nodes
    CALL = "call"
    ASSIGN = "assign"
    ANN_ASSIGN = "ann_assign"
    
    # Function parts
    ARG = "arg"
    KEYWORD = "keyword"
    SUBSCRIPT = "subscript"

class NodePosition(BaseModel):
    line_no: int
    col_offset: int
    end_line_no: Optional[int] = None
    end_col_offset: Optional[int] = None

class BaseNode(BaseModel):
    node_type: NodeType
    position: NodePosition

class ParentNode(BaseNode):
    children: List["BaseNode"] = Field(default_factory=list)

# Core reference nodes
class NameNode(BaseNode):
    node_type: NodeType = NodeType.NAME
    name: str

class AttributeNode(BaseNode):
    node_type: NodeType = NodeType.ATTRIBUTE
    name: str  # The attribute name (e.g., 'method' in obj.method)
    value: Optional[Union["NameNode", "AttributeNode"]] = None  # The object being accessed

class SubscriptNode(BaseNode):
    """Represents a complex subscripted type like List[int] or Dict[str, User]"""
    node_type: NodeType = NodeType.SUBSCRIPT
    full_str: str  # The full, readable string representation, e.g., "List[Union[s,b]]"
    elements: List[Union[NameNode, AttributeNode]] = Field(default_factory=list) # A flat list of all names found inside

# Import nodes
class ImportAliasNode(BaseNode):
    node_type: NodeType = NodeType.IMPORT_ALIAS
    name: str
    asname: Optional[str] = None

class ImportNode(BaseNode):
    node_type: NodeType = NodeType.IMPORT
    names: List[ImportAliasNode] = Field(default_factory=list)

class ImportFromNode(BaseNode):
    node_type: NodeType = NodeType.IMPORT_FROM
    module_name: Optional[str] = None
    names: List[ImportAliasNode] = Field(default_factory=list)
    level: int = 0

# Function/Class definition nodes
class ArgNode(BaseNode):
    node_type: NodeType = NodeType.ARG
    name: str
    annotation: Optional[Union[NameNode, AttributeNode, SubscriptNode, str]] = None

class FunctionNode(ParentNode):
    node_type: NodeType = NodeType.FUNCTION
    name: str
    args: List[ArgNode] = Field(default_factory=list)
    return_annotation: Optional[Union[NameNode, AttributeNode, SubscriptNode,str]] = None
    return_values: List[Union[NameNode, AttributeNode, SubscriptNode,str]] = Field(default_factory=list)
    decorator_list: List[Union[NameNode, AttributeNode]] = Field(default_factory=list)

class ClassNode(ParentNode):
    node_type: NodeType = NodeType.CLASS
    name: str
    implements: List[Union[NameNode, AttributeNode]] = Field(default_factory=list)
    decorator_list: List[Union[NameNode, AttributeNode]] = Field(default_factory=list)

# Usage tracking nodes

class KeywordNode(BaseNode):
    node_type: NodeType = NodeType.KEYWORD
    name: str
    value: Optional[Union[NameNode, AttributeNode, BaseNode,str,object]] = None

class CallNode(BaseNode):
    node_type: NodeType = NodeType.CALL
    func: Union[NameNode, AttributeNode, "BaseNode"]  # Function being called
    args: List[Union[NameNode, AttributeNode,object]] = Field(default_factory=list)  # Only track name/attribute args
    keywords: List[KeywordNode] = Field(default_factory=list)

class AssignNode(BaseNode):
    node_type: NodeType = NodeType.ASSIGN
    targets: List[NameNode|AttributeNode] = Field(default_factory=list)  # Variables being assigned
    value: List[NameNode|AttributeNode|CallNode] = Field(default_factory=list)

class AnnAssignNode(BaseNode):
    node_type: NodeType = NodeType.ANN_ASSIGN
    target: NameNode|AttributeNode
    annotation: Union[NameNode, AttributeNode, SubscriptNode,str]
    value: List[Union[NameNode, AttributeNode, CallNode]] = Field(default_factory=list)


