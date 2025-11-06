"""
Component Recognition Tools for Instrument Diagnosis Assistant

These tools identify hardware and software components from documentation,
build component inventories, and manage component-function relationships.
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
class SystemComponent:
    """Represents a system component with its properties"""
    name: str
    component_type: str  # "hardware", "software", "firmware"
    function: str
    specifications: Dict[str, Any]
    related_components: List[str]
    aliases: List[str]
    failure_indicators: List[str]
    confidence: float


@dataclass
class ComponentInventory:
    """Complete inventory of system components"""
    components: List[SystemComponent]
    relationships: Dict[str, List[str]]
    component_count: Dict[str, int]
    extraction_metadata: Dict[str, Any]


class ComponentExtractor:
    """Core component extraction functionality"""
    
    def __init__(self):
        # Component identification patterns
        self.component_patterns = {
            'hardware': {
                'module_pattern': r'(?i)(\w+\s+(?:module|unit|system|array|sensor|detector))\s*\(([^)]+)\)',
                'device_pattern': r'(?i)(\w+(?:\s+\w+)*)\s*-\s*([A-Z0-9-]+)',
                'spec_pattern': r'(?i)(laser|detector|sensor|pump|valve|motor|controller|power|temperature)',
                'model_pattern': r'([A-Z]{2,}-[A-Z0-9]+|[A-Z]+\d+[A-Z]*|\w+-\d+)'
            },
            'software': {
                'software_pattern': r'(?i)(\w+(?:\s+\w+)*\s+(?:software|system|module|application))\s*\(([^)]+)\)',
                'version_pattern': r'(?i)(v\d+\.\d+(?:\.\d+)?|\d+\.\d+(?:\.\d+)?)',
                'module_pattern': r'(?i)(\w+\s+(?:module|interface|manager|processor|controller))',
                'framework_pattern': r'(?i)(\.NET\s+Framework|Windows|Linux|SQLite|USB|Ethernet)'
            }
        }
        
        # Function extraction patterns
        self.function_patterns = {
            'function_indicators': r'(?i)function[s]?:\s*([^.\n]+)',
            'purpose_indicators': r'(?i)(?:purpose|role|responsibility):\s*([^.\n]+)',
            'description_indicators': r'(?i)description:\s*([^.\n]+)',
            'manages_controls': r'(?i)(?:manages|controls|handles|processes|monitors)\s+([^.\n]+)'
        }
        
        # Specification extraction patterns
        self.spec_patterns = {
            'range_specs': r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*([A-Za-z%°]+)',
            'value_specs': r'([A-Za-z\s]+):\s*([0-9.±<>]+)\s*([A-Za-z%°/]+)',
            'performance_specs': r'(?i)(accuracy|precision|sensitivity|range|capacity|power|voltage|current):\s*([^.\n]+)'
        }
        
        # Relationship indicators
        self.relationship_patterns = {
            'related_components': r'(?i)related\s+components?:\s*([^.\n]+)',
            'dependencies': r'(?i)(?:depends\s+on|requires|needs):\s*([^.\n]+)',
            'interfaces_with': r'(?i)(?:interfaces?\s+with|connects?\s+to|communicates?\s+with):\s*([^.\n]+)'
        }
        
        # Failure indicator patterns
        self.failure_patterns = {
            'failure_indicators': r'(?i)failure\s+indicators?:\s*([^.\n]+)',
            'error_conditions': r'(?i)(?:error|fault|alarm)\s+conditions?:\s*([^.\n]+)',
            'warning_signs': r'(?i)warning\s+signs?:\s*([^.\n]+)'
        }
    
    def extract_components_from_text(self, text: str, doc_type: str = "engineering") -> List[SystemComponent]:
        """Extract components from document text"""
        components = []
        
        # Extract hardware components
        hardware_components = self._extract_hardware_components(text)
        components.extend(hardware_components)
        
        # Extract software components
        software_components = self._extract_software_components(text)
        components.extend(software_components)
        
        return components
    
    def _extract_hardware_components(self, text: str) -> List[SystemComponent]:
        """Extract hardware components from text"""
        components = []
        
        # Find component sections (typically marked by headers)
        sections = self._split_into_sections(text)
        
        for section_title, section_content in sections:
            if any(keyword in section_title.lower() for keyword in ['hardware', 'component', 'module', 'system']):
                # Extract individual components from this section
                component_blocks = self._extract_component_blocks(section_content)
                
                for block in component_blocks:
                    component = self._parse_hardware_component(block)
                    if component:
                        components.append(component)
        
        return components
    
    def _extract_software_components(self, text: str) -> List[SystemComponent]:
        """Extract software components from text"""
        components = []
        
        # Find software sections
        sections = self._split_into_sections(text)
        
        for section_title, section_content in sections:
            if any(keyword in section_title.lower() for keyword in ['software', 'application', 'program', 'system']):
                # Extract software components
                component_blocks = self._extract_component_blocks(section_content)
                
                for block in component_blocks:
                    component = self._parse_software_component(block)
                    if component:
                        components.append(component)
        
        return components
    
    def _split_into_sections(self, text: str) -> List[Tuple[str, str]]:
        """Split document into sections based on headers"""
        sections = []
        
        # Split by markdown headers or other section indicators
        lines = text.split('\n')
        current_section = ""
        current_title = "Introduction"
        
        for line in lines:
            # Check for markdown headers
            if line.startswith('#'):
                if current_section.strip():
                    sections.append((current_title, current_section))
                current_title = line.strip('#').strip()
                current_section = ""
            else:
                current_section += line + '\n'
        
        # Add final section
        if current_section.strip():
            sections.append((current_title, current_section))
        
        return sections
    
    def _extract_component_blocks(self, section_content: str) -> List[str]:
        """Extract individual component blocks from section content"""
        blocks = []
        
        # Split by component headers (### or component names with specifications)
        lines = section_content.split('\n')
        current_block = ""
        
        for line in lines:
            # Check for component start indicators
            if (line.startswith('###') or 
                re.search(r'(?i)^\w+(?:\s+\w+)*\s*\([^)]+\)', line.strip()) or
                re.search(r'(?i)^\*\*[^*]+\*\*', line.strip())):
                
                if current_block.strip():
                    blocks.append(current_block)
                current_block = line + '\n'
            else:
                current_block += line + '\n'
        
        # Add final block
        if current_block.strip():
            blocks.append(current_block)
        
        return blocks
    
    def _parse_hardware_component(self, block: str) -> Optional[SystemComponent]:
        """Parse a hardware component from a text block"""
        try:
            # Extract component name and model
            name_match = re.search(r'(?i)###\s*([^(]+)(?:\s*\(([^)]+)\))?', block)
            if not name_match:
                # Try alternative patterns
                name_match = re.search(r'(?i)\*\*([^*]+)\*\*', block)
            
            if not name_match:
                return None
            
            name = name_match.group(1).strip()
            model = name_match.group(2) if name_match.lastindex > 1 else ""
            
            # Extract function
            function = self._extract_function(block)
            
            # Extract specifications
            specifications = self._extract_specifications(block)
            
            # Extract related components
            related_components = self._extract_related_components(block)
            
            # Extract failure indicators
            failure_indicators = self._extract_failure_indicators(block)
            
            # Generate aliases
            aliases = self._generate_aliases(name, model)
            
            # Calculate confidence based on extracted information
            confidence = self._calculate_extraction_confidence(name, function, specifications)
            
            return SystemComponent(
                name=name,
                component_type="hardware",
                function=function,
                specifications=specifications,
                related_components=related_components,
                aliases=aliases,
                failure_indicators=failure_indicators,
                confidence=confidence
            )
            
        except Exception as e:
            logger.warning(f"Error parsing hardware component: {str(e)}")
            return None
    
    def _parse_software_component(self, block: str) -> Optional[SystemComponent]:
        """Parse a software component from a text block"""
        try:
            # Extract component name and version
            name_match = re.search(r'(?i)###\s*([^(]+)(?:\s*\(([^)]+)\))?', block)
            if not name_match:
                name_match = re.search(r'(?i)\*\*([^*]+)\*\*', block)
            
            if not name_match:
                return None
            
            name = name_match.group(1).strip()
            version = name_match.group(2) if name_match.lastindex > 1 else ""
            
            # Extract function
            function = self._extract_function(block)
            
            # Extract specifications (modules, dependencies, etc.)
            specifications = self._extract_software_specifications(block)
            
            # Extract related components
            related_components = self._extract_related_components(block)
            
            # Extract failure indicators
            failure_indicators = self._extract_failure_indicators(block)
            
            # Generate aliases
            aliases = self._generate_aliases(name, version)
            
            # Calculate confidence
            confidence = self._calculate_extraction_confidence(name, function, specifications)
            
            return SystemComponent(
                name=name,
                component_type="software",
                function=function,
                specifications=specifications,
                related_components=related_components,
                aliases=aliases,
                failure_indicators=failure_indicators,
                confidence=confidence
            )
            
        except Exception as e:
            logger.warning(f"Error parsing software component: {str(e)}")
            return None
    
    def _extract_function(self, block: str) -> str:
        """Extract component function from text block"""
        for pattern in self.function_patterns.values():
            match = re.search(pattern, block)
            if match:
                return match.group(1).strip()
        
        # Fallback: look for first sentence after component name
        lines = block.split('\n')
        for line in lines[1:]:  # Skip first line (component name)
            if line.strip() and not line.startswith('-') and not line.startswith('*'):
                return line.strip()
        
        return "Function not specified"
    
    def _extract_specifications(self, block: str) -> Dict[str, Any]:
        """Extract technical specifications from text block"""
        specs = {}
        
        # Extract range specifications
        for match in re.finditer(self.spec_patterns['range_specs'], block):
            min_val, max_val, unit = match.groups()
            key = f"range_{unit.lower()}"
            specs[key] = {"min": float(min_val), "max": float(max_val), "unit": unit}
        
        # Extract value specifications
        for match in re.finditer(self.spec_patterns['value_specs'], block):
            param, value, unit = match.groups()
            key = param.strip().lower().replace(' ', '_')
            specs[key] = {"value": value, "unit": unit}
        
        # Extract performance specifications
        for match in re.finditer(self.spec_patterns['performance_specs'], block):
            param, value = match.groups()
            key = param.strip().lower()
            specs[key] = value.strip()
        
        return specs
    
    def _extract_software_specifications(self, block: str) -> Dict[str, Any]:
        """Extract software-specific specifications"""
        specs = {}
        
        # Extract modules
        modules_match = re.search(r'(?i)modules?:\s*([^.\n]+)', block)
        if modules_match:
            modules = [m.strip() for m in modules_match.group(1).split(',')]
            specs['modules'] = modules
        
        # Extract dependencies
        deps_match = re.search(r'(?i)dependencies:\s*([^.\n]+)', block)
        if deps_match:
            dependencies = [d.strip() for d in deps_match.group(1).split(',')]
            specs['dependencies'] = dependencies
        
        # Extract version information
        version_match = re.search(self.component_patterns['software']['version_pattern'], block)
        if version_match:
            specs['version'] = version_match.group(0)
        
        return specs
    
    def _extract_related_components(self, block: str) -> List[str]:
        """Extract related components from text block"""
        related = []
        
        for pattern in self.relationship_patterns.values():
            match = re.search(pattern, block)
            if match:
                components = [c.strip() for c in match.group(1).split(',')]
                related.extend(components)
        
        return list(set(related))  # Remove duplicates
    
    def _extract_failure_indicators(self, block: str) -> List[str]:
        """Extract failure indicators from text block"""
        indicators = []
        
        for pattern in self.failure_patterns.values():
            match = re.search(pattern, block)
            if match:
                failure_items = [f.strip() for f in match.group(1).split(',')]
                indicators.extend(failure_items)
        
        return indicators
    
    def _generate_aliases(self, name: str, model_or_version: str) -> List[str]:
        """Generate aliases for component names"""
        aliases = []
        
        # Add model/version as alias
        if model_or_version:
            aliases.append(model_or_version)
        
        # Add acronym if name has multiple words
        words = name.split()
        if len(words) > 1:
            acronym = ''.join(word[0].upper() for word in words if word)
            aliases.append(acronym)
        
        # Add variations without common words
        common_words = {'system', 'module', 'unit', 'control', 'management', 'software'}
        filtered_name = ' '.join(word for word in words if word.lower() not in common_words)
        if filtered_name != name:
            aliases.append(filtered_name)
        
        return aliases
    
    def _calculate_extraction_confidence(self, name: str, function: str, specifications: Dict) -> float:
        """Calculate confidence score for extracted component"""
        confidence = 0.5  # Base confidence
        
        # Boost for clear name
        if name and len(name) > 3:
            confidence += 0.2
        
        # Boost for function description
        if function and function != "Function not specified":
            confidence += 0.2
        
        # Boost for specifications
        if specifications:
            confidence += min(0.3, len(specifications) * 0.05)
        
        return min(1.0, confidence)


# Initialize global extractor
_component_extractor = ComponentExtractor()


@tool(
    name="extract_components",
    description="Parse engineering documents to identify and extract hardware and software components"
)
def extract_components(
    document_content: str,
    document_type: str = "engineering",
    component_types: List[str] = None
) -> Dict[str, Any]:
    """
    Extract components from engineering documentation.
    
    Args:
        document_content: Raw text content of the engineering document
        document_type: Type of document ("engineering", "specification", "manual")
        component_types: List of component types to extract (["hardware", "software"])
    
    Returns:
        Dictionary containing extracted components and metadata
    """
    try:
        if not document_content or not document_content.strip():
            return {"error": "Empty or invalid document content provided"}
        
        # Set default component types if not specified
        if component_types is None:
            component_types = ["hardware", "software"]
        
        # Extract components
        all_components = _component_extractor.extract_components_from_text(document_content, document_type)
        
        # Filter by requested component types
        filtered_components = [
            comp for comp in all_components 
            if comp.component_type in component_types
        ]
        
        # Generate summary statistics
        component_stats = {
            'total_components': len(filtered_components),
            'hardware_components': len([c for c in filtered_components if c.component_type == "hardware"]),
            'software_components': len([c for c in filtered_components if c.component_type == "software"]),
            'avg_confidence': sum(c.confidence for c in filtered_components) / len(filtered_components) if filtered_components else 0
        }
        
        # Create component dictionary for easy lookup
        component_dict = {comp.name: asdict(comp) for comp in filtered_components}
        
        result = {
            'components': component_dict,
            'component_list': [asdict(comp) for comp in filtered_components],
            'statistics': component_stats,
            'extraction_metadata': {
                'document_type': document_type,
                'requested_types': component_types,
                'extraction_timestamp': str(Path().cwd()),  # Placeholder for timestamp
                'confidence_threshold': 0.5
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in extract_components: {str(e)}")
        return {"error": f"Component extraction failed: {str(e)}"}


@tool(
    name="map_functions",
    description="Associate components with their functions and create function-component mappings"
)
def map_functions(
    components_data: Dict[str, Any],
    function_categories: List[str] = None
) -> Dict[str, Any]:
    """
    Create mappings between components and their functions.
    
    Args:
        components_data: Output from extract_components tool
        function_categories: List of function categories to organize by
    
    Returns:
        Dictionary containing function mappings and analysis
    """
    try:
        if 'error' in components_data:
            return {"error": "Invalid components data provided"}
        
        components = components_data.get('component_list', [])
        if not components:
            return {"error": "No components found in provided data"}
        
        # Default function categories
        if function_categories is None:
            function_categories = [
                "control", "detection", "processing", "communication", 
                "storage", "analysis", "monitoring", "interface"
            ]
        
        # Create function mappings
        function_map = {}
        component_function_map = {}
        
        for component in components:
            comp_name = component['name']
            comp_function = component['function'].lower()
            
            # Categorize function
            category = _categorize_function(comp_function, function_categories)
            
            # Add to function map
            if category not in function_map:
                function_map[category] = []
            function_map[category].append({
                'component': comp_name,
                'function': component['function'],
                'type': component['component_type'],
                'confidence': component['confidence']
            })
            
            # Add to component-function map
            component_function_map[comp_name] = {
                'primary_function': component['function'],
                'function_category': category,
                'related_functions': _extract_related_functions(component['function'])
            }
        
        # Generate function analysis
        function_analysis = {
            'total_functions': len(component_function_map),
            'function_distribution': {cat: len(comps) for cat, comps in function_map.items()},
            'most_common_category': max(function_map.keys(), key=lambda k: len(function_map[k])) if function_map else None,
            'coverage_analysis': _analyze_function_coverage(function_map, function_categories)
        }
        
        result = {
            'function_mappings': function_map,
            'component_functions': component_function_map,
            'function_analysis': function_analysis,
            'categories_used': list(function_map.keys()),
            'mapping_metadata': {
                'total_components_mapped': len(components),
                'categories_available': function_categories,
                'mapping_confidence': _calculate_mapping_confidence(components)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in map_functions: {str(e)}")
        return {"error": f"Function mapping failed: {str(e)}"}


@tool(
    name="build_inventory",
    description="Create comprehensive component database with relationships and specifications"
)
def build_inventory(
    components_data: Dict[str, Any],
    function_mappings: Dict[str, Any] = None,
    include_relationships: bool = True
) -> Dict[str, Any]:
    """
    Build a comprehensive component inventory database.
    
    Args:
        components_data: Output from extract_components tool
        function_mappings: Output from map_functions tool (optional)
        include_relationships: Whether to include component relationships
    
    Returns:
        Dictionary containing complete component inventory
    """
    try:
        if 'error' in components_data:
            return {"error": "Invalid components data provided"}
        
        components = components_data.get('component_list', [])
        if not components:
            return {"error": "No components found in provided data"}
        
        # Build inventory structure
        inventory = {
            'components': {},
            'relationships': {},
            'specifications': {},
            'failure_indicators': {},
            'aliases': {}
        }
        
        # Process each component
        for component in components:
            comp_name = component['name']
            
            # Add component to inventory
            inventory['components'][comp_name] = {
                'name': comp_name,
                'type': component['component_type'],
                'function': component['function'],
                'confidence': component['confidence'],
                'aliases': component.get('aliases', [])
            }
            
            # Add specifications
            if component.get('specifications'):
                inventory['specifications'][comp_name] = component['specifications']
            
            # Add failure indicators
            if component.get('failure_indicators'):
                inventory['failure_indicators'][comp_name] = component['failure_indicators']
            
            # Add aliases mapping
            for alias in component.get('aliases', []):
                inventory['aliases'][alias] = comp_name
            
            # Add relationships if requested
            if include_relationships and component.get('related_components'):
                inventory['relationships'][comp_name] = component['related_components']
        
        # Add function mappings if provided
        if function_mappings and 'component_functions' in function_mappings:
            for comp_name, func_data in function_mappings['component_functions'].items():
                if comp_name in inventory['components']:
                    inventory['components'][comp_name]['function_category'] = func_data.get('function_category')
                    inventory['components'][comp_name]['related_functions'] = func_data.get('related_functions', [])
        
        # Generate inventory statistics
        stats = {
            'total_components': len(inventory['components']),
            'component_types': _count_by_type(components),
            'components_with_specs': len(inventory['specifications']),
            'components_with_failures': len(inventory['failure_indicators']),
            'total_relationships': sum(len(rels) for rels in inventory['relationships'].values()),
            'total_aliases': len(inventory['aliases'])
        }
        
        # Create lookup indices
        lookup_indices = {
            'by_type': _create_type_index(components),
            'by_function_category': _create_function_index(inventory['components']),
            'by_confidence': _create_confidence_index(components)
        }
        
        result = {
            'inventory': inventory,
            'statistics': stats,
            'lookup_indices': lookup_indices,
            'search_capabilities': {
                'component_search': True,
                'alias_resolution': True,
                'relationship_traversal': include_relationships,
                'specification_lookup': True,
                'failure_indicator_lookup': True
            },
            'inventory_metadata': {
                'build_timestamp': str(Path().cwd()),  # Placeholder
                'source_documents': 1,  # Could be enhanced to track multiple docs
                'total_data_points': len(components) + len(inventory['specifications']) + len(inventory['relationships'])
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in build_inventory: {str(e)}")
        return {"error": f"Inventory building failed: {str(e)}"}


# Helper functions

def _categorize_function(function_text: str, categories: List[str]) -> str:
    """Categorize a function based on keywords"""
    function_lower = function_text.lower()
    
    # Define category keywords
    category_keywords = {
        'control': ['control', 'manage', 'coordinate', 'regulate'],
        'detection': ['detect', 'sense', 'measure', 'capture', 'monitor'],
        'processing': ['process', 'analyze', 'compute', 'calculate', 'filter'],
        'communication': ['communicate', 'interface', 'connect', 'transmit'],
        'storage': ['store', 'save', 'database', 'memory', 'backup'],
        'analysis': ['analyze', 'evaluate', 'assess', 'interpret'],
        'monitoring': ['monitor', 'watch', 'track', 'observe'],
        'interface': ['interface', 'display', 'show', 'present', 'user']
    }
    
    # Find best matching category
    for category in categories:
        if category in category_keywords:
            keywords = category_keywords[category]
            if any(keyword in function_lower for keyword in keywords):
                return category
    
    return 'other'


def _extract_related_functions(function_text: str) -> List[str]:
    """Extract related functions from function description"""
    # Simple extraction based on common patterns
    related = []
    
    # Look for "and" connections
    if ' and ' in function_text.lower():
        parts = function_text.lower().split(' and ')
        related.extend([part.strip() for part in parts[1:]])
    
    # Look for comma-separated functions
    if ',' in function_text:
        parts = function_text.split(',')
        related.extend([part.strip() for part in parts[1:]])
    
    return related[:3]  # Limit to 3 related functions


def _analyze_function_coverage(function_map: Dict, categories: List[str]) -> Dict[str, Any]:
    """Analyze function coverage across categories"""
    covered_categories = set(function_map.keys())
    missing_categories = set(categories) - covered_categories
    
    return {
        'coverage_percentage': len(covered_categories) / len(categories) * 100,
        'covered_categories': list(covered_categories),
        'missing_categories': list(missing_categories),
        'well_covered': [cat for cat, comps in function_map.items() if len(comps) > 2]
    }


def _calculate_mapping_confidence(components: List[Dict]) -> float:
    """Calculate overall confidence for function mapping"""
    if not components:
        return 0.0
    
    confidences = [comp['confidence'] for comp in components]
    return sum(confidences) / len(confidences)


def _count_by_type(components: List[Dict]) -> Dict[str, int]:
    """Count components by type"""
    type_counts = {}
    for comp in components:
        comp_type = comp['component_type']
        type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
    return type_counts


def _create_type_index(components: List[Dict]) -> Dict[str, List[str]]:
    """Create index of components by type"""
    index = {}
    for comp in components:
        comp_type = comp['component_type']
        if comp_type not in index:
            index[comp_type] = []
        index[comp_type].append(comp['name'])
    return index


def _create_function_index(components_dict: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Create index of components by function category"""
    index = {}
    for comp_name, comp_data in components_dict.items():
        func_cat = comp_data.get('function_category', 'other')
        if func_cat not in index:
            index[func_cat] = []
        index[func_cat].append(comp_name)
    return index


