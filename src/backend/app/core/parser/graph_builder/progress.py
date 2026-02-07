import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Enhanced progress tracker for hierarchical progress tracking.
    
    Tracks progress at two levels:
    1. File-level: Files being processed (scanning, collecting, analyzing)
    2. Entity-level: Functions/Classes being discovered and analyzed
    """

    def __init__(self, project_id: str, socket_manager, throttle_interval: float = 0.1):
        """
        Initialize the progress tracker.
        
        Args:
            project_id: The project ID to track progress for
            socket_manager: Socket manager instance for emitting events
            throttle_interval: Minimum seconds between emits (default: 0.1s = 10 emits/sec max)
        """
        self.project_id = project_id
        self.socket = socket_manager
        
        # Phase tracking
        self.phase: str = "initializing"
        self.status: str = "running"
        self.error_message: Optional[str] = None
        
        # File Stats
        self.total_files = 0
        self.processed_files = 0
        self.current_file_path: str = ""
        
        # Entity Stats
        self.total_entities = 0  # Total discovered in Phase 1
        self.processed_entities = 0  # How many fully analyzed in Phase 2
        self.functions_found = 0
        self.classes_found = 0
        self.current_function_qname: str = ""  # Current function/class being processed
        
        # Throttling
        self.throttle_interval = throttle_interval
        self._last_emit_time: float = 0.0
        
    def start_phase(self, phase: str):
        """Start a new phase."""
        self.phase = phase
        self.status = "running"
        self.error_message = None
        
        # Reset phase-specific counters
        if phase == "collecting":
            # Reset file counters for collection phase
            self.processed_files = 0
            self.current_file_path = ""
            self.current_function_qname = ""
            # Reset entity discovery counters
            self.functions_found = 0
            self.classes_found = 0
        elif phase == "analyzing":
            # Set total entities from discovery phase
            self.total_entities = self.functions_found + self.classes_found
            # Reset processed entities counter
            self.processed_entities = 0
            # Reset file counter for analysis phase
            self.processed_files = 0
            self.current_file_path = ""
            self.current_function_qname = ""
    
    def set_total_files(self, total: int):
        """Set the total number of files to process."""
        self.total_files = total
    
    def set_current_file(self, file_path: str):
        """Set the current file being processed (called at start of processing)."""
        self.current_file_path = file_path
    
    def set_current_function(self, function_qname: str):
        """Set the current function/class qname being processed."""
        self.current_function_qname = function_qname
    
    def clear_current_function(self):
        """Clear the current function qname (when done processing a function)."""
        self.current_function_qname = ""
    
    def increment_file_processed(self, file_path: str = ""):
        """Increment the processed files counter."""
        self.processed_files += 1
        # Keep current_file_path set until next file starts
    
    def increment_discovery(self, entity_type: str):
        """
        Increment entity discovery counters during Phase 1 (Collection).
        
        Args:
            entity_type: Either 'function' or 'class'
        """
        if entity_type == "function":
            self.functions_found += 1
        elif entity_type == "class":
            self.classes_found += 1
    
    def increment_entity_processed(self):
        """Increment the processed entities counter during Phase 2 (Analysis)."""
        self.processed_entities += 1
    
    def set_error(self, error_message: str):
        """Set error state."""
        self.status = "failed"
        self.error_message = error_message
        self.phase = "error"
    
    async def emit(self, force: bool = False):
        """
        Emit progress event to frontend.
        
        Args:
            force: If True, bypass throttling (useful for phase changes, completion)
        """
        import time
        
        # Throttle emits to prevent performance issues
        if not force:
            current_time = time.time()
            time_since_last_emit = current_time - self._last_emit_time
            if time_since_last_emit < self.throttle_interval:
                return  # Skip this emit due to throttling
            self._last_emit_time = current_time
        
        payload = {
            "project_id": self.project_id,
            "phase": self.phase,
            "files": {
                "total": self.total_files,
                "processed": self.processed_files,
                "remaining": max(0, self.total_files - self.processed_files),
                "current_path": self.current_file_path
            },
            "entities": {
                "total": self.total_entities,
                "processed": self.processed_entities,
                "functions_found": self.functions_found,
                "classes_found": self.classes_found,
                "current_qname": self.current_function_qname
            },
            "status": self.status,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.error_message:
            payload["error_message"] = self.error_message
        
        try:
            await self.socket.emit_to_project(
                self.project_id,
                "project:progress",
                payload
            )
        except Exception as e:
            logger.warning(f"Failed to emit progress event: {e}")
    
    async def complete(self):
        """Mark progress as complete."""
        self.phase = "complete"
        self.status = "success"
        self.processed_files = self.total_files
        self.processed_entities = self.total_entities
        self.current_file_path = ""
        self.current_function_qname = ""
        await self.emit(force=True)
