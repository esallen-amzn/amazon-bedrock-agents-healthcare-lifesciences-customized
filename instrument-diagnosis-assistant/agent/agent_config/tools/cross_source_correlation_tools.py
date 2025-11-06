"""
Cross-Source Correlation Tools for Instrument Diagnosis Assistant

These tools correlate information across different data sources (logs, documentation, guides)
to provide unified analysis and consistent component identification.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from strands import tool

logger = logging.getLogger(__name__)


@dataclass
class ComponentCorrelation:
    """Represents correlation of a component across different sources"""
    component_name: str
    canonical_name: str
    source_references: Dict[str, List[str]]  # source_type -> list of references
    confidence_scores: Dict[str, float]  # source_type -> confidence
    failure_associations: List[str]
    troubleshooting_procedures: List[str]
    consistency_score: float


@dataclass
class FailurePatternCorrelation:
    """Represents correlation between failure patterns and troubleshooting procedures"""
    failure_pattern: str
    pattern_type: str
    severity: str
    associated_components: List[str]
    troubleshooting_procedures: List[Dict[str, Any]]
    documentation_references: List[str]
    correlation_strength: float


@dataclass
class UnifiedAnalysis:
    """Unified analysis combining multiple data sources"""
    overall_status: str
    confidence_level: float
    component_correlations: List[ComponentCorrelation]
    failure_correlations: List[FailurePatternCorrelation]
    cross_source_consistency: Dict[str, float]
    unified_recommendations: List[Dict[str, Any]]
    analysis_metadata: Dict[str, Any]


class CrossSourceCorrelationEngine:
    """Core engine for cross-source correlation and analysis"""
    
    def __init__(self):
        # Component name normalization patterns
        self.normalization_patterns = {
            'common_abbreviations': {
                'temp': 'temperature',
                'ctrl': 'control',
                'sys': 'system',
                'mod': 'module',
                'det': 'detector',
                'opt': 'optical',
                'proc': 'processor',
                'mgmt': 'management',
                'intf': 'interface'
            },
            'unit_variations': {
                'sensor': ['sensors', 'sensing', 'detection'],
                'controller': ['control', 'controlling', 'management'],
                'module': ['unit', 'component', 'assembly'],
                'system': ['subsystem', 'sys']
            }
        }
        
        # Failure pattern to procedure mapping keywords
        self.failure_procedure_keywords = {
            'connection_timeout': ['connection', 'cable', 'communication', 'timeout'],
            'service_failures': ['service', 'software', 'restart', 'process'],
            'memory_issues': ['memory', 'ram', 'allocation', 'leak'],
            'disk_issues': ['disk', 'storage', 'space', 'write'],
            'performance_degradation': ['performance', 'slow', 'optimization', 'speed'],
            'driver_issues': ['driver', 'version', 'compatibility', 'update'],
            'optical_alignment': ['optical', 'alignment', 'laser', 'mirror'],
            'temperature_control': ['temperature', 'heating', 'cooling', 'thermal']
        }
        
        # Source type priorities for conflict resolution
        self.source_priorities = {
            'engineering_docs': 1.0,
            'troubleshooting_guides': 0.9,
            'log_analysis': 0.8,
            'component_inventory': 0.7
        }
    
    def normalize_component_name(self, name: str) -> str:
        """Normalize component name for consistent identification"""
        normalized = name.lower().strip()
        
        # Apply abbreviation expansions
        for abbrev, full_form in self.normalization_patterns['common_abbreviations'].items():
            normalized = re.sub(r'\b' + abbrev + r'\b', full_form, normalized)
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'\b(main|primary|secondary|backup)\s+', '', normalized)
        normalized = re.sub(r'\s+(unit|module|system|component)$', '', normalized)
        
        # Clean up whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def find_component_matches(self, target_component: str, 
                             source_components: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, float]]]:
        """Find component matches across different sources"""
        target_normalized = self.normalize_component_name(target_component)
        matches = {}
        
        for source_type, components in source_components.items():
            source_matches = []
            
            for component in components:
                component_normalized = self.normalize_component_name(component)
                similarity = self._calculate_similarity(target_normalized, component_normalized)
                
                if similarity > 0.6:  # Threshold for considering a match
                    source_matches.append((component, similarity))
            
            # Sort by similarity score
            source_matches.sort(key=lambda x: x[1], reverse=True)
            matches[source_type] = source_matches[:5]  # Top 5 matches per source
        
        return matches
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two component names"""
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return 0.9
        
        # Word-based similarity
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost for key technical terms
        key_terms = {'laser', 'detector', 'sensor', 'controller', 'optical', 'temperature', 'pressure'}
        if intersection.intersection(key_terms):
            jaccard_similarity += 0.1
        
        return min(1.0, jaccard_similarity)
    
    def correlate_failure_patterns_to_procedures(self, 
                                               failure_patterns: List[Dict[str, Any]],
                                               troubleshooting_procedures: List[Dict[str, Any]]) -> List[FailurePatternCorrelation]:
        """Correlate failure patterns with relevant troubleshooting procedures"""
        correlations = []
        
        for pattern in failure_patterns:
            pattern_type = pattern.get('type', pattern.get('pattern_type', ''))
            pattern_desc = pattern.get('description', '')
            severity = pattern.get('severity', 'MEDIUM')
            
            # Find matching procedures
            matching_procedures = []
            for procedure in troubleshooting_procedures:
                correlation_strength = self._calculate_pattern_procedure_correlation(
                    pattern_type, pattern_desc, procedure
                )
                
                if correlation_strength > 0.5:
                    matching_procedures.append({
                        'procedure': procedure,
                        'correlation_strength': correlation_strength
                    })
            
            # Sort by correlation strength
            matching_procedures.sort(key=lambda x: x['correlation_strength'], reverse=True)
            
            # Extract associated components
            associated_components = pattern.get('components', [])
            if not associated_components and 'matched_lines' in pattern:
                # Try to extract component names from matched lines
                associated_components = self._extract_components_from_text(
                    ' '.join(pattern['matched_lines'][:5])
                )
            
            correlation = FailurePatternCorrelation(
                failure_pattern=pattern_desc,
                pattern_type=pattern_type,
                severity=severity,
                associated_components=associated_components,
                troubleshooting_procedures=[mp['procedure'] for mp in matching_procedures[:3]],
                documentation_references=[],  # Will be populated by caller
                correlation_strength=max([mp['correlation_strength'] for mp in matching_procedures], default=0.0)
            )
            
            correlations.append(correlation)
        
        return correlations
    
    def _calculate_pattern_procedure_correlation(self, pattern_type: str, pattern_desc: str, 
                                              procedure: Dict[str, Any]) -> float:
        """Calculate correlation strength between failure pattern and procedure"""
        correlation_score = 0.0
        
        # Get procedure text content
        procedure_text = ' '.join([
            procedure.get('title', ''),
            procedure.get('description', ''),
            ' '.join(procedure.get('symptoms', [])),
            ' '.join(procedure.get('troubleshooting_steps', []))
        ]).lower()
        
        # Check for direct pattern type match
        if pattern_type in self.failure_procedure_keywords:
            keywords = self.failure_procedure_keywords[pattern_type]
            keyword_matches = sum(1 for keyword in keywords if keyword in procedure_text)
            correlation_score += (keyword_matches / len(keywords)) * 0.6
        
        # Check for description overlap
        pattern_words = set(pattern_desc.lower().split())
        procedure_words = set(procedure_text.split())
        
        if pattern_words and procedure_words:
            word_overlap = len(pattern_words.intersection(procedure_words)) / len(pattern_words.union(procedure_words))
            correlation_score += word_overlap * 0.4
        
        return min(1.0, correlation_score)
    
    def _extract_components_from_text(self, text: str) -> List[str]:
        """Extract component names from text using pattern matching"""
        components = []
        
        # Common component patterns
        component_patterns = [
            r'\b(\w+\s+(?:sensor|detector|controller|module|system|unit))\b',
            r'\b(laser|optical|temperature|pressure|flow)\s+(\w+)\b',
            r'\b(\w+)\s+(?:component|assembly|interface)\b'
        ]
        
        for pattern in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    components.extend([m.strip() for m in match if m.strip()])
                else:
                    components.append(match.strip())
        
        return list(set(components))  # Remove duplicates
    
    def calculate_cross_source_consistency(self, 
                                         component_correlations: List[ComponentCorrelation]) -> Dict[str, float]:
        """Calculate consistency metrics across different sources"""
        consistency_metrics = {}
        
        if not component_correlations:
            return consistency_metrics
        
        # Overall component identification consistency
        total_components = len(component_correlations)
        high_confidence_components = len([c for c in component_correlations if c.consistency_score > 0.8])
        consistency_metrics['component_identification'] = high_confidence_components / total_components if total_components > 0 else 0.0
        
        # Source agreement consistency
        source_agreements = []
        for correlation in component_correlations:
            if len(correlation.source_references) > 1:
                # Calculate agreement between sources
                source_names = list(correlation.source_references.keys())
                agreements = 0
                comparisons = 0
                
                for i in range(len(source_names)):
                    for j in range(i + 1, len(source_names)):
                        comparisons += 1
                        source1_refs = correlation.source_references[source_names[i]]
                        source2_refs = correlation.source_references[source_names[j]]
                        
                        # Check if sources refer to the same component
                        if any(self._calculate_similarity(ref1, ref2) > 0.7 
                               for ref1 in source1_refs for ref2 in source2_refs):
                            agreements += 1
                
                if comparisons > 0:
                    source_agreements.append(agreements / comparisons)
        
        consistency_metrics['source_agreement'] = sum(source_agreements) / len(source_agreements) if source_agreements else 0.0
        
        # Failure pattern consistency
        failure_associations = [len(c.failure_associations) for c in component_correlations]
        if failure_associations:
            avg_failure_associations = sum(failure_associations) / len(failure_associations)
            consistency_metrics['failure_pattern_coverage'] = min(1.0, avg_failure_associations / 3.0)  # Normalize to 0-1
        else:
            consistency_metrics['failure_pattern_coverage'] = 0.0
        
        return consistency_metrics
    
    def resolve_component_conflicts(self, 
                                  component_matches: Dict[str, List[Tuple[str, float]]]) -> Tuple[str, float]:
        """Resolve conflicts when multiple sources have different names for the same component"""
        if not component_matches:
            return "", 0.0
        
        # Weight matches by source priority and similarity score
        weighted_matches = []
        
        for source_type, matches in component_matches.items():
            source_priority = self.source_priorities.get(source_type, 0.5)
            
            for component_name, similarity in matches:
                weighted_score = similarity * source_priority
                weighted_matches.append((component_name, weighted_score, source_type))
        
        if not weighted_matches:
            return "", 0.0
        
        # Sort by weighted score
        weighted_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest weighted match
        best_match = weighted_matches[0]
        return best_match[0], best_match[1]


