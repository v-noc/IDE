export type ProcessingPhase = 
  | 'idle'
  | 'scanning' 
  | 'collecting' 
  | 'analyzing' 
  | 'complete' 
  | 'error';

export interface FileProgress {
  total: number;
  processed: number;
  remaining: number;
  current_path: string;
}

export interface EntityProgress {
  total: number;      // Total discovered in Phase 1
  processed: number;  // How many fully analyzed in Phase 2
  functions_found: number;
  classes_found: number;
  current_qname: string;  // Current function/class qname being processed
}

export interface ProgressEventPayload {
  project_id: string;
  phase: ProcessingPhase;
  
  // File-level stats
  files: FileProgress;
  
  // Entity-level stats (Functions/Classes)
  entities: EntityProgress;
  
  status: 'running' | 'success' | 'failed';
  error_message?: string;
  timestamp: string;
}
