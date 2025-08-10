# Virtual File Structure Implementation Plan

## Overview
This plan extends the existing v-noc system to support virtual file structures alongside the real file system. Users will be able to create custom organizational views, group related code elements, and maintain both real and virtual hierarchies.

## Current Architecture Analysis

### Backend (Python/FastAPI)
- **Models**: `ProjectNode`, `FolderNode`, `FileNode`, `FunctionNode`, `ClassNode`, `PackageNode`
- **Core Objects**: `Project`, `Folder`, `File` with relationship management
- **Database**: ArangoDB with nodes and edges collections
- **API**: Basic CRUD operations for projects and tree structure

### Frontend (React/TypeScript)
- **Store**: Zustand with basic virtual folder support (frontend-only)
- **Components**: `ProjectTree`, `CustomFolders`, `TreeNode`
- **Types**: `ProjectTreeResponse` interface for tree structure

### Current Limitations
1. Virtual structures are frontend-only (not persisted)
2. No linking between virtual and real code elements
3. No virtual file support (only folders)
4. No unified view of real + virtual structures

## Implementation Plan

### Phase 1: Backend Model Extensions

#### 1.1 Extend Node Models
**File**: `src/backend/app/models/node.py`

```python
# Add new virtual node types
class VirtualFolderNode(BaseNode):
    node_type: Literal["virtual_folder"] = "virtual_folder"
    name: str
    qname: str
    description: Optional[str] = None
    properties: VirtualFolderProperties
    
class VirtualFileNode(BaseNode):
    node_type: Literal["virtual_file"] = "virtual_file"
    name: str
    qname: str
    description: Optional[str] = None
    properties: VirtualFileProperties

# Update the discriminated union
Node = Annotated[
    Union[
        ProjectNode,
        FolderNode,
        FileNode,
        VirtualFolderNode,  # New
        VirtualFileNode,    # New
        FunctionNode,
        ClassNode,
        PackageNode,
    ],
    Field(discriminator="node_type"),
]
```

#### 1.2 Extend Properties Models
**File**: `src/backend/app/models/properties.py`

```python
class BaseVirtualProperties(BaseProperties):
    """Base properties for virtual nodes."""
    created_by: str = Field(..., description="User who created this virtual structure")
    created_at: str = Field(..., description="Creation timestamp")
    is_persistent: bool = Field(default=True, description="Whether to persist across sessions")
    color: Optional[str] = Field(None, description="Custom color for UI")
    icon: Optional[str] = Field(None, description="Custom icon for UI")

class VirtualFolderProperties(BaseVirtualProperties):
    """Properties for virtual folders."""
    view_type: str = Field(default="default", description="Display view type (list, grid, etc.)")
    auto_organize: bool = Field(default=False, description="Auto-organize by criteria")
    organize_criteria: Optional[str] = Field(None, description="Organization criteria (type, name, etc.)")

class VirtualFileProperties(BaseVirtualProperties):
    """Properties for virtual files."""
    virtual_content: Optional[str] = Field(None, description="Virtual file content or notes")
    file_type: str = Field(default="text", description="Virtual file type")
    template: Optional[str] = Field(None, description="Template for code generation")
```

#### 1.3 Extend Edge Models
**File**: `src/backend/app/models/edges.py`

```python
class VirtualContainsEdge(BaseEdge):
    """Links virtual nodes to real or other virtual nodes."""
    edge_type: str = "virtual_contains"
    position: NodePosition = Field(
        ..., description="The position of the contained node."
    )
    sort_order: int = Field(default=0, description="Custom sort order")

class LinksToRealEdge(BaseEdge):
    """Links virtual structures to real code elements."""
    edge_type: str = "links_to_real"
    link_type: str = Field(..., description="Type of link (reference, copy, alias)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional link metadata")

class VirtualGroupEdge(BaseEdge):
    """Groups related virtual nodes."""
    edge_type: str = "virtual_group"
    group_name: str = Field(..., description="Name of the group")
    group_type: str = Field(..., description="Type of grouping (feature, module, etc.)")
```

### Phase 2: Core Domain Extensions

#### 2.1 Virtual Folder Domain Object
**File**: `src/backend/app/core/virtual_folder.py`

```python
class VirtualFolder(DomainObject[node.VirtualFolderNode]):
    """Domain object for virtual folders."""
    
    def add_virtual_file(self, name: str, **kwargs) -> 'VirtualFile':
        """Create a virtual file within this virtual folder."""
        
    def add_real_file_reference(self, real_file_id: str, alias: str = None) -> None:
        """Link a real file to this virtual folder."""
        
    def add_virtual_folder(self, name: str, **kwargs) -> 'VirtualFolder':
        """Create a nested virtual folder."""
        
    def get_mixed_contents(self) -> List[Union['VirtualFile', 'VirtualFolder', File]]:
        """Get all contents (virtual and real references)."""
        
    def organize_by_criteria(self, criteria: str) -> None:
        """Auto-organize contents by specified criteria."""
```

