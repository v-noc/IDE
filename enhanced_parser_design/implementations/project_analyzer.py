"""
Enhanced ProjectAnalyzer Implementation

This module provides the main orchestration for project analysis,
integrating with the existing domain layer while adding comprehensive
parsing capabilities.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.manager import CodeGraphManager
from app.core.project import Project
from app.core.file import File
from ..models.enhanced_models import (
    AnalysisResult, AnalysisReport, AnalysisStatus, AnalysisMetrics
)


class ProjectAnalyzer:
    """
    Enhanced project analyzer that integrates with the existing domain layer
    while providing comprehensive code analysis capabilities.
    """
    
    def __init__(self, manager: CodeGraphManager):
        self.manager = manager
        self.config = AnalyzerConfig()
        
    async def analyze_project(
        self, 
        project: Project, 
        config: Optional[AnalyzerConfig] = None
    ) -> AnalysisResult:
        """
        Main entry point for project analysis.
        
        Args:
            project: Project domain object to analyze
            config: Optional analysis configuration
            
        Returns:
            AnalysisResult with complete analysis report and metrics
        """
        analysis_config = config or self.config
        
        # Initialize analysis report
        report = AnalysisReport(
            project_id=project.id,
            status=AnalysisStatus.IN_PROGRESS,
            configuration=analysis_config.to_dict()
        )
        
        try:
            # Create orchestrator for this analysis
            orchestrator = AnalysisOrchestrator(
                project=project,
                manager=self.manager,
                config=analysis_config,
                report=report
            )
            
            # Run the analysis
            result = await orchestrator.run()
            
            # Update final status
            report.status = (
                AnalysisStatus.COMPLETED_WITH_ISSUES 
                if report.issues 
                else AnalysisStatus.COMPLETED
            )
            report.completed_at = datetime.utcnow()
            report.duration_seconds = (
                report.completed_at - report.started_at
            ).total_seconds()
            
            return result
            
        except Exception as e:
            report.add_error(f"Analysis failed: {str(e)}")
            report.status = AnalysisStatus.FAILED
            report.completed_at = datetime.utcnow()
            report.duration_seconds = (
                report.completed_at - report.started_at
            ).total_seconds()
            
            return AnalysisResult(
                project_id=project.id,
                report=report,
                success=False
            )
    
    async def analyze_incremental(
        self, 
        project: Project, 
        changed_files: List[str],
        config: Optional[AnalyzerConfig] = None
    ) -> AnalysisResult:
        """
        Perform incremental analysis on only changed files and their dependents.
        
        Args:
            project: Project domain object
            changed_files: List of file paths that have changed
            config: Optional analysis configuration
            
        Returns:
            AnalysisResult for incremental analysis
        """
        analysis_config = config or self.config
        analysis_config.incremental = True
        analysis_config.changed_files = changed_files
        
        # Use main analysis with incremental config
        return await self.analyze_project(project, analysis_config)


class AnalysisOrchestrator:
    """
    Orchestrates the multi-phase analysis process for a project.
    Handles file discovery, visitor pipeline execution, and result aggregation.
    """
    
    def __init__(
        self, 
        project: Project,
        manager: CodeGraphManager,
        config: AnalyzerConfig,
        report: AnalysisReport
    ):
        self.project = project
        self.manager = manager
        self.config = config
        self.report = report
        
        # Initialize core components
        from .symbol_registry import SymbolRegistry
        from .ast_cache import ASTCache
        from .visitor_pipeline import VisitorPipeline
        
        self.symbol_registry = SymbolRegistry(
            db_client=manager._db_client,  # Access to database
            config=config.registry_config
        )
        self.ast_cache = ASTCache(config.cache_config)
        self.visitor_pipeline = VisitorPipeline(
            symbol_registry=self.symbol_registry,
            config=config.visitor_config
        )
        
        # Analysis state
        self.metrics = AnalysisMetrics()
        
    async def run(self) -> AnalysisResult:
        """
        Run the complete analysis orchestration.
        
        Returns:
            AnalysisResult with all analysis data
        """
        start_time = datetime.utcnow()
        
        try:
            # Phase 0: Discovery and Setup
            files = await self._discover_files()
            
            if self.config.incremental:
                files = await self._filter_incremental_files(files)
            
            self.metrics.files_processed = len(files)
            
            # Phase 1: Declaration Phase (Parallelizable)
            await self._run_declaration_phase(files)
            
            # Phase 2: Analysis Phase (Dependency-aware parallelization)
            await self._run_analysis_phase(files)
            
            # Phase 3: Linking Phase (Sequential for consistency)
            await self._run_linking_phase(files)
            
            # Phase 4: Post-processing and validation
            await self._run_post_processing()
            
        except Exception as e:
            self.report.add_error(f"Orchestration failed: {str(e)}")
            self.metrics.files_failed += len(files)
            
        finally:
            # Update metrics
            end_time = datetime.utcnow()
            self.metrics.processing_time_seconds = (
                end_time - start_time
            ).total_seconds()
            
        return AnalysisResult(
            project_id=self.project.id,
            report=self.report,
            success=self.report.status != AnalysisStatus.FAILED
        )
    
    async def _discover_files(self) -> List[File]:
        """
        Discover all Python files in the project.
        Uses existing domain object methods.
        """
        try:
            # Use existing domain object method
            all_files = self.project.get_files()
            
            # Filter for Python files
            python_files = [
                file for file in all_files 
                if file.name.endswith('.py')
            ]
            
            return python_files
            
        except Exception as e:
            self.report.add_error(f"File discovery failed: {str(e)}")
            return []
    
    async def _filter_incremental_files(self, files: List[File]) -> List[File]:
        """
        Filter files for incremental analysis.
        Includes changed files and their dependents.
        """
        if not self.config.changed_files:
            return files
            
        # Find files that match changed paths
        changed_files = []
        for file in files:
            if any(file.path.endswith(changed) for changed in self.config.changed_files):
                changed_files.append(file)
        
        # Find dependent files (files that import the changed files)
        dependent_files = await self._find_dependent_files(changed_files)
        
        # Combine and deduplicate
        incremental_files = list(set(changed_files + dependent_files))
        
        self.report.add_info(
            f"Incremental analysis: {len(incremental_files)} files "
            f"({len(changed_files)} changed, {len(dependent_files)} dependent)"
        )
        
        return incremental_files
    
    async def _find_dependent_files(self, changed_files: List[File]) -> List[File]:
        """
        Find files that depend on the changed files through imports.
        This would use the existing graph structure to find dependencies.
        """
        # This would query the database for files that import the changed files
        # For now, return empty list (placeholder for MVP)
        return []
    
    async def _run_declaration_phase(self, files: List[File]) -> None:
        """
        Run the declaration phase - discover all high-level symbols.
        This phase can be fully parallelized.
        """
        self.report.add_info("Starting declaration phase")
        
        # Configure visitor pipeline for declaration phase
        self.visitor_pipeline.configure_for_phase("declaration")
        
        # Process files in parallel batches
        batch_size = self.config.parallel_batch_size
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [
                self._process_file_declarations(file) 
                for file in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for file, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.report.add_error(
                        f"Declaration phase failed for {file.path}: {str(result)}",
                        file.path
                    )
                    self.metrics.files_failed += 1
                else:
                    # Update metrics
                    self.metrics.nodes_created += len(result.get('nodes', []))
    
    async def _process_file_declarations(self, file: File) -> Dict[str, Any]:
        """
        Process a single file for declarations.
        """
        try:
            # Read and parse file
            content = await self._read_file_content(file)
            ast_tree = await self.ast_cache.parse_file(file.path, content)
            
            # Run declaration visitors
            result = await self.visitor_pipeline.process_file_phase(
                file=file,
                ast_tree=ast_tree,
                phase="declaration",
                report=self.report
            )
            
            # Store nodes in database via domain objects
            await self._store_nodes(result.nodes, file)
            
            return {
                'nodes': result.nodes,
                'success': True
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    async def _run_analysis_phase(self, files: List[File]) -> None:
        """
        Run the analysis phase - deep analysis with visitors.
        This phase has limited parallelization due to dependencies.
        """
        self.report.add_info("Starting analysis phase")
        
        # Configure visitor pipeline for analysis phase
        self.visitor_pipeline.configure_for_phase("analysis")
        
        # Process files with dependency awareness
        # For MVP, process sequentially to avoid complexity
        for file in files:
            try:
                await self._process_file_analysis(file)
            except Exception as e:
                self.report.add_error(
                    f"Analysis phase failed for {file.path}: {str(e)}",
                    file.path
                )
                self.metrics.files_failed += 1
    
    async def _process_file_analysis(self, file: File) -> None:
        """
        Process a single file for detailed analysis.
        """
        # Get cached AST
        ast_tree = self.ast_cache.get(file.path)
        if not ast_tree:
            # Re-parse if not in cache
            content = await self._read_file_content(file)
            ast_tree = await self.ast_cache.parse_file(file.path, content)
        
        # Run analysis visitors
        result = await self.visitor_pipeline.process_file_phase(
            file=file,
            ast_tree=ast_tree,
            phase="analysis",
            report=self.report
        )
        
        # Store edges in database
        await self._store_edges(result.edges, file)
        
        # Update metrics
        self.metrics.edges_created += len(result.edges)
    
    async def _run_linking_phase(self, files: List[File]) -> None:
        """
        Run the linking phase - create cross-file relationships.
        This phase runs sequentially for consistency.
        """
        self.report.add_info("Starting linking phase")
        
        # This phase would create relationships between symbols across files
        # For MVP, this might be simplified or skipped
        pass
    
    async def _run_post_processing(self) -> None:
        """
        Run post-processing - validation, metrics calculation, etc.
        """
        self.report.add_info("Starting post-processing")
        
        # Calculate final metrics
        await self._calculate_metrics()
        
        # Validate graph consistency
        await self._validate_graph()
        
        # Generate summary statistics
        await self._generate_statistics()
    
    async def _read_file_content(self, file: File) -> str:
        """
        Read file content efficiently.
        """
        # This would use the existing file reading mechanisms
        # For now, simple file read
        with open(file.path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _store_nodes(self, nodes: List[Any], file: File) -> None:
        """
        Store nodes in database using existing ORM.
        """
        # Use existing domain objects and ORM to store nodes
        for node in nodes:
            # This would use the existing db.collections.nodes.create()
            pass
    
    async def _store_edges(self, edges: List[Any], file: File) -> None:
        """
        Store edges in database using existing ORM.
        """
        # Use existing domain objects and ORM to store edges
        for edge in edges:
            # This would use the existing db.collections.edges.create()
            pass
    
    async def _calculate_metrics(self) -> None:
        """
        Calculate final analysis metrics.
        """
        # Calculate averages and totals
        if self.metrics.nodes_created > 0:
            # This would calculate complexity averages, etc.
            pass
    
    async def _validate_graph(self) -> None:
        """
        Validate the created graph for consistency.
        """
        # Check for broken references, orphaned nodes, etc.
        pass
    
    async def _generate_statistics(self) -> None:
        """
        Generate summary statistics for the analysis.
        """
        # Generate insights about the codebase
        pass


class AnalyzerConfig:
    """
    Configuration for the project analyzer.
    """
    
    def __init__(self):
        # General settings
        self.incremental = False
        self.changed_files: List[str] = []
        
        # Performance settings
        self.parallel_batch_size = 10
        self.max_concurrent_files = 5
        
        # Cache settings
        self.cache_config = CacheConfig()
        
        # Registry settings
        self.registry_config = RegistryConfig()
        
        # Visitor settings
        self.visitor_config = VisitorConfig()
        
        # Feature flags
        self.enable_type_inference = True
        self.enable_control_flow = True
        self.enable_dependency_analysis = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for storage"""
        return {
            'incremental': self.incremental,
            'changed_files': self.changed_files,
            'parallel_batch_size': self.parallel_batch_size,
            'max_concurrent_files': self.max_concurrent_files,
            'enable_type_inference': self.enable_type_inference,
            'enable_control_flow': self.enable_control_flow,
            'enable_dependency_analysis': self.enable_dependency_analysis,
        }


class CacheConfig:
    """Configuration for caching systems"""
    
    def __init__(self):
        self.ast_cache_size = 1000
        self.symbol_cache_size = 5000
        self.enable_persistent_cache = False


class RegistryConfig:
    """Configuration for symbol registry"""
    
    def __init__(self):
        self.project_id: Optional[str] = None
        self.cache_prefix: str = "default"
        self.cache_ttl = 3600  # 1 hour


class VisitorConfig:
    """Configuration for visitor pipeline"""
    
    def __init__(self):
        self.enabled_visitors: List[str] = [
            "DeclarationVisitor",
            "DependencyVisitor",
            "ControlFlowVisitor"
        ]
        self.visitor_timeout = 30  # seconds per visitor
        self.enable_parallel_visitors = True 