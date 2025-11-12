# Design Document

## Overview

This design implements a scalable log analysis architecture for the Instrument Diagnosis Assistant, enabling efficient processing of large log datasets (GB-scale) and entire folder structures without context window limitations. The solution uses the existing **AgentCore/Strands framework** and is inspired by Anthropic's MCP code execution strategy, where the agent writes and executes Python code to process data outside the context window, using progressive disclosure to load only necessary tools and data.

### Framework Integration

**AgentCore/Strands Architecture:**
- The agent continues to use **Strands** for tool orchestration and multi-agent collaboration
- The agent runs on **AgentCore Runtime** with managed execution and scaling
- **AgentCore Gateway** serves as a unified MCP tool server, providing centralized tool management
- **AgentCore Memory** maintains conversation context and analysis history

**Implementation Approach - Start Simple, Scale as Needed:**

**Phase 1: Enhanced Strands Tools (Start Here)**
- Extend existing Strands @tool functions with smarter sampling and streaming
- Add folder structure support to existing S3 integration
- Implement progressive disclosure through tool organization
- Agent generates Python code snippets that tools execute locally
- Benefits: Simple, no new infrastructure, builds on existing code

**Phase 2: MCP Server via Gateway (If Needed)**
- If Phase 1 hits performance limits, create dedicated MCP server
- Deploy MCP server to AgentCore Runtime as separate service
- Add as target in AgentCore Gateway for centralized management
- Benefits: Independent scaling, centralized tool management

**This design focuses on Phase 1** - enhancing existing Strands tools with code execution and better sampling strategies, inspired by the Anthropic MCP blog patterns but implemented as direct Strands tools first.

### Key Design Principles

1. **Progressive Disclosure**: Load tool definitions and data on-demand rather than upfront
2. **Code-First Analysis**: Agent generates Python code for complex operations (filtering, aggregation, correlation)
3. **Streaming Processing**: Process files line-by-line to avoid memory limits
4. **Filesystem-Based Tools**: Organize tools as a discoverable filesystem structure (Strands tools)
5. **Persistent Workspace**: Store intermediate results for resumable analysis (S3 + AgentCore Memory)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  (Folder Upload, Progress Display, Results Visualization)   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│    AgentCore Runtime: InstrumentDiagnosisAgent              │
│  - Strands Agent with diagnosis logic                       │
│  - Enhanced Strands @tool functions:                         │
│    • Folder structure analysis                               │
│    • Code execution tools (execute Python snippets)          │
│    • Advanced sampling tools (statistical, error-focused)    │
│    • Batch processing coordinator                            │
│    • Cross-file correlation                                  │
│  - AgentCore Memory integration                             │
│  - Existing AgentCore Gateway connection (optional)          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Enhanced Strands Tools (agent/agent_config/tools/)   │
│  /folder_analysis_tools.py    - Folder structure handling    │
│  /code_execution_tools.py     - Execute Python snippets      │
│  /advanced_sampling_tools.py  - Smart sampling strategies    │
│  /batch_processing_tools.py   - Coordinate multi-file work   │
│  /correlation_tools.py        - Cross-file pattern detection │
│  (All implemented as Strands @tool decorated functions)      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│    Session Workspace (S3 + AgentCore Memory)                │
│  S3: /sessions/{session-id}/                                 │
│    /logs/          - Original log files                      │
│    /analysis/      - Intermediate results                    │
│    /code/          - Generated analysis scripts              │
│    /indexes/       - Search indexes (optional)               │
│    /summaries/     - File summaries & metadata               │
│  AgentCore Memory: Conversation history & context            │
└──────────────────────────────────────────────────────────────┘

Note: If this approach hits performance limits, we can later migrate to
a dedicated MCP server deployed via AgentCore Gateway (Phase 2).
```

### Component Interaction Flow

```
User Upload Folder → S3 Storage → Folder Structure Analysis
                                          ↓
                              Agent Receives Folder Metadata
                                          ↓
                              Strategy Selection (based on size/count)
                                          ↓
                    ┌─────────────────────┴─────────────────────┐
                    │                                             │
            Small Dataset (<100MB)                    Large Dataset (>100MB)
                    │                                             │
            Direct Sampling Tools                    Code Execution Path
                    │                                             │
                    ↓                                             ↓
            Load Sampling Tools                   Generate Analysis Code
                    │                                             │
                    ↓                                             ↓
            Process Files                         Execute in Sandbox
                    │                                             │
                    └─────────────────────┬─────────────────────┘
                                          ↓
                              Store Results in Workspace
                                          ↓
                              Return Summary to Agent
                                          ↓
                              Generate Diagnosis Report