#### 2.2 Virtual File Domain Object
**File**: `src/backend/app/core/virtual_file.py`

```python
class VirtualFile(DomainObject[node.VirtualFileNode]):
    """Domain object for virtual files."""
    
    def link_to_real_elements(self, element_ids: List[str]) -> None:
        """Link to real code elements (functions, classes, etc.)."""
        
    def get_linked_elements(self) -> List[Union[Function, Class]]:
        """Get all linked real code elements."""
        
    def generate_from_template(self, template_data: Dict[str, Any]) -> str:
        """Generate content from template."""
        
    def set_virtual_content(self, content: str) -> None:
        """Set custom virtual content."""
```

#### 2.3 Virtual Structure Manager
**File**: `src/backend/app/core/virtual_manager.py`

```python
class VirtualStructureManager:
    """Manages virtual file structures and their relationships."""
    
    def create_virtual_workspace(self, project_id: str, name: str) -> VirtualFolder:
        """Create a new virtual workspace for organizing project views."""
        
    def get_unified_tree(self, project_id: str, include_virtual: bool = True) -> Dict[str, Any]:
        """Get unified tree combining real and virtual structures."""
        
    def import_real_structure_as_virtual(self, source_path: str, virtual_parent_id: str) -> None:
        """Import existing real structure as virtual references."""
        
    def sync_virtual_with_real(self, virtual_id: str) -> None:
        """Sync virtual structure with changes in real files."""
```

### Phase 3: API Extensions

#### 3.1 Virtual Structure CRUD API
**File**: `src/backend/app/api/core/virtual_structures/crud.py`

```python
# Request/Response models
class VirtualFolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

class VirtualFileCreate(BaseModel):
    name: str
    parent_id: str
    file_type: str = "text"
    virtual_content: Optional[str] = None
    linked_elements: List[str] = Field(default_factory=list)

# API endpoints
@router.post("/virtual-folder", response_model=VirtualFolderResponse)
def create_virtual_folder(folder: VirtualFolderCreate, project_id: str):
    """Create a virtual folder structure."""

@router.post("/virtual-file", response_model=VirtualFileResponse)
def create_virtual_file(file: VirtualFileCreate, project_id: str):
    """Create a virtual file with optional code element links."""

@router.get("/project/{project_id}/unified-tree")
def get_unified_tree(project_id: str, include_virtual: bool = True):
    """Get combined real and virtual file tree."""

@router.post("/virtual-structure/{virtual_id}/link-elements")
def link_to_real_elements(virtual_id: str, element_ids: List[str]):
    """Link virtual structure to real code elements."""

@router.put("/virtual-structure/{virtual_id}/organize")
def auto_organize(virtual_id: str, criteria: str):
    """Auto-organize virtual structure by criteria."""
```

#### 3.2 Code Element Linking API
**File**: `src/backend/app/api/core/code_links/crud.py`

```python
@router.get("/code-elements/search")
def search_code_elements(query: str, project_id: str, element_types: List[str]):
    """Search for code elements to link to virtual structures."""

@router.post("/virtual-structure/{virtual_id}/bulk-link")
def bulk_link_elements(virtual_id: str, link_operations: List[LinkOperation]):
    """Perform bulk linking operations."""

@router.get("/virtual-structure/{virtual_id}/dependency-graph")
def get_virtual_dependency_graph(virtual_id: str):
    """Get dependency graph for virtual structure and its linked elements."""
```

### Phase 4: Frontend Extensions

#### 4.1 Enhanced Store Management
**File**: `src/frontend/src/stores/useVirtualStructureStore.ts`

```typescript
interface VirtualStructureState {
  // Existing state
  virtualFolderStructures: ProjectTreeResponse[];
  
  // New state
  virtualFiles: VirtualFile[];
  unifiedTree: UnifiedTreeNode[];
  selectedViewMode: 'real' | 'virtual' | 'unified';
  linkingMode: boolean;
  selectedRealElements: string[];
  
  // Actions
  createVirtualFile: (parentId: string, name: string, type: string) => void;
  linkElementsToVirtual: (virtualId: string, elementIds: string[]) => void;
  setViewMode: (mode: 'real' | 'virtual' | 'unified') => void;
  toggleLinkingMode: () => void;
  organizeVirtualStructure: (virtualId: string, criteria: string) => void;
  syncWithBackend: () => Promise<void>;
}
```

#### 4.2 Enhanced Tree Components
**File**: `src/frontend/src/features/Dashboard/features/Sidebar/components/UnifiedTree.tsx`

```typescript
interface UnifiedTreeProps {
  projectId: string;
  viewMode: 'real' | 'virtual' | 'unified';
  onNodeSelect: (node: UnifiedTreeNode) => void;
}

const UnifiedTree: React.FC<UnifiedTreeProps> = ({ projectId, viewMode, onNodeSelect }) => {
  // Render unified tree with virtual and real nodes
  // Support drag-drop for linking
  // Context menus for virtual operations
  // Visual indicators for node types
};
```

#### 4.3 Virtual File Management Components
**File**: `src/frontend/src/features/Dashboard/features/Sidebar/components/VirtualFileManager.tsx`

```typescript
const VirtualFileManager = () => {
  return (
    <div className="virtual-file-manager">
      <VirtualFileCreator />
      <CodeElementLinker />
      <StructureOrganizer />
      <TemplateManager />
    </div>
  );
};
```

#### 4.4 Code Element Linking Interface
**File**: `src/frontend/src/features/Dashboard/features/Sidebar/components/CodeElementLinker.tsx`

```typescript
interface CodeElementLinkerProps {
  virtualNodeId: string;
  onLink: (elementIds: string[]) => void;
}

const CodeElementLinker: React.FC<CodeElementLinkerProps> = ({ virtualNodeId, onLink }) => {
  // Search interface for code elements
  // Multi-select capabilities
  // Preview of elements to be linked
  // Dependency visualization
};
```

### Phase 5: Database Schema Updates

#### 5.1 Collections
```javascript
// New collections in ArangoDB
db._create("virtual_nodes");
db._createEdgeCollection("virtual_contains_edges");
db._createEdgeCollection("links_to_real_edges");
db._createEdgeCollection("virtual_group_edges");

// Indexes for performance
db.virtual_nodes.ensureIndex({ type: "persistent", fields: ["node_type", "project_id"] });
db.virtual_nodes.ensureIndex({ type: "persistent", fields: ["created_by", "created_at"] });
db.links_to_real_edges.ensureIndex({ type: "persistent", fields: ["_from", "_to", "link_type"] });
```

#### 5.2 Migration Scripts
**File**: `src/backend/migrations/add_virtual_structures.py`

```python
def migrate_virtual_structures():
    """Add virtual structure support to existing database."""
    # Create new collections
    # Add indexes
    # Update existing projects with virtual workspace roots
```

### Phase 6: Advanced Features

#### 6.1 Template System
**File**: `src/backend/app/core/templates/`
- Code generation templates
- Virtual file templates
- Project structure templates
- Custom template creation

#### 6.2 Smart Organization
- Auto-organize by file type, dependencies, or usage patterns
- ML-based suggestions for structure improvements
- Pattern recognition for common organizational schemes

#### 6.3 Collaboration Features  
- Shared virtual workspaces
- Team templates
- Change tracking for virtual structures
- Comments and annotations on virtual files

#### 6.4 Export/Import
- Export virtual structures as JSON
- Import from other project management tools
- Template marketplace

## Implementation Phases

### Phase 1: Foundation (1-2 weeks)
- [ ] Backend model extensions
- [ ] Basic virtual folder/file creation
- [ ] Database schema updates
- [ ] Basic API endpoints

### Phase 2: Core Functionality (2-3 weeks)
- [ ] Domain objects implementation
- [ ] Code element linking
- [ ] Frontend store updates
- [ ] Basic UI components

### Phase 3: Advanced UI (2-3 weeks)
- [ ] Unified tree view
- [ ] Drag-drop interface
- [ ] Code element linker
- [ ] Virtual file editor

### Phase 4: Enhanced Features (2-3 weeks)
- [ ] Template system
- [ ] Auto-organization
- [ ] Import/export functionality
- [ ] Performance optimization

### Phase 5: Polish & Testing (1-2 weeks)
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Performance tuning
- [ ] User experience refinement

## Technical Considerations

### Performance
- Lazy loading for large virtual structures
- Caching for frequently accessed virtual trees
- Efficient database queries with proper indexing
- Frontend virtualization for large lists

### Security
- User-based access control for virtual structures
- Validation of virtual-to-real element links
- Sanitization of virtual file content
- Rate limiting for API endpoints

### Scalability
- Horizontal scaling support
- Database partitioning strategies
- CDN for template assets
- Microservice architecture consideration

### Testing Strategy
- Unit tests for all new domain objects
- Integration tests for API endpoints
- Frontend component testing
- End-to-end user workflow testing
- Performance testing with large datasets

## Success Metrics

1. **Functionality**: Users can create and manage virtual structures
2. **Integration**: Seamless linking between virtual and real code elements  
3. **Performance**: Sub-second response times for tree operations
4. **Usability**: Intuitive UI for complex operations
5. **Reliability**: 99.9% uptime with data consistency

## Future Enhancements

1. **AI Integration**: Smart suggestions for virtual organization
2. **Version Control**: Track changes in virtual structures
3. **Mobile Support**: Mobile app for viewing virtual structures
4. **Plugin System**: Third-party extensions for virtual structure management
5. **Advanced Analytics**: Usage patterns and optimization suggestions

This plan provides a comprehensive roadmap for implementing virtual file structures while maintaining compatibility with your existing codebase and following established patterns. 