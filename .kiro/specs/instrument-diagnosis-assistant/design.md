# Design Document

## Overview

The Instrument Diagnosis Assistant is a streamlined GenAI-powered system built on the Amazon Bedrock AgentCore template. It leverages Amazon Nova's multi-modal capabilities to analyze instrument logs, recognize system components, and provide troubleshooting guidance. The design prioritizes simplicity for easy customer transfer while maintaining powerful diagnostic capabilities.

## Architecture

The system follows a simple, modular architecture using the existing AgentCore template structure:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  Diagnosis      │────│   Amazon Nova   │
│                 │    │  Assistant      │    │   Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │  Knowledge Base │    │  Configuration  │
│   Interface     │    │  (Bedrock KB)   │    │  Files          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Diagnosis Assistant Agent**: Main AI agent using Amazon Nova models
2. **Log Analysis Tools**: Custom tools for processing large log files
3. **Component Recognition Tools**: Tools for identifying hardware/software from documentation
4. **Multi-modal Document Processor**: Nova-powered analysis of troubleshooting guides
5. **Configuration Management**: YAML-based configuration for all parameters

## Components and Interfaces

### 1. Diagnosis Assistant Agent

**Purpose**: Core AI agent that orchestrates all diagnostic capabilities

**Implementation**:
- Built on AgentCore template's agent structure
- Uses Amazon Nova Pro for text analysis and reasoning
- Uses Amazon Nova Canvas for multi-modal document processing
- Configurable model selection via YAML configuration

**Key Features**:
- Log analysis and failure pattern recognition
- Component identification and correlation
- Multi-modal troubleshooting guide interpretation
- Cross-source data correlation and analysis

### 2. Log Analysis Tools with S3 Storage

**Purpose**: Process and analyze large instrument log files using S3 for scalable storage

**Tools**:
- `upload_log_to_s3`: Upload log files to S3 bucket and return S3 URI
- `analyze_s3_log`: Analyze log file stored in S3 by streaming chunks
- `extract_s3_log_summary`: Extract key patterns and errors from S3-stored logs
- `compare_s3_logs`: Compare multiple S3-stored logs for pattern analysis
- `generate_diagnosis`: Provide pass/fail determination with confidence

**Implementation**:
- **S3 Storage**: All uploaded logs stored in S3 bucket with session-based prefixes
- **Streaming Analysis**: Process large files from S3 in chunks without loading into memory
- **Smart Extraction**: Extract only relevant sections (errors, warnings, critical events)
- **Metadata Storage**: Store analysis results and summaries separately from raw logs
- **Presigned URLs**: Generate temporary access URLs for log retrieval when needed
- **Pattern Matching**: Identify failure signatures across distributed log chunks
- **Integration**: Nova models analyze extracted summaries, not full raw logs

### 3. Component Recognition Tools

**Purpose**: Identify and catalog system components from documentation

**Tools**:
- `extract_components`: Parse engineering documents for component names
- `map_functions`: Associate components with their functions
- `build_inventory`: Maintain comprehensive component database
- `resolve_naming`: Handle component naming variations

**Implementation**:
- NLP-based entity extraction
- Function mapping from technical documentation
- Component relationship modeling
- Configurable recognition patterns

### 4. Multi-modal Document Processor

**Purpose**: Process troubleshooting guides with text, images, and diagrams

**Tools**:
- `process_multimodal_docs`: Analyze documents with Nova Canvas
- `extract_visual_info`: Process diagrams and technical images
- `correlate_text_images`: Link textual instructions to visual references
- `generate_guidance`: Provide contextual troubleshooting steps

**Implementation**:
- Amazon Nova Canvas for vision capabilities
- Document parsing and structure analysis
- Image-text correlation algorithms
- Contextual guidance generation

### 5. Configuration Management

**Purpose**: Centralized configuration for all system parameters

**Configuration File Structure** (`config.yaml`):
```yaml
models:
  text_model: "us.amazon.nova-pro-v1:0"
  multimodal_model: "us.amazon.nova-canvas-v1:0"
  
knowledge_base:
  kb_id: "KB123456789"
  retrieval_config:
    max_results: 10
    score_threshold: 0.7

s3_storage:
  bucket_name: "instrument-diagnosis-logs"
  region: "us-east-1"
  prefix: "sessions"
  lifecycle_days: 7
  enable_versioning: false
  encryption: "AES256"
  max_file_size_mb: 500
  allowed_extensions: [".log", ".txt", ".csv", ".out", ".err"]

log_analysis:
  chunk_size_mb: 10  # Smaller chunks for S3 streaming
  stream_buffer_size: 8192
  failure_threshold: 0.8
  confidence_threshold: 0.75
  max_summary_length: 5000  # Characters in extracted summary

component_recognition:
  entity_confidence: 0.6
  naming_variations: true
  
deployment:
  aws_region: "us-east-1"
  auth_mode: "oauth"
```

## Data Models

### S3 Log Storage Model

```python
@dataclass
class S3LogMetadata:
    s3_uri: str  # S3 location of the log file
    bucket: str
    key: str
    file_name: str
    file_size: int
    upload_timestamp: str
    session_id: str
    content_type: str
    presigned_url: Optional[str] = None  # Temporary access URL
```

### Log Analysis Model

```python
@dataclass
class LogAnalysisResult:
    status: str  # "PASS", "FAIL", "UNCERTAIN"
    confidence: float
    failure_indicators: List[str]
    comparison_summary: str
    recommendations: List[str]
    s3_metadata: Optional[S3LogMetadata] = None  # Reference to source log
    analysis_timestamp: str = ""
```

