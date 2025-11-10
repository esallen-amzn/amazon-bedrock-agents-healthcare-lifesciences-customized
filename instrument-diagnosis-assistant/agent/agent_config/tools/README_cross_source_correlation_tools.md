# Cross-Source Correlation Tools

## Overview

The `cross_source_correlation_tools.py` module provides cross-source correlation capabilities that unify information from logs, documentation, and troubleshooting guides. It creates consistent component identification, correlates failure patterns with procedures, and generates unified analysis across multiple data sources.

## Purpose

This module enables:
- Correlate component references across different sources
- Resolve component naming inconsistencies
- Associate failure patterns with troubleshooting procedures
- Generate unified analysis combining multiple sources
- Calculate cross-source consistency metrics
- Provide comprehensive recommendations

## Key Components

### ComponentCorrelation (Dataclass)

Represents correlation of a component across different sources:

- `component_name`: Original component name
- `canonical_name`: Standardized canonical name
- `source_references`: Dictionary mapping source types to reference lists
- `confidence_scores`: Dictionary mapping source types to confidence scores
- `failure_associations`: List of associated failure patterns
- `troubleshooting_procedures`: List of relevant procedures
- `consistency_score`: Overall consistency score (0.0-1.0)

### FailurePatternCorrelation (Dataclass)

Represents correlation between failure patterns and procedures:

- `failure_pattern`: Description of failure pattern
- `pattern_type`: Type of pattern (connection_timeout, memory_issues, etc.)
- `severity`: Severity level (CRITICAL, WARNING, INFO)
- `associated_components`: List of related components
- `troubleshooting_procedures`: List of relevant procedures
- `documentation_references`: List of documentation links
- `correlation_strength`: Strength score (0.0-1.0)

### CrossSourceCorrelationEngine (Class)

Core engine for cross-source correlation and analysis.

**Component Name Normalization**:
- Expands abbreviations (temp → temperature, ctrl → control)
- Removes common prefixes/suffixes (main, primary, secondary)
- Standardizes whitespace
- Creates canonical forms

**Failure-Procedure Mapping Keywords**:
- connection_timeout: ['connection', 'cable', 'communication', 'timeout']
- service_failures: ['service', 'software', 'restart', 'process']
- memory_issues: ['memory', 'ram', 'allocation', 'leak']
- disk_issues: ['disk', 'storage', 'space', 'write']
- performance_degradation: ['performance', 'slow', 'optimization', 'speed']
- driver_issues: ['driver', 'version', 'compatibility', 'update']

## Available Tools

### 1. correlate_components_across_sources

**Description**: Correlate component references across log files, documentation, and troubleshooting guides.

**Parameters**:
- `log_analysis_data` (Dict[str, Any]): Results from log analysis tools
- `component_inventory` (Dict[str, Any]): Results from component recognition tools
- `document_analysis` (Dict[str, Any]): Results from multimodal document processing
- `correlation_threshold` (float): Minimum correlation score to consider a match - default: 0.6

**Returns**: Dictionary containing component correlations across sources

**Usage Example**:
```python
# Gather data from different sources
log_data = analyze_s3_log(s3_uri="...")
inventory = build_inventory(components_data=...)
doc_data = process_multimodal_docs(document_content=...)

# Correlate across sources
result = correlate_components_across_sources(
    log_analysis_data=log_data,
    component_inventory=inventory,
    document_analysis=doc_data,
    correlation_threshold=0.6
)
```

**Output Structure**:
```json
{
  "component_correlations": [
    {
      "component_name": "Temperature Controller",
      "canonical_name": "Temperature Control Module",
      "source_references": {
        "log_analysis": ["temp controller", "temperature ctrl"],
        "component_inventory": ["Temperature Controller"],
        "document_analysis": ["Temperature Control Module", "Temp Controller"]
      },
      "confidence_scores": {
        "log_analysis": 0.75,
        "component_inventory": 0.95,
        "document_analysis": 0.90
      },
      "failure_associations": [
        "Temperature sensor timeout",
        "Heating element failure"
      ],
      "troubleshooting_procedures": [
        "Check Temperature Sensor Connections",
        "Verify Heating Element Operation"
      ],
      "consistency_score": 0.87
    }
  ],
  "consistency_metrics": {
    "component_identification": 0.85,
    "source_agreement": 0.78,
    "failure_pattern_coverage": 0.65
  },
  "correlation_summary": {
    "total_components_found": 25,
    "components_correlated": 20,
    "correlation_rate": 0.80,
    "sources_analyzed": ["log_analysis", "component_inventory", "document_analysis"],
    "avg_consistency_score": 0.82
  },
  "source_components": {
    "log_analysis": ["temp controller", "laser module", ...],
    "component_inventory": ["Temperature Controller", "Laser Module", ...],
    "document_analysis": ["Temperature Control Module", "Laser System", ...]
  },
  "correlation_metadata": {
    "correlation_threshold": 0.6,
    "normalization_applied": true,
    "conflict_resolution_used": true,
    "total_sources": 3
  }
}
```