def _create_confidence_index(components: List[Dict]) -> Dict[str, List[str]]:
    """Create index of components by confidence level"""
    index = {'high': [], 'medium': [], 'low': []}
    for comp in components:
        confidence = comp['confidence']
        if confidence > 0.8:
            index['high'].append(comp['name'])
        elif confidence > 0.6:
            index['medium'].append(comp['name'])
        else:
            index['low'].append(comp['name'])
    return index


# List of available component recognition tools
COMPONENT_RECOGNITION_TOOLS = [
    extract_components,
    map_functions,
    build_inventory
]

# Additional tools for component relationship management (Task 3.2)

class ComponentRelationshipManager:
    """Manages component relationships and naming variations"""
    
    def __init__(self):
        # Naming variation patterns
        self.naming_patterns = {
            'abbreviations': {
                'temperature': ['temp', 'tmp'],
                'control': ['ctrl', 'ctl'],
                'system': ['sys'],
                'module': ['mod'],
                'interface': ['if', 'intf'],
                'management': ['mgmt', 'mgr'],
                'processor': ['proc'],
                'detector': ['det'],
                'optical': ['opt']
            },
            'common_substitutions': {
                'centre': 'center',
                'colour': 'color',
                'analogue': 'analog',
                'programme': 'program'
            },
            'version_patterns': [
                r'v\d+\.\d+',
                r'\d+\.\d+',
                r'ver\s*\d+',
                r'version\s*\d+'
            ]
        }
        
        # Relationship types
        self.relationship_types = {
            'depends_on': 'Component requires another component to function',
            'controls': 'Component manages or controls another component',
            'interfaces_with': 'Component communicates with another component',
            'contains': 'Component physically contains another component',
            'monitors': 'Component observes or tracks another component',
            'processes_data_from': 'Component handles data from another component'
        }
    
    def resolve_naming_variations(self, component_name: str, known_components: List[str]) -> List[str]:
        """Find potential matches for component name variations"""
        matches = []
        name_lower = component_name.lower()
        
        for known_comp in known_components:
            known_lower = known_comp.lower()
            
            # Exact match
            if name_lower == known_lower:
                matches.append((known_comp, 1.0, 'exact_match'))
                continue
            
            # Check abbreviations
            similarity = self._check_abbreviation_match(name_lower, known_lower)
            if similarity > 0.8:
                matches.append((known_comp, similarity, 'abbreviation_match'))
            
            # Check common substitutions
            similarity = self._check_substitution_match(name_lower, known_lower)
            if similarity > 0.8:
                matches.append((known_comp, similarity, 'substitution_match'))
            
            # Check partial matches
            similarity = self._calculate_partial_similarity(name_lower, known_lower)
            if similarity > 0.7:
                matches.append((known_comp, similarity, 'partial_match'))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]  # Return top 5 matches
    
    def _check_abbreviation_match(self, name1: str, name2: str) -> float:
        """Check if names match through abbreviation patterns"""
        # Check if one is abbreviation of the other
        for full_word, abbrevs in self.naming_patterns['abbreviations'].items():
            for abbrev in abbrevs:
                if (abbrev in name1 and full_word in name2) or (abbrev in name2 and full_word in name1):
                    return 0.9
        return 0.0
    
    def _check_substitution_match(self, name1: str, name2: str) -> float:
        """Check if names match through common substitutions"""
        for original, substitute in self.naming_patterns['common_substitutions'].items():
            name1_sub = name1.replace(original, substitute)
            name2_sub = name2.replace(original, substitute)
            if name1_sub == name2_sub:
                return 0.95
        return 0.0
    
    def _calculate_partial_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity based on common words"""
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        return len(common_words) / len(total_words)
    
    def infer_relationships(self, components: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Infer relationships between components based on their properties"""
        relationships = {}
        
        for comp in components:
            comp_name = comp['name']
            relationships[comp_name] = []
            
            # Check explicit relationships
            if comp.get('related_components'):
                for related in comp['related_components']:
                    relationships[comp_name].append({
                        'target': related,
                        'type': 'explicitly_related',
                        'confidence': 0.9,
                        'source': 'documentation'
                    })
            
            # Infer relationships from function and type
            inferred_rels = self._infer_from_function(comp, components)
            relationships[comp_name].extend(inferred_rels)
        
        return relationships
    
    def _infer_from_function(self, component: Dict[str, Any], all_components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer relationships based on component function"""
        relationships = []
        comp_function = component['function'].lower()
        comp_name = component['name']
        
        for other_comp in all_components:
            if other_comp['name'] == comp_name:
                continue
            
            other_function = other_comp['function'].lower()
            
            # Control relationships
            if 'control' in comp_function and any(word in other_function for word in ['temperature', 'pressure', 'flow']):
                relationships.append({
                    'target': other_comp['name'],
                    'type': 'controls',
                    'confidence': 0.7,
                    'source': 'function_inference'
                })
            
            # Processing relationships
            if 'process' in comp_function and 'detect' in other_function:
                relationships.append({
                    'target': other_comp['name'],
                    'type': 'processes_data_from',
                    'confidence': 0.6,
                    'source': 'function_inference'
                })
            
            # Interface relationships
            if 'interface' in comp_function or 'communication' in comp_function:
                relationships.append({
                    'target': other_comp['name'],
                    'type': 'interfaces_with',
                    'confidence': 0.5,
                    'source': 'function_inference'
                })
        
        return relationships


# Initialize global relationship manager
_relationship_manager = ComponentRelationshipManager()


@tool(
    name="resolve_naming",
    description="Handle component naming variations and find matches across different naming conventions"
)
def resolve_naming(
    target_component: str,
    component_inventory: Dict[str, Any],
    similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Resolve naming variations and find component matches.
    
    Args:
        target_component: Component name to resolve
        component_inventory: Output from build_inventory tool
        similarity_threshold: Minimum similarity score for matches (0.0-1.0)
    
    Returns:
        Dictionary containing naming resolution results and matches
    """
    try:
        if 'error' in component_inventory:
            return {"error": "Invalid component inventory provided"}
        
        inventory = component_inventory.get('inventory', {})
        known_components = list(inventory.get('components', {}).keys())
        aliases = inventory.get('aliases', {})
        
        if not known_components:
            return {"error": "No components found in inventory"}
        
        # Check direct alias match first
        if target_component in aliases:
            return {
                'resolved_name': aliases[target_component],
                'match_type': 'direct_alias',
                'confidence': 1.0,
                'alternatives': [],
                'resolution_successful': True
            }
        
        # Check exact match
        if target_component in known_components:
            return {
                'resolved_name': target_component,
                'match_type': 'exact_match',
                'confidence': 1.0,
                'alternatives': [],
                'resolution_successful': True
            }
        
        # Find naming variations
        matches = _relationship_manager.resolve_naming_variations(target_component, known_components)
        
        # Filter by threshold
        valid_matches = [(name, score, match_type) for name, score, match_type in matches if score >= similarity_threshold]
        
        if valid_matches:
            best_match = valid_matches[0]
            alternatives = valid_matches[1:5]  # Up to 4 alternatives
            
            result = {
                'resolved_name': best_match[0],
                'match_type': best_match[2],
                'confidence': best_match[1],
                'alternatives': [
                    {
                        'name': alt[0],
                        'confidence': alt[1],
                        'match_type': alt[2]
                    }
                    for alt in alternatives
                ],
                'resolution_successful': True
            }
        else:
            result = {
                'resolved_name': None,
                'match_type': 'no_match',
                'confidence': 0.0,
                'alternatives': [],
                'resolution_successful': False,
                'suggestions': _generate_naming_suggestions(target_component, known_components)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in resolve_naming: {str(e)}")
        return {"error": f"Naming resolution failed: {str(e)}"}


@tool(
    name="correlate_components",
    description="Establish and track relationships between components based on their interactions and dependencies"
)
def correlate_components(
    component_inventory: Dict[str, Any],
    relationship_sources: List[str] = None,
    include_inferred: bool = True
) -> Dict[str, Any]:
    """
    Correlate components and establish relationships.
    
    Args:
        component_inventory: Output from build_inventory tool
        relationship_sources: Sources to consider ("documentation", "function_inference", "specification_analysis")
        include_inferred: Whether to include inferred relationships
    
    Returns:
        Dictionary containing component correlations and relationship analysis
    """
    try:
        if 'error' in component_inventory:
            return {"error": "Invalid component inventory provided"}
        
        inventory = component_inventory.get('inventory', {})
        components_dict = inventory.get('components', {})
        
        if not components_dict:
            return {"error": "No components found in inventory"}
        
        # Convert to list format for processing
        components_list = [
            {**comp_data, 'related_components': inventory.get('relationships', {}).get(comp_name, [])}
            for comp_name, comp_data in components_dict.items()
        ]
        
        # Set default relationship sources
        if relationship_sources is None:
            relationship_sources = ["documentation", "function_inference"]
        
        # Infer relationships
        all_relationships = _relationship_manager.infer_relationships(components_list)
        
        # Filter relationships by source
        filtered_relationships = {}
        for comp_name, relationships in all_relationships.items():
            filtered_rels = []
            for rel in relationships:
                if rel['source'] in relationship_sources:
                    if rel['source'] == 'function_inference' and not include_inferred:
                        continue
                    filtered_rels.append(rel)
            filtered_relationships[comp_name] = filtered_rels
        
        # Analyze relationship patterns
        relationship_analysis = _analyze_relationships(filtered_relationships, components_dict)
        
        # Create relationship matrix
        relationship_matrix = _create_relationship_matrix(filtered_relationships, list(components_dict.keys()))
        
        # Identify component clusters
        clusters = _identify_component_clusters(filtered_relationships, components_dict)
        
        result = {
            'component_relationships': filtered_relationships,
            'relationship_matrix': relationship_matrix,
            'relationship_analysis': relationship_analysis,
            'component_clusters': clusters,
            'correlation_metadata': {
                'total_components': len(components_dict),
                'total_relationships': sum(len(rels) for rels in filtered_relationships.values()),
                'relationship_sources_used': relationship_sources,
                'inferred_relationships_included': include_inferred,
                'relationship_density': _calculate_relationship_density(filtered_relationships, len(components_dict))
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in correlate_components: {str(e)}")
        return {"error": f"Component correlation failed: {str(e)}"}


@tool(
    name="search_components",
    description="Search and lookup components with advanced filtering and relationship traversal"
)
def search_components(
    component_inventory: Dict[str, Any],
    search_query: str = "",
    search_type: str = "name",
    filters: Dict[str, Any] = None,
    include_relationships: bool = False
) -> Dict[str, Any]:
    """
    Search components with advanced filtering capabilities.
    
    Args:
        component_inventory: Output from build_inventory tool
        search_query: Search term or query
        search_type: Type of search ("name", "function", "type", "specification")
        filters: Additional filters (type, confidence, etc.)
        include_relationships: Whether to include related components in results
    
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        if 'error' in component_inventory:
            return {"error": "Invalid component inventory provided"}
        
        inventory = component_inventory.get('inventory', {})
        components = inventory.get('components', {})
        specifications = inventory.get('specifications', {})
        aliases = inventory.get('aliases', {})
        relationships = inventory.get('relationships', {})
        
        if not components:
            return {"error": "No components found in inventory"}
        
        # Set default filters
        if filters is None:
            filters = {}
        
        # Perform search based on type
        search_results = []
        
        if search_type == "name":
            search_results = _search_by_name(search_query, components, aliases)
        elif search_type == "function":
            search_results = _search_by_function(search_query, components)
        elif search_type == "type":
            search_results = _search_by_type(search_query, components)
        elif search_type == "specification":
            search_results = _search_by_specification(search_query, components, specifications)
        else:
            # General search across all fields
            search_results = _general_search(search_query, components, specifications, aliases)
        
        # Apply filters
        filtered_results = _apply_search_filters(search_results, filters)
        
        # Add relationship information if requested
        if include_relationships:
            for result in filtered_results:
                comp_name = result['name']
                result['relationships'] = relationships.get(comp_name, [])
                result['related_components'] = [rel['target'] for rel in result['relationships']]
        
        # Generate search metadata
        search_metadata = {
            'query': search_query,
            'search_type': search_type,
            'total_results': len(filtered_results),
            'filters_applied': filters,
            'relationships_included': include_relationships
        }
        
        result = {
            'search_results': filtered_results,
            'search_metadata': search_metadata,
            'suggestions': _generate_search_suggestions(search_query, components) if len(filtered_results) == 0 else []
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_components: {str(e)}")
        return {"error": f"Component search failed: {str(e)}"}


# Helper functions for relationship management

def _generate_naming_suggestions(target: str, known_components: List[str]) -> List[str]:
    """Generate naming suggestions for unresolved components"""
    suggestions = []
    target_words = set(target.lower().split())
    
    for comp in known_components:
        comp_words = set(comp.lower().split())
        if target_words.intersection(comp_words):
            suggestions.append(comp)
    
    return suggestions[:3]


def _analyze_relationships(relationships: Dict[str, List[Dict]], components: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze relationship patterns"""
    total_rels = sum(len(rels) for rels in relationships.values())
    
    # Count relationship types
    type_counts = {}
    for rels in relationships.values():
        for rel in rels:
            rel_type = rel['type']
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
    
    # Find most connected components
    connection_counts = {comp: len(rels) for comp, rels in relationships.items()}
    most_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total_relationships': total_rels,
        'relationship_types': type_counts,
        'most_connected_components': most_connected,
        'average_connections_per_component': total_rels / len(components) if components else 0
    }


def _create_relationship_matrix(relationships: Dict[str, List[Dict]], component_names: List[str]) -> Dict[str, Dict[str, str]]:
    """Create a relationship matrix"""
    matrix = {}
    
    for comp1 in component_names:
        matrix[comp1] = {}
        for comp2 in component_names:
            if comp1 == comp2:
                matrix[comp1][comp2] = "self"
            else:
                # Find relationship type
                rel_type = "none"
                if comp1 in relationships:
                    for rel in relationships[comp1]:
                        if rel['target'] == comp2:
                            rel_type = rel['type']
                            break
                matrix[comp1][comp2] = rel_type
    
    return matrix


def _identify_component_clusters(relationships: Dict[str, List[Dict]], components: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Identify clusters of related components"""
    clusters = []
    visited = set()
    
    for comp_name in components.keys():
        if comp_name not in visited:
            cluster = _find_connected_components(comp_name, relationships, visited)
            if len(cluster) > 1:  # Only include clusters with multiple components
                clusters.append({
                    'cluster_id': len(clusters) + 1,
                    'components': cluster,
                    'size': len(cluster),
                    'primary_component': cluster[0]  # Component with most connections
                })
    
    return clusters


def _find_connected_components(start_comp: str, relationships: Dict[str, List[Dict]], visited: Set[str]) -> List[str]:
    """Find all components connected to the starting component"""
    cluster = []
    to_visit = [start_comp]
    
    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        
        visited.add(current)
        cluster.append(current)
        
        # Add related components
        if current in relationships:
            for rel in relationships[current]:
                target = rel['target']
                if target not in visited:
                    to_visit.append(target)
    
    return cluster


def _calculate_relationship_density(relationships: Dict[str, List[Dict]], num_components: int) -> float:
    """Calculate relationship density (actual relationships / possible relationships)"""
    if num_components <= 1:
        return 0.0
    
    actual_relationships = sum(len(rels) for rels in relationships.values())
    possible_relationships = num_components * (num_components - 1)  # Directed relationships
    
    return actual_relationships / possible_relationships if possible_relationships > 0 else 0.0


def _search_by_name(query: str, components: Dict[str, Dict], aliases: Dict[str, str]) -> List[Dict[str, Any]]:
    """Search components by name"""
    results = []
    query_lower = query.lower()
    
    for comp_name, comp_data in components.items():
        if query_lower in comp_name.lower():
            results.append({**comp_data, 'match_score': 1.0 if query_lower == comp_name.lower() else 0.8})
    
    # Check aliases
    for alias, comp_name in aliases.items():
        if query_lower in alias.lower() and comp_name in components:
            comp_data = components[comp_name]
            results.append({**comp_data, 'match_score': 0.9, 'matched_via': f'alias: {alias}'})
    
    return results


def _search_by_function(query: str, components: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Search components by function"""
    results = []
    query_lower = query.lower()
    
    for comp_name, comp_data in components.items():
        function = comp_data.get('function', '').lower()
        if query_lower in function:
            results.append({**comp_data, 'match_score': 0.8})
    
    return results


def _search_by_type(query: str, components: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Search components by type"""
    results = []
    query_lower = query.lower()
    
    for comp_name, comp_data in components.items():
        comp_type = comp_data.get('type', '').lower()
        if query_lower == comp_type:
            results.append({**comp_data, 'match_score': 1.0})
    
    return results


def _search_by_specification(query: str, components: Dict[str, Dict], specifications: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Search components by specifications"""
    results = []
    query_lower = query.lower()
    
    for comp_name, comp_data in components.items():
        if comp_name in specifications:
            specs = specifications[comp_name]
            spec_text = json.dumps(specs).lower()
            if query_lower in spec_text:
                results.append({**comp_data, 'match_score': 0.7})
    
    return results


def _general_search(query: str, components: Dict[str, Dict], specifications: Dict[str, Dict], aliases: Dict[str, str]) -> List[Dict[str, Any]]:
    """General search across all fields"""
    results = []
    
    # Combine all search types
    results.extend(_search_by_name(query, components, aliases))
    results.extend(_search_by_function(query, components))
    results.extend(_search_by_specification(query, components, specifications))
    
    # Remove duplicates and sort by match score
    seen = set()
    unique_results = []
    for result in results:
        comp_name = result['name']
        if comp_name not in seen:
            seen.add(comp_name)
            unique_results.append(result)
    
    return sorted(unique_results, key=lambda x: x.get('match_score', 0), reverse=True)


def _apply_search_filters(results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply filters to search results"""
    filtered = results
    
    if 'type' in filters:
        filtered = [r for r in filtered if r.get('type') == filters['type']]
    
    if 'min_confidence' in filters:
        filtered = [r for r in filtered if r.get('confidence', 0) >= filters['min_confidence']]
    
    if 'max_results' in filters:
        filtered = filtered[:filters['max_results']]
    
    return filtered


def _generate_search_suggestions(query: str, components: Dict[str, Dict]) -> List[str]:
    """Generate search suggestions for empty results"""
    suggestions = []
    
    # Suggest component types
    types = set(comp.get('type', '') for comp in components.values())
    suggestions.extend([f"type:{t}" for t in types if t])
    
    # Suggest common function keywords
    functions = [comp.get('function', '') for comp in components.values()]
    common_words = set()
    for func in functions:
        common_words.update(func.lower().split())
    
    suggestions.extend(list(common_words)[:5])
    
    return suggestions


# Update the tools list to include new tools
COMPONENT_RECOGNITION_TOOLS.extend([
    resolve_naming,
    correlate_components,
    search_components
])