"""
Consistency Management Tools for Instrument Diagnosis Assistant

These tools implement consistent component identification across sources,
cross-reference validation, conflict resolution, and comprehensive diagnostic reporting.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
from strands import tool

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyViolation:
    """Represents a consistency violation between sources"""
    violation_type: str
    description: str
    affected_sources: List[str]
    conflicting_values: Dict[str, Any]
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    resolution_suggestion: str
    confidence: float


@dataclass
class CrossReference:
    """Represents a cross-reference between different data sources"""
    source_type: str
    target_type: str
    source_item: str
    target_item: str
    reference_strength: float
    validation_status: str  # "VALID", "INVALID", "UNCERTAIN"
    validation_details: Dict[str, Any]


@dataclass
class ConsistencyReport:
    """Comprehensive consistency analysis report"""
    overall_consistency_score: float
    consistency_level: str  # "HIGH", "MEDIUM", "LOW"
    violations_found: List[ConsistencyViolation]
    cross_references: List[CrossReference]
    resolution_recommendations: List[Dict[str, Any]]
    data_quality_metrics: Dict[str, float]
    report_metadata: Dict[str, Any]


class ConsistencyManager:
    """Core consistency management and validation engine"""
    
    def __init__(self):
        # Consistency rules and thresholds
        self.consistency_rules = {
            'component_naming': {
                'max_name_variations': 3,
                'similarity_threshold': 0.8,
                'canonical_name_required': True
            },
            'failure_associations': {
                'max_conflicting_severities': 1,
                'severity_consistency_threshold': 0.7,
                'pattern_overlap_threshold': 0.6
            },
            'cross_reference_validation': {
                'min_reference_strength': 0.5,
                'validation_confidence_threshold': 0.7,
                'max_broken_references': 0.2  # 20% of references can be broken
            }
        }
        
        # Severity mapping for violations
        self.violation_severity_mapping = {
            'component_name_conflict': 'MEDIUM',
            'failure_severity_mismatch': 'HIGH',
            'broken_cross_reference': 'MEDIUM',
            'missing_canonical_name': 'LOW',
            'inconsistent_failure_association': 'HIGH',
            'data_source_mismatch': 'MEDIUM'
        }
        
        # Resolution strategies
        self.resolution_strategies = {
            'component_name_conflict': 'Use highest confidence source for canonical name',
            'failure_severity_mismatch': 'Review failure analysis criteria and re-evaluate',
            'broken_cross_reference': 'Update references or mark as deprecated',
            'missing_canonical_name': 'Generate canonical name from most common variant',
            'inconsistent_failure_association': 'Cross-validate with additional data sources',
            'data_source_mismatch': 'Verify data source integrity and update if necessary'
        }
    
    def validate_component_consistency(self, component_correlations: List[Dict[str, Any]]) -> List[ConsistencyViolation]:
        """Validate consistency of component identification across sources"""
        violations = []
        
        for correlation in component_correlations:
            component_name = correlation.get('component_name', '')
            canonical_name = correlation.get('canonical_name', '')
            source_references = correlation.get('source_references', {})
            confidence_scores = correlation.get('confidence_scores', {})
            
            # Check for component naming violations
            if len(source_references) > 1:
                # Check for excessive name variations
                all_names = []
                for source_refs in source_references.values():
                    all_names.extend(source_refs)
                
                unique_names = set(all_names)
                if len(unique_names) > self.consistency_rules['component_naming']['max_name_variations']:
                    violations.append(ConsistencyViolation(
                        violation_type='component_name_conflict',
                        description=f'Component "{component_name}" has {len(unique_names)} different name variations across sources',
                        affected_sources=list(source_references.keys()),
                        conflicting_values={'name_variations': list(unique_names)},
                        severity=self.violation_severity_mapping['component_name_conflict'],
                        resolution_suggestion=self.resolution_strategies['component_name_conflict'],
                        confidence=0.9
                    ))
                
                # Check for missing canonical name
                if not canonical_name or canonical_name == component_name:
                    violations.append(ConsistencyViolation(
                        violation_type='missing_canonical_name',
                        description=f'Component "{component_name}" lacks a proper canonical name',
                        affected_sources=list(source_references.keys()),
                        conflicting_values={'canonical_name': canonical_name, 'component_name': component_name},
                        severity=self.violation_severity_mapping['missing_canonical_name'],
                        resolution_suggestion=self.resolution_strategies['missing_canonical_name'],
                        confidence=0.8
                    ))
                
                # Check for low confidence scores
                low_confidence_sources = [
                    source for source, confidence in confidence_scores.items()
                    if confidence < self.consistency_rules['component_naming']['similarity_threshold']
                ]
                
                if low_confidence_sources:
                    violations.append(ConsistencyViolation(
                        violation_type='data_source_mismatch',
                        description=f'Low confidence component identification in sources: {", ".join(low_confidence_sources)}',
                        affected_sources=low_confidence_sources,
                        conflicting_values={'low_confidence_scores': {s: confidence_scores[s] for s in low_confidence_sources}},
                        severity=self.violation_severity_mapping['data_source_mismatch'],
                        resolution_suggestion=self.resolution_strategies['data_source_mismatch'],
                        confidence=0.7
                    ))
        
        return violations
    
    def validate_failure_consistency(self, failure_correlations: List[Dict[str, Any]]) -> List[ConsistencyViolation]:
        """Validate consistency of failure pattern associations"""
        violations = []
        
        # Group failures by pattern type
        pattern_groups = defaultdict(list)
        for correlation in failure_correlations:
            pattern_type = correlation.get('pattern_type', 'unknown')
            pattern_groups[pattern_type].append(correlation)
        
        # Check for severity consistency within pattern types
        for pattern_type, correlations in pattern_groups.items():
            if len(correlations) > 1:
                severities = [corr.get('severity', 'MEDIUM') for corr in correlations]
                unique_severities = set(severities)
                
                if len(unique_severities) > self.consistency_rules['failure_associations']['max_conflicting_severities']:
                    violations.append(ConsistencyViolation(
                        violation_type='failure_severity_mismatch',
                        description=f'Pattern type "{pattern_type}" has inconsistent severity levels: {", ".join(unique_severities)}',
                        affected_sources=['failure_analysis'],
                        conflicting_values={'severities': list(unique_severities), 'pattern_type': pattern_type},
                        severity=self.violation_severity_mapping['failure_severity_mismatch'],
                        resolution_suggestion=self.resolution_strategies['failure_severity_mismatch'],
                        confidence=0.8
                    ))
        
        # Check for inconsistent component associations
        component_failure_map = defaultdict(set)
        for correlation in failure_correlations:
            pattern = correlation.get('failure_pattern', '')
            components = correlation.get('associated_components', [])
            for component in components:
                component_failure_map[component].add(pattern)
        
        # Look for components with conflicting failure associations
        for component, patterns in component_failure_map.items():
            if len(patterns) > 3:  # Arbitrary threshold for too many associations
                violations.append(ConsistencyViolation(
                    violation_type='inconsistent_failure_association',
                    description=f'Component "{component}" is associated with {len(patterns)} different failure patterns',
                    affected_sources=['failure_analysis', 'component_correlation'],
                    conflicting_values={'component': component, 'failure_patterns': list(patterns)},
                    severity=self.violation_severity_mapping['inconsistent_failure_association'],
                    resolution_suggestion=self.resolution_strategies['inconsistent_failure_association'],
                    confidence=0.6
                ))
        
        return violations
    
    def validate_cross_references(self, 
                                component_correlations: List[Dict[str, Any]],
                                failure_correlations: List[Dict[str, Any]]) -> Tuple[List[CrossReference], List[ConsistencyViolation]]:
        """Validate cross-references between components and failures"""
        cross_references = []
        violations = []
        
        # Build component-failure reference map
        component_names = set()
        for corr in component_correlations:
            component_names.add(corr.get('canonical_name', corr.get('component_name', '')))
        
        # Check references from failures to components
        for failure_corr in failure_correlations:
            associated_components = failure_corr.get('associated_components', [])
            
            for component in associated_components:
                # Find matching component in correlations
                matching_components = [
                    comp_corr for comp_corr in component_correlations
                    if self._components_match(component, comp_corr)
                ]
                
                if matching_components:
                    # Valid reference
                    best_match = matching_components[0]
                    reference_strength = self._calculate_reference_strength(component, best_match)
                    
                    cross_ref = CrossReference(
                        source_type='failure_correlation',
                        target_type='component_correlation',
                        source_item=failure_corr.get('failure_pattern', ''),
                        target_item=best_match.get('canonical_name', ''),
                        reference_strength=reference_strength,
                        validation_status='VALID' if reference_strength > 0.7 else 'UNCERTAIN',
                        validation_details={
                            'match_confidence': reference_strength,
                            'source_component': component,
                            'target_component': best_match.get('canonical_name', '')
                        }
                    )
                    cross_references.append(cross_ref)
                else:
                    # Broken reference
                    cross_ref = CrossReference(
                        source_type='failure_correlation',
                        target_type='component_correlation',
                        source_item=failure_corr.get('failure_pattern', ''),
                        target_item=component,
                        reference_strength=0.0,
                        validation_status='INVALID',
                        validation_details={
                            'error': 'Component not found in component correlations',
                            'missing_component': component
                        }
                    )
                    cross_references.append(cross_ref)
                    
                    # Add violation for broken reference
                    violations.append(ConsistencyViolation(
                        violation_type='broken_cross_reference',
                        description=f'Failure pattern references unknown component "{component}"',
                        affected_sources=['failure_correlation', 'component_correlation'],
                        conflicting_values={'missing_component': component, 'failure_pattern': failure_corr.get('failure_pattern', '')},
                        severity=self.violation_severity_mapping['broken_cross_reference'],
                        resolution_suggestion=self.resolution_strategies['broken_cross_reference'],
                        confidence=0.9
                    ))
        
        return cross_references, violations
    
    def _components_match(self, component_name: str, component_correlation: Dict[str, Any]) -> bool:
        """Check if a component name matches a component correlation"""
        canonical_name = component_correlation.get('canonical_name', '')
        original_name = component_correlation.get('component_name', '')
        source_references = component_correlation.get('source_references', {})
        
        # Check direct matches
        if component_name.lower() in [canonical_name.lower(), original_name.lower()]:
            return True
        
        # Check source references
        for source_refs in source_references.values():
            if any(component_name.lower() == ref.lower() for ref in source_refs):
                return True
        
        # Check similarity
        similarity_scores = [
            self._calculate_name_similarity(component_name, canonical_name),
            self._calculate_name_similarity(component_name, original_name)
        ]
        
        return max(similarity_scores) > 0.8
    
    def _calculate_reference_strength(self, component_name: str, component_correlation: Dict[str, Any]) -> float:
        """Calculate strength of cross-reference"""
        canonical_name = component_correlation.get('canonical_name', '')
        confidence_scores = component_correlation.get('confidence_scores', {})
        
        # Base strength from name similarity
        similarity = self._calculate_name_similarity(component_name, canonical_name)
        
        # Boost from source confidence
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5
        
        # Combined strength
        reference_strength = (similarity * 0.7) + (avg_confidence * 0.3)
        
        return min(1.0, reference_strength)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two component names"""
        if not name1 or not name2:
            return 0.0
        
        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()
        
        # Exact match
        if name1_lower == name2_lower:
            return 1.0
        
        # Substring match
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.9
        
        # Word-based similarity
        words1 = set(name1_lower.split())
        words2 = set(name2_lower.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def resolve_conflicts(self, violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
        """Generate conflict resolution recommendations"""
        resolutions = []
        
        # Group violations by type
        violation_groups = defaultdict(list)
        for violation in violations:
            violation_groups[violation.violation_type].append(violation)
        
        # Generate resolutions for each violation type
        for violation_type, type_violations in violation_groups.items():
            if violation_type == 'component_name_conflict':
                resolutions.extend(self._resolve_component_name_conflicts(type_violations))
            elif violation_type == 'failure_severity_mismatch':
                resolutions.extend(self._resolve_severity_mismatches(type_violations))
            elif violation_type == 'broken_cross_reference':
                resolutions.extend(self._resolve_broken_references(type_violations))
            else:
                # Generic resolution
                for violation in type_violations:
                    resolutions.append({
                        'violation_id': f"{violation_type}_{hash(violation.description) % 10000}",
                        'resolution_type': 'manual_review',
                        'priority': violation.severity,
                        'action': violation.resolution_suggestion,
                        'description': violation.description,
                        'affected_items': violation.conflicting_values
                    })
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        resolutions.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return resolutions
    
    def _resolve_component_name_conflicts(self, violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
        """Resolve component naming conflicts"""
        resolutions = []
        
        for violation in violations:
            name_variations = violation.conflicting_values.get('name_variations', [])
            
            # Suggest canonical name based on most common or shortest variation
            if name_variations:
                suggested_canonical = min(name_variations, key=len)  # Shortest name as canonical
                
                resolutions.append({
                    'violation_id': f"name_conflict_{hash(violation.description) % 10000}",
                    'resolution_type': 'canonical_name_assignment',
                    'priority': violation.severity,
                    'action': f'Set canonical name to "{suggested_canonical}"',
                    'description': f'Resolve naming conflict by standardizing on "{suggested_canonical}"',
                    'affected_items': {
                        'name_variations': name_variations,
                        'suggested_canonical': suggested_canonical,
                        'affected_sources': violation.affected_sources
                    }
                })
        
        return resolutions
    
    def _resolve_severity_mismatches(self, violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
        """Resolve failure severity mismatches"""
        resolutions = []
        
        for violation in violations:
            severities = violation.conflicting_values.get('severities', [])
            pattern_type = violation.conflicting_values.get('pattern_type', '')
            
            # Suggest using highest severity as conservative approach
            if severities:
                severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
                suggested_severity = min(severities, key=lambda x: severity_order.index(x) if x in severity_order else 999)
                
                resolutions.append({
                    'violation_id': f"severity_mismatch_{hash(violation.description) % 10000}",
                    'resolution_type': 'severity_standardization',
                    'priority': violation.severity,
                    'action': f'Standardize severity for pattern "{pattern_type}" to "{suggested_severity}"',
                    'description': f'Use conservative approach and set severity to highest level: {suggested_severity}',
                    'affected_items': {
                        'pattern_type': pattern_type,
                        'conflicting_severities': severities,
                        'suggested_severity': suggested_severity
                    }
                })
        
        return resolutions
    
    def _resolve_broken_references(self, violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
        """Resolve broken cross-references"""
        resolutions = []
        
        for violation in violations:
            missing_component = violation.conflicting_values.get('missing_component', '')
            failure_pattern = violation.conflicting_values.get('failure_pattern', '')
            
            resolutions.append({
                'violation_id': f"broken_ref_{hash(violation.description) % 10000}",
                'resolution_type': 'reference_repair',
                'priority': violation.severity,
                'action': f'Add component "{missing_component}" to component inventory or update reference',
                'description': f'Repair broken reference from failure pattern to component',
                'affected_items': {
                    'missing_component': missing_component,
                    'failure_pattern': failure_pattern,
                    'suggested_actions': [
                        'Add missing component to component inventory',
                        'Update failure pattern to reference existing component',
                        'Remove invalid component reference'
                    ]
                }
            })
        
        return resolutions
    
    def calculate_consistency_metrics(self, 
                                    violations: List[ConsistencyViolation],
                                    cross_references: List[CrossReference],
                                    total_components: int,
                                    total_failures: int) -> Dict[str, float]:
        """Calculate comprehensive consistency metrics"""
        metrics = {}
        
        # Overall consistency score (inverse of violation rate)
        total_items = total_components + total_failures
        if total_items > 0:
            violation_rate = len(violations) / total_items
            metrics['overall_consistency'] = max(0.0, 1.0 - violation_rate)
        else:
            metrics['overall_consistency'] = 1.0
        
        # Component consistency
        component_violations = len([v for v in violations if 'component' in v.violation_type])
        if total_components > 0:
            metrics['component_consistency'] = max(0.0, 1.0 - (component_violations / total_components))
        else:
            metrics['component_consistency'] = 1.0
        
        # Failure consistency
        failure_violations = len([v for v in violations if 'failure' in v.violation_type])
        if total_failures > 0:
            metrics['failure_consistency'] = max(0.0, 1.0 - (failure_violations / total_failures))
        else:
            metrics['failure_consistency'] = 1.0
        
        # Cross-reference validity
        if cross_references:
            valid_refs = len([ref for ref in cross_references if ref.validation_status == 'VALID'])
            metrics['cross_reference_validity'] = valid_refs / len(cross_references)
        else:
            metrics['cross_reference_validity'] = 1.0
        
        # Severity-weighted consistency (higher penalty for critical violations)
        severity_weights = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        weighted_violations = sum(severity_weights.get(v.severity, 1) for v in violations)
        max_possible_weight = total_items * severity_weights['CRITICAL']
        
        if max_possible_weight > 0:
            metrics['severity_weighted_consistency'] = max(0.0, 1.0 - (weighted_violations / max_possible_weight))
        else:
            metrics['severity_weighted_consistency'] = 1.0
        
        return metrics


# Initialize global consistency manager
_consistency_manager = ConsistencyManager()


@tool(
    name="validate_cross_source_consistency",
    description="Validate consistency of component identification and failure associations across all data sources"
)
def validate_cross_source_consistency(
    unified_analysis_data: Dict[str, Any],
    consistency_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Validate consistency across all data sources and identify violations.
    
    Args:
        unified_analysis_data: Results from generate_unified_analysis tool
        consistency_threshold: Minimum consistency score for acceptable quality
    
    Returns:
        Dictionary containing consistency validation results and violations
    """
    try:
        if 'error' in unified_analysis_data:
            return {"error": "Invalid unified analysis data provided"}
        
        unified_analysis = unified_analysis_data.get('unified_analysis', {})
        if not unified_analysis:
            return {"error": "No unified analysis data found"}
        
        component_correlations = unified_analysis.get('component_correlations', [])
        failure_correlations = unified_analysis.get('failure_correlations', [])
        
        # Validate component consistency
        component_violations = _consistency_manager.validate_component_consistency(component_correlations)
        
        # Validate failure consistency
        failure_violations = _consistency_manager.validate_failure_consistency(failure_correlations)
        
        # Validate cross-references
        cross_references, reference_violations = _consistency_manager.validate_cross_references(
            component_correlations, failure_correlations
        )
        
        # Combine all violations
        all_violations = component_violations + failure_violations + reference_violations
        
        # Calculate consistency metrics
        consistency_metrics = _consistency_manager.calculate_consistency_metrics(
            all_violations, cross_references, len(component_correlations), len(failure_correlations)
        )
        
        # Determine overall consistency level
        overall_score = consistency_metrics.get('overall_consistency', 0.0)
        if overall_score >= 0.8:
            consistency_level = 'HIGH'
        elif overall_score >= 0.6:
            consistency_level = 'MEDIUM'
        else:
            consistency_level = 'LOW'
        
        # Generate violation summary
        violation_summary = {
            'total_violations': len(all_violations),
            'critical_violations': len([v for v in all_violations if v.severity == 'CRITICAL']),
            'high_violations': len([v for v in all_violations if v.severity == 'HIGH']),
            'medium_violations': len([v for v in all_violations if v.severity == 'MEDIUM']),
            'low_violations': len([v for v in all_violations if v.severity == 'LOW']),
            'violation_types': list(set(v.violation_type for v in all_violations))
        }
        
        # Cross-reference summary
        cross_ref_summary = {
            'total_references': len(cross_references),
            'valid_references': len([ref for ref in cross_references if ref.validation_status == 'VALID']),
            'invalid_references': len([ref for ref in cross_references if ref.validation_status == 'INVALID']),
            'uncertain_references': len([ref for ref in cross_references if ref.validation_status == 'UNCERTAIN']),
            'avg_reference_strength': sum(ref.reference_strength for ref in cross_references) / len(cross_references) if cross_references else 0.0
        }
        
        result = {
            'consistency_validation': {
                'overall_consistency_score': overall_score,
                'consistency_level': consistency_level,
                'meets_threshold': overall_score >= consistency_threshold,
                'consistency_metrics': consistency_metrics
            },
            'violations_found': [asdict(violation) for violation in all_violations],
            'violation_summary': violation_summary,
            'cross_references': [asdict(ref) for ref in cross_references],
            'cross_reference_summary': cross_ref_summary,
            'validation_metadata': {
                'consistency_threshold': consistency_threshold,
                'components_analyzed': len(component_correlations),
                'failures_analyzed': len(failure_correlations),
                'validation_timestamp': str(Path(__file__).stat().st_mtime)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in validate_cross_source_consistency: {str(e)}")
        return {"error": f"Consistency validation failed: {str(e)}"}


@tool(
    name="resolve_consistency_conflicts",
    description="Generate resolution recommendations for consistency violations and conflicts"
)
def resolve_consistency_conflicts(
    consistency_validation_data: Dict[str, Any],
    resolution_priority: str = "critical_first"
) -> Dict[str, Any]:
    """
    Generate resolution recommendations for consistency violations.
    
    Args:
        consistency_validation_data: Results from validate_cross_source_consistency tool
        resolution_priority: Priority strategy ("critical_first", "high_impact", "quick_wins")
    
    Returns:
        Dictionary containing resolution recommendations and implementation plan
    """
    try:
        if 'error' in consistency_validation_data:
            return {"error": "Invalid consistency validation data provided"}
        
        violations_data = consistency_validation_data.get('violations_found', [])
        if not violations_data:
            return {
                'resolution_plan': {
                    'total_resolutions': 0,
                    'message': 'No consistency violations found - system is consistent'
                },
                'implementation_timeline': {},
                'resolution_summary': {'status': 'no_action_required'}
            }
        
        # Convert violation data back to objects
        violations = [ConsistencyViolation(**v_data) for v_data in violations_data]
        
        # Generate resolution recommendations
        resolutions = _consistency_manager.resolve_conflicts(violations)
        
        # Prioritize resolutions based on strategy
        if resolution_priority == "critical_first":
            # Sort by severity, then by confidence
            resolutions.sort(key=lambda x: (
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x['priority'], 4),
                -violations_data[0].get('confidence', 0.5)  # Higher confidence first
            ))
        elif resolution_priority == "high_impact":
            # Prioritize resolutions that affect multiple sources
            resolutions.sort(key=lambda x: (
                -len(x.get('affected_items', {}).get('affected_sources', [])),
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x['priority'], 4)
            ))
        elif resolution_priority == "quick_wins":
            # Prioritize easy-to-implement resolutions
            quick_resolution_types = ['canonical_name_assignment', 'reference_repair']
            resolutions.sort(key=lambda x: (
                0 if x['resolution_type'] in quick_resolution_types else 1,
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(x['priority'], 4)
            ))
        
        # Create implementation timeline
        timeline = _create_resolution_timeline(resolutions)
        
        # Generate resolution summary
        resolution_summary = {
            'total_resolutions': len(resolutions),
            'critical_resolutions': len([r for r in resolutions if r['priority'] == 'CRITICAL']),
            'high_priority_resolutions': len([r for r in resolutions if r['priority'] == 'HIGH']),
            'resolution_types': list(set(r['resolution_type'] for r in resolutions)),
            'estimated_effort': _estimate_resolution_effort(resolutions),
            'success_probability': _estimate_success_probability(resolutions, violations)
        }
        
        # Generate implementation guidance
        implementation_guidance = _generate_implementation_guidance(resolutions, violations)
        
        result = {
            'resolution_plan': {
                'resolutions': resolutions,
                'prioritization_strategy': resolution_priority,
                'total_resolutions': len(resolutions)
            },
            'implementation_timeline': timeline,
            'resolution_summary': resolution_summary,
            'implementation_guidance': implementation_guidance,
            'conflict_resolution_metadata': {
                'violations_processed': len(violations),
                'resolution_strategy': resolution_priority,
                'resolution_timestamp': str(Path(__file__).stat().st_mtime)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in resolve_consistency_conflicts: {str(e)}")
        return {"error": f"Conflict resolution failed: {str(e)}"}


@tool(
    name="generate_comprehensive_diagnostic_report",
    description="Create comprehensive diagnostic report combining all analysis results with consistency validation"
)
def generate_comprehensive_diagnostic_report(
    unified_analysis_data: Dict[str, Any],
    consistency_validation_data: Dict[str, Any],
    resolution_plan_data: Optional[Dict[str, Any]] = None,
    report_format: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Generate comprehensive diagnostic report with all analysis results.
    
    Args:
        unified_analysis_data: Results from generate_unified_analysis tool
        consistency_validation_data: Results from validate_cross_source_consistency tool
        resolution_plan_data: Optional results from resolve_consistency_conflicts tool
        report_format: Report format ("comprehensive", "executive", "technical")
    
    Returns:
        Dictionary containing comprehensive diagnostic report
    """
    try:
        # Validate inputs
        required_data = [unified_analysis_data, consistency_validation_data]
        if any('error' in data for data in required_data):
            return {"error": "One or more required input data sources contain errors"}
        
        # Extract key information
        unified_analysis = unified_analysis_data.get('unified_analysis', {})
        consistency_validation = consistency_validation_data.get('consistency_validation', {})
        
        # Build comprehensive report
        report = {
            'report_header': {
                'report_type': 'Comprehensive Instrument Diagnostic Report',
                'format': report_format,
                'generation_timestamp': str(Path(__file__).stat().st_mtime),
                'analysis_scope': 'Cross-source correlation with consistency validation'
            },
            'executive_summary': _generate_executive_summary_report(
                unified_analysis, consistency_validation
            ),
            'system_status': {
                'overall_status': unified_analysis.get('overall_status', 'UNCERTAIN'),
                'confidence_level': unified_analysis.get('confidence_level', 0.0),
                'consistency_level': consistency_validation.get('consistency_level', 'UNKNOWN'),
                'data_quality': _assess_overall_data_quality(unified_analysis_data, consistency_validation_data)
            },
            'detailed_findings': _compile_detailed_findings(
                unified_analysis, consistency_validation_data
            ),
            'recommendations': _compile_comprehensive_recommendations(
                unified_analysis, consistency_validation_data, resolution_plan_data
            ),
            'technical_appendix': _generate_technical_appendix(
                unified_analysis_data, consistency_validation_data
            ) if report_format in ['comprehensive', 'technical'] else None
        }
        
        # Add format-specific sections
        if report_format == "executive":
            report = _format_executive_report(report)
        elif report_format == "technical":
            report = _format_technical_report(report)
        
        # Generate report metadata
        report_metadata = {
            'total_components_analyzed': len(unified_analysis.get('component_correlations', [])),
            'total_failure_patterns': len(unified_analysis.get('failure_correlations', [])),
            'consistency_violations': len(consistency_validation_data.get('violations_found', [])),
            'data_sources_integrated': len(unified_analysis.get('analysis_metadata', {}).get('sources_analyzed', [])),
            'report_completeness': _calculate_report_completeness(report),
            'quality_indicators': _generate_quality_indicators(unified_analysis, consistency_validation)
        }
        
        report['report_metadata'] = report_metadata
        
        return {
            'diagnostic_report': report,
            'report_summary': _generate_report_summary(report),
            'export_options': _generate_export_options(report),
            'follow_up_recommendations': _generate_follow_up_recommendations(report)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_comprehensive_diagnostic_report: {str(e)}")
        return {"error": f"Comprehensive report generation failed: {str(e)}"}


# Helper functions for consistency management

def _create_resolution_timeline(resolutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create implementation timeline for resolutions"""
    timeline = {
        'immediate': {'timeframe': '0-1 hours', 'resolutions': []},
        'short_term': {'timeframe': '1-8 hours', 'resolutions': []},
        'medium_term': {'timeframe': '1-3 days', 'resolutions': []},
        'long_term': {'timeframe': '1+ weeks', 'resolutions': []}
    }
    
    for resolution in resolutions:
        priority = resolution.get('priority', 'MEDIUM')
        resolution_type = resolution.get('resolution_type', 'manual_review')
        
        if priority == 'CRITICAL':
            timeline['immediate']['resolutions'].append(resolution)
        elif priority == 'HIGH':
            timeline['short_term']['resolutions'].append(resolution)
        elif resolution_type in ['canonical_name_assignment', 'reference_repair']:
            timeline['short_term']['resolutions'].append(resolution)
        elif priority == 'MEDIUM':
            timeline['medium_term']['resolutions'].append(resolution)
        else:
            timeline['long_term']['resolutions'].append(resolution)
    
    return timeline


def _estimate_resolution_effort(resolutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Estimate effort required for resolutions"""
    effort_mapping = {
        'canonical_name_assignment': 'LOW',
        'severity_standardization': 'MEDIUM',
        'reference_repair': 'MEDIUM',
        'manual_review': 'HIGH'
    }
    
    effort_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
    
    for resolution in resolutions:
        resolution_type = resolution.get('resolution_type', 'manual_review')
        effort = effort_mapping.get(resolution_type, 'HIGH')
        effort_counts[effort] += 1
    
    total_resolutions = len(resolutions)
    return {
        'total_resolutions': total_resolutions,
        'low_effort': effort_counts['LOW'],
        'medium_effort': effort_counts['MEDIUM'],
        'high_effort': effort_counts['HIGH'],
        'estimated_hours': (effort_counts['LOW'] * 0.5) + (effort_counts['MEDIUM'] * 2) + (effort_counts['HIGH'] * 8)
    }


def _estimate_success_probability(resolutions: List[Dict[str, Any]], 
                                violations: List[ConsistencyViolation]) -> float:
    """Estimate probability of successful resolution"""
    if not violations:
        return 1.0
    
    # Base success rate by violation type
    success_rates = {
        'component_name_conflict': 0.9,
        'failure_severity_mismatch': 0.7,
        'broken_cross_reference': 0.8,
        'missing_canonical_name': 0.95,
        'inconsistent_failure_association': 0.6,
        'data_source_mismatch': 0.5
    }
    
    # Calculate weighted average based on violation confidence
    total_weight = 0
    weighted_success = 0
    
    for violation in violations:
        violation_type = violation.violation_type
        confidence = violation.confidence
        success_rate = success_rates.get(violation_type, 0.7)
        
        weight = confidence
        weighted_success += success_rate * weight
        total_weight += weight
    
    return weighted_success / total_weight if total_weight > 0 else 0.7


def _generate_implementation_guidance(resolutions: List[Dict[str, Any]], 
                                    violations: List[ConsistencyViolation]) -> List[Dict[str, Any]]:
    """Generate implementation guidance for resolutions"""
    guidance = []
    
    # Group resolutions by type
    resolution_groups = defaultdict(list)
    for resolution in resolutions:
        resolution_groups[resolution['resolution_type']].append(resolution)
    
    # Generate guidance for each type
    for resolution_type, type_resolutions in resolution_groups.items():
        if resolution_type == 'canonical_name_assignment':
            guidance.append({
                'step': f'Standardize component names ({len(type_resolutions)} items)',
                'description': 'Update component inventory with canonical names',
                'prerequisites': ['Access to component inventory system'],
                'estimated_time': f'{len(type_resolutions) * 5} minutes',
                'risk_level': 'LOW'
            })
        elif resolution_type == 'severity_standardization':
            guidance.append({
                'step': f'Standardize failure severities ({len(type_resolutions)} items)',
                'description': 'Review and update failure pattern severity levels',
                'prerequisites': ['Domain expertise in failure analysis'],
                'estimated_time': f'{len(type_resolutions) * 15} minutes',
                'risk_level': 'MEDIUM'
            })
        elif resolution_type == 'reference_repair':
            guidance.append({
                'step': f'Repair broken references ({len(type_resolutions)} items)',
                'description': 'Update or remove invalid cross-references',
                'prerequisites': ['Access to all data sources'],
                'estimated_time': f'{len(type_resolutions) * 10} minutes',
                'risk_level': 'MEDIUM'
            })
    
    return guidance


def _generate_executive_summary_report(unified_analysis: Dict[str, Any], 
                                     consistency_validation: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary for comprehensive report"""
    return {
        'system_health': unified_analysis.get('overall_status', 'UNCERTAIN'),
        'confidence_assessment': 'HIGH' if unified_analysis.get('confidence_level', 0) > 0.8 else 'MEDIUM' if unified_analysis.get('confidence_level', 0) > 0.6 else 'LOW',
        'data_consistency': consistency_validation.get('consistency_level', 'UNKNOWN'),
        'key_findings': {
            'components_identified': len(unified_analysis.get('component_correlations', [])),
            'failure_patterns_detected': len(unified_analysis.get('failure_correlations', [])),
            'consistency_violations': len(consistency_validation.get('violations_found', [])),
            'critical_issues': len([f for f in unified_analysis.get('failure_correlations', []) if f.get('severity') == 'CRITICAL'])
        },
        'immediate_actions_required': len([r for r in unified_analysis.get('unified_recommendations', []) if r.get('priority') == 'IMMEDIATE']),
        'overall_assessment': _determine_overall_assessment(unified_analysis, consistency_validation)
    }


def _determine_overall_assessment(unified_analysis: Dict[str, Any], 
                                consistency_validation: Dict[str, Any]) -> str:
    """Determine overall system assessment"""
    status = unified_analysis.get('overall_status', 'UNCERTAIN')
    confidence = unified_analysis.get('confidence_level', 0.0)
    consistency_score = consistency_validation.get('overall_consistency_score', 0.0)
    
    if status == 'FAIL' or confidence < 0.5 or consistency_score < 0.5:
        return 'CRITICAL - Immediate attention required'
    elif status == 'UNCERTAIN' or confidence < 0.7 or consistency_score < 0.7:
        return 'CAUTION - Further investigation recommended'
    else:
        return 'ACCEPTABLE - Continue monitoring'


def _compile_detailed_findings(unified_analysis: Dict[str, Any], 
                             consistency_validation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compile detailed findings from all analyses"""
    return {
        'component_analysis': {
            'total_components': len(unified_analysis.get('component_correlations', [])),
            'high_confidence_components': len([c for c in unified_analysis.get('component_correlations', []) if c.get('consistency_score', 0) > 0.8]),
            'components_with_failures': len([c for c in unified_analysis.get('component_correlations', []) if c.get('failure_associations', [])])
        },
        'failure_analysis': {
            'total_patterns': len(unified_analysis.get('failure_correlations', [])),
            'critical_failures': len([f for f in unified_analysis.get('failure_correlations', []) if f.get('severity') == 'CRITICAL']),
            'patterns_with_procedures': len([f for f in unified_analysis.get('failure_correlations', []) if f.get('troubleshooting_procedures', [])])
        },
        'consistency_analysis': {
            'overall_score': consistency_validation_data.get('consistency_validation', {}).get('overall_consistency_score', 0.0),
            'violations_by_severity': consistency_validation_data.get('violation_summary', {}),
            'cross_reference_validity': consistency_validation_data.get('cross_reference_summary', {}).get('valid_references', 0)
        }
    }


def _compile_comprehensive_recommendations(unified_analysis: Dict[str, Any],
                                         consistency_validation_data: Dict[str, Any],
                                         resolution_plan_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compile comprehensive recommendations from all sources"""
    recommendations = []
    
    # Add unified analysis recommendations
    unified_recs = unified_analysis.get('unified_recommendations', [])
    recommendations.extend(unified_recs)
    
    # Add consistency resolution recommendations
    if resolution_plan_data and 'resolution_plan' in resolution_plan_data:
        resolution_recs = resolution_plan_data['resolution_plan'].get('resolutions', [])
        for rec in resolution_recs:
            recommendations.append({
                'priority': rec.get('priority', 'MEDIUM'),
                'category': 'CONSISTENCY',
                'action': rec.get('action', ''),
                'description': rec.get('description', ''),
                'source': 'consistency_resolution'
            })
    
    # Remove duplicates and sort by priority
    unique_recommendations = []
    seen_actions = set()
    
    for rec in recommendations:
        action = rec.get('action', '')
        if action not in seen_actions:
            unique_recommendations.append(rec)
            seen_actions.add(action)
    
    # Sort by priority
    priority_order = {'IMMEDIATE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    unique_recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'MEDIUM'), 4))
    
    return unique_recommendations


def _generate_technical_appendix(unified_analysis_data: Dict[str, Any],
                               consistency_validation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate technical appendix with detailed data"""
    return {
        'raw_data_summary': {
            'unified_analysis_keys': list(unified_analysis_data.keys()),
            'consistency_validation_keys': list(consistency_validation_data.keys()),
            'data_completeness': _assess_data_completeness(unified_analysis_data, consistency_validation_data)
        },
        'correlation_matrices': {
            'component_correlations': len(unified_analysis_data.get('unified_analysis', {}).get('component_correlations', [])),
            'failure_correlations': len(unified_analysis_data.get('unified_analysis', {}).get('failure_correlations', []))
        },
        'validation_details': consistency_validation_data.get('validation_metadata', {}),
        'processing_statistics': unified_analysis_data.get('unified_analysis', {}).get('analysis_metadata', {})
    }


def _format_executive_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Format report for executive audience"""
    # Keep only high-level information
    executive_report = {
        'report_header': report['report_header'],
        'executive_summary': report['executive_summary'],
        'system_status': report['system_status'],
        'key_recommendations': report['recommendations'][:5],  # Top 5 only
        'report_metadata': {
            'format': 'executive',
            'detail_level': 'summary_only'
        }
    }
    return executive_report


def _format_technical_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Format report for technical audience"""
    # Include all technical details
    report['technical_details'] = report.get('technical_appendix', {})
    report['report_metadata']['format'] = 'technical'
    report['report_metadata']['detail_level'] = 'comprehensive'
    return report


def _assess_overall_data_quality(unified_analysis_data: Dict[str, Any],
                               consistency_validation_data: Dict[str, Any]) -> str:
    """Assess overall data quality"""
    consistency_score = consistency_validation_data.get('consistency_validation', {}).get('overall_consistency_score', 0.0)
    confidence_level = unified_analysis_data.get('unified_analysis', {}).get('confidence_level', 0.0)
    
    avg_quality = (consistency_score + confidence_level) / 2
    
    if avg_quality > 0.8:
        return 'HIGH'
    elif avg_quality > 0.6:
        return 'MEDIUM'
    else:
        return 'LOW'


def _assess_data_completeness(unified_analysis_data: Dict[str, Any],
                            consistency_validation_data: Dict[str, Any]) -> float:
    """Assess completeness of data analysis"""
    required_sections = [
        'unified_analysis', 'executive_summary', 'actionable_insights'
    ]
    
    present_sections = sum(1 for section in required_sections if section in unified_analysis_data)
    completeness = present_sections / len(required_sections)
    
    # Bonus for consistency validation
    if 'consistency_validation' in consistency_validation_data:
        completeness += 0.1
    
    return min(1.0, completeness)


def _calculate_report_completeness(report: Dict[str, Any]) -> float:
    """Calculate completeness of generated report"""
    required_sections = [
        'report_header', 'executive_summary', 'system_status', 
        'detailed_findings', 'recommendations'
    ]
    
    present_sections = sum(1 for section in required_sections if section in report and report[section])
    return present_sections / len(required_sections)


def _generate_quality_indicators(unified_analysis: Dict[str, Any],
                               consistency_validation: Dict[str, Any]) -> Dict[str, str]:
    """Generate quality indicators for the report"""
    indicators = {}
    
    # Data consistency indicator
    consistency_score = consistency_validation.get('overall_consistency_score', 0.0)
    if consistency_score > 0.8:
        indicators['data_consistency'] = 'EXCELLENT'
    elif consistency_score > 0.6:
        indicators['data_consistency'] = 'GOOD'
    else:
        indicators['data_consistency'] = 'NEEDS_IMPROVEMENT'
    
    # Analysis confidence indicator
    confidence_level = unified_analysis.get('confidence_level', 0.0)
    if confidence_level > 0.8:
        indicators['analysis_confidence'] = 'HIGH'
    elif confidence_level > 0.6:
        indicators['analysis_confidence'] = 'MEDIUM'
    else:
        indicators['analysis_confidence'] = 'LOW'
    
    # Completeness indicator
    component_count = len(unified_analysis.get('component_correlations', []))
    failure_count = len(unified_analysis.get('failure_correlations', []))
    
    if component_count > 5 and failure_count > 3:
        indicators['analysis_completeness'] = 'COMPREHENSIVE'
    elif component_count > 2 and failure_count > 1:
        indicators['analysis_completeness'] = 'ADEQUATE'
    else:
        indicators['analysis_completeness'] = 'LIMITED'
    
    return indicators


def _generate_report_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of the diagnostic report"""
    return {
        'report_type': report['report_header']['report_type'],
        'system_status': report['system_status']['overall_status'],
        'confidence_level': report['system_status']['confidence_level'],
        'total_recommendations': len(report.get('recommendations', [])),
        'critical_issues': len([r for r in report.get('recommendations', []) if r.get('priority') == 'IMMEDIATE']),
        'report_completeness': report['report_metadata']['report_completeness'],
        'generation_timestamp': report['report_header']['generation_timestamp']
    }


def _generate_export_options(report: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate export options for the report"""
    return [
        {'format': 'JSON', 'description': 'Machine-readable format for integration'},
        {'format': 'PDF', 'description': 'Formatted document for sharing'},
        {'format': 'CSV', 'description': 'Tabular data for spreadsheet analysis'},
        {'format': 'XML', 'description': 'Structured format for system integration'}
    ]


def _generate_follow_up_recommendations(report: Dict[str, Any]) -> List[str]:
    """Generate follow-up recommendations based on report findings"""
    recommendations = []
    
    system_status = report['system_status']['overall_status']
    confidence_level = report['system_status']['confidence_level']
    
    if system_status == 'FAIL':
        recommendations.append('Schedule immediate maintenance intervention')
        recommendations.append('Implement continuous monitoring until issues resolved')
    elif system_status == 'UNCERTAIN':
        recommendations.append('Perform additional diagnostic tests')
        recommendations.append('Increase monitoring frequency')
    
    if isinstance(confidence_level, (int, float)) and confidence_level < 0.7:
        recommendations.append('Collect additional data to improve analysis confidence')
        recommendations.append('Consider expert review of findings')
    
    recommendations.append('Schedule follow-up analysis in 24-48 hours')
    recommendations.append('Document all maintenance actions taken')
    
    return recommendations


# List of available consistency management tools
CONSISTENCY_MANAGEMENT_TOOLS = [
    validate_cross_source_consistency,
    resolve_consistency_conflicts,
    generate_comprehensive_diagnostic_report
]