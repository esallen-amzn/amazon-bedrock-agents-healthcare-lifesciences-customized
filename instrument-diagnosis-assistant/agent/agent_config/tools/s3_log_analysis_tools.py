"""
S3-Based Log Analysis Tools for Instrument Diagnosis Assistant

These tools analyze log files stored in S3 using streaming and chunked processing
to handle large files efficiently without loading entire files into memory.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from strands import tool
from .s3_storage_tools import get_storage_manager
from .log_analysis_tools import LogProcessor, FailurePattern

logger = logging.getLogger(__name__)


@dataclass
class LogSummary:
    """Summary of key information extracted from a log file"""
    s3_uri: str
    file_name: str
    total_lines: int
    error_count: int
    warning_count: int
    critical_events: List[str]
    error_patterns: List[str]
    warning_patterns: List[str]
    timestamp_range: Optional[Tuple[str, str]]
    summary_length: int


class S3LogAnalyzer:
    """Analyzer for S3-stored log files with streaming support"""
    
    def __init__(self, chunk_size_mb: int = 10, buffer_size: int = 8192):
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        self.buffer_size = buffer_size
        self.log_processor = LogProcessor(chunk_size_mb=chunk_size_mb)
    
    def extract_summary(self, content: str, max_length: int = 5000) -> LogSummary:
        """
        Extract key information from log content.
        
        Args:
            content: Log file content
            max_length: Maximum length of summary in characters
        
        Returns:
            LogSummary object with extracted information
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Count errors and warnings
        error_count = 0
        warning_count = 0
        error_lines = []
        warning_lines = []
        critical_events = []
        
        error_pattern = re.compile(r'(?i)(error|fail|exception|critical)', re.IGNORECASE)
        warning_pattern = re.compile(r'(?i)(warning|warn|caution)', re.IGNORECASE)
        critical_pattern = re.compile(r'(?i)(critical|fatal|severe|emergency)', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            if critical_pattern.search(line):
                critical_events.append(f"Line {i+1}: {line.strip()}")
            elif error_pattern.search(line):
                error_count += 1
                if len(error_lines) < 20:  # Keep first 20 errors
                    error_lines.append(f"Line {i+1}: {line.strip()}")
            elif warning_pattern.search(line):
                warning_count += 1
                if len(warning_lines) < 10:  # Keep first 10 warnings
                    warning_lines.append(f"Line {i+1}: {line.strip()}")
        
        # Extract timestamp range (if available)
        timestamp_range = self._extract_timestamp_range(lines)
        
        # Create summary
        summary = LogSummary(
            s3_uri="",  # Will be set by caller
            file_name="",  # Will be set by caller
            total_lines=total_lines,
            error_count=error_count,
            warning_count=warning_count,
            critical_events=critical_events[:10],  # Limit to 10
            error_patterns=error_lines[:10],  # Limit to 10
            warning_patterns=warning_lines[:5],  # Limit to 5
            timestamp_range=timestamp_range,
            summary_length=len(content)
        )
        
        return summary
    
    def _extract_timestamp_range(self, lines: List[str]) -> Optional[Tuple[str, str]]:
        """Extract first and last timestamps from log lines"""
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}')
        
        first_timestamp = None
        last_timestamp = None
        
        # Find first timestamp
        for line in lines[:100]:  # Check first 100 lines
            match = timestamp_pattern.search(line)
            if match:
                first_timestamp = match.group()
                break
        
        # Find last timestamp
        for line in reversed(lines[-100:]):  # Check last 100 lines
            match = timestamp_pattern.search(line)
            if match:
                last_timestamp = match.group()
                break
        
        if first_timestamp and last_timestamp:
            return (first_timestamp, last_timestamp)
        return None
    
    def analyze_with_streaming(self, s3_key: str) -> Dict[str, Any]:
        """
        Analyze S3 log file using streaming to handle large files.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            storage_manager = get_storage_manager()
            
            # Stream content from S3
            content = storage_manager.stream_file_content(s3_key)
            
            # Extract patterns using log processor
            patterns = self.log_processor.extract_patterns(content)
            
            # Extract summary
            summary = self.extract_summary(content)
            summary.s3_uri = f"s3://{storage_manager.bucket_name}/{s3_key}"
            summary.file_name = s3_key.split('/')[-1]
            
            # Categorize patterns
            critical_patterns = [p for p in patterns if p.severity == 'CRITICAL']
            warning_patterns = [p for p in patterns if p.severity == 'WARNING']
            
            return {
                'success': True,
                's3_key': s3_key,
                's3_uri': summary.s3_uri,
                'summary': asdict(summary),
                'patterns': {
                    'total': len(patterns),
                    'critical': len(critical_patterns),
                    'warnings': len(warning_patterns),
                    'details': [
                        {
                            'type': p.pattern_type,
                            'severity': p.severity,
                            'description': p.description,
                            'confidence': p.confidence,
                            'matches': len(p.matched_lines),
                            'sample_lines': p.matched_lines[:3]
                        }
                        for p in patterns[:10]  # Limit to top 10 patterns
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_with_streaming: {str(e)}")
            raise
    
    def compare_s3_logs(self, test_s3_key: str, baseline_s3_key: str) -> Dict[str, Any]:
        """
        Compare two S3-stored log files for pattern analysis.
        
        Args:
            test_s3_key: S3 key for test log
            baseline_s3_key: S3 key for baseline log
        
        Returns:
            Dictionary containing comparison results
        """
        try:
            storage_manager = get_storage_manager()
            
            # Stream both files
            test_content = storage_manager.stream_file_content(test_s3_key)
            baseline_content = storage_manager.stream_file_content(baseline_s3_key)
            
            # Extract patterns from both
            test_patterns = self.log_processor.extract_patterns(test_content)
            baseline_patterns = self.log_processor.extract_patterns(baseline_content)
            
            # Compare patterns
            comparison = self.log_processor.compare_with_baseline(test_content, baseline_content)
            
            # Extract summaries
            test_summary = self.extract_summary(test_content)
            baseline_summary = self.extract_summary(baseline_content)
            
            return {
                'success': True,
                'test_file': {
                    's3_key': test_s3_key,
                    'summary': asdict(test_summary),
                    'patterns': len(test_patterns)
                },
                'baseline_file': {
                    's3_key': baseline_s3_key,
                    'summary': asdict(baseline_summary),
                    'patterns': len(baseline_patterns)
                },
                'comparison': comparison,
                'deviation_analysis': {
                    'critical_deviation': comparison['critical_deviation'],
                    'warning_deviation': comparison['warning_deviation'],
                    'status': comparison['status'],
                    'severity': comparison['severity']
                }
            }
            
        except Exception as e:
            logger.error(f"Error in compare_s3_logs: {str(e)}")
            raise


# Global analyzer instance
_s3_analyzer = None


def get_s3_analyzer() -> S3LogAnalyzer:
    """Get or create global S3 analyzer instance"""
    global _s3_analyzer
    if _s3_analyzer is None:
        _s3_analyzer = S3LogAnalyzer()
    return _s3_analyzer


@tool(
    name="analyze_s3_log",
    description="Analyze a log file stored in S3 by streaming content and extracting failure patterns. Efficient for large files."
)
def analyze_s3_log(
    s3_uri: str = "",
    s3_key: str = ""
) -> Dict[str, Any]:
    """
    Analyze S3-stored log file with streaming.
    
    Args:
        s3_uri: S3 URI (s3://bucket/key) - provide either this or s3_key
        s3_key: S3 object key - provide either this or s3_uri
    
    Returns:
        Dictionary containing analysis results with patterns and summary
    """
    try:
        # Parse S3 URI if provided
        if s3_uri:
            if not s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format. Must start with s3://'}
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            bucket, key = parts
            s3_key = key
        
        if not s3_key:
            return {'error': 'Either s3_uri or s3_key must be provided'}
        
        # Analyze log
        analyzer = get_s3_analyzer()
        result = analyzer.analyze_with_streaming(s3_key)
        
        # Add recommendations based on findings
        summary = result['summary']
        patterns = result['patterns']
        
        recommendations = []
        if patterns['critical'] > 0:
            recommendations.append("CRITICAL: Critical failure patterns detected - immediate investigation required")
        if summary['error_count'] > 50:
            recommendations.append(f"HIGH: {summary['error_count']} errors detected - system may be unstable")
        if summary['warning_count'] > 100:
            recommendations.append(f"MEDIUM: {summary['warning_count']} warnings detected - monitor system closely")
        if patterns['critical'] == 0 and summary['error_count'] < 10:
            recommendations.append("INFO: Log appears healthy with minimal issues")
        
        result['recommendations'] = recommendations
        
        # Determine overall status
        if patterns['critical'] > 0:
            result['status'] = 'FAIL'
            result['confidence'] = 0.9
        elif summary['error_count'] > 50:
            result['status'] = 'UNCERTAIN'
            result['confidence'] = 0.7
        else:
            result['status'] = 'PASS'
            result['confidence'] = 0.8
        
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_s3_log: {str(e)}")
        return {'error': f'Analysis failed: {str(e)}'}


@tool(
    name="extract_s3_log_summary",
    description="Extract a smart summary from an S3-stored log file including error counts, critical events, and key patterns. Use this for large files before full analysis."
)
def extract_s3_log_summary(
    s3_uri: str = "",
    s3_key: str = "",
    max_summary_length: int = 5000
) -> Dict[str, Any]:
    """
    Extract summary information from S3-stored log file.
    
    Args:
        s3_uri: S3 URI (s3://bucket/key) - provide either this or s3_key
        s3_key: S3 object key - provide either this or s3_uri
        max_summary_length: Maximum length of summary in characters
    
    Returns:
        Dictionary containing log summary with key metrics and events
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI if provided
        if s3_uri:
            if not s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format. Must start with s3://'}
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            bucket, key = parts
            s3_key = key
        
        if not s3_key:
            return {'error': 'Either s3_uri or s3_key must be provided'}
        
        # Stream content
        content = storage_manager.stream_file_content(s3_key)
        
        # Extract summary
        analyzer = get_s3_analyzer()
        summary = analyzer.extract_summary(content, max_summary_length)
        summary.s3_uri = f"s3://{storage_manager.bucket_name}/{s3_key}"
        summary.file_name = s3_key.split('/')[-1]
        
        result = asdict(summary)
        result['success'] = True
        
        # Add quick assessment
        if summary.error_count > 50 or len(summary.critical_events) > 0:
            result['quick_assessment'] = 'ISSUES_DETECTED'
            result['severity'] = 'HIGH' if len(summary.critical_events) > 0 else 'MEDIUM'
        elif summary.warning_count > 20:
            result['quick_assessment'] = 'WARNINGS_PRESENT'
            result['severity'] = 'LOW'
        else:
            result['quick_assessment'] = 'APPEARS_HEALTHY'
            result['severity'] = 'NONE'
        
        return result
        
    except Exception as e:
        logger.error(f"Error in extract_s3_log_summary: {str(e)}")
        return {'error': f'Summary extraction failed: {str(e)}'}


@tool(
    name="compare_s3_logs",
    description="Compare two S3-stored log files to identify differences and deviations. Useful for comparing test logs against gold standard baselines."
)
def compare_s3_logs(
    test_s3_uri: str = "",
    test_s3_key: str = "",
    baseline_s3_uri: str = "",
    baseline_s3_key: str = ""
) -> Dict[str, Any]:
    """
    Compare two S3-stored log files for pattern analysis.
    
    Args:
        test_s3_uri: S3 URI for test log - provide either this or test_s3_key
        test_s3_key: S3 key for test log - provide either this or test_s3_uri
        baseline_s3_uri: S3 URI for baseline log - provide either this or baseline_s3_key
        baseline_s3_key: S3 key for baseline log - provide either this or baseline_s3_uri
    
    Returns:
        Dictionary containing comparison results and deviation analysis
    """
    try:
        # Parse test S3 URI if provided
        if test_s3_uri:
            if not test_s3_uri.startswith('s3://'):
                return {'error': 'Invalid test S3 URI format'}
            parts = test_s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid test S3 URI format'}
            test_s3_key = parts[1]
        
        # Parse baseline S3 URI if provided
        if baseline_s3_uri:
            if not baseline_s3_uri.startswith('s3://'):
                return {'error': 'Invalid baseline S3 URI format'}
            parts = baseline_s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid baseline S3 URI format'}
            baseline_s3_key = parts[1]
        
        if not test_s3_key or not baseline_s3_key:
            return {'error': 'Both test and baseline S3 keys/URIs must be provided'}
        
        # Compare logs
        analyzer = get_s3_analyzer()
        result = analyzer.compare_s3_logs(test_s3_key, baseline_s3_key)
        
        # Add recommendations
        comparison = result['comparison']
        recommendations = []
        
        if comparison['critical_deviation'] > 0:
            recommendations.append("CRITICAL: Test log shows more critical issues than baseline - investigate immediately")
        if comparison['warning_deviation'] > 5:
            recommendations.append("WARNING: Significant increase in warning patterns compared to baseline")
        if comparison['status'] == 'BASELINE_MATCH':
            recommendations.append("INFO: Test log patterns match baseline - system operating normally")
        if comparison['unique_test_patterns']:
            recommendations.append(f"ATTENTION: New pattern types detected: {', '.join(comparison['unique_test_patterns'])}")
        
        result['recommendations'] = recommendations
        
        # Overall assessment
        if comparison['critical_deviation'] > 0:
            result['overall_status'] = 'FAIL'
            result['confidence'] = 0.9
        elif comparison['warning_deviation'] > 3:
            result['overall_status'] = 'UNCERTAIN'
            result['confidence'] = 0.7
        else:
            result['overall_status'] = 'PASS'
            result['confidence'] = 0.85
        
        return result
        
    except Exception as e:
        logger.error(f"Error in compare_s3_logs: {str(e)}")
        return {'error': f'Comparison failed: {str(e)}'}


@tool(
    name="batch_analyze_s3_logs",
    description="Analyze multiple S3-stored log files in batch for comprehensive diagnosis across multiple instruments or sessions."
)
def batch_analyze_s3_logs(
    s3_keys: List[str],
    baseline_s3_key: str = ""
) -> Dict[str, Any]:
    """
    Analyze multiple S3-stored log files in batch.
    
    Args:
        s3_keys: List of S3 object keys to analyze
        baseline_s3_key: Optional baseline S3 key for comparison
    
    Returns:
        Dictionary containing aggregated analysis results
    """
    try:
        if not s3_keys:
            return {'error': 'No S3 keys provided'}
        
        analyzer = get_s3_analyzer()
        all_results = []
        total_critical = 0
        total_errors = 0
        total_warnings = 0
        
        # Analyze each file
        for i, s3_key in enumerate(s3_keys):
            logger.info(f"Analyzing file {i+1}/{len(s3_keys)}: {s3_key}")
            
            try:
                result = analyzer.analyze_with_streaming(s3_key)
                all_results.append(result)
                
                # Aggregate statistics
                total_critical += result['patterns']['critical']
                total_errors += result['summary']['error_count']
                total_warnings += result['summary']['warning_count']
                
            except Exception as e:
                logger.warning(f"Failed to analyze {s3_key}: {str(e)}")
                all_results.append({
                    'success': False,
                    's3_key': s3_key,
                    'error': str(e)
                })
        
        # Determine overall status
        if total_critical > 0:
            overall_status = 'FAIL'
            confidence = 0.9
        elif total_errors > len(s3_keys) * 50:
            overall_status = 'UNCERTAIN'
            confidence = 0.7
        else:
            overall_status = 'PASS'
            confidence = 0.8
        
        # Generate summary
        successful_analyses = len([r for r in all_results if r.get('success', False)])
        summary = f"Batch analysis of {len(s3_keys)} files: {successful_analyses} successful. "
        summary += f"Total: {total_critical} critical patterns, {total_errors} errors, {total_warnings} warnings."
        
        # Recommendations
        recommendations = []
        if total_critical > 0:
            recommendations.append("CRITICAL: Multiple files show critical patterns - system-wide investigation required")
        if total_errors > len(s3_keys) * 100:
            recommendations.append("HIGH: High error density across files - check system configuration")
        if overall_status == 'PASS':
            recommendations.append("INFO: All files show acceptable patterns - continue monitoring")
        
        return {
            'success': True,
            'overall_status': overall_status,
            'confidence': confidence,
            'files_analyzed': len(s3_keys),
            'successful_analyses': successful_analyses,
            'total_critical_patterns': total_critical,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'summary': summary,
            'recommendations': recommendations,
            'individual_results': all_results[:5]  # Limit to first 5 for brevity
        }
        
    except Exception as e:
        logger.error(f"Error in batch_analyze_s3_logs: {str(e)}")
        return {'error': f'Batch analysis failed: {str(e)}'}


# List of S3 log analysis tools
S3_LOG_ANALYSIS_TOOLS = [
    analyze_s3_log,
    extract_s3_log_summary,
    compare_s3_logs,
    batch_analyze_s3_logs
]
