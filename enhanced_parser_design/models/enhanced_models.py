"""
Enhanced Models for V2 Parser Architecture

Key improvements:
1. Flattened properties (no nested properties objects)
2. Enhanced metadata for analysis
3. Better type safety and validation
4. Analysis-specific fields for caching and optimization
"""

from typing import Union, Literal, List, Optional, Dict, Any
from pydantic import Field, BaseModel
from datetime import datetime
from enum import Enum

from app.models.base import BaseNode, BaseEdge


# ===============================================================================
# Enums for Better Type Safety
# ===============================================================================


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPLETED_WITH_ISSUES = "completed_with_issues"
    FAILED = "failed"

class CallType(str, Enum):
    DIRECT = "direct"  # foo()
    METHOD = "method"  # obj.method()
    PROPERTY = "property"  # obj.prop
    ATTRIBUTE = "attribute"  # obj.attr
    CONSTRUCTOR = "constructor"  # Class()


class ScopeType(str, Enum):
    GLOBAL = "global"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    LAMBDA = "lambda"


# ===============================================================================
# Enhanced Core Models
# ===============================================================================

class ParameterInfo(BaseModel):
    """Enhanced parameter information"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_vararg: bool = False
    is_kwarg: bool = False
    position: int


class ArgumentInfo(BaseModel):
    """Call argument information"""
    value: str
    is_keyword: bool = False
    keyword_name: Optional[str] = None
    position: int


class CodePosition(BaseModel):
    """Enhanced position tracking"""
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int
    
    @property
    def span_lines(self) -> int:
        return self.end_line_no - self.line_no + 1


# ===============================================================================
# Enhanced Node Models (Flattened Properties)
# ===============================================================================

class ProjectNode(BaseNode):
    node_type: Literal["project"] = "project"
    name: str
    qname: str
    
    # Flattened properties (was ProjectProperties)
    path: str
    description: Optional[str] = None
    
    # Analysis metadata
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    last_analyzed: Optional[datetime] = None
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0


class FolderNode(BaseNode):
    node_type: Literal["folder"] = "folder"
    name: str
    qname: str
    
    # Flattened properties
    path: str
    
    # Analysis metadata
    file_count: int = 0
    subdirectory_count: int = 0


class FileNode(BaseNode):
    node_type: Literal["file"] = "file"
    name: str
    qname: str
    
    # Flattened properties (was FileProperties)
    path: str
    extension: str = ".py"
    encoding: str = "utf-8"
    
    # Analysis metadata
    line_count: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    complexity_score: Optional[float] = None
    last_modified: Optional[datetime] = None
    analysis_version: str = "1.0"
    
    # Syntax analysis
    has_syntax_errors: bool = False
    syntax_error_count: int = 0


class FunctionNode(BaseNode):
    node_type: Literal["function"] = "function"
    name: str
    qname: str
    
    # Flattened properties (was FunctionProperties)
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0
    
    # Function characteristics
    is_async: bool = False
    is_method: bool = False
    is_static: bool = False
    is_class_method: bool = False
    is_property: bool = False
    
    # Parameters and return
    parameters: List[ParameterInfo] = []
    return_type_hint: Optional[str] = None
    
    # Documentation
    docstring: Optional[str] = None
    
    # Analysis metadata
    complexity_score: Optional[int] = None
    is_tested: bool = False
    test_coverage: Optional[float] = None
    call_count: int = 0  # How many times this function is called
    calls_made: int = 0  # How many calls this function makes
    
    # Scope information
    scope_type: ScopeType = ScopeType.FUNCTION
    parent_scope_id: Optional[str] = None


class ClassNode(BaseNode):
    node_type: Literal["class"] = "class"
    name: str
    qname: str
    
    # Flattened properties (was ClassProperties)
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0
    
    # Class characteristics
    base_classes: List[str] = []  # qnames of base classes
    is_abstract: bool = False
    is_dataclass: bool = False
    
    # Documentation
    docstring: Optional[str] = None
    
    # Analysis metadata
    method_count: int = 0
    property_count: int = 0
    complexity_score: Optional[int] = None
    is_tested: bool = False
    instantiation_count: int = 0  # How many times this class is instantiated
    
    # Scope information
    scope_type: ScopeType = ScopeType.CLASS
    parent_scope_id: Optional[str] = None


class PackageNode(BaseNode):
    node_type: Literal["package"] = "package"
    name: str
    qname: str
    
    # Package information
    version: Optional[str] = None
    is_external: bool = True
    is_standard_library: bool = False
    
    # Usage tracking
    import_count: int = 0  # How many times imported in project
    usage_count: int = 0   # How many times symbols from this package are used


class VariableNode(BaseNode):
    """New node type for tracking variables and constants"""
    node_type: Literal["variable"] = "variable"
    name: str
    qname: str
    
    # Variable information
    position: CodePosition
    inferred_type: Optional[str] = None
    is_constant: bool = False
    is_global: bool = False
    
    # Scope information
    scope_id: str  # ID of the containing scope
    scope_type: ScopeType


# ===============================================================================
# Enhanced Edge Models
# ===============================================================================

class BelongsToEdge(BaseEdge):
    """Links a node to a project"""
    edge_type: str = "belongs_to"


class ContainsEdge(BaseEdge):
    """Enhanced containment relationship"""
    edge_type: str = "contains"
    position: CodePosition
    
    # Container metadata
    container_type: str  # "project", "folder", "file", "class"
    order_index: int = 0  # Order within container


class CallEdge(BaseEdge):
    """Enhanced call relationship"""
    edge_type: str = "calls"
    
    # Enhanced position tracking
    call_site: CodePosition
    
    # Call context
    call_type: CallType = CallType.DIRECT
    arguments: List[ArgumentInfo] = []
    is_conditional: bool = False  # Called within if/try/except block
    
    # Analysis metadata
    frequency: int = 1  # How many times this call appears
    confidence_score: float = 1.0  # How confident we are in this resolution
    
    # Performance data (can be populated by profiling)
    avg_execution_time: Optional[float] = None
    call_depth: int = 0  # Depth in call stack


class UsesImportEdge(BaseEdge):
    """Enhanced import usage relationship"""
    edge_type: str = "uses_import"
    
    # Import details
    target_symbol: str
    alias: Optional[str] = None
    import_position: CodePosition
    usage_positions: List[CodePosition] = []
    
    # Import type
    is_from_import: bool = False
    import_level: int = 0  # For relative imports
    
    # Usage tracking
    usage_count: int = 0
    is_used: bool = True


class ImplementsEdge(BaseEdge):
    """Links a class to one of its methods"""
    edge_type: str = "implements"
    
    # Implementation details
    implementation_type: str = "method"  # method, property, static_method, class_method
    is_override: bool = False
    overridden_method: Optional[str] = None  # qname of overridden method


class InheritsEdge(BaseEdge):
    """Class inheritance relationship"""
    edge_type: str = "inherits"
    
    # Inheritance details
    inheritance_order: int = 0  # For multiple inheritance
    is_direct: bool = True


class DefinesEdge(BaseEdge):
    """Links a scope to variables defined within it"""
    edge_type: str = "defines"
    
    # Definition details
    variable_name: str
    definition_position: CodePosition
    is_reassignment: bool = False


class ExecutesEdge(BaseEdge):
    """Control flow execution relationship"""
    edge_type: str = "executes"
    
    # Execution details
    branch_type: Optional[str] = None  # "true", "false", "except", "finally"
    condition: Optional[str] = None  # For conditional execution
    execution_order: int = 0


# ===============================================================================
# Analysis and Reporting Models
# ===============================================================================

class AnalysisIssue(BaseModel):
    """Enhanced issue reporting"""
    severity: Literal["error", "warning", "info"]
    category: str
    message: str
    
    # Location information
    file_path: Optional[str] = None
    position: Optional[CodePosition] = None
    
    # Context
    context: Dict[str, Any] = {}
    suggested_fix: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rule_id: Optional[str] = None


class AnalysisMetrics(BaseModel):
    """Comprehensive analysis metrics"""
    # Processing metrics
    files_processed: int = 0
    files_failed: int = 0
    processing_time_seconds: float = 0.0
    
    # Content metrics
    nodes_created: int = 0
    edges_created: int = 0
    symbols_resolved: int = 0
    symbols_unresolved: int = 0
    
    # Code quality metrics
    avg_complexity: float = 0.0
    max_complexity: float = 0.0
    test_coverage: float = 0.0
    
    # Dependencies
    external_dependencies: int = 0
    internal_dependencies: int = 0
    circular_dependencies: int = 0
    
    # Performance indicators
    memory_usage_mb: float = 0.0
    cache_hit_rate: float = 0.0


class AnalysisReport(BaseModel):
    """Enhanced analysis reporting"""
    project_id: str
    status: AnalysisStatus
    issues: List[AnalysisIssue] = []
    metrics: AnalysisMetrics = Field(default_factory=AnalysisMetrics)
    
    # Timing information
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Configuration
    analysis_version: str = "2.0"
    configuration: Dict[str, Any] = {}
    
    def add_issue(self, issue: AnalysisIssue):
        """Add an issue to the report"""
        self.issues.append(issue)
        
    def add_error(
        self, 
        message: str, 
        file_path: str = None, 
        position: CodePosition = None
    ):
        """Convenience method to add an error"""
        issue = AnalysisIssue(
            severity="error",
            category="ParsingError",
            message=message,
            file_path=file_path,
            position=position
        )
        self.add_issue(issue)
        
    def add_warning(
        self, 
        message: str, 
        file_path: str = None, 
        position: CodePosition = None
    ):
        """Convenience method to add a warning"""
        issue = AnalysisIssue(
            severity="warning",
            category="AnalysisWarning",
            message=message,
            file_path=file_path,
            position=position
        )
        self.add_issue(issue)


class AnalysisResult(BaseModel):
    """Final analysis result"""
    project_id: str
    report: AnalysisReport
    
    # Summary information
    success: bool = True
    nodes_created: List[str] = []  # IDs of created nodes
    edges_created: List[str] = []  # IDs of created edges
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_version: str = "2.0"


# ===============================================================================
# Discriminated Union of All Node Types
# ===============================================================================

Node = Union[
    ProjectNode,
    FolderNode,
    FileNode,
    FunctionNode,
    ClassNode,
    PackageNode,
    VariableNode,
]

# ===============================================================================
# Discriminated Union of All Edge Types  
# ===============================================================================

Edge = Union[
    BelongsToEdge,
    ContainsEdge,
    CallEdge,
    UsesImportEdge,
    ImplementsEdge,
    InheritsEdge,
    DefinesEdge,
    ExecutesEdge,
] 