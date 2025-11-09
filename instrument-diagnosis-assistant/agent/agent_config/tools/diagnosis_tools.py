"""
Diagnosis Generation Tools for Instrument Diagnosis Assistant

These tools generate comprehensive diagnoses based on S3 log analysis results,
with confidence scoring and recommendation generation.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from strands import tool
from .s3_storage_tools import get_storage_manager
from .s3_log_analysis_tools import get_s3_analyzer

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisResult:
    """Comprehensive diagnosis result"""
    diagnosis_id: str
    timestamp: str
    status: str  # "PASS", "FAIL", "UNCERTAIN"
    confidence: float
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"
    summary: str
    failure_indicators: List[str]
    root_causes: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    supporting_evidence: Dict[str, Any]
    s3_references: List[str]


class DiagnosisGenerator:
    """Generates comprehensive diagnoses from log analysis results"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
    
    def generate_diagnosis(
        self,
        analysis_results: Dict[str, Any],
        session_id: str,
        additional_context: str = ""
    ) -> DiagnosisResult:
        """
        Generate comprehensive diagnosis from analysis results.
        
        Args:
            analysis_results: Results from log analysis
            session_id: Session identifier
            additional_context: Additional context for diagnosis
        
        Returns:
            DiagnosisResult object
        """
        # Generate unique diagnosis ID
        diagnosis_id = f"DIAG-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Extract key information from analysis
        status = analysis_results.get('status', 'UNCERTAIN')
        confidence = analysis_results.get('confidence', 0.5)
        
        # Determine severity
        severity = self._determine_severity(analysis_results)
        
        # Extract failure indicators
        failure_indicators = self._extract_failure_indicators(analysis_results)
        
        # Identify root causes
        root_causes = self._identify_root_causes(analysis_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            status, severity, root_causes, analysis_results
        )
        
        # Create summary
        summary = self._create_summary(
            status, severity, failure_indicators, root_causes
        )
        
        # Collect supporting evidence
        supporting_evidence = self._collect_evidence(analysis_results)
        
        # Extract S3 references
        s3_references = self._extract_s3_references(analysis_results)
        
        diagnosis = DiagnosisResult(
            diagnosis_id=diagnosis_id,
            timestamp=datetime.utcnow().isoformat(),
            status=status,
            confidence=confidence,
            severity=severity,
            summary=summary,
            failure_indicators=failure_indicators,
            root_causes=root_causes,
            recommendations=recommendations,
            supporting_evidence=supporting_evidence,
            s3_references=s3_references
        )
        
        return diagnosis
    
    def _determine_severity(self, analysis_results: Dict[str, Any]) -> str:
        """Determine severity level from analysis results"""
        patterns = analysis_results.get('patterns', {})
        summary = analysis_results.get('summary', {})
        
        critical_patterns = patterns.get('critical', 0)
        error_count = summary.get('error_count', 0)
        critical_events = len(summary.get('critical_events', []))
        
        if critical_patterns > 0 or critical_events > 0:
            return 'CRITICAL'
        elif error_count > 50:
            return 'HIGH'
        elif error_count > 20 or patterns.get('warnings', 0) > 50:
            return 'MEDIUM'
        elif error_count > 0 or patterns.get('warnings', 0) > 0:
            return 'LOW'
        else:
            return 'NONE'
    
    def _extract_failure_indicators(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract failure indicators from analysis results"""
        indicators = []
        
        # From patterns
        patterns = analysis_results.get('patterns', {})
        pattern_details = patterns.get('details', [])
        
        for pattern in pattern_details:
            if pattern.get('severity') == 'CRITICAL':
                indicators.append(pattern.get('description', 'Unknown critical issue'))
        
        # From summary
        summary = analysis_results.get('summary', {})
        critical_events = summary.get('critical_events', [])
        
        for event in critical_events[:5]:  # Limit to 5
            indicators.append(f"Critical event: {event}")
        
        return indicators
    
    def _identify_root_causes(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential root causes from analysis results"""
        root_causes = []
        
        patterns = analysis_results.get('patterns', {})
        pattern_details = patterns.get('details', [])
        
        # Group patterns by type to identify root causes
        pattern_types = {}
        for pattern in pattern_details:
            ptype = pattern.get('type', 'unknown')
            if ptype not in pattern_types:
                pattern_types[ptype] = []
            pattern_types[ptype].append(pattern)
        
        # Analyze pattern groups
        for ptype, plist in pattern_types.items():
            if len(plist) > 0:
                # Calculate aggregate confidence
                avg_confidence = sum(p.get('confidence', 0) for p in plist) / len(plist)
                
                root_cause = {
                    'category': ptype,
                    'description': plist[0].get('description', 'Unknown issue'),
                    'confidence': round(avg_confidence, 2),
                    'occurrence_count': len(plist),
                    'severity': plist[0].get('severity', 'UNKNOWN'),
                    'evidence': [p.get('sample_lines', [])[:2] for p in plist[:3]]  # First 2 lines from first 3 patterns
                }
                root_causes.append(root_cause)
        
        # Sort by severity and confidence
        severity_order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
        root_causes.sort(
            key=lambda x: (severity_order.get(x['severity'], 3), -x['confidence'])
        )
        
        return root_causes[:10]  # Limit to top 10
    
    def _generate_recommendations(
        self,
        status: str,
        severity: str,
        root_causes: List[Dict[str, Any]],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Priority recommendations based on severity
        if severity == 'CRITICAL':
            recommendations.append({
                'priority': 'URGENT',
                'action': 'Immediate Investigation Required',
                'description': 'Critical system failures detected. Stop operations and investigate immediately.',
                'estimated_time': 'Immediate'
            })
        
        # Recommendations based on root causes
        for cause in root_causes[:5]:  # Top 5 causes
            category = cause['category']
            
            if category == 'connection_timeout':
                recommendations.append({
                    'priority': 'HIGH',
                    'action': 'Check Network and USB Connections',
                    'description': 'Verify all physical connections, network cables, and USB ports. Test connectivity.',
                    'estimated_time': '15-30 minutes'
                })
            elif category == 'memory_issues':
                recommendations.append({
                    'priority': 'HIGH',
                    'action': 'Monitor System Resources',
                    'description': 'Check available memory, close unnecessary applications, consider system restart.',
                    'estimated_time': '10-20 minutes'
                })
            elif category == 'disk_issues':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'action': 'Check Disk Space',
                    'description': 'Verify available disk space, clean up temporary files, check disk health.',
                    'estimated_time': '20-30 minutes'
                })
            elif category == 'service_failures':
                recommendations.append({
                    'priority': 'HIGH',
                    'action': 'Restart Services',
                    'description': 'Restart affected services or perform system reboot. Check service logs.',
                    'estimated_time': '10-15 minutes'
                })
            elif category == 'performance_degradation':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'action': 'Performance Optimization',
                    'description': 'Monitor system performance, check for resource-intensive processes, optimize settings.',
                    'estimated_time': '30-60 minutes'
                })
            elif category == 'driver_issues':
                recommendations.append({
                    'priority': 'MEDIUM',
                    'action': 'Update Drivers',
                    'description': 'Check for driver updates, verify driver compatibility, reinstall if necessary.',
                    'estimated_time': '30-45 minutes'
                })
        
        # General recommendations based on status
        if status == 'PASS':
            recommendations.append({
                'priority': 'LOW',
                'action': 'Continue Monitoring',
                'description': 'System appears healthy. Continue normal operations with routine monitoring.',
                'estimated_time': 'Ongoing'
            })
        elif status == 'UNCERTAIN':
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Enhanced Monitoring',
                'description': 'Some issues detected. Increase monitoring frequency and watch for pattern changes.',
                'estimated_time': 'Ongoing'
            })
        
        # Remove duplicates and limit
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = rec['action']
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:8]  # Limit to 8 recommendations
    
    def _create_summary(
        self,
        status: str,
        severity: str,
        failure_indicators: List[str],
        root_causes: List[Dict[str, Any]]
    ) -> str:
        """Create human-readable summary"""
        summary_parts = []
        
        # Status summary
        if status == 'FAIL':
            summary_parts.append("DIAGNOSIS: System failure detected.")
        elif status == 'UNCERTAIN':
            summary_parts.append("DIAGNOSIS: Potential issues detected requiring investigation.")
        else:
            summary_parts.append("DIAGNOSIS: System appears to be operating normally.")
        
        # Severity
        summary_parts.append(f"Severity: {severity}.")
        
        # Failure indicators
        if failure_indicators:
            summary_parts.append(f"Detected {len(failure_indicators)} failure indicator(s).")
        
        # Root causes
        if root_causes:
            top_causes = [rc['category'].replace('_', ' ').title() for rc in root_causes[:3]]
            summary_parts.append(f"Primary concerns: {', '.join(top_causes)}.")
        
        return " ".join(summary_parts)
    
    def _collect_evidence(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Collect supporting evidence from analysis"""
        evidence = {
            'log_statistics': {},
            'pattern_summary': {},
            'critical_events': []
        }
        
        # Log statistics
        summary = analysis_results.get('summary', {})
        evidence['log_statistics'] = {
            'total_lines': summary.get('total_lines', 0),
            'error_count': summary.get('error_count', 0),
            'warning_count': summary.get('warning_count', 0),
            'timestamp_range': summary.get('timestamp_range')
        }
        
        # Pattern summary
        patterns = analysis_results.get('patterns', {})
        evidence['pattern_summary'] = {
            'total_patterns': patterns.get('total', 0),
            'critical_patterns': patterns.get('critical', 0),
            'warning_patterns': patterns.get('warnings', 0)
        }
        
        # Critical events
        evidence['critical_events'] = summary.get('critical_events', [])[:10]
        
        return evidence
    
    def _extract_s3_references(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract S3 references from analysis results"""
        references = []
        
        # From main result
        if 's3_uri' in analysis_results:
            references.append(analysis_results['s3_uri'])
        
        # From summary
        summary = analysis_results.get('summary', {})
        if 's3_uri' in summary:
            references.append(summary['s3_uri'])
        
        # From comparison results
        if 'test_file' in analysis_results:
            test_file = analysis_results['test_file']
            if 's3_key' in test_file:
                references.append(f"Test: {test_file['s3_key']}")
        
        if 'baseline_file' in analysis_results:
            baseline_file = analysis_results['baseline_file']
            if 's3_key' in baseline_file:
                references.append(f"Baseline: {baseline_file['s3_key']}")
        
        return list(set(references))  # Remove duplicates
    
    def save_diagnosis_to_s3(
        self,
        diagnosis: DiagnosisResult,
        session_id: str
    ) -> str:
        """
        Save diagnosis result to S3 for audit trail.
        
        Args:
            diagnosis: DiagnosisResult object
            session_id: Session identifier
        
        Returns:
            S3 URI of saved diagnosis
        """
        try:
            storage_manager = get_storage_manager()
            
            # Convert diagnosis to JSON
            diagnosis_json = json.dumps(asdict(diagnosis), indent=2)
            
            # Generate S3 key
            s3_key = f"sessions/{session_id}/analysis/diagnosis_{diagnosis.diagnosis_id}.json"
            
            # Save to S3
            storage_manager.s3_client.put_object(
                Bucket=storage_manager.bucket_name,
                Key=s3_key,
                Body=diagnosis_json.encode('utf-8'),
                ContentType='application/json',
                ServerSideEncryption='AES256',
                Metadata={
                    'diagnosis-id': diagnosis.diagnosis_id,
                    'session-id': session_id,
                    'status': diagnosis.status,
                    'severity': diagnosis.severity,
                    'timestamp': diagnosis.timestamp
                }
            )
            
            s3_uri = f"s3://{storage_manager.bucket_name}/{s3_key}"
            logger.info(f"Saved diagnosis to {s3_uri}")
            
            return s3_uri
            
        except Exception as e:
            logger.error(f"Error saving diagnosis to S3: {str(e)}")
            raise


# Global diagnosis generator instance
_diagnosis_generator = None


def get_diagnosis_generator() -> DiagnosisGenerator:
    """Get or create global diagnosis generator instance"""
    global _diagnosis_generator
    if _diagnosis_generator is None:
        _diagnosis_generator = DiagnosisGenerator()
    return _diagnosis_generator


@tool(
    name="generate_diagnosis",
    description="Generate comprehensive diagnosis from S3 log analysis results with confidence scoring, root cause analysis, and actionable recommendations."
)
def generate_diagnosis(
    s3_uri: str = "",
    s3_key: str = "",
    session_id: str = "",
    baseline_s3_uri: str = "",
    baseline_s3_key: str = "",
    additional_context: str = ""
) -> Dict[str, Any]:
    """
    Generate comprehensive diagnosis from S3-stored log analysis.
    
    Args:
        s3_uri: S3 URI of log file to diagnose - provide either this or s3_key
        s3_key: S3 key of log file to diagnose - provide either this or s3_uri
        session_id: Session identifier for organizing results
        baseline_s3_uri: Optional baseline S3 URI for comparison
        baseline_s3_key: Optional baseline S3 key for comparison
        additional_context: Additional context to inform diagnosis
    
    Returns:
        Dictionary containing comprehensive diagnosis with recommendations
    """
    try:
        # Parse S3 URI if provided
        if s3_uri:
            if not s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format. Must start with s3://'}
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            s3_key = parts[1]
        
        if not s3_key:
            return {'error': 'Either s3_uri or s3_key must be provided'}
        
        if not session_id:
            # Generate session ID from S3 key if not provided
            session_id = s3_key.split('/')[1] if '/' in s3_key else 'default'
        
        # Analyze log file
        analyzer = get_s3_analyzer()
        
        if baseline_s3_uri or baseline_s3_key:
            # Parse baseline URI if provided
            if baseline_s3_uri:
                parts = baseline_s3_uri.replace('s3://', '').split('/', 1)
                baseline_s3_key = parts[1] if len(parts) == 2 else baseline_s3_key
            
            # Compare with baseline
            analysis_results = analyzer.compare_s3_logs(s3_key, baseline_s3_key)
        else:
            # Standalone analysis
            analysis_results = analyzer.analyze_with_streaming(s3_key)
        
        # Generate diagnosis
        generator = get_diagnosis_generator()
        diagnosis = generator.generate_diagnosis(
            analysis_results,
            session_id,
            additional_context
        )
        
        # Save diagnosis to S3
        try:
            diagnosis_s3_uri = generator.save_diagnosis_to_s3(diagnosis, session_id)
            diagnosis_saved = True
        except Exception as e:
            logger.warning(f"Could not save diagnosis to S3: {e}")
            diagnosis_s3_uri = None
            diagnosis_saved = False
        
        # Convert to dictionary
        result = asdict(diagnosis)
        result['success'] = True
        result['diagnosis_saved_to_s3'] = diagnosis_saved
        if diagnosis_s3_uri:
            result['diagnosis_s3_uri'] = diagnosis_s3_uri
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_diagnosis: {str(e)}")
        return {'error': f'Diagnosis generation failed: {str(e)}'}


@tool(
    name="get_diagnosis_from_s3",
    description="Retrieve a previously generated diagnosis from S3 storage by diagnosis ID or S3 URI."
)
def get_diagnosis_from_s3(
    diagnosis_id: str = "",
    session_id: str = "",
    diagnosis_s3_uri: str = ""
) -> Dict[str, Any]:
    """
    Retrieve diagnosis from S3 storage.
    
    Args:
        diagnosis_id: Diagnosis ID to retrieve
        session_id: Session ID (required if using diagnosis_id)
        diagnosis_s3_uri: Direct S3 URI to diagnosis file
    
    Returns:
        Dictionary containing diagnosis information
    """
    try:
        storage_manager = get_storage_manager()
        
        # Determine S3 key
        if diagnosis_s3_uri:
            if not diagnosis_s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format'}
            parts = diagnosis_s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            s3_key = parts[1]
        elif diagnosis_id and session_id:
            s3_key = f"sessions/{session_id}/analysis/diagnosis_{diagnosis_id}.json"
        else:
            return {'error': 'Either diagnosis_s3_uri or both diagnosis_id and session_id must be provided'}
        
        # Retrieve from S3
        content = storage_manager.stream_file_content(s3_key)
        diagnosis_data = json.loads(content)
        
        diagnosis_data['success'] = True
        diagnosis_data['retrieved_from'] = f"s3://{storage_manager.bucket_name}/{s3_key}"
        
        return diagnosis_data
        
    except Exception as e:
        logger.error(f"Error in get_diagnosis_from_s3: {str(e)}")
        return {'error': f'Failed to retrieve diagnosis: {str(e)}'}


# List of diagnosis tools
DIAGNOSIS_TOOLS = [
    generate_diagnosis,
    get_diagnosis_from_s3
]