```

## Components and Interfaces

### 1. Folder Upload Handler

**Purpose**: Handle folder structure uploads and organize files in S3

**Interface**:
```python
class FolderUploadHandler:
    def upload_folder_structure(
        self,
        folder_files: List[UploadedFile],
        session_id: str
    ) -> FolderMetadata:
        """
        Upload folder structure to S3 with hierarchy preservation.
        
        Returns:
            FolderMetadata with structure, file counts, sizes, and organization pattern
        """
        pass
    
    def analyze_folder_structure(
        self,
        folder_metadata: FolderMetadata
    ) -> StructureAnalysis:
        """
        Analyze folder organization pattern (chronological, component-based, etc.)
        
        Returns:
            StructureAnalysis with detected patterns and recommended processing order
        """
        pass
```

**Key Features**:
- Preserves folder hierarchy in S3 keys
- Detects organization patterns from folder names
- Extracts metadata from folder/file names (dates, components, test IDs)
- Generates processing order recommendations

### 2. Enhanced Strands Tools

**Purpose**: Extend existing Strands tools with code execution and advanced sampling

**Implementation**: Strands @tool decorated functions in agent/agent_config/tools/

**New Tool Categories**:

**A. Folder Analysis Tools**:
```python
from strands import tool
from typing import Dict, List, Any

@tool(
    name="analyze_folder_structure",
    description="Analyze uploaded folder structure and recommend processing strategy"
)
def analyze_folder_structure(session_id: str) -> Dict[str, Any]:
    """
    Analyze folder organization in S3 and detect patterns.
    Returns: Structure summary, file counts, recommended processing order
    """
    pass

@tool(
    name="list_folder_files",
    description="List all files in folder structure with metadata"
)
def list_folder_files(
    session_id: str,
    folder_path: str = ""
) -> List[Dict[str, Any]]:
    """
    List files in folder with size, type, and path information.
    """
    pass
```

**B. Code Execution Tools**:
```python
@tool(
    name="execute_analysis_code",
    description="Execute Python code snippet for log analysis. Use for complex filtering, aggregation, or correlation."
)
def execute_analysis_code(
    code: str,
    s3_uris: List[str],
    session_id: str
) -> Dict[str, Any]:
    """
    Execute Python code with access to S3 files.
    Code runs in agent's runtime environment with safety checks.
    """
    pass
```

**C. Advanced Sampling Tools**:
```python
@tool(
    name="smart_sample_log",
    description="Intelligently sample large log file focusing on errors and key events"
)
def smart_sample_log(
    s3_uri: str,
    max_lines: int = 1000,
    focus: str = "errors"
) -> Dict[str, Any]:
    """
    Sample log file with focus on: errors, warnings, all, timeline
    Returns: Sampled content + statistics about full file
    """
    pass
```

**D. Batch Processing Tools**:
```python
@tool(
    name="batch_analyze_logs",
    description="Analyze multiple log files in coordinated batches"
)
def batch_analyze_logs(
    s3_uris: List[str],
    analysis_type: str,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Process files in batches with progress tracking.
    Returns: Per-file results + aggregate summary
    """
    pass
```

**File Structure**:
```
instrument-diagnosis-assistant/agent/agent_config/tools/
  __init__.py
  # Existing tools
  s3_storage_tools.py
  s3_log_sampling_tools.py
  # New tools (Phase 1)
  folder_analysis_tools.py      # NEW: Folder structure handling
  code_execution_tools.py       # NEW: Execute Python snippets
  advanced_sampling_tools.py    # NEW: Smart sampling strategies
  batch_processing_tools.py     # NEW: Batch coordination
  correlation_tools.py          # NEW: Cross-file analysis
```

### 3. Code Execution in Strands Tools

**Purpose**: Execute agent-generated Python code for complex analysis

**Implementation**: Strands @tool that executes code in agent's runtime environment

**How It Works**:
1. Agent generates Python code snippet for complex operation (filtering, aggregation, etc.)
2. Agent calls execute_analysis_code Strands tool
3. Tool validates and executes code in agent's runtime with S3 access
4. Results returned directly to agent

**Code Execution Tool Implementation**:
```python
from strands import tool
import subprocess
import tempfile
import os
import json
from typing import Dict, List, Any

@tool(
    name="execute_analysis_code",
    description="Execute Python code for log analysis. Use for complex filtering, aggregation, or correlation that's hard to express as simple tool calls."
)
def execute_analysis_code(
    code: str,
    s3_uris: List[str],
    session_id: str,
    timeout: int = 180
) -> Dict[str, Any]:
    """
    Execute Python code with access to S3 files.
    
    Args:
        code: Python code to execute (validated for safety)
        s3_uris: S3 URIs the code needs access to
        session_id: Session ID for workspace isolation
        timeout: Execution timeout (default 3 minutes)
    
    Returns:
        Execution results with output and any errors
    """
    # Validate code (check for dangerous imports/operations)
    if not _validate_code_safety(code):
        return {'success': False, 'error': 'Code validation failed - unsafe operations detected'}
    
    # Create workspace
    workspace_dir = f"/tmp/workspace/{session_id}"
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Write code to temp file
    code_file = f"{workspace_dir}/analysis.py"
    with open(code_file, 'w') as f:
        # Add helper imports
        f.write("import boto3\nimport json\nimport re\nfrom collections import Counter\n\n")
        f.write(code)
    
    # Execute with timeout
    try:
        result = subprocess.run(
            ['python', code_file],
            capture_output=True,
            timeout=timeout,
            text=True,
            cwd=workspace_dir,
            env={
                'S3_URIS': json.dumps(s3_uris),
                'SESSION_ID': session_id,
                'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1')
            }
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': f'Execution timeout after {timeout} seconds'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def _validate_code_safety(code: str) -> bool:
    """Validate code doesn't contain dangerous operations"""
    dangerous_patterns = [
        'import os',
        'import subprocess',
        'import sys',
        '__import__',
        'eval(',
        'exec(',
        'compile(',
        'open(',  # Allow only S3 access
    ]
    return not any(pattern in code for pattern in dangerous_patterns)
```

**Security Constraints**:
- Code validation before execution (block dangerous imports)
- Execution in agent's runtime (already sandboxed by AgentCore)
- Limited to safe operations (boto3 S3 access, data processing)
- Timeout enforcement (3 minutes default)
- Workspace isolation per session

### 4. Streaming Log Processor

**Purpose**: Process large log files line-by-line without loading into memory

**Interface**:
```python
class StreamingLogProcessor:
    def stream_process(
        self,
        s3_uri: str,
        processor_func: Callable[[str], Any],
        batch_size: int = 1000
    ) -> Iterator[ProcessedBatch]:
        """
        Stream process log file with custom processor function.
        
        Yields batches of processed results.
        """
        pass
    
    def build_index(
        self,
        s3_uri: str,
        index_type: str = "error_locations"
    ) -> IndexMetadata:
        """
        Build searchable index of log file.
        
        Index types: error_locations, timestamp_index, component_index
        """
        pass
```

### 5. Batch Analysis Coordinator

**Purpose**: Coordinate analysis of multiple files with progress tracking

**Interface**:
```python
class BatchAnalysisCoordinator:
    def analyze_batch(
        self,
        file_uris: List[str],
        analysis_type: str,
        batch_size: int = 10
    ) -> BatchAnalysisResult:
        """
        Analyze files in batches with progress updates.
        
        Returns:
            BatchAnalysisResult with per-file results and aggregate summary
        """
        pass
    
    def get_progress(
        self,
        batch_id: str
    ) -> ProgressStatus:
        """Get current progress of batch analysis"""
        pass
    
    def pause_batch(
        self,
        batch_id: str
    ) -> None:
        """Pause batch processing for review"""
        pass
```

### 6. Correlation Engine

**Purpose**: Identify patterns and relationships across multiple log files

**Interface**:
```python
class CorrelationEngine:
    def correlate_by_timestamp(
        self,
        file_uris: List[str],
        time_window: timedelta
    ) -> CorrelationResult:
        """Find events occurring within time window across files"""
        pass
    
    def correlate_by_session(
        self,
        file_uris: List[str],
        session_id_pattern: str
    ) -> CorrelationResult:
        """Group events by session/transaction ID"""
        pass
    
    def detect_causal_patterns(
        self,
        file_uris: List[str]
    ) -> CausalAnalysis:
        """Detect potential causal relationships between events"""
        pass
```

## Data Models

### FolderMetadata
```python
@dataclass
class FolderMetadata:
    session_id: str
    root_path: str
    total_files: int
    total_size_bytes: int
    folder_structure: Dict[str, FolderNode]
    organization_pattern: str  # "chronological", "component", "test_run", "mixed"
    file_types: Dict[str, int]  # Extension -> count
    processing_order: List[str]  # Recommended file processing order
```

### ToolDefinition
```python
@dataclass
class ToolDefinition:
    name: str
    category: str
    description: str
    parameters: List[Parameter]
    code_template: str  # Python code template
    example_usage: str
    memory_requirement: str  # "low", "medium", "high"
    suitable_for_sizes: List[str]  # ["<10MB", "10MB-100MB", ">100MB"]
```

### ExecutionResult
```python
@dataclass
class ExecutionResult:
    success: bool
    output: Any
    logs: List[str]
    execution_time: float
    memory_used: int
    artifacts: List[str]  # Paths to generated files
    error: Optional[str]
```

### BatchAnalysisResult
```python
@dataclass
class BatchAnalysisResult:
    batch_id: str
    total_files: int
    completed_files: int
    failed_files: int
    file_results: Dict[str, FileAnalysisResult]
    aggregate_summary: AggregateSummary
    processing_time: float
```

### CorrelationResult
```python
@dataclass
class CorrelationResult:
    correlation_type: str
    matched_events: List[CorrelatedEvent]
    confidence_score: float
    visualization_data: Dict[str, Any]
    summary: str
```

## Error Handling

### Error Categories

1. **Upload Errors**
   - Folder structure too deep (>10 levels)
   - Individual file too large (>5GB)
   - Total upload size exceeds limit (>50GB)
   - Invalid file types

2. **Processing Errors**
   - Code execution timeout
   - Memory limit exceeded
   - Invalid log format
   - Corrupted files

3. **Analysis Errors**
   - Insufficient data for correlation
   - Pattern detection failure
   - Index build failure

### Error Handling Strategy

```python
class ErrorHandler:
    def handle_upload_error(self, error: UploadError) -> ErrorResponse:
        """
        Provide actionable feedback for upload errors.
        Suggest: splitting folders, compressing files, filtering file types
        """
        pass
    
    def handle_processing_error(self, error: ProcessingError) -> ErrorResponse:
        """
        Recover from processing errors.
        Strategy: Skip failed files, use fallback analysis, reduce batch size
        """
        pass
    
    def handle_analysis_error(self, error: AnalysisError) -> ErrorResponse:
        """
        Provide partial results when analysis fails.
        Return: What was successfully analyzed + error details
        """
        pass
```

## Testing Strategy

### Unit Tests

1. **Tool Discovery Tests**
   - Test tool category listing
   - Test on-demand tool loading
   - Test tool search functionality
   - Test caching behavior

2. **Code Execution Tests**
   - Test sandbox isolation
   - Test timeout enforcement
   - Test memory limits
   - Test workspace file access

3. **Streaming Processor Tests**
   - Test line-by-line processing
   - Test batch processing
   - Test index building
   - Test memory efficiency

### Integration Tests

1. **End-to-End Folder Analysis**
   - Upload folder with 100+ files
   - Verify structure preservation
   - Verify processing order
   - Verify results accuracy

2. **Large File Processing**
   - Test with 1GB log file
   - Verify streaming behavior
   - Verify memory usage stays within limits
   - Verify analysis completeness

3. **Batch Processing**
   - Test batch coordination
   - Test progress tracking
   - Test pause/resume
   - Test error recovery

4. **Cross-File Correlation**
   - Test timestamp correlation
   - Test session correlation
   - Test causal detection
   - Test visualization generation

### Performance Tests

1. **Scalability Tests**
   - 10 files × 10MB each
   - 100 files × 10MB each
   - 10 files × 100MB each
   - 1 file × 1GB

2. **Latency Tests**
   - Time to first result
   - Time to complete analysis
   - Tool loading latency
   - Code execution latency

3. **Memory Tests**
   - Peak memory usage
   - Memory growth over time
   - Memory cleanup after processing

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Implement folder upload handler
- Implement tool discovery service
- Create filesystem-based tool library structure
- Implement basic code execution engine

### Phase 2: Core Processing (Weeks 3-4)
- Implement streaming log processor
- Implement batch analysis coordinator
- Create sampling tools (statistical, error-focused, time-window)
- Create filtering tools (pattern, timestamp, component)

### Phase 3: Advanced Analysis (Weeks 5-6)
- Implement correlation engine
- Create aggregation tools (counters, statistics, summaries)
- Implement cross-file analysis
- Create visualization generators

### Phase 4: Optimization & Polish (Week 7)
- Performance optimization
- Error handling improvements
- UI enhancements
- Documentation

## Security Considerations

1. **Code Execution Sandbox**
   - Use AWS Lambda with restricted IAM role
   - No network access except S3
   - Limited execution time (5 minutes)
   - Limited memory (3GB)

2. **Data Access Control**
   - Session-based isolation
   - S3 bucket policies
   - Presigned URLs with expiration
   - No cross-session data access

3. **Input Validation**
   - Validate folder structure depth
   - Validate file sizes
   - Sanitize file names
   - Validate generated code before execution

4. **Audit Logging**
   - Log all code executions
   - Log all file accesses
   - Log all errors
   - CloudWatch integration for monitoring

## Performance Optimization

1. **Caching Strategy**
   - Cache tool definitions (1 hour TTL)
   - Cache file indexes (session lifetime)
   - Cache analysis results (session lifetime)
   - Use Redis for distributed caching

2. **Parallel Processing**
   - Process multiple files concurrently (up to 10)
   - Use thread pools for I/O operations
   - Use process pools for CPU-intensive operations

3. **Lazy Loading**
   - Load tool definitions on-demand
   - Stream file content (don't load entire files)
   - Paginate large result sets
   - Use generators for large iterations

4. **Resource Management**
   - Implement connection pooling for S3
   - Reuse execution environments when possible
   - Clean up temporary files after processing
   - Monitor and limit concurrent executions