# Initialize global correlation engine
_correlation_engine = CrossSourceCorrelationEngine()


@tool(
    name="correlate_components_across_sources",
    description="Correlate component references across log files, documentation, and troubleshooting guides"
)
def correlate_components_across_sources(
    log_analysis_data: Dict[str, Any],
    component_inventory: Dict[str, Any],
    document_analysis: Dict[str, Any],
    correlation_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Correlate component references across different data sources.
    
    Args:
        log_analysis_data: Results from log analysis tools
        component_inventory: Results from component recognition tools
        document_analysis: Results from multi-modal document processing
        correlation_threshold: Minimum correlation score to consider a match
    
    Returns:
        Dictionary containing component correlations across sources
    """
    try:
        # Validate inputs
        if any('error' in data for data in [log_analysis_data, component_inventory, document_analysis] if data):
            return {"error": "One or more input data sources contain errors"}
        
        # Extract components from each source
        source_components = {}
        
        # From log analysis
        if log_analysis_data and 'top_issues' in log_analysis_data:
            log_components = []
            for issue in log_analysis_data['top_issues']:
                components = _correlation_engine._extract_components_from_text(
                    issue.get('description', '') + ' ' + ' '.join(issue.get('sample_matches', []))
                )
                log_components.extend(components)
            source_components['log_analysis'] = list(set(log_components))
        
        # From component inventory
        if component_inventory and 'inventory' in component_inventory:
            inventory = component_inventory['inventory']
            source_components['component_inventory'] = list(inventory.get('components', {}).keys())
        
        # From document analysis
        if document_analysis and 'document_analysis' in document_analysis:
            doc_data = document_analysis['document_analysis']
            doc_components = []
            
            # Extract from structured sections
            structured_sections = doc_data.get('structured_sections', {})
            for section_content in structured_sections.values():
                if isinstance(section_content, list):
                    for item in section_content:
                        if isinstance(item, dict):
                            text_content = ' '.join([str(v) for v in item.values() if isinstance(v, str)])
                        else:
                            text_content = str(item)
                        components = _correlation_engine._extract_components_from_text(text_content)
                        doc_components.extend(components)
            
            source_components['document_analysis'] = list(set(doc_components))
        
        # Find all unique components across sources
        all_components = set()
        for components in source_components.values():
            all_components.update(components)
        
        # Correlate each component across sources
        component_correlations = []
        
        for component in all_components:
            # Find matches across sources
            matches = _correlation_engine.find_component_matches(component, source_components)
            
            # Resolve conflicts and determine canonical name
            canonical_name, confidence = _correlation_engine.resolve_component_conflicts(matches)
            
            if confidence >= correlation_threshold:
                # Build source references
                source_references = {}
                confidence_scores = {}
                
                for source_type, source_matches in matches.items():
                    if source_matches:
                        source_references[source_type] = [match[0] for match in source_matches]
                        confidence_scores[source_type] = max(match[1] for match in source_matches)
                
                # Extract failure associations from log analysis
                failure_associations = []
                if 'log_analysis' in source_references and log_analysis_data:
                    for issue in log_analysis_data.get('top_issues', []):
                        if any(comp in issue.get('description', '') for comp in source_references['log_analysis']):
                            failure_associations.append(issue.get('description', ''))
                
                # Extract troubleshooting procedures from document analysis
                troubleshooting_procedures = []
                if 'document_analysis' in source_references and document_analysis:
                    doc_data = document_analysis.get('document_analysis', {})
                    procedures = doc_data.get('structured_sections', {}).get('procedures', [])
                    for proc in procedures:
                        if isinstance(proc, dict) and any(comp in str(proc) for comp in source_references.get('document_analysis', [])):
                            troubleshooting_procedures.append(proc.get('title', 'Unnamed procedure'))
                
                # Calculate consistency score
                consistency_score = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
                
                correlation = ComponentCorrelation(
                    component_name=component,
                    canonical_name=canonical_name or component,
                    source_references=source_references,
                    confidence_scores=confidence_scores,
                    failure_associations=failure_associations,
                    troubleshooting_procedures=troubleshooting_procedures,
                    consistency_score=consistency_score
                )
                
                component_correlations.append(correlation)
        
        # Calculate cross-source consistency metrics
        consistency_metrics = _correlation_engine.calculate_cross_source_consistency(component_correlations)
        
        # Generate correlation summary
        correlation_summary = {
            'total_components_found': len(all_components),
            'components_correlated': len(component_correlations),
            'correlation_rate': len(component_correlations) / len(all_components) if all_components else 0.0,
            'sources_analyzed': list(source_components.keys()),
            'avg_consistency_score': sum(c.consistency_score for c in component_correlations) / len(component_correlations) if component_correlations else 0.0
        }
        
        result = {
            'component_correlations': [asdict(corr) for corr in component_correlations],
            'consistency_metrics': consistency_metrics,
            'correlation_summary': correlation_summary,
            'source_components': source_components,
            'correlation_metadata': {
                'correlation_threshold': correlation_threshold,
                'normalization_applied': True,
                'conflict_resolution_used': True,
                'total_sources': len(source_components)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in correlate_components_across_sources: {str(e)}")
        return {"error": f"Component correlation failed: {str(e)}"}


@tool(
    name="correlate_failures_to_procedures",
    description="Associate failure patterns with relevant troubleshooting procedures from guides"
)
def correlate_failures_to_procedures(
    failure_analysis_data: Dict[str, Any],
    troubleshooting_guides: Dict[str, Any],
    correlation_strength_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Correlate failure patterns with troubleshooting procedures.
    
    Args:
        failure_analysis_data: Results from failure indicator extraction
        troubleshooting_guides: Results from multi-modal document processing
        correlation_strength_threshold: Minimum correlation strength to include
    
    Returns:
        Dictionary containing failure-procedure correlations
    """
    try:
        # Validate inputs
        if 'error' in failure_analysis_data or 'error' in troubleshooting_guides:
            return {"error": "Invalid input data provided"}
        
        # Extract failure patterns
        failure_patterns = []
        
        # From categorized indicators
        if 'categorized_indicators' in failure_analysis_data:
            for category, indicators in failure_analysis_data['categorized_indicators'].items():
                for indicator in indicators:
                    failure_patterns.append({
                        'type': indicator.get('type', category),
                        'description': indicator.get('description', ''),
                        'severity': indicator.get('severity', 'MEDIUM'),
                        'confidence': indicator.get('confidence', 0.5),
                        'matched_lines': indicator.get('sample_lines', [])
                    })
        
        # From top issues
        if 'top_issues' in failure_analysis_data:
            for issue in failure_analysis_data['top_issues']:
                failure_patterns.append({
                    'type': issue.get('type', 'unknown'),
                    'description': issue.get('description', ''),
                    'severity': issue.get('severity', 'MEDIUM'),
                    'confidence': issue.get('confidence', 0.5),
                    'matched_lines': issue.get('sample_matches', [])
                })
        
        # Extract troubleshooting procedures
        procedures = []
        
        if 'document_analysis' in troubleshooting_guides:
            doc_data = troubleshooting_guides['document_analysis']
            structured_sections = doc_data.get('structured_sections', {})
            
            # Extract procedures from structured sections
            if 'procedures' in structured_sections:
                procedures.extend(structured_sections['procedures'])
            
            # Extract from symptoms and troubleshooting steps
            if 'symptoms' in structured_sections:
                for i, symptom in enumerate(structured_sections['symptoms']):
                    procedures.append({
                        'title': f'Symptom {i+1} Resolution',
                        'description': symptom,
                        'symptoms': [symptom],
                        'troubleshooting_steps': []
                    })
            
            if 'troubleshooting_steps' in structured_sections:
                for i, step in enumerate(structured_sections['troubleshooting_steps']):
                    procedures.append({
                        'title': f'Troubleshooting Step {i+1}',
                        'description': step,
                        'symptoms': [],
                        'troubleshooting_steps': [step]
                    })
        
        # Correlate failure patterns with procedures
        failure_correlations = _correlation_engine.correlate_failure_patterns_to_procedures(
            failure_patterns, procedures
        )
        
        # Filter by correlation strength threshold
        filtered_correlations = [
            corr for corr in failure_correlations 
            if corr.correlation_strength >= correlation_strength_threshold
        ]
        
        # Generate correlation statistics
        correlation_stats = {
            'total_failure_patterns': len(failure_patterns),
            'total_procedures': len(procedures),
            'correlations_found': len(filtered_correlations),
            'correlation_rate': len(filtered_correlations) / len(failure_patterns) if failure_patterns else 0.0,
            'avg_correlation_strength': sum(c.correlation_strength for c in filtered_correlations) / len(filtered_correlations) if filtered_correlations else 0.0,
            'high_confidence_correlations': len([c for c in filtered_correlations if c.correlation_strength > 0.8])
        }
        
        # Group correlations by severity
        correlations_by_severity = {}
        for correlation in filtered_correlations:
            severity = correlation.severity
            if severity not in correlations_by_severity:
                correlations_by_severity[severity] = []
            correlations_by_severity[severity].append(correlation)
        
        # Generate actionable procedure recommendations
        procedure_recommendations = []
        for correlation in filtered_correlations:
            if correlation.correlation_strength > 0.7:  # High confidence correlations
                for procedure in correlation.troubleshooting_procedures:
                    procedure_recommendations.append({
                        'failure_pattern': correlation.failure_pattern,
                        'severity': correlation.severity,
                        'procedure_title': procedure.get('title', 'Unnamed procedure'),
                        'procedure_description': procedure.get('description', ''),
                        'correlation_strength': correlation.correlation_strength,
                        'associated_components': correlation.associated_components
                    })
        
        result = {
            'failure_correlations': [asdict(corr) for corr in filtered_correlations],
            'correlation_statistics': correlation_stats,
            'correlations_by_severity': {k: [asdict(c) for c in v] for k, v in correlations_by_severity.items()},
            'procedure_recommendations': procedure_recommendations,
            'correlation_metadata': {
                'correlation_threshold': correlation_strength_threshold,
                'failure_patterns_analyzed': len(failure_patterns),
                'procedures_analyzed': len(procedures),
                'correlation_method': 'keyword_and_semantic_matching'
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in correlate_failures_to_procedures: {str(e)}")
        return {"error": f"Failure-procedure correlation failed: {str(e)}"}


@tool(
    name="generate_unified_analysis",
    description="Create unified analysis combining logs, documentation, and troubleshooting guides"
)
def generate_unified_analysis(
    log_analysis_data: Dict[str, Any],
    component_correlations: Dict[str, Any],
    failure_correlations: Dict[str, Any],
    diagnosis_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate unified analysis combining multiple data sources.
    
    Args:
        log_analysis_data: Results from log analysis tools
        component_correlations: Results from correlate_components_across_sources
        failure_correlations: Results from correlate_failures_to_procedures
        diagnosis_data: Optional diagnosis results for additional context
    
    Returns:
        Dictionary containing unified analysis and recommendations
    """
    try:
        # Validate inputs
        required_inputs = [log_analysis_data, component_correlations, failure_correlations]
        if any('error' in data for data in required_inputs if data):
            return {"error": "One or more required input data sources contain errors"}
        
        # Determine overall status from multiple sources
        overall_status = _determine_unified_status(log_analysis_data, diagnosis_data)
        
        # Calculate unified confidence level
        confidence_factors = []
        
        # Log analysis confidence
        if 'summary' in log_analysis_data:
            risk_level = log_analysis_data['summary'].get('risk_level', 'MEDIUM')
            log_confidence = 0.9 if risk_level in ['HIGH', 'LOW'] else 0.6
            confidence_factors.append(log_confidence)
        
        # Component correlation confidence
        if 'correlation_summary' in component_correlations:
            corr_rate = component_correlations['correlation_summary'].get('correlation_rate', 0.0)
            component_confidence = min(0.9, corr_rate + 0.3)
            confidence_factors.append(component_confidence)
        
        # Failure correlation confidence
        if 'correlation_statistics' in failure_correlations:
            fail_corr_rate = failure_correlations['correlation_statistics'].get('correlation_rate', 0.0)
            failure_confidence = min(0.9, fail_corr_rate + 0.2)
            confidence_factors.append(failure_confidence)
        
        unified_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Extract component correlations
        component_corr_list = []
        if 'component_correlations' in component_correlations:
            for corr_data in component_correlations['component_correlations']:
                component_corr_list.append(ComponentCorrelation(**corr_data))
        
        # Extract failure correlations
        failure_corr_list = []
        if 'failure_correlations' in failure_correlations:
            for corr_data in failure_correlations['failure_correlations']:
                failure_corr_list.append(FailurePatternCorrelation(**corr_data))
        
        # Calculate cross-source consistency
        cross_source_consistency = {}
        
        # Component identification consistency
        if component_corr_list:
            high_consistency_components = len([c for c in component_corr_list if c.consistency_score > 0.8])
            cross_source_consistency['component_consistency'] = high_consistency_components / len(component_corr_list)
        else:
            cross_source_consistency['component_consistency'] = 0.0
        
        # Failure pattern consistency
        if failure_corr_list:
            high_confidence_failures = len([f for f in failure_corr_list if f.correlation_strength > 0.8])
            cross_source_consistency['failure_pattern_consistency'] = high_confidence_failures / len(failure_corr_list)
        else:
            cross_source_consistency['failure_pattern_consistency'] = 0.0
        
        # Overall data consistency
        consistency_values = list(cross_source_consistency.values())
        cross_source_consistency['overall_consistency'] = sum(consistency_values) / len(consistency_values) if consistency_values else 0.0
        
        # Generate unified recommendations
        unified_recommendations = _generate_unified_recommendations(
            overall_status, component_corr_list, failure_corr_list, log_analysis_data
        )
        
        # Compile analysis metadata
        analysis_metadata = {
            'sources_analyzed': ['log_analysis', 'component_inventory', 'troubleshooting_guides'],
            'total_components_identified': len(component_corr_list),
            'total_failure_patterns': len(failure_corr_list),
            'confidence_level': 'HIGH' if unified_confidence > 0.8 else 'MEDIUM' if unified_confidence > 0.6 else 'LOW',
            'consistency_level': 'HIGH' if cross_source_consistency['overall_consistency'] > 0.8 else 'MEDIUM' if cross_source_consistency['overall_consistency'] > 0.6 else 'LOW',
            'analysis_timestamp': str(Path(__file__).stat().st_mtime),
            'diagnosis_included': diagnosis_data is not None
        }
        
        # Create unified analysis result
        unified_analysis = UnifiedAnalysis(
            overall_status=overall_status,
            confidence_level=unified_confidence,
            component_correlations=component_corr_list,
            failure_correlations=failure_corr_list,
            cross_source_consistency=cross_source_consistency,
            unified_recommendations=unified_recommendations,
            analysis_metadata=analysis_metadata
        )
        
        result = {
            'unified_analysis': asdict(unified_analysis),
            'executive_summary': _generate_executive_summary(unified_analysis),
            'actionable_insights': _extract_actionable_insights(unified_analysis),
            'data_quality_assessment': _assess_data_quality(log_analysis_data, component_correlations, failure_correlations)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_unified_analysis: {str(e)}")
        return {"error": f"Unified analysis generation failed: {str(e)}"}


# Helper functions

def _determine_unified_status(log_analysis_data: Dict[str, Any], 
                            diagnosis_data: Optional[Dict[str, Any]]) -> str:
    """Determine overall status from multiple sources"""
    # Priority: diagnosis > log analysis > default
    if diagnosis_data and 'diagnosis' in diagnosis_data:
        return diagnosis_data['diagnosis']
    
    if 'summary' in log_analysis_data:
        risk_level = log_analysis_data['summary'].get('risk_level', 'MEDIUM')
        if risk_level == 'HIGH':
            return 'FAIL'
        elif risk_level == 'LOW':
            return 'PASS'
        else:
            return 'UNCERTAIN'
    
    return 'UNCERTAIN'


def _generate_unified_recommendations(overall_status: str,
                                    component_correlations: List[ComponentCorrelation],
                                    failure_correlations: List[FailurePatternCorrelation],
                                    log_analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate unified recommendations from all sources"""
    recommendations = []
    
    # Status-based recommendations
    if overall_status == 'FAIL':
        recommendations.append({
            'priority': 'IMMEDIATE',
            'category': 'SAFETY',
            'action': 'Stop instrument operation immediately',
            'description': 'Critical issues detected across multiple data sources',
            'source': 'unified_analysis'
        })
    
    # Component-specific recommendations
    for component_corr in component_correlations:
        if component_corr.failure_associations:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'COMPONENT',
                'action': f'Investigate {component_corr.canonical_name}',
                'description': f'Component has {len(component_corr.failure_associations)} associated failure patterns',
                'source': 'component_correlation',
                'component': component_corr.canonical_name
            })
    
    # Failure pattern recommendations
    for failure_corr in failure_correlations:
        if failure_corr.severity in ['CRITICAL', 'HIGH'] and failure_corr.troubleshooting_procedures:
            procedure = failure_corr.troubleshooting_procedures[0]  # First/best procedure
            recommendations.append({
                'priority': 'HIGH' if failure_corr.severity == 'CRITICAL' else 'MEDIUM',
                'category': 'TROUBLESHOOTING',
                'action': f'Execute procedure: {procedure.get("title", "Unnamed")}',
                'description': f'Address {failure_corr.failure_pattern}',
                'source': 'failure_correlation',
                'procedure': procedure
            })
    
    # Sort by priority
    priority_order = {'IMMEDIATE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    return recommendations[:10]  # Limit to top 10


def _generate_executive_summary(unified_analysis: UnifiedAnalysis) -> Dict[str, Any]:
    """Generate executive summary of unified analysis"""
    return {
        'overall_status': unified_analysis.overall_status,
        'confidence_level': 'HIGH' if unified_analysis.confidence_level > 0.8 else 'MEDIUM' if unified_analysis.confidence_level > 0.6 else 'LOW',
        'key_findings': {
            'components_analyzed': len(unified_analysis.component_correlations),
            'failure_patterns_identified': len(unified_analysis.failure_correlations),
            'critical_issues': len([f for f in unified_analysis.failure_correlations if f.severity == 'CRITICAL']),
            'immediate_actions_required': len([r for r in unified_analysis.unified_recommendations if r['priority'] == 'IMMEDIATE'])
        },
        'data_consistency': unified_analysis.cross_source_consistency['overall_consistency'],
        'recommendation_summary': f"{len(unified_analysis.unified_recommendations)} actionable recommendations generated"
    }


def _extract_actionable_insights(unified_analysis: UnifiedAnalysis) -> List[Dict[str, Any]]:
    """Extract key actionable insights from unified analysis"""
    insights = []
    
    # Component insights
    high_risk_components = [c for c in unified_analysis.component_correlations 
                           if len(c.failure_associations) > 2]
    if high_risk_components:
        insights.append({
            'type': 'component_risk',
            'insight': f"{len(high_risk_components)} components have multiple failure associations",
            'action': 'Prioritize inspection of high-risk components',
            'components': [c.canonical_name for c in high_risk_components]
        })
    
    # Failure pattern insights
    critical_failures = [f for f in unified_analysis.failure_correlations if f.severity == 'CRITICAL']
    if critical_failures:
        insights.append({
            'type': 'critical_failures',
            'insight': f"{len(critical_failures)} critical failure patterns detected",
            'action': 'Address critical failures immediately',
            'patterns': [f.failure_pattern for f in critical_failures]
        })
    
    # Consistency insights
    if unified_analysis.cross_source_consistency['overall_consistency'] < 0.6:
        insights.append({
            'type': 'data_consistency',
            'insight': 'Low consistency between data sources detected',
            'action': 'Verify data quality and consider additional diagnostics',
            'consistency_score': unified_analysis.cross_source_consistency['overall_consistency']
        })
    
    return insights


def _assess_data_quality(log_analysis_data: Dict[str, Any],
                        component_correlations: Dict[str, Any],
                        failure_correlations: Dict[str, Any]) -> Dict[str, Any]:
    """Assess quality of input data sources"""
    quality_assessment = {}
    
    # Log analysis quality
    if 'analysis_summary' in log_analysis_data:
        total_patterns = log_analysis_data['analysis_summary'].get('total_patterns', 0)
        quality_assessment['log_analysis'] = {
            'quality': 'HIGH' if total_patterns > 5 else 'MEDIUM' if total_patterns > 0 else 'LOW',
            'patterns_detected': total_patterns,
            'completeness': 'COMPLETE' if 'chunk_details' in log_analysis_data else 'PARTIAL'
        }
    
    # Component correlation quality
    if 'correlation_summary' in component_correlations:
        corr_rate = component_correlations['correlation_summary'].get('correlation_rate', 0.0)
        quality_assessment['component_correlations'] = {
            'quality': 'HIGH' if corr_rate > 0.8 else 'MEDIUM' if corr_rate > 0.5 else 'LOW',
            'correlation_rate': corr_rate,
            'sources_analyzed': len(component_correlations['correlation_summary'].get('sources_analyzed', []))
        }
    
    # Failure correlation quality
    if 'correlation_statistics' in failure_correlations:
        fail_corr_rate = failure_correlations['correlation_statistics'].get('correlation_rate', 0.0)
        quality_assessment['failure_correlations'] = {
            'quality': 'HIGH' if fail_corr_rate > 0.7 else 'MEDIUM' if fail_corr_rate > 0.4 else 'LOW',
            'correlation_rate': fail_corr_rate,
            'procedures_matched': failure_correlations['correlation_statistics'].get('correlations_found', 0)
        }
    
    # Overall quality
    quality_scores = []
    for assessment in quality_assessment.values():
        if assessment['quality'] == 'HIGH':
            quality_scores.append(1.0)
        elif assessment['quality'] == 'MEDIUM':
            quality_scores.append(0.6)
        else:
            quality_scores.append(0.3)
    
    overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    quality_assessment['overall'] = {
        'quality': 'HIGH' if overall_quality > 0.8 else 'MEDIUM' if overall_quality > 0.5 else 'LOW',
        'score': overall_quality,
        'recommendation': 'Data quality is sufficient for reliable analysis' if overall_quality > 0.7 else 'Consider additional data collection for improved accuracy'
    }
    
    return quality_assessment


# List of available cross-source correlation tools
CROSS_SOURCE_CORRELATION_TOOLS = [
    correlate_components_across_sources,
    correlate_failures_to_procedures,
    generate_unified_analysis
]