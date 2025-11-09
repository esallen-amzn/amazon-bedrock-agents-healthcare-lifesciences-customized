"""
Log Analysis Tools for Instrument Diagnosis Assistant

These tools handle processing large log files, comparing against gold standards,
and extracting failure patterns for diagnosis generation.
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from strands import tool

logger = logging.getLogger(__name__)


@dataclass
class LogAnalysisResult:
    """Result of log analysis operation"""
    status: str  # "PASS", "FAIL", "UNCERTAIN"
    confidence: float
    failure_indicators: List[str]
    comparison_summary: str
    recommendations: List[str]
    processing_stats: Dict[str, Any]


@dataclass
class LogChunk:
    """Represents a chunk of log data for processing"""
    chunk_id: int
    content: str
    start_line: int
    end_line: int
    size_bytes: int


@dataclass
class FailurePattern:
    """Represents a detected failure pattern"""
    pattern_type: str
    severity: str  # "CRITICAL", "WARNING", "INFO"
    description: str
    matched_lines: List[str]
    confidence: float
    timestamp_range: Optional[Tuple[str, str]] = None


class LogProcessor:
    """Core log processing functionality"""
    
    def __init__(self, chunk_size_mb: int = 50, max_file_size_mb: int = 250):
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Common failure patterns to detect
        self.failure_patterns = {
            'connection_timeout': {
                'regex': r'(?i)(timeout|connection.*failed|communication.*timeout)',
                'severity': 'CRITICAL',
                'description': 'Connection or communication timeout detected'
            },
            'memory_issues': {
                'regex': r'(?i)(memory.*leak|overflow|out of memory|high usage)',
                'severity': 'CRITICAL', 
                'description': 'Memory-related issues detected'
            },
            'disk_issues': {
                'regex': r'(?i)(disk.*error|write.*error|low space|disk.*full)',
                'severity': 'WARNING',
                'description': 'Disk or storage issues detected'
            },
            'service_failures': {
                'regex': r'(?i)(service.*failed|failed.*start|error.*loading)',
                'severity': 'CRITICAL',
                'description': 'Service or component failure detected'
            },
            'performance_degradation': {
                'regex': r'(?i)(degraded|slow|intermittent|partial.*success)',
                'severity': 'WARNING',
                'description': 'Performance degradation detected'
            },
            'driver_issues': {
                'regex': r'(?i)(driver.*error|outdated.*driver|version.*mismatch)',
                'severity': 'WARNING',
                'description': 'Driver-related issues detected'
            }
        }
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate log file before processing"""
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size_bytes:
                return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {self.max_file_size_bytes / (1024*1024)}MB)"
            
            # Try to read first few lines to validate format
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(5)]
                if not any(line.strip() for line in first_lines):
                    return False, "File appears to be empty or unreadable"
            
            return True, "File validation passed"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    def chunk_file(self, file_path: str) -> List[LogChunk]:
        """Split large log file into manageable chunks"""
        chunks = []
        chunk_id = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_chunk = ""
                current_size = 0
                start_line = 1
                line_number = 0
                
                for line in f:
                    line_number += 1
                    line_size = len(line.encode('utf-8'))
                    
                    if current_size + line_size > self.chunk_size_bytes and current_chunk:
                        # Create chunk
                        chunks.append(LogChunk(
                            chunk_id=chunk_id,
                            content=current_chunk,
                            start_line=start_line,
                            end_line=line_number - 1,
                            size_bytes=current_size
                        ))
                        
                        # Reset for next chunk
                        chunk_id += 1
                        current_chunk = line
                        current_size = line_size
                        start_line = line_number
                    else:
                        current_chunk += line
                        current_size += line_size
                
                # Add final chunk if there's remaining content
                if current_chunk:
                    chunks.append(LogChunk(
                        chunk_id=chunk_id,
                        content=current_chunk,
                        start_line=start_line,
                        end_line=line_number,
                        size_bytes=current_size
                    ))
            
            logger.info(f"Split file into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking file {file_path}: {str(e)}")
            raise
    
    def extract_patterns(self, content: str) -> List[FailurePattern]:
        """Extract failure patterns from log content"""
        patterns = []
        lines = content.split('\n')
        
        for pattern_name, pattern_config in self.failure_patterns.items():
            regex = re.compile(pattern_config['regex'])
            matched_lines = []
            
            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    matched_lines.append(f"Line {line_num}: {line.strip()}")
            
            if matched_lines:
                # Calculate confidence based on number of matches and severity
                base_confidence = 0.7 if pattern_config['severity'] == 'CRITICAL' else 0.5
                match_boost = min(0.3, len(matched_lines) * 0.1)
                confidence = min(1.0, base_confidence + match_boost)
                
                patterns.append(FailurePattern(
                    pattern_type=pattern_name,
                    severity=pattern_config['severity'],
                    description=pattern_config['description'],
                    matched_lines=matched_lines[:10],  # Limit to first 10 matches
                    confidence=confidence
                ))
        
        return patterns
    
    def compare_with_baseline(self, test_content: str, baseline_content: str) -> Dict[str, Any]:
        """Compare test log content with baseline (gold standard)"""
        test_patterns = self.extract_patterns(test_content)
        baseline_patterns = self.extract_patterns(baseline_content)
        
        # Count critical vs warning patterns
        test_critical = len([p for p in test_patterns if p.severity == 'CRITICAL'])
        test_warnings = len([p for p in test_patterns if p.severity == 'WARNING'])
        baseline_critical = len([p for p in baseline_patterns if p.severity == 'CRITICAL'])
        baseline_warnings = len([p for p in baseline_patterns if p.severity == 'WARNING'])
        
        # Calculate deviation scores
        critical_deviation = test_critical - baseline_critical
        warning_deviation = test_warnings - baseline_warnings
        
        # Determine overall status
        if critical_deviation > 0:
            status = "SIGNIFICANT_DEVIATION"
            severity = "CRITICAL"
        elif warning_deviation > 2:
            status = "MODERATE_DEVIATION" 
            severity = "WARNING"
        elif warning_deviation > 0:
            status = "MINOR_DEVIATION"
            severity = "INFO"
        else:
            status = "BASELINE_MATCH"
            severity = "INFO"
        
        return {
            'status': status,
            'severity': severity,
            'test_patterns': len(test_patterns),
            'baseline_patterns': len(baseline_patterns),
            'critical_deviation': critical_deviation,
            'warning_deviation': warning_deviation,
            'unique_test_patterns': [p.pattern_type for p in test_patterns 
                                   if p.pattern_type not in [bp.pattern_type for bp in baseline_patterns]]
        }


# Initialize global processor
_log_processor = LogProcessor()


@tool(
    name="analyze_logs",
    description="Analyze log files with optional gold standard comparison to identify failures and anomalies. Can process single files or multiple files in batch."
)
def analyze_logs(
    test_log_path: str,
    baseline_log_path: str = "",
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """
    Analyze log files with optional gold standard baseline comparison.
    
    Args:
        test_log_path: Path to the log file to analyze
        baseline_log_path: Optional path to the gold standard log file for comparison (empty string if not available)
        analysis_type: Type of analysis ("full", "patterns_only", "quick")
    
    Returns:
        Dictionary containing analysis results with status, patterns, and recommendations
    """
    try:
        # Validate test log file
        test_valid, test_msg = _log_processor.validate_file(test_log_path)
        if not test_valid:
            return {"error": f"Test log validation failed: {test_msg}"}
        
        # Read test file content
        with open(test_log_path, 'r', encoding='utf-8', errors='ignore') as f:
            test_content = f.read()
        
        # Extract patterns from test file
        test_patterns = _log_processor.extract_patterns(test_content)
        
        # Handle optional baseline
        baseline_content = ""
        baseline_patterns = []
        comparison = None
        
        if baseline_log_path and baseline_log_path.strip():
            # Validate baseline file if provided
            baseline_valid, baseline_msg = _log_processor.validate_file(baseline_log_path)
            if baseline_valid:
                with open(baseline_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    baseline_content = f.read()
                
                baseline_patterns = _log_processor.extract_patterns(baseline_content)
                comparison = _log_processor.compare_with_baseline(test_content, baseline_content)
            else:
                logger.warning(f"Baseline log validation failed: {baseline_msg}. Proceeding with standalone analysis.")
        
        # Determine analysis mode
        has_baseline = comparison is not None
        
        # Generate recommendations based on findings
        recommendations = []
        critical_patterns = [p for p in test_patterns if p.severity == 'CRITICAL']
        warning_patterns = [p for p in test_patterns if p.severity == 'WARNING']
        
        if has_baseline:
            # Baseline comparison recommendations
            if comparison['critical_deviation'] > 0:
                recommendations.append("CRITICAL: Investigate connection timeouts and service failures immediately")
            if comparison['warning_deviation'] > 2:
                recommendations.append("WARNING: Multiple performance issues detected - check system resources")
            if comparison['status'] == 'BASELINE_MATCH':
                recommendations.append("System appears to be operating within normal parameters")
        else:
            # Standalone analysis recommendations
            if critical_patterns:
                recommendations.append("CRITICAL: Critical failure patterns detected - immediate investigation required")
            if len(warning_patterns) > 3:
                recommendations.append("WARNING: Multiple warning patterns detected - system monitoring recommended")
            if not test_patterns:
                recommendations.append("INFO: No obvious failure patterns detected in log analysis")
        
        # Determine status and confidence
        if has_baseline:
            # Use comparison-based status
            status = "FAIL" if comparison['critical_deviation'] > 0 else \
                    "UNCERTAIN" if comparison['warning_deviation'] > 1 else "PASS"
            confidence = 0.9 if comparison['critical_deviation'] > 0 else \
                        0.7 if comparison['warning_deviation'] > 0 else 0.85
            comparison_summary = f"Found {len(test_patterns)} patterns vs {len(baseline_patterns)} in baseline. Status: {comparison['status']}"
        else:
            # Use standalone analysis status
            status = "FAIL" if critical_patterns else \
                    "UNCERTAIN" if len(warning_patterns) > 2 else "PASS"
            confidence = 0.85 if critical_patterns else \
                        0.7 if warning_patterns else 0.8
            comparison_summary = f"Standalone analysis: Found {len(test_patterns)} patterns ({len(critical_patterns)} critical, {len(warning_patterns)} warnings). No baseline comparison available."
        
        # Build result
        result = LogAnalysisResult(
            status=status,
            confidence=confidence,
            failure_indicators=[p.description for p in critical_patterns],
            comparison_summary=comparison_summary,
            recommendations=recommendations,
            processing_stats={
                'test_file_size': len(test_content),
                'baseline_file_size': len(baseline_content) if baseline_content else 0,
                'patterns_detected': len(test_patterns),
                'critical_patterns': len(critical_patterns),
                'warning_patterns': len(warning_patterns),
                'has_baseline': has_baseline,
                'comparison_result': comparison
            }
        )
        
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_logs: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}


@tool(
    name="analyze_multiple_logs",
    description="Analyze multiple log files in batch for comprehensive diagnosis across multiple instruments or time periods"
)
def analyze_multiple_logs(
    log_file_paths: List[str],
    baseline_log_path: str = "",
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """
    Analyze multiple log files in batch for comprehensive diagnosis.
    
    Args:
        log_file_paths: List of paths to log files to analyze
        baseline_log_path: Optional path to gold standard log file for comparison
        analysis_type: Type of analysis ("full", "patterns_only", "quick")
    
    Returns:
        Dictionary containing aggregated analysis results across all files
    """
    try:
        if not log_file_paths:
            return {"error": "No log file paths provided"}
        
        all_results = []
        aggregated_patterns = []
        total_critical = 0
        total_warnings = 0
        
        # Process each file
        for i, log_path in enumerate(log_file_paths):
            logger.info(f"Processing file {i+1}/{len(log_file_paths)}: {log_path}")
            
            # Analyze individual file
            result = analyze_logs(log_path, baseline_log_path, analysis_type)
            
            if "error" not in result:
                all_results.append({
                    'file_path': log_path,
                    'result': result
                })
                
                # Aggregate statistics
                stats = result.get('processing_stats', {})
                total_critical += stats.get('critical_patterns', 0)
                total_warnings += stats.get('warning_patterns', 0)
        
        if not all_results:
            return {"error": "No files could be processed successfully"}
        
        # Determine overall status
        if total_critical > 0:
            overall_status = "FAIL"
            confidence = 0.9
        elif total_warnings > len(log_file_paths) * 2:  # More than 2 warnings per file
            overall_status = "UNCERTAIN"
            confidence = 0.7
        else:
            overall_status = "PASS"
            confidence = 0.8
        
        # Generate summary
        summary = f"Batch analysis of {len(log_file_paths)} files completed. "
        summary += f"Total critical patterns: {total_critical}, Total warnings: {total_warnings}. "
        summary += f"Overall assessment: {overall_status}"
        
        # Recommendations
        recommendations = []
        if total_critical > 0:
            recommendations.append("CRITICAL: Multiple files show critical failure patterns - immediate investigation required")
        if total_warnings > len(log_file_paths) * 3:
            recommendations.append("WARNING: High warning pattern density across files - system monitoring recommended")
        if overall_status == "PASS":
            recommendations.append("INFO: All files show acceptable patterns - continue normal operation")
        
        return {
            'overall_status': overall_status,
            'confidence': confidence,
            'files_processed': len(log_file_paths),
            'total_critical_patterns': total_critical,
            'total_warning_patterns': total_warnings,
            'summary': summary,
            'recommendations': recommendations,
            'individual_results': all_results[:5],  # Limit to first 5 for brevity
            'batch_analysis': True
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_multiple_logs: {str(e)}")
        return {"error": f"Batch analysis failed: {str(e)}"}


@tool(
    name="scan_for_uploaded_files",
    description="MANDATORY FIRST STEP: Always use this tool first to scan temp_uploads directory for available log files before any analysis"
)
def scan_for_uploaded_files() -> Dict[str, Any]:
    """
    Scan for uploaded files in the temp_uploads directory.
    
    Returns:
        Dictionary containing information about available files for analysis
    """
    try:
        from pathlib import Path
        import os
        
        temp_dir = Path("temp_uploads")
        
        if not temp_dir.exists():
            return {
                "files_found": 0,
                "message": "No temp_uploads directory found. Please upload log files first.",
                "files": []
            }
        
        # Find log files
        log_files = []
        for pattern in ["*.log", "*.txt", "*.csv"]:
            log_files.extend(temp_dir.glob(pattern))
        
        if not log_files:
            return {
                "files_found": 0,
                "message": "No log files found in temp_uploads directory. Please upload log files.",
                "files": []
            }
        
        # Process file information
        file_info = []
        for file_path in log_files:
            try:
                file_size = file_path.stat().st_size
                file_info.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "type": "error_log" if "error" in file_path.name.lower() else "log"
                })
            except Exception as e:
                logger.warning(f"Could not process file {file_path}: {e}")
        
        # Sort by size (largest first) and limit to most recent 10
        file_info.sort(key=lambda x: x["size_bytes"], reverse=True)
        file_info = file_info[:10]
        
        return {
            "files_found": len(file_info),
            "message": f"Found {len(file_info)} log files ready for analysis",
            "files": file_info,
            "recommended_action": f"Use analyze_logs('{file_info[0]['path']}', '') to analyze the largest file, or analyze_multiple_logs([paths]) for batch analysis"
        }
        
    except Exception as e:
        logger.error(f"Error scanning for files: {str(e)}")
        return {"error": f"File scan failed: {str(e)}"}


@tool(
    name="process_large_files", 
    description="Process large log files (>50MB) using chunked processing for memory efficiency"
)
def process_large_files(
    file_path: str,
    processing_mode: str = "patterns",
    chunk_size_mb: int = 50
) -> Dict[str, Any]:
    """
    Process large log files using chunked approach to handle files up to 250MB.
    
    Args:
        file_path: Path to the large log file to process
        processing_mode: Processing mode ("patterns", "summary", "full")
        chunk_size_mb: Size of each chunk in MB (default: 50)
    
    Returns:
        Dictionary containing processing results and aggregated analysis
    """
    try:
        # Update processor chunk size if specified
        processor = LogProcessor(chunk_size_mb=chunk_size_mb)
        
        # Validate file
        valid, msg = processor.validate_file(file_path)
        if not valid:
            return {"error": f"File validation failed: {msg}"}
        
        # Split into chunks
        chunks = processor.chunk_file(file_path)
        
        # Process each chunk
        all_patterns = []
        chunk_summaries = []
        total_lines = 0
        
        for chunk in chunks:
            # Extract patterns from chunk
            patterns = processor.extract_patterns(chunk.content)
            all_patterns.extend(patterns)
            
            # Create chunk summary
            chunk_summary = {
                'chunk_id': chunk.chunk_id,
                'lines': f"{chunk.start_line}-{chunk.end_line}",
                'size_mb': chunk.size_bytes / (1024 * 1024),
                'patterns_found': len(patterns),
                'critical_patterns': len([p for p in patterns if p.severity == 'CRITICAL']),
                'warning_patterns': len([p for p in patterns if p.severity == 'WARNING'])
            }
            chunk_summaries.append(chunk_summary)
            total_lines = max(total_lines, chunk.end_line)
        
        # Aggregate results
        critical_patterns = [p for p in all_patterns if p.severity == 'CRITICAL']
        warning_patterns = [p for p in all_patterns if p.severity == 'WARNING']
        
        # Determine overall status
        if len(critical_patterns) > 0:
            overall_status = "CRITICAL_ISSUES_DETECTED"
            confidence = 0.9
        elif len(warning_patterns) > 3:
            overall_status = "MULTIPLE_WARNINGS"
            confidence = 0.7
        elif len(warning_patterns) > 0:
            overall_status = "MINOR_ISSUES"
            confidence = 0.6
        else:
            overall_status = "NO_ISSUES_DETECTED"
            confidence = 0.8
        
        result = {
            'status': overall_status,
            'confidence': confidence,
            'file_info': {
                'path': file_path,
                'total_chunks': len(chunks),
                'total_lines': total_lines,
                'file_size_mb': os.path.getsize(file_path) / (1024 * 1024)
            },
            'analysis_summary': {
                'total_patterns': len(all_patterns),
                'critical_patterns': len(critical_patterns),
                'warning_patterns': len(warning_patterns),
                'pattern_types': list(set(p.pattern_type for p in all_patterns))
            },
            'chunk_details': chunk_summaries,
            'top_issues': [
                {
                    'type': p.pattern_type,
                    'severity': p.severity,
                    'description': p.description,
                    'confidence': p.confidence,
                    'sample_matches': p.matched_lines[:3]  # First 3 matches
                }
                for p in sorted(all_patterns, key=lambda x: (x.severity == 'CRITICAL', x.confidence), reverse=True)[:10]
            ]
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_large_files: {str(e)}")
        return {"error": f"Large file processing failed: {str(e)}"}


@tool(
    name="analyze_log_content",
    description="Analyze log content directly without requiring file paths - useful for uploaded file content"
)
def analyze_log_content(
    test_log_content: str,
    baseline_log_content: str = "",
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """
    Analyze log content directly by comparing against baseline content.
    
    Args:
        test_log_content: The log content to analyze
        baseline_log_content: Optional baseline log content for comparison
        analysis_type: Type of analysis ("full", "patterns_only", "quick")
    
    Returns:
        Dictionary containing analysis results with status, patterns, and recommendations
    """
    try:
        if not test_log_content or not test_log_content.strip():
            return {"error": "Empty or invalid test log content provided"}
        
        # Extract patterns from test content
        test_patterns = _log_processor.extract_patterns(test_log_content)
        
        # If baseline provided, do comparison
        comparison = None
        if baseline_log_content and baseline_log_content.strip():
            comparison = _log_processor.compare_with_baseline(test_log_content, baseline_log_content)
        
        # Generate recommendations based on findings
        recommendations = []
        critical_patterns = [p for p in test_patterns if p.severity == 'CRITICAL']
        warning_patterns = [p for p in test_patterns if p.severity == 'WARNING']
        
        if critical_patterns:
            recommendations.append("CRITICAL: Investigate connection timeouts and service failures immediately")
        if len(warning_patterns) > 2:
            recommendations.append("WARNING: Multiple performance issues detected - check system resources")
        if not test_patterns:
            recommendations.append("No obvious failure patterns detected in the log content")
        
        # Determine status
        if comparison:
            status = "FAIL" if comparison['critical_deviation'] > 0 else \
                    "UNCERTAIN" if comparison['warning_deviation'] > 1 else "PASS"
            confidence = 0.9 if comparison['critical_deviation'] > 0 else \
                        0.7 if comparison['warning_deviation'] > 0 else 0.85
        else:
            # Standalone analysis without baseline
            status = "FAIL" if critical_patterns else \
                    "UNCERTAIN" if len(warning_patterns) > 2 else "PASS"
            confidence = 0.8 if critical_patterns else \
                        0.6 if warning_patterns else 0.7
        
        # Build result
        result = LogAnalysisResult(
            status=status,
            confidence=confidence,
            failure_indicators=[p.description for p in critical_patterns],
            comparison_summary=f"Found {len(test_patterns)} patterns. " + 
                             (f"Comparison: {comparison['status']}" if comparison else "No baseline comparison"),
            recommendations=recommendations,
            processing_stats={
                'content_length': len(test_log_content),
                'baseline_length': len(baseline_log_content) if baseline_log_content else 0,
                'patterns_detected': len(test_patterns),
                'critical_patterns': len(critical_patterns),
                'warning_patterns': len(warning_patterns),
                'comparison_result': comparison
            }
        )
        
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_log_content: {str(e)}")
        return {"error": f"Content analysis failed: {str(e)}"}


@tool(
    name="extract_failure_indicators",
    description="Extract and categorize specific failure patterns and indicators from log content"
)
def extract_failure_indicators(
    log_content: str,
    indicator_types: List[str] = None,
    severity_filter: str = "all"
) -> Dict[str, Any]:
    """
    Extract specific failure indicators and patterns from log content.
    
    Args:
        log_content: Raw log content to analyze
        indicator_types: List of specific indicator types to look for (optional)
        severity_filter: Filter by severity ("all", "critical", "warning")
    
    Returns:
        Dictionary containing categorized failure indicators and analysis
    """
    try:
        if not log_content or not log_content.strip():
            return {"error": "Empty or invalid log content provided"}
        
        # Extract all patterns
        patterns = _log_processor.extract_patterns(log_content)
        
        # Filter by indicator types if specified
        if indicator_types:
            patterns = [p for p in patterns if p.pattern_type in indicator_types]
        
        # Filter by severity
        if severity_filter.lower() == "critical":
            patterns = [p for p in patterns if p.severity == "CRITICAL"]
        elif severity_filter.lower() == "warning":
            patterns = [p for p in patterns if p.severity == "WARNING"]
        
        # Categorize patterns
        categorized = {
            'critical_failures': [],
            'performance_issues': [],
            'connection_problems': [],
            'resource_issues': [],
            'other_warnings': []
        }
        
        for pattern in patterns:
            if pattern.pattern_type in ['connection_timeout', 'service_failures']:
                if pattern.severity == 'CRITICAL':
                    categorized['critical_failures'].append(pattern)
                else:
                    categorized['connection_problems'].append(pattern)
            elif pattern.pattern_type in ['memory_issues', 'disk_issues']:
                categorized['resource_issues'].append(pattern)
            elif pattern.pattern_type == 'performance_degradation':
                categorized['performance_issues'].append(pattern)
            else:
                categorized['other_warnings'].append(pattern)
        
        # Generate summary statistics
        total_indicators = len(patterns)
        critical_count = len([p for p in patterns if p.severity == 'CRITICAL'])
        warning_count = len([p for p in patterns if p.severity == 'WARNING'])
        
        # Calculate risk score (0-100)
        risk_score = min(100, (critical_count * 30) + (warning_count * 10))
        
        result = {
            'summary': {
                'total_indicators': total_indicators,
                'critical_count': critical_count,
                'warning_count': warning_count,
                'risk_score': risk_score,
                'risk_level': 'HIGH' if risk_score > 70 else 'MEDIUM' if risk_score > 30 else 'LOW'
            },
            'categorized_indicators': {
                category: [
                    {
                        'type': p.pattern_type,
                        'severity': p.severity,
                        'description': p.description,
                        'confidence': p.confidence,
                        'matches': len(p.matched_lines),
                        'sample_lines': p.matched_lines[:5]  # First 5 matches
                    }
                    for p in indicators
                ]
                for category, indicators in categorized.items()
                if indicators  # Only include categories with indicators
            },
            'recommendations': _generate_indicator_recommendations(categorized, risk_score)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in extract_failure_indicators: {str(e)}")
        return {"error": f"Failure indicator extraction failed: {str(e)}"}


def _generate_indicator_recommendations(categorized: Dict, risk_score: int) -> List[str]:
    """Generate recommendations based on categorized indicators"""
    recommendations = []
    
    if categorized['critical_failures']:
        recommendations.append("URGENT: Critical system failures detected - immediate investigation required")
    
    if categorized['connection_problems']:
        recommendations.append("Check network connectivity and USB/serial connections")
    
    if categorized['resource_issues']:
        recommendations.append("Monitor system resources - memory and disk space may be insufficient")
    
    if categorized['performance_issues']:
        recommendations.append("Performance degradation detected - consider system optimization")
    
    if risk_score > 70:
        recommendations.append("HIGH RISK: Multiple critical issues - system may be unreliable")
    elif risk_score > 30:
        recommendations.append("MEDIUM RISK: Several issues detected - preventive maintenance recommended")
    else:
        recommendations.append("LOW RISK: Minor issues detected - monitor for trends")
    
    return recommendations


# List of available log analysis tools
LOG_ANALYSIS_TOOLS = [
    analyze_logs,
    analyze_log_content,
    process_large_files,
    extract_failure_indicators
]