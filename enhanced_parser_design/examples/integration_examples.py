"""
Integration Examples for Enhanced Parser Architecture

This module provides practical examples of how to integrate the enhanced
parser system with the existing codebase and domain objects.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from app.core.manager import CodeGraphManager
from app.core.project import Project
from ..implementations.project_analyzer import ProjectAnalyzer, AnalyzerConfig
from ..models.enhanced_models import AnalysisResult


# =============================================================================
# Basic Integration Examples
# =============================================================================

async def example_basic_analysis():
    """
    Example: Basic project analysis using existing domain objects
    """
    # Use existing CodeGraphManager
    manager = CodeGraphManager()
    
    # Load or create project using existing domain methods
    project = manager.create_project(
        name="my_project",
        path="/path/to/my/project"
    )
    
    # Create enhanced analyzer
    analyzer = ProjectAnalyzer(manager)
    
    # Run analysis
    result = await analyzer.analyze_project(project)
    
    # Handle results
    if result.success:
        print(f"Analysis completed successfully!")
        print(f"Files processed: {result.report.metrics.files_processed}")
        print(f"Nodes created: {result.report.metrics.nodes_created}")
        print(f"Edges created: {result.report.metrics.edges_created}")
    else:
        print(f"Analysis failed with {len(result.report.issues)} issues")
        for issue in result.report.issues:
            print(f"  {issue.severity}: {issue.message}")


async def example_incremental_analysis():
    """
    Example: Incremental analysis for changed files only
    """
    manager = CodeGraphManager()
    project = manager.load_project("existing_project_id")
    
    # List of changed files (from git, file watcher, etc.)
    changed_files = [
        "src/main.py",
        "src/utils.py"
    ]
    
    analyzer = ProjectAnalyzer(manager)
    
    # Run incremental analysis
    result = await analyzer.analyze_incremental(
        project=project,
        changed_files=changed_files
    )
    
    print(f"Incremental analysis processed {result.report.metrics.files_processed} files")
    return result


async def example_custom_configuration():
    """
    Example: Using custom configuration for specific analysis needs
    """
    manager = CodeGraphManager()
    project = manager.load_project("project_id")
    
    # Create custom configuration
    config = AnalyzerConfig()
    config.enable_type_inference = True
    config.enable_control_flow = False  # Skip control flow for performance
    config.parallel_batch_size = 20    # Larger batches for better performance
    
    analyzer = ProjectAnalyzer(manager)
    
    result = await analyzer.analyze_project(project, config)
    return result


# =============================================================================
# API Endpoint Integration Examples
# =============================================================================

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    project_id: str
    incremental: bool = False
    changed_files: List[str] = []


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    started_at: datetime


async def analyze_project_endpoint(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    manager: CodeGraphManager
) -> AnalysisResponse:
    """
    Example API endpoint that integrates enhanced analysis
    """
    try:
        # Load project using existing domain objects
        project = manager.load_project(request.project_id)
        
        # Create analyzer
        analyzer = ProjectAnalyzer(manager)
        
        # Start analysis in background
        if request.incremental:
            task = background_tasks.add_task(
                run_incremental_analysis,
                analyzer, project, request.changed_files
            )
        else:
            task = background_tasks.add_task(
                run_full_analysis,
                analyzer, project
            )
        
        return AnalysisResponse(
            analysis_id=f"analysis_{datetime.utcnow().timestamp()}",
            status="started",
            message="Analysis started successfully",
            started_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


async def run_full_analysis(analyzer: ProjectAnalyzer, project: Project):
    """Background task for full analysis"""
    try:
        result = await analyzer.analyze_project(project)
        
        # Store result or trigger events
        await store_analysis_result(result)
        await notify_analysis_complete(result)
        
    except Exception as e:
        await notify_analysis_failed(project.id, str(e))


async def run_incremental_analysis(
    analyzer: ProjectAnalyzer, 
    project: Project, 
    changed_files: List[str]
):
    """Background task for incremental analysis"""
    try:
        result = await analyzer.analyze_incremental(project, changed_files)
        
        # Handle incremental results
        await update_incremental_results(result)
        await notify_analysis_complete(result)
        
    except Exception as e:
        await notify_analysis_failed(project.id, str(e))


# =============================================================================
# Event-Driven Integration Examples
# =============================================================================

class AnalysisEventHandler:
    """
    Example event handler for analysis events
    """
    
    def __init__(self, manager: CodeGraphManager):
        self.manager = manager
        self.analyzer = ProjectAnalyzer(manager)
    
    async def handle_file_changed(self, project_id: str, file_path: str):
        """Handle file change events"""
        project = self.manager.load_project(project_id)
        
        # Run incremental analysis
        result = await self.analyzer.analyze_incremental(
            project=project,
            changed_files=[file_path]
        )
        
        # Update search indexes, caches, etc.
        await self.update_search_index(result)
        
    async def handle_project_created(self, project_id: str):
        """Handle new project creation"""
        project = self.manager.load_project(project_id)
        
        # Run initial analysis
        config = AnalyzerConfig()
        config.enable_type_inference = True
        
        result = await self.analyzer.analyze_project(project, config)
        
        # Initialize project metadata
        await self.initialize_project_metadata(result)
    
    async def update_search_index(self, result: AnalysisResult):
        """Update search indexes with analysis results"""
        # This would update Elasticsearch, etc.
        pass
        
    async def initialize_project_metadata(self, result: AnalysisResult):
        """Initialize project metadata from analysis"""
        # This would populate project statistics, etc.
        pass


# =============================================================================
# Database Integration Examples
# =============================================================================

async def example_database_integration():
    """
    Example: Integrating analysis results with existing database schema
    """
    manager = CodeGraphManager()
    project = manager.load_project("project_id")
    
    analyzer = ProjectAnalyzer(manager)
    result = await analyzer.analyze_project(project)
    
    # The analysis automatically integrates with existing ORM
    # But you can also manually query the results
    
    # Query using existing ORM methods
    from app.db import collections as db
    
    # Find all functions in the project
    functions = db.nodes.find({
        "node_type": "function",
        # Add project filter based on your schema
    })
    
    # Find call relationships
    calls = db.edges.find({
        "edge_type": "calls",
        # Add project filter
    })
    
    print(f"Found {len(functions)} functions and {len(calls)} call relationships")


async def example_graph_queries():
    """
    Example: Complex graph queries using the enhanced schema
    """
    from app.db import collections as db
    
    # Find most called functions
    most_called_query = """
    FOR edge IN edges
        FILTER edge.edge_type == "calls"
        COLLECT target = edge._to WITH COUNT INTO call_count
        SORT call_count DESC
        LIMIT 10
        LET func = DOCUMENT(target)
        RETURN {
            function: func.name,
            qname: func.qname,
            call_count: call_count
        }
    """
    
    # Find complex functions (high complexity score)
    complex_functions_query = """
    FOR node IN nodes
        FILTER node.node_type == "function"
        FILTER node.complexity_score > 10
        SORT node.complexity_score DESC
        RETURN {
            name: node.name,
            qname: node.qname,
            complexity: node.complexity_score,
            line_count: node.end_line - node.start_line + 1
        }
    """
    
    # Find unused functions (no incoming calls)
    unused_functions_query = """
    FOR func IN nodes
        FILTER func.node_type == "function"
        LET incoming_calls = (
            FOR edge IN edges
                FILTER edge.edge_type == "calls"
                FILTER edge._to == func._id
                RETURN 1
        )
        FILTER LENGTH(incoming_calls) == 0
        RETURN {
            name: func.name,
            qname: func.qname,
            file: func.file_path
        }
    """
    
    # Execute queries (using your existing ArangoDB client)
    # This would use your existing database client methods


# =============================================================================
# Testing Integration Examples
# =============================================================================

import pytest

@pytest.fixture
async def analyzer_with_test_project():
    """Test fixture for analyzer with test project"""
    manager = CodeGraphManager()
    
    # Create test project
    project = manager.create_project(
        name="test_project",
        path="tests/sample_project"
    )
    
    analyzer = ProjectAnalyzer(manager)
    return analyzer, project


async def test_basic_analysis(analyzer_with_test_project):
    """Test basic analysis functionality"""
    analyzer, project = analyzer_with_test_project
    
    result = await analyzer.analyze_project(project)
    
    assert result.success
    assert result.report.status == "completed"
    assert result.report.metrics.files_processed > 0
    assert result.report.metrics.nodes_created > 0


async def test_incremental_analysis(analyzer_with_test_project):
    """Test incremental analysis"""
    analyzer, project = analyzer_with_test_project
    
    # First, run full analysis
    full_result = await analyzer.analyze_project(project)
    
    # Then run incremental analysis
    incremental_result = await analyzer.analyze_incremental(
        project=project,
        changed_files=["test_file.py"]
    )
    
    assert incremental_result.success
    assert incremental_result.report.metrics.files_processed <= full_result.report.metrics.files_processed


async def test_error_handling(analyzer_with_test_project):
    """Test error handling in analysis"""
    analyzer, project = analyzer_with_test_project
    
    # Create config that might cause issues
    config = AnalyzerConfig()
    config.parallel_batch_size = 1000  # Very large batch
    
    result = await analyzer.analyze_project(project, config)
    
    # Should still complete, possibly with warnings
    assert result.report.status in ["completed", "completed_with_issues"]


# =============================================================================
# Performance Monitoring Examples
# =============================================================================

class AnalysisMonitor:
    """
    Example monitoring for analysis performance
    """
    
    def __init__(self):
        self.metrics = {}
    
    async def monitor_analysis(self, analyzer: ProjectAnalyzer, project: Project):
        """Monitor analysis performance"""
        start_time = datetime.utcnow()
        
        result = await analyzer.analyze_project(project)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Collect metrics
        self.metrics[project.id] = {
            'duration': duration,
            'files_processed': result.report.metrics.files_processed,
            'nodes_created': result.report.metrics.nodes_created,
            'edges_created': result.report.metrics.edges_created,
            'errors': len([i for i in result.report.issues if i.severity == 'error']),
            'warnings': len([i for i in result.report.issues if i.severity == 'warning']),
        }
        
        # Log performance metrics
        await self.log_performance_metrics(project.id, self.metrics[project.id])
        
        return result
    
    async def log_performance_metrics(self, project_id: str, metrics: Dict[str, Any]):
        """Log performance metrics to monitoring system"""
        print(f"Analysis metrics for {project_id}:")
        print(f"  Duration: {metrics['duration']:.2f}s")
        print(f"  Throughput: {metrics['files_processed'] / metrics['duration']:.2f} files/s")
        print(f"  Node creation rate: {metrics['nodes_created'] / metrics['duration']:.2f} nodes/s")
        
        # This would send to monitoring system (Prometheus, etc.)


# =============================================================================
# Usage Examples
# =============================================================================

async def main():
    """
    Main example showing various integration patterns
    """
    print("Running enhanced parser integration examples...")
    
    # Basic analysis
    print("\n1. Basic Analysis:")
    await example_basic_analysis()
    
    # Incremental analysis
    print("\n2. Incremental Analysis:")
    await example_incremental_analysis()
    
    # Custom configuration
    print("\n3. Custom Configuration:")
    await example_custom_configuration()
    
    # Database integration
    print("\n4. Database Integration:")
    await example_database_integration()
    
    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())


# =============================================================================
# Helper Functions
# =============================================================================

async def store_analysis_result(result: AnalysisResult):
    """Store analysis result for later retrieval"""
    # This would store the result in database or cache
    pass

async def notify_analysis_complete(result: AnalysisResult):
    """Notify other services that analysis is complete"""
    # This would publish events, send webhooks, etc.
    pass

async def notify_analysis_failed(project_id: str, error: str):
    """Notify that analysis failed"""
    # This would log errors, send alerts, etc.
    pass

async def update_incremental_results(result: AnalysisResult):
    """Update incremental analysis results"""
    # This would merge incremental results with existing data
    pass 