### 2. correlate_failures_to_procedures

**Description**: Associate failure patterns with relevant troubleshooting procedures from guides.

**Parameters**:
- `failure_analysis_data` (Dict[str, Any]): Results from failure indicator extraction
- `troubleshooting_guides` (Dict[str, Any]): Results from multimodal document processing
- `correlation_strength_threshold` (float): Minimum correlation strength to include - default: 0.5

**Returns**: Dictionary containing failure-procedure correlations

**Usage Example**:
```python
# Extract failure patterns
failure_data = extract_failure_indicators(log_content=...)

# Process troubleshooting guides
guide_data = process_multimodal_docs(document_content=...)

# Correlate failures to procedures
result = correlate_failures_to_procedures(
    failure_analysis_data=failure_data,
    troubleshooting_guides=guide_data,
    correlation_strength_threshold=0.5
)
```

**Output Structure**:
```json
{
  "failure_correlations": [
    {
      "failure_pattern": "Connection or communication timeout detected",
      "pattern_type": "connection_timeout",
      "severity": "CRITICAL",
      "associated_components": ["Network Interface", "USB Controller"],
      "troubleshooting_procedures": [
        {
          "title": "Check Network Connections",
          "description": "Verify all network cables and connections...",
          "symptoms": ["Connection timeout", "Communication failure"],
          "troubleshooting_steps": ["Step 1: Check cables", "Step 2: Test connectivity"]
        }
      ],
      "documentation_references": [],
      "correlation_strength": 0.85
    }
  ],
  "correlation_statistics": {
    "total_failure_patterns": 15,
    "total_procedures": 25,
    "correlations_found": 12,
    "correlation_rate": 0.80,
    "avg_correlation_strength": 0.75,
    "high_confidence_correlations": 8
  },
  "correlations_by_severity": {
    "CRITICAL": [
      {
        "failure_pattern": "Connection timeout",
        "correlation_strength": 0.85,
        ...
      }
    ],
    "WARNING": [...],
    "INFO": [...]
  },
  "procedure_recommendations": [
    {
      "failure_pattern": "Connection or communication timeout detected",
      "severity": "CRITICAL",
      "procedure_title": "Check Network Connections",
      "procedure_description": "Verify all network cables...",
      "correlation_strength": 0.85,
      "associated_components": ["Network Interface", "USB Controller"]
    }
  ],
  "correlation_metadata": {
    "correlation_threshold": 0.5,
    "failure_patterns_analyzed": 15,
    "procedures_analyzed": 25,
    "correlation_method": "keyword_and_semantic_matching"
  }
}
```

### 3. generate_unified_analysis

**Description**: Create unified analysis combining logs, documentation, and troubleshooting guides.

**Parameters**:
- `log_analysis_data` (Dict[str, Any]): Results from log analysis
- `component_correlations` (Dict[str, Any]): Results from correlate_components_across_sources
- `failure_correlations` (Dict[str, Any]): Results from correlate_failures_to_procedures
- `diagnosis_data` (Dict[str, Any]): Results from diagnosis generation

**Returns**: Dictionary containing unified analysis and recommendations

**Usage Example**:
```python
# Gather all analysis data
log_data = analyze_s3_log(s3_uri=...)
comp_corr = correlate_components_across_sources(...)
fail_corr = correlate_failures_to_procedures(...)
diagnosis = generate_diagnosis(...)

# Generate unified analysis
result = generate_unified_analysis(
    log_analysis_data=log_data,
    component_correlations=comp_corr,
    failure_correlations=fail_corr,
    diagnosis_data=diagnosis
)
```

**Output Structure**:
```json
{
  "overall_status": "FAIL",
  "confidence_level": 0.9,
  "component_correlations": [...],
  "failure_correlations": [...],
  "cross_source_consistency": {
    "component_identification": 0.85,
    "source_agreement": 0.78,
    "failure_pattern_coverage": 0.65,
    "overall_consistency": 0.76
  },
  "unified_recommendations": [
    {
      "priority": "URGENT",
      "category": "connection_issues",
      "action": "Check Network and USB Connections",
      "description": "Multiple sources indicate connection timeouts...",
      "supporting_evidence": {
        "log_patterns": ["Connection timeout detected 15 times"],
        "component_references": ["Network Interface", "USB Controller"],
        "procedure_matches": ["Check Network Connections procedure"]
      },
      "estimated_time": "15-30 minutes",
      "confidence": 0.9
    }
  ],
  "analysis_metadata": {
    "sources_analyzed": 4,
    "total_components_identified": 20,
    "total_failure_patterns": 15,
    "total_procedures_matched": 12,
    "analysis_timestamp": "2025-01-09T12:00:00",
    "consistency_threshold": 0.6
  }
}
```

## Component Name Normalization

The module uses intelligent normalization to handle naming variations:

### Normalization Process

1. **Convert to lowercase**: "Temperature Controller" → "temperature controller"
2. **Expand abbreviations**: "temp ctrl" → "temperature control"
3. **Remove common words**: "main temperature controller" → "temperature controller"
4. **Standardize whitespace**: "temperature  controller" → "temperature controller"

### Similarity Calculation

Components are matched using multiple strategies:

1. **Exact Match**: Identical normalized names (similarity: 1.0)
2. **Containment**: One name contains the other (similarity: 0.9)
3. **Word-Based**: Jaccard similarity of word sets
4. **Technical Term Boost**: +0.1 for matching key technical terms

**Example**:
```
"Temperature Controller" vs "Temp Control Module"
→ Normalized: "temperature controller" vs "temperature control module"
→ Words: {temperature, controller} vs {temperature, control, module}
→ Intersection: {temperature, control/controller}
→ Similarity: 0.75 + 0.1 (technical term) = 0.85
```

## Failure-Procedure Correlation

The module correlates failure patterns with procedures using:

### Keyword Matching
- Each pattern type has associated keywords
- Procedures are searched for these keywords
- Match score based on keyword coverage

### Description Overlap
- Compare failure description with procedure text
- Calculate word overlap using Jaccard similarity
- Boost score for exact phrase matches

### Correlation Strength Calculation
```
correlation_score = (keyword_match * 0.6) + (description_overlap * 0.4)
```

**Example**:
```
Failure: "Connection timeout detected"
Pattern Type: connection_timeout
Keywords: ['connection', 'cable', 'communication', 'timeout']

Procedure: "Check Network Connections - Verify all network cables..."
Keyword Matches: 3/4 (connection, cable, network)
Description Overlap: 0.4

Correlation Score: (0.75 * 0.6) + (0.4 * 0.4) = 0.61
```

## Cross-Source Consistency Metrics

The module calculates consistency across sources:

### 1. Component Identification Consistency
- Percentage of components with high confidence (>0.8)
- Measures how well components are identified

### 2. Source Agreement Consistency
- Agreement between different sources on component names
- Measures naming consistency across sources

### 3. Failure Pattern Coverage
- Average number of failure associations per component
- Measures completeness of failure information

### Overall Consistency
```
overall = (component_id + source_agreement + failure_coverage) / 3
```

## Dependencies

- `strands`: Tool decorator for agent integration
- `re`: Regular expression pattern matching
- `json`: JSON data handling
- `dataclasses`: Structured data representation
- `pathlib`: File path operations
- `logging`: Error and info logging

## Error Handling

- Invalid input data returns descriptive error messages
- Missing required fields trigger validation errors
- Empty data sources are handled gracefully
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Gather comprehensive data**: Use all available sources for best results
2. **Set appropriate thresholds**: Adjust correlation thresholds based on data quality
3. **Review consistency metrics**: High consistency indicates reliable correlations
4. **Prioritize high-confidence correlations**: Focus on correlations with strength >0.7
5. **Use canonical names**: Reference components by canonical names for consistency
6. **Combine with diagnosis**: Use unified analysis with diagnosis for complete picture
7. **Verify procedure matches**: Review procedure recommendations for accuracy
8. **Monitor source agreement**: Low agreement may indicate data quality issues
9. **Document findings**: Note correlations for future reference
10. **Iterate on thresholds**: Adjust thresholds based on results quality
