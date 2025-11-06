"""
Diagnosis Generation Tools for Instrument Diagnosis Assistant

These tools generate intelligent diagnoses using Amazon Nova Pro, providing
pass/fail determinations, confidence scoring, and actionable recommendations.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from strands import tool

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisResult:
    """Complete diagnosis result with recommendations"""
    diagnosis: str  # "PASS", "FAIL", "UNCERTAIN"
    confidence_score: float  # 0.0 to 1.0
    severity_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    primary_issues: List[str]
    root_cause_analysis: str
    recommendations: List[Dict[str, Any]]
    technical_details: Dict[str, Any]
    timestamp: str


@dataclass
class RecommendationItem:
    """Individual recommendation with priority and details"""
    priority: str  # "IMMEDIATE", "HIGH", "MEDIUM", "LOW"
    category: str  # "HARDWARE", "SOFTWARE", "CONFIGURATION", "MAINTENANCE"
    action: str
    description: str
    estimated_time: str
    required_expertise: str
    risk_if_ignored: str


class DiagnosisEngine:
    """Core diagnosis generation engine"""
    
    def __init__(self):
        # Diagnosis criteria and thresholds
        self.diagnosis_criteria = {
            'pass_thresholds': {
                'max_critical_issues': 0,
                'max_warning_issues': 2,
                'min_confidence': 0.7
            },
            'fail_thresholds': {
                'critical_issues': 1,
                'warning_issues': 5,
                'risk_score': 70
            },
            'uncertain_conditions': {
                'low_confidence': 0.5,
                'mixed_signals': True,
                'insufficient_data': True
            }
        }
        
        # Issue severity mapping
        self.severity_mapping = {
            'connection_timeout': 'CRITICAL',
            'service_failures': 'CRITICAL', 
            'memory_issues': 'HIGH',
            'disk_issues': 'MEDIUM',
            'performance_degradation': 'MEDIUM',
            'driver_issues': 'MEDIUM'
        }
        
        # Recommendation templates
        self.recommendation_templates = {
            'connection_timeout': {
                'priority': 'IMMEDIATE',
                'category': 'HARDWARE',
                'action': 'Check and replace connection cables',
                'description': 'Connection timeouts indicate hardware connectivity issues',
                'estimated_time': '15-30 minutes',
                'required_expertise': 'Technician Level 1',
                'risk_if_ignored': 'System will remain non-functional'
            },
            'service_failures': {
                'priority': 'IMMEDIATE',
                'category': 'SOFTWARE',
                'action': 'Restart failed services and check dependencies',
                'description': 'Critical services have failed to start or crashed',
                'estimated_time': '10-20 minutes',
                'required_expertise': 'Technician Level 2',
                'risk_if_ignored': 'Complete system failure'
            },
            'memory_issues': {
                'priority': 'HIGH',
                'category': 'HARDWARE',
                'action': 'Monitor memory usage and restart system if needed',
                'description': 'Memory leaks or insufficient memory detected',
                'estimated_time': '5-15 minutes',
                'required_expertise': 'Technician Level 1',
                'risk_if_ignored': 'System instability and crashes'
            },
            'disk_issues': {
                'priority': 'MEDIUM',
                'category': 'MAINTENANCE',
                'action': 'Free up disk space and check disk health',
                'description': 'Disk space or write errors detected',
                'estimated_time': '20-45 minutes',
                'required_expertise': 'Technician Level 1',
                'risk_if_ignored': 'Data loss and system failures'
            },
            'performance_degradation': {
                'priority': 'MEDIUM',
                'category': 'CONFIGURATION',
                'action': 'Optimize system settings and check background processes',
                'description': 'System performance is below optimal levels',
                'estimated_time': '30-60 minutes',
                'required_expertise': 'Technician Level 2',
                'risk_if_ignored': 'Reduced efficiency and potential failures'
            },
            'driver_issues': {
                'priority': 'HIGH',
                'category': 'SOFTWARE',
                'action': 'Update drivers to latest compatible versions',
                'description': 'Outdated or incompatible drivers detected',
                'estimated_time': '15-30 minutes',
                'required_expertise': 'Technician Level 2',
                'risk_if_ignored': 'Hardware compatibility issues'
            }
        }
    
    def calculate_confidence_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on analysis quality and consistency"""
        base_confidence = 0.5
        
        # Boost confidence for clear patterns
        if 'analysis_summary' in analysis_data:
            summary = analysis_data['analysis_summary']
            critical_count = summary.get('critical_patterns', 0)
            warning_count = summary.get('warning_patterns', 0)
            
            # Clear failure indicators boost confidence
            if critical_count > 0:
                base_confidence += 0.3
            elif warning_count > 3:
                base_confidence += 0.2
            elif warning_count == 0:
                base_confidence += 0.25  # Clear pass also boosts confidence
        
        # Boost for consistent patterns across chunks
        if 'chunk_details' in analysis_data:
            chunks = analysis_data['chunk_details']
            if len(chunks) > 1:
                # Check consistency across chunks
                critical_counts = [chunk.get('critical_patterns', 0) for chunk in chunks]
                if all(count > 0 for count in critical_counts) or all(count == 0 for count in critical_counts):
                    base_confidence += 0.1  # Consistent pattern across chunks
        
        # Reduce confidence for edge cases
        if 'comparison_result' in analysis_data:
            comp = analysis_data['comparison_result']
            if comp.get('status') == 'UNCERTAIN':
                base_confidence -= 0.2
        
        return min(1.0, max(0.1, base_confidence))
    
    def determine_diagnosis(self, analysis_data: Dict[str, Any]) -> str:
        """Determine primary diagnosis based on analysis data"""
        # Extract key metrics
        critical_issues = 0
        warning_issues = 0
        risk_score = 0
        
        if 'analysis_summary' in analysis_data:
            summary = analysis_data['analysis_summary']
            critical_issues = summary.get('critical_patterns', 0)
            warning_issues = summary.get('warning_patterns', 0)
        
        if 'summary' in analysis_data:
            summary = analysis_data['summary']
            risk_score = summary.get('risk_score', 0)
        
        # Apply diagnosis criteria
        if critical_issues >= self.diagnosis_criteria['fail_thresholds']['critical_issues']:
            return "FAIL"
        elif risk_score >= self.diagnosis_criteria['fail_thresholds']['risk_score']:
            return "FAIL"
        elif warning_issues >= self.diagnosis_criteria['fail_thresholds']['warning_issues']:
            return "FAIL"
        elif critical_issues == 0 and warning_issues <= self.diagnosis_criteria['pass_thresholds']['max_warning_issues']:
            return "PASS"
        else:
            return "UNCERTAIN"
    
    def determine_severity_level(self, analysis_data: Dict[str, Any]) -> str:
        """Determine overall severity level"""
        critical_issues = 0
        warning_issues = 0
        risk_score = 0
        
        if 'analysis_summary' in analysis_data:
            summary = analysis_data['analysis_summary']
            critical_issues = summary.get('critical_patterns', 0)
            warning_issues = summary.get('warning_patterns', 0)
        
        if 'summary' in analysis_data:
            summary = analysis_data['summary']
            risk_score = summary.get('risk_score', 0)
        
        if critical_issues > 2 or risk_score > 80:
            return "CRITICAL"
        elif critical_issues > 0 or risk_score > 50:
            return "HIGH"
        elif warning_issues > 3 or risk_score > 25:
            return "MEDIUM"
        else:
            return "LOW"
    
    def extract_primary_issues(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract primary issues from analysis data"""
        issues = []
        
        # From top issues
        if 'top_issues' in analysis_data:
            for issue in analysis_data['top_issues'][:5]:  # Top 5 issues
                issues.append(f"{issue['severity']}: {issue['description']}")
        
        # From categorized indicators
        if 'categorized_indicators' in analysis_data:
            categories = analysis_data['categorized_indicators']
            for category, indicators in categories.items():
                if indicators and category in ['critical_failures', 'connection_problems']:
                    for indicator in indicators[:2]:  # Top 2 per critical category
                        issues.append(f"{indicator['description']}")
        
        return issues[:10]  # Limit to top 10 issues
    
    def generate_recommendations(self, analysis_data: Dict[str, Any], diagnosis: str) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Get pattern types from analysis
        pattern_types = set()
        if 'analysis_summary' in analysis_data:
            pattern_types.update(analysis_data['analysis_summary'].get('pattern_types', []))
        
        if 'top_issues' in analysis_data:
            for issue in analysis_data['top_issues']:
                pattern_types.add(issue.get('type', ''))
        
        # Generate specific recommendations for each pattern type
        for pattern_type in pattern_types:
            if pattern_type in self.recommendation_templates:
                template = self.recommendation_templates[pattern_type]
                recommendations.append({
                    'id': f"rec_{pattern_type}",
                    'priority': template['priority'],
                    'category': template['category'],
                    'action': template['action'],
                    'description': template['description'],
                    'estimated_time': template['estimated_time'],
                    'required_expertise': template['required_expertise'],
                    'risk_if_ignored': template['risk_if_ignored']
                })
        
        # Add general recommendations based on diagnosis
        if diagnosis == "FAIL":
            recommendations.append({
                'id': 'rec_general_fail',
                'priority': 'IMMEDIATE',
                'category': 'GENERAL',
                'action': 'Do not use instrument until issues are resolved',
                'description': 'Critical failures detected - instrument is not safe to operate',
                'estimated_time': 'Until repairs complete',
                'required_expertise': 'Qualified Technician',
                'risk_if_ignored': 'Equipment damage, safety hazards, invalid results'
            })
        elif diagnosis == "UNCERTAIN":
            recommendations.append({
                'id': 'rec_general_uncertain',
                'priority': 'HIGH',
                'category': 'GENERAL',
                'action': 'Perform additional diagnostics and monitoring',
                'description': 'Unclear system status requires further investigation',
                'estimated_time': '30-60 minutes',
                'required_expertise': 'Technician Level 2',
                'risk_if_ignored': 'Potential undetected failures'
            })
        elif diagnosis == "PASS":
            recommendations.append({
                'id': 'rec_general_pass',
                'priority': 'LOW',
                'category': 'MAINTENANCE',
                'action': 'Continue normal operation with routine monitoring',
                'description': 'System appears healthy - maintain regular maintenance schedule',
                'estimated_time': 'Ongoing',
                'required_expertise': 'Operator',
                'risk_if_ignored': 'Minimal - continue monitoring'
            })
        
        # Sort by priority
        priority_order = {'IMMEDIATE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def generate_root_cause_analysis(self, analysis_data: Dict[str, Any], diagnosis: str) -> str:
        """Generate root cause analysis narrative"""
        if diagnosis == "PASS":
            return ("System analysis indicates normal operation. All critical systems are functioning "
                   "within expected parameters. Minor warnings, if any, are within acceptable limits "
                   "and do not indicate systemic issues.")
        
        # Analyze patterns for root cause
        root_causes = []
        
        if 'top_issues' in analysis_data:
            critical_issues = [issue for issue in analysis_data['top_issues'] 
                             if issue.get('severity') == 'CRITICAL']
            
            if any('connection' in issue.get('type', '') for issue in critical_issues):
                root_causes.append("Hardware connectivity failures are preventing proper communication")
            
            if any('service' in issue.get('type', '') for issue in critical_issues):
                root_causes.append("Critical software services are failing to start or maintain operation")
            
            if any('memory' in issue.get('type', '') for issue in critical_issues):
                root_causes.append("Memory management issues are causing system instability")
        
        if not root_causes:
            if diagnosis == "FAIL":
                root_causes.append("Multiple system degradations have accumulated to cause overall failure")
            else:
                root_causes.append("System status is unclear due to mixed or insufficient diagnostic signals")
        
        return ". ".join(root_causes) + "."


# Initialize global diagnosis engine
_diagnosis_engine = DiagnosisEngine()


@tool(
    name="generate_diagnosis",
    description="Generate comprehensive pass/fail diagnosis with confidence scoring and recommendations using Nova Pro intelligence"
)
def generate_diagnosis(
    analysis_data: Dict[str, Any],
    context_info: Optional[Dict[str, Any]] = None,
    diagnosis_mode: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Generate intelligent diagnosis based on log analysis data using Nova Pro reasoning.
    
    Args:
        analysis_data: Results from log analysis tools (analyze_logs, process_large_files, etc.)
        context_info: Additional context about the instrument or test conditions
        diagnosis_mode: Mode of diagnosis ("comprehensive", "quick", "detailed")
    
    Returns:
        Dictionary containing complete diagnosis with recommendations and technical details
    """
    try:
        if not analysis_data or 'error' in analysis_data:
            return {"error": "Invalid or missing analysis data for diagnosis generation"}
        
        # Generate core diagnosis components
        diagnosis = _diagnosis_engine.determine_diagnosis(analysis_data)
        confidence_score = _diagnosis_engine.calculate_confidence_score(analysis_data)
        severity_level = _diagnosis_engine.determine_severity_level(analysis_data)
        primary_issues = _diagnosis_engine.extract_primary_issues(analysis_data)
        root_cause_analysis = _diagnosis_engine.generate_root_cause_analysis(analysis_data, diagnosis)
        recommendations = _diagnosis_engine.generate_recommendations(analysis_data, diagnosis)
        
        # Compile technical details
        technical_details = {
            'analysis_source': analysis_data.get('file_info', {}),
            'pattern_analysis': analysis_data.get('analysis_summary', {}),
            'risk_assessment': analysis_data.get('summary', {}),
            'processing_stats': analysis_data.get('processing_stats', {}),
            'diagnosis_criteria_applied': _diagnosis_engine.diagnosis_criteria,
            'confidence_factors': {
                'base_analysis_quality': 'High' if confidence_score > 0.7 else 'Medium' if confidence_score > 0.5 else 'Low',
                'pattern_consistency': 'Good' if 'chunk_details' in analysis_data else 'Limited',
                'data_completeness': 'Complete' if analysis_data.get('total_patterns', 0) > 0 else 'Partial'
            }
        }
        
        # Add context information if provided
        if context_info:
            technical_details['context'] = context_info
        
        # Create final diagnosis result
        result = DiagnosisResult(
            diagnosis=diagnosis,
            confidence_score=round(confidence_score, 3),
            severity_level=severity_level,
            primary_issues=primary_issues,
            root_cause_analysis=root_cause_analysis,
            recommendations=recommendations,
            technical_details=technical_details,
            timestamp=datetime.now().isoformat()
        )
        
        return asdict(result)
        
    except Exception as e:
        logger.error(f"Error in generate_diagnosis: {str(e)}")
        return {"error": f"Diagnosis generation failed: {str(e)}"}


@tool(
    name="calculate_confidence_score",
    description="Calculate confidence score for diagnosis based on analysis quality and data consistency"
)
def calculate_confidence_score(
    analysis_results: List[Dict[str, Any]],
    cross_validation: bool = True
) -> Dict[str, Any]:
    """
    Calculate overall confidence score by analyzing multiple analysis results.
    
    Args:
        analysis_results: List of analysis results from different tools or sources
        cross_validation: Whether to perform cross-validation between results
    
    Returns:
        Dictionary containing confidence metrics and validation results
    """
    try:
        if not analysis_results:
            return {"error": "No analysis results provided for confidence calculation"}
        
        individual_scores = []
        consistency_metrics = []
        
        # Calculate individual confidence scores
        for result in analysis_results:
            if 'error' not in result:
                score = _diagnosis_engine.calculate_confidence_score(result)
                individual_scores.append(score)
        
        if not individual_scores:
            return {"error": "No valid analysis results for confidence calculation"}
        
        # Cross-validation if multiple results
        if cross_validation and len(analysis_results) > 1:
            # Check consistency of diagnoses
            diagnoses = []
            for result in analysis_results:
                if 'status' in result:
                    diagnoses.append(result['status'])
                elif 'diagnosis' in result:
                    diagnoses.append(result['diagnosis'])
            
            # Calculate consistency score
            if diagnoses:
                most_common = max(set(diagnoses), key=diagnoses.count)
                consistency_ratio = diagnoses.count(most_common) / len(diagnoses)
                consistency_metrics.append({
                    'metric': 'diagnosis_consistency',
                    'score': consistency_ratio,
                    'description': f"{consistency_ratio:.1%} of analyses agree on diagnosis"
                })
        
        # Calculate overall confidence
        base_confidence = sum(individual_scores) / len(individual_scores)
        
        # Apply consistency adjustments
        consistency_adjustment = 0
        if consistency_metrics:
            avg_consistency = sum(m['score'] for m in consistency_metrics) / len(consistency_metrics)
            if avg_consistency > 0.8:
                consistency_adjustment = 0.1  # Boost for high consistency
            elif avg_consistency < 0.5:
                consistency_adjustment = -0.2  # Penalty for low consistency
        
        final_confidence = min(1.0, max(0.1, base_confidence + consistency_adjustment))
        
        result = {
            'overall_confidence': round(final_confidence, 3),
            'confidence_level': 'HIGH' if final_confidence > 0.8 else 'MEDIUM' if final_confidence > 0.6 else 'LOW',
            'individual_scores': [round(score, 3) for score in individual_scores],
            'consistency_metrics': consistency_metrics,
            'confidence_factors': {
                'number_of_analyses': len(analysis_results),
                'average_individual_confidence': round(base_confidence, 3),
                'consistency_adjustment': round(consistency_adjustment, 3),
                'cross_validation_performed': cross_validation and len(analysis_results) > 1
            },
            'recommendations': _generate_confidence_recommendations(final_confidence, consistency_metrics)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in calculate_confidence_score: {str(e)}")
        return {"error": f"Confidence calculation failed: {str(e)}"}


def _generate_confidence_recommendations(confidence: float, consistency_metrics: List[Dict]) -> List[str]:
    """Generate recommendations based on confidence analysis"""
    recommendations = []
    
    if confidence > 0.8:
        recommendations.append("High confidence diagnosis - results are reliable for decision making")
    elif confidence > 0.6:
        recommendations.append("Medium confidence - consider additional validation if critical decisions depend on results")
    else:
        recommendations.append("Low confidence - perform additional diagnostics before making critical decisions")
    
    if consistency_metrics:
        avg_consistency = sum(m['score'] for m in consistency_metrics) / len(consistency_metrics)
        if avg_consistency < 0.7:
            recommendations.append("Inconsistent results detected - review analysis parameters and data quality")
    
    return recommendations


@tool(
    name="generate_recommendations",
    description="Generate prioritized, actionable recommendations based on diagnosis results"
)
def generate_recommendations(
    diagnosis_result: Dict[str, Any],
    user_expertise_level: str = "technician_level_1",
    available_resources: List[str] = None
) -> Dict[str, Any]:
    """
    Generate detailed, prioritized recommendations tailored to user expertise and available resources.
    
    Args:
        diagnosis_result: Result from generate_diagnosis tool
        user_expertise_level: User's technical expertise ("operator", "technician_level_1", "technician_level_2", "engineer")
        available_resources: List of available resources/tools
    
    Returns:
        Dictionary containing prioritized recommendations with implementation details
    """
    try:
        if 'error' in diagnosis_result:
            return {"error": "Invalid diagnosis result provided"}
        
        base_recommendations = diagnosis_result.get('recommendations', [])
        diagnosis = diagnosis_result.get('diagnosis', 'UNCERTAIN')
        severity = diagnosis_result.get('severity_level', 'MEDIUM')
        
        # Filter recommendations based on expertise level
        expertise_mapping = {
            'operator': ['GENERAL', 'MAINTENANCE'],
            'technician_level_1': ['GENERAL', 'MAINTENANCE', 'HARDWARE'],
            'technician_level_2': ['GENERAL', 'MAINTENANCE', 'HARDWARE', 'SOFTWARE', 'CONFIGURATION'],
            'engineer': ['GENERAL', 'MAINTENANCE', 'HARDWARE', 'SOFTWARE', 'CONFIGURATION', 'ADVANCED']
        }
        
        allowed_categories = expertise_mapping.get(user_expertise_level, ['GENERAL'])
        filtered_recommendations = [
            rec for rec in base_recommendations 
            if rec.get('category') in allowed_categories
        ]
        
        # Add expertise-specific guidance
        expertise_guidance = []
        if user_expertise_level == 'operator':
            expertise_guidance.append("Contact qualified technician for hardware/software issues")
        elif user_expertise_level == 'technician_level_1':
            expertise_guidance.append("Escalate software configuration issues to Level 2 technician")
        
        # Generate implementation timeline
        immediate_actions = [rec for rec in filtered_recommendations if rec.get('priority') == 'IMMEDIATE']
        high_priority = [rec for rec in filtered_recommendations if rec.get('priority') == 'HIGH']
        medium_priority = [rec for rec in filtered_recommendations if rec.get('priority') == 'MEDIUM']
        low_priority = [rec for rec in filtered_recommendations if rec.get('priority') == 'LOW']
        
        timeline = {
            'immediate_actions': {
                'timeframe': 'Next 15 minutes',
                'actions': immediate_actions,
                'critical': True
            },
            'short_term': {
                'timeframe': 'Next 1-2 hours', 
                'actions': high_priority,
                'critical': diagnosis == 'FAIL'
            },
            'medium_term': {
                'timeframe': 'Next 24 hours',
                'actions': medium_priority,
                'critical': False
            },
            'long_term': {
                'timeframe': 'Next week',
                'actions': low_priority,
                'critical': False
            }
        }
        
        result = {
            'summary': {
                'total_recommendations': len(filtered_recommendations),
                'immediate_actions_required': len(immediate_actions),
                'user_expertise_level': user_expertise_level,
                'diagnosis_severity': severity,
                'system_status': diagnosis
            },
            'prioritized_recommendations': filtered_recommendations,
            'implementation_timeline': timeline,
            'expertise_guidance': expertise_guidance,
            'safety_notes': _generate_safety_notes(diagnosis, severity),
            'escalation_criteria': _generate_escalation_criteria(diagnosis, severity, user_expertise_level)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_recommendations: {str(e)}")
        return {"error": f"Recommendation generation failed: {str(e)}"}


def _generate_safety_notes(diagnosis: str, severity: str) -> List[str]:
    """Generate safety notes based on diagnosis and severity"""
    safety_notes = []
    
    if diagnosis == "FAIL":
        safety_notes.append("⚠️ SAFETY WARNING: Do not operate instrument until all critical issues are resolved")
        safety_notes.append("Ensure proper safety protocols are followed during repair procedures")
    
    if severity in ["CRITICAL", "HIGH"]:
        safety_notes.append("Use appropriate personal protective equipment during maintenance")
        safety_notes.append("Follow lockout/tagout procedures if working on electrical components")
    
    safety_notes.append("Document all maintenance actions performed")
    safety_notes.append("Verify system functionality after completing repairs")
    
    return safety_notes


def _generate_escalation_criteria(diagnosis: str, severity: str, expertise_level: str) -> Dict[str, Any]:
    """Generate escalation criteria based on context"""
    criteria = {
        'escalate_immediately': [],
        'escalate_if_no_improvement': [],
        'escalate_for_verification': []
    }
    
    if diagnosis == "FAIL" and expertise_level in ['operator', 'technician_level_1']:
        criteria['escalate_immediately'].append("Critical system failures detected")
    
    if severity == "CRITICAL":
        criteria['escalate_immediately'].append("Critical severity issues require expert attention")
    
    criteria['escalate_if_no_improvement'].append("No improvement after following recommendations for 2 hours")
    criteria['escalate_for_verification'].append("System status remains uncertain after troubleshooting")
    
    return criteria


# List of available diagnosis tools
DIAGNOSIS_TOOLS = [
    generate_diagnosis,
    calculate_confidence_score,
    generate_recommendations
]