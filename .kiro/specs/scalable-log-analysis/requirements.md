# Requirements Document

## Introduction

The Instrument Diagnosis Assistant currently handles log file analysis through S3 storage with basic sampling tools. However, when dealing with large volumes of log messages (hundreds of MB to GB) or entire folder structures with multiple log files, the system faces context window limitations and performance issues. This feature will implement a scalable log analysis architecture inspired by Anthropic's MCP code execution strategy, enabling the agent to efficiently analyze massive log datasets without loading entire files into context.

## Glossary

- **Agent**: The AI-powered Instrument Diagnosis Assistant that analyzes log files
- **MCP (Model Context Protocol)**: Open standard for connecting AI agents to external systems
- **Code Execution Environment**: Secure sandbox where agent-generated code runs to process data
- **Progressive Disclosure**: Strategy of loading tool definitions and data on-demand rather than upfront
- **Log Sampling**: Technique of extracting specific portions of log files without loading entire content
- **S3 Storage Manager**: Component managing file storage and retrieval from Amazon S3
- **Context Window**: Limited token capacity available to the agent for processing information
- **Folder Structure**: Hierarchical organization of multiple log files in directories
- **Batch Analysis**: Processing multiple log files in a coordinated workflow

## Requirements

### Requirement 1: Scalable Log File Processing

**User Story:** As a technician, I want to analyze entire folders containing hundreds of log files (totaling several GB) so that I can diagnose complex instrument failures that span multiple sessions and components.

#### Acceptance Criteria

1. WHEN a user uploads a folder structure with more than 100 log files, THE Agent SHALL process the folder hierarchy without exceeding context window limits
2. WHEN total log file size exceeds 1 GB, THE Agent SHALL use progressive disclosure to analyze files incrementally
3. WHEN analyzing multiple large files, THE Agent SHALL provide progress updates showing which files have been processed
4. WHERE folder structures contain nested directories, THE Agent SHALL preserve and report the hierarchical organization
5. WHILE processing large datasets, THE Agent SHALL maintain response time under 5 minutes for initial analysis summary

### Requirement 2: Code-Based Log Analysis Tools

**User Story:** As a developer, I want the agent to use code execution for log analysis so that complex filtering, aggregation, and correlation operations can be performed efficiently outside the context window.

#### Acceptance Criteria

1. THE Agent SHALL generate Python code to filter log entries based on multiple criteria (timestamp ranges, error types, component names)
2. THE Agent SHALL execute aggregation code to count error frequencies, calculate statistics, and identify patterns across multiple files
3. WHEN correlating events across files, THE Agent SHALL use code to join and merge log entries by timestamp or session ID
4. THE Agent SHALL store intermediate analysis results in the execution environment to avoid re-processing
5. WHERE log parsing requires custom logic, THE Agent SHALL write reusable parsing functions that can be applied to multiple files

### Requirement 3: Filesystem-Based Tool Discovery

**User Story:** As a system architect, I want log analysis tools to be organized as a filesystem structure so that the agent can discover and load only the tools it needs for each specific analysis task.

#### Acceptance Criteria

1. THE Agent SHALL access log analysis tools through a filesystem structure organized by capability (sampling, filtering, aggregation, correlation)
2. WHEN the agent needs a specific tool, THE Agent SHALL read only that tool's definition from the filesystem
3. THE Agent SHALL list available tool categories without loading full tool definitions
4. WHERE multiple tools provide similar functionality, THE Agent SHALL select the most appropriate tool based on file size and analysis requirements
5. THE Agent SHALL cache frequently used tool definitions to reduce filesystem reads

### Requirement 4: Intelligent Log Sampling Strategy

**User Story:** As a technician analyzing a 500 MB log file, I want the agent to intelligently sample relevant sections so that I get diagnostic insights quickly without waiting for the entire file to be processed.

#### Acceptance Criteria

1. WHEN a log file exceeds 10 MB, THE Agent SHALL use statistical sampling to analyze representative portions
2. THE Agent SHALL prioritize sampling around error events, warnings, and critical messages
3. WHEN initial sampling suggests specific issues, THE Agent SHALL perform targeted deep-dive sampling in relevant sections
4. THE Agent SHALL provide confidence levels indicating how much of the file was analyzed
5. WHERE sampling reveals patterns, THE Agent SHALL verify patterns across multiple sample points before reporting conclusions

### Requirement 5: Folder Structure Analysis

**User Story:** As a technician, I want to upload an entire diagnostic data folder (with subfolders for different components, time periods, or test runs) so that the agent can analyze the complete diagnostic picture.

#### Acceptance Criteria

1. THE Agent SHALL accept folder uploads containing nested directory structures
2. WHEN analyzing folder structures, THE Agent SHALL identify and report the organizational pattern (by component, by date, by test type)
3. THE Agent SHALL process files in logical order based on folder structure (chronological, hierarchical, or dependency-based)
4. WHERE folder names contain metadata (dates, component names, test IDs), THE Agent SHALL extract and use this information in analysis
5. THE Agent SHALL generate a folder structure summary showing file counts, sizes, and types for each directory

### Requirement 6: Intermediate Result Persistence

**User Story:** As a developer, I want analysis results to be stored persistently so that the agent can resume work, reference previous findings, and avoid re-processing the same data.

#### Acceptance Criteria

1. THE Agent SHALL store intermediate analysis results (error counts, pattern summaries, component inventories) in persistent storage
2. WHEN resuming analysis after interruption, THE Agent SHALL load previous results and continue from the last checkpoint
3. THE Agent SHALL maintain a session-based workspace where analysis artifacts are organized by session ID
4. WHERE multiple analysis requests reference the same files, THE Agent SHALL reuse cached analysis results
5. THE Agent SHALL provide commands to clear cached results when fresh analysis is required

### Requirement 7: Batch Processing Workflow

**User Story:** As a technician with 200 log files to analyze, I want the agent to process them in batches so that I can see incremental results and adjust the analysis strategy if needed.

#### Acceptance Criteria

1. WHEN processing more than 20 files, THE Agent SHALL divide the workload into batches of 10-20 files
2. THE Agent SHALL provide summary results after each batch completion
3. WHEN errors occur in batch processing, THE Agent SHALL continue with remaining batches and report failures separately
4. THE Agent SHALL allow users to pause batch processing and review intermediate results
5. WHERE batch results reveal specific issues, THE Agent SHALL offer to perform detailed analysis on relevant files

### Requirement 8: Memory-Efficient Data Structures

**User Story:** As a system architect, I want log analysis to use memory-efficient data structures so that the system can handle large datasets without running out of memory or exceeding execution limits.

#### Acceptance Criteria

1. THE Agent SHALL use streaming parsers that process log files line-by-line without loading entire files into memory
2. WHEN building indexes or summaries, THE Agent SHALL use compact data structures (dictionaries, counters, bloom filters)
3. THE Agent SHALL implement pagination for large result sets, returning results in manageable chunks
4. WHERE full-text search is required, THE Agent SHALL use indexed search rather than scanning entire files
5. THE Agent SHALL monitor memory usage and switch to disk-based processing when memory limits are approached

### Requirement 9: Cross-File Correlation

**User Story:** As a technician diagnosing intermittent failures, I want the agent to correlate events across multiple log files so that I can identify patterns that span different components or time periods.

#### Acceptance Criteria

1. THE Agent SHALL identify common error patterns that appear across multiple log files
2. WHEN analyzing time-series data, THE Agent SHALL align events by timestamp across different files
3. THE Agent SHALL detect causal relationships where errors in one component precede failures in another
4. WHERE session IDs or transaction IDs exist, THE Agent SHALL group related events across files
5. THE Agent SHALL generate correlation reports showing which files contain related events

### Requirement 10: Adaptive Analysis Strategy

**User Story:** As a technician, I want the agent to automatically adjust its analysis strategy based on file characteristics so that I get optimal results regardless of log format, size, or structure.

#### Acceptance Criteria

1. WHEN encountering structured logs (JSON, CSV), THE Agent SHALL use structured parsing for efficient analysis
2. WHEN encountering unstructured logs (plain text), THE Agent SHALL use pattern matching and natural language processing
3. WHERE files are compressed, THE Agent SHALL decompress on-the-fly during streaming
4. WHEN file size exceeds 100 MB, THE Agent SHALL automatically switch to sampling-based analysis
5. THE Agent SHALL detect log format automatically and select appropriate parsing tools