### Component Model

```python
@dataclass
class SystemComponent:
    name: str
    component_type: str  # "hardware", "software"
    function: str
    aliases: List[str]
    related_components: List[str]
```

### Document Analysis Model

```python
@dataclass
class DocumentAnalysis:
    text_content: str
    visual_elements: List[Dict]
    correlations: List[Dict]
    guidance_steps: List[str]
```

## S3 Integration Strategy

### Upload Workflow
1. **User uploads file** via Streamlit interface
2. **File validation**: Check size, format, and content type
3. **S3 upload**: Stream file directly to S3 with session-based key
4. **Metadata creation**: Store S3 URI and file metadata
5. **Initial scan**: Extract quick summary (errors/warnings count)
6. **Agent notification**: Pass S3 URI and summary to agent, not raw content

### Analysis Workflow
1. **Agent receives**: S3 URI + summary metadata
2. **Smart extraction**: Tool streams relevant sections from S3
3. **Pattern analysis**: Process extracted chunks for failure patterns
4. **Result storage**: Save analysis results back to S3
5. **Response generation**: Agent uses summaries to provide diagnosis

### Benefits
- **Scalability**: Handle files of any size (5MB, 50MB, 500MB)
- **Memory efficiency**: Never load entire files into agent context
- **Cost optimization**: Store raw logs cheaply in S3
- **Parallel processing**: Multiple files analyzed concurrently
- **Session isolation**: Each session has dedicated S3 prefix
- **Audit trail**: All uploads and analyses tracked in S3

## Error Handling

### S3 Storage Errors
- **Upload failures**: Retry with exponential backoff
- **Access denied**: Validate IAM permissions and bucket policies
- **Bucket not found**: Auto-create bucket if configured
- **Network issues**: Resume interrupted uploads

### File Processing Errors
- **Large File Handling**: Stream from S3 in chunks with progress tracking
- **Format Issues**: Graceful handling of various log formats
- **Memory Management**: Process S3 streams without loading full files

### Model Errors
- **API Limits**: Retry logic with exponential backoff
- **Model Failures**: Fallback to alternative models when available
- **Token Limits**: Intelligent chunking and summarization

### Configuration Errors
- **Invalid Settings**: Validation with helpful error messages
- **Missing Parameters**: Default values with warnings
- **Environment Issues**: Clear setup guidance

## Testing Strategy

### Unit Testing
- **Tool Functions**: Test each diagnostic tool independently
- **Configuration Loading**: Validate YAML parsing and defaults
- **Data Models**: Test serialization and validation
- **Error Handling**: Verify graceful failure scenarios

### Integration Testing
- **End-to-End Workflows**: Complete diagnostic scenarios
- **Model Integration**: Test Nova model interactions
- **Knowledge Base**: Validate KB retrieval and processing
- **File Processing**: Test with sample large log files

### Performance Testing
- **Large File Processing**: Measure performance with 250MB+ files
- **Concurrent Analysis**: Test multiple simultaneous diagnoses
- **Memory Usage**: Monitor resource consumption
- **Response Times**: Ensure acceptable user experience

## Deployment Architecture

### AWS Resources
1. **Bedrock Models**: Amazon Nova Pro and Canvas
2. **Knowledge Base**: Bedrock KB for troubleshooting documents
3. **AgentCore Runtime**: Standard template deployment
4. **S3 Storage**: Primary storage for uploaded log files (required)
   - Bucket structure: `{bucket-name}/{session-id}/logs/{filename}`
   - Lifecycle policy: Auto-delete files after 7 days
   - Versioning: Disabled for cost optimization
   - Encryption: Server-side encryption enabled
5. **IAM Roles**: Enhanced permissions for S3 access
   - Agent runtime role: Read/write access to log bucket
   - Lambda role: Read access for log processing

### Configuration Files
- `config.yaml`: Main configuration file with S3 bucket settings
- `.agentcore.yaml`: AgentCore runtime configuration
- `dev-requirements.txt`: Python dependencies (includes boto3)

### S3 Bucket Structure
```
s3://{bucket-name}/
├── sessions/
│   ├── {session-id-1}/
│   │   ├── logs/
│   │   │   ├── system_log_001.txt
│   │   │   └── pc_log_001.txt
│   │   ├── summaries/
│   │   │   ├── system_log_001_summary.json
│   │   │   └── pc_log_001_summary.json
│   │   └── analysis/
│   │       └── diagnosis_result.json
│   └── {session-id-2}/
│       └── logs/...
├── gold_standards/
│   ├── system_log_good_001.txt
│   └── pc_log_good_001.txt
└── knowledge_base_docs/
    ├── component_specifications.pdf
    └── troubleshooting_guides.pdf
```

### Sample Data Structure (Local)
```
sample_data/
├── test_logs/
│   ├── system_log_fail_001.txt
│   └── pc_log_fail_001.txt
└── config_examples/
    └── s3_config.yaml
```

## Simplicity Principles

1. **Use Existing Template**: Leverage AgentCore template without modifications
2. **Configuration-Driven**: All parameters in YAML files, no code changes needed
3. **Minimal Dependencies**: Use only Bedrock services and standard libraries
4. **Clear Documentation**: Step-by-step setup and transfer instructions
5. **Sample Data Included**: Ready-to-test configuration with example files

This design ensures the system can be easily transferred to customers while providing powerful diagnostic capabilities through Amazon Nova's advanced AI models.