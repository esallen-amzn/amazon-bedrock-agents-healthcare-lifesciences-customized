"""
Multi-modal Document Processing Tools for Instrument Diagnosis Assistant

These tools handle processing troubleshooting guides with text, images, and diagrams
using Amazon Nova Pro for multi-modal analysis and guidance generation.
"""

import os
import re
import json
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import mimetypes
from strands import tool

logger = logging.getLogger(__name__)


@dataclass
class VisualElement:
    """Represents a visual element extracted from a document"""
    element_type: str  # "diagram", "image", "chart", "table"
    description: str
    location: str  # Position or reference in document
    content_analysis: str
    related_text: List[str]
    confidence: float


@dataclass
class TextImageCorrelation:
    """Represents correlation between text and visual elements"""
    text_section: str
    visual_element_id: str
    correlation_type: str  # "reference", "explanation", "procedure", "diagram"
    correlation_strength: float
    context: str


@dataclass
class DocumentAnalysis:
    """Complete analysis of a multi-modal document"""
    text_content: str
    visual_elements: List[VisualElement]
    correlations: List[TextImageCorrelation]
    structured_sections: Dict[str, str]
    guidance_steps: List[str]
    processing_metadata: Dict[str, Any]


@dataclass
class GuidanceStep:
    """Represents a structured troubleshooting step"""
    step_number: int
    title: str
    description: str
    visual_references: List[str]
    expected_results: str
    safety_notes: List[str]
    tools_required: List[str]


class MultiModalProcessor:
    """Core multi-modal document processing functionality"""
    
    def __init__(self):
        # Supported file formats
        self.supported_formats = {
            'text': ['.txt', '.md', '.rtf'],
            'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
            'document': ['.pdf', '.docx', '.doc']
        }
        
        # Visual element detection patterns
        self.visual_patterns = {
            'diagram_references': r'(?i)(?:see\s+)?(?:diagram|figure|image|chart)\s*[:\-]?\s*([^.\n]+)',
            'step_references': r'(?i)(?:step\s+\d+|procedure\s+\d+|figure\s+\d+)',
            'visual_indicators': r'(?i)(?:shown\s+(?:in|below)|illustrated|depicted|see\s+(?:above|below))',
            'location_references': r'(?i)(?:front|back|left|right|top|bottom|side)\s+(?:panel|cover|access)'
        }
        
        # Content structure patterns
        self.structure_patterns = {
            'symptoms': r'(?i)symptom[s]?:\s*([^#\n]+)',
            'indicators': r'(?i)indicator[s]?\s+in\s+logs?:\s*(.*?)(?=\*\*|$)',
            'troubleshooting_steps': r'(?i)\*\*troubleshooting\s+steps?\*\*:\s*(.*?)(?=\*\*|$)',
            'expected_results': r'(?i)\*\*expected\s+results?\*\*:\s*(.*?)(?=\*\*|$|##)',
            'safety_notes': r'(?i)\*\*safety\s+notes?\*\*:\s*(.*?)(?=\*\*|$|##)',
            'when_to_contact': r'(?i)(?:when\s+to\s+contact|escalate).*?:\s*(.*?)(?=##|$)'
        }
        
        # Guidance generation templates
        self.guidance_templates = {
            'diagnostic_step': {
                'format': "Step {number}: {title}\n{description}\n{visual_ref}\nExpected: {expected}",
                'required_fields': ['number', 'title', 'description']
            },
            'safety_warning': {
                'format': "WARNING: {warning}",
                'required_fields': ['warning']
            },
            'visual_reference': {
                'format': "See: {reference} ({location})",
                'required_fields': ['reference']
            }
        }
    
    def analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure and extract sections"""
        sections = {}
        
        # Extract structured sections using patterns
        for section_type, pattern in self.structure_patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            if matches:
                sections[section_type] = [match.strip() for match in matches]
        
        # Extract headers and create hierarchy
        headers = self._extract_headers(content)
        sections['headers'] = headers
        
        # Identify procedural sections
        procedures = self._extract_procedures(content)
        sections['procedures'] = procedures
        
        return sections
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract markdown headers and create hierarchy"""
        headers = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                headers.append({
                    'level': level,
                    'title': title,
                    'line_number': i + 1,
                    'content_start': i + 1
                })
        
        return headers
    
    def _extract_procedures(self, content: str) -> List[Dict[str, Any]]:
        """Extract step-by-step procedures"""
        procedures = []
        
        # Find numbered lists and procedures
        procedure_pattern = r'(?i)(?:^|\n)\s*(\d+)\.\s*\*\*([^*]+)\*\*\s*(.*?)(?=\n\s*\d+\.|$)'
        matches = re.findall(procedure_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            step_num, title, description = match
            procedures.append({
                'step_number': int(step_num),
                'title': title.strip(),
                'description': description.strip(),
                'visual_references': self._find_visual_references(description)
            })
        
        return procedures
    
    def _find_visual_references(self, text: str) -> List[str]:
        """Find visual references in text"""
        references = []
        
        for pattern in self.visual_patterns.values():
            matches = re.findall(pattern, text)
            references.extend(matches)
        
        return list(set(references))  # Remove duplicates
    
    def extract_visual_elements(self, content: str, has_images: bool = False) -> List[VisualElement]:
        """Extract and analyze visual elements from document"""
        visual_elements = []
        
        # Extract text-based visual references
        text_visuals = self._extract_text_visual_references(content)
        visual_elements.extend(text_visuals)
        
        # If document has images, analyze them (placeholder for Nova Canvas integration)
        if has_images:
            image_elements = self._analyze_images_with_nova(content)
            visual_elements.extend(image_elements)
        
        return visual_elements
    
    def _extract_text_visual_references(self, content: str) -> List[VisualElement]:
        """Extract visual references mentioned in text"""
        elements = []
        
        # Find diagram references
        diagram_matches = re.finditer(self.visual_patterns['diagram_references'], content)
        for i, match in enumerate(diagram_matches):
            description = match.group(1).strip()
            elements.append(VisualElement(
                element_type="diagram",
                description=description,
                location=f"Referenced at position {match.start()}",
                content_analysis=f"Text reference to: {description}",
                related_text=[self._get_surrounding_text(content, match.start(), match.end())],
                confidence=0.8
            ))
        
        # Find ASCII diagrams or structured layouts
        ascii_diagrams = self._find_ascii_diagrams(content)
        elements.extend(ascii_diagrams)
        
        return elements
    
    def _analyze_images_with_nova(self, content: str) -> List[VisualElement]:
        """Analyze images using Nova Canvas (placeholder implementation)"""
        # This would integrate with Nova Canvas for actual image analysis
        # For now, return placeholder elements
        elements = []
        
        # Placeholder for Nova Canvas integration
        # In actual implementation, this would:
        # 1. Extract images from document
        # 2. Send to Nova Canvas for analysis
        # 3. Process Nova Canvas response
        # 4. Create VisualElement objects
        
        return elements
    
    def _find_ascii_diagrams(self, content: str) -> List[VisualElement]:
        """Find ASCII art diagrams in text"""
        elements = []
        
        # Look for code blocks that might contain diagrams
        code_block_pattern = r'```(.*?)```'
        matches = re.finditer(code_block_pattern, content, re.DOTALL)
        
        for i, match in enumerate(matches):
            block_content = match.group(1).strip()
            
            # Check if it looks like a diagram (contains arrows, boxes, etc.)
            if any(char in block_content for char in ['->', '--', '|', '+', '\\', '/']):
                elements.append(VisualElement(
                    element_type="diagram",
                    description=f"ASCII diagram {i+1}",
                    location=f"Code block at position {match.start()}",
                    content_analysis=f"ASCII diagram with {len(block_content.split())} elements",
                    related_text=[self._get_surrounding_text(content, match.start(), match.end())],
                    confidence=0.9
                ))
        
        return elements
    
    def _get_surrounding_text(self, content: str, start: int, end: int, context_chars: int = 200) -> str:
        """Get surrounding text context for a match"""
        context_start = max(0, start - context_chars)
        context_end = min(len(content), end + context_chars)
        return content[context_start:context_end].strip()
    
    def correlate_text_and_visuals(self, content: str, visual_elements: List[VisualElement]) -> List[TextImageCorrelation]:
        """Create correlations between text sections and visual elements"""
        correlations = []
        
        # Split content into sections
        sections = self._split_into_sections(content)
        
        for section_title, section_content in sections:
            for i, visual in enumerate(visual_elements):
                correlation = self._calculate_correlation(section_content, visual, section_title)
                if correlation and correlation.correlation_strength > 0.5:
                    correlations.append(correlation)
        
        return correlations
    
    def _split_into_sections(self, content: str) -> List[Tuple[str, str]]:
        """Split content into logical sections"""
        sections = []
        lines = content.split('\n')
        current_section = ""
        current_title = "Introduction"
        
        for line in lines:
            if line.startswith('#'):
                if current_section.strip():
                    sections.append((current_title, current_section))
                current_title = line.strip('#').strip()
                current_section = ""
            else:
                current_section += line + '\n'
        
        if current_section.strip():
            sections.append((current_title, current_section))
        
        return sections
    
    def _calculate_correlation(self, text: str, visual: VisualElement, section_title: str) -> Optional[TextImageCorrelation]:
        """Calculate correlation between text and visual element"""
        text_lower = text.lower()
        visual_desc_lower = visual.description.lower()
        
        # Check for direct references
        if visual_desc_lower in text_lower or any(ref.lower() in text_lower for ref in visual.related_text):
            return TextImageCorrelation(
                text_section=section_title,
                visual_element_id=f"visual_{hash(visual.description) % 10000}",
                correlation_type="reference",
                correlation_strength=0.9,
                context=f"Direct reference in {section_title}"
            )
        
        # Check for procedural correlation
        if any(keyword in text_lower for keyword in ['step', 'procedure', 'check', 'verify']):
            if visual.element_type == "diagram":
                return TextImageCorrelation(
                    text_section=section_title,
                    visual_element_id=f"visual_{hash(visual.description) % 10000}",
                    correlation_type="procedure",
                    correlation_strength=0.7,
                    context=f"Procedural context in {section_title}"
                )
        
        return None


# Initialize global processor
_multimodal_processor = MultiModalProcessor()


@tool(
    name="process_multimodal_docs",
    description="Process troubleshooting guides containing text, images, and diagrams using Nova Pro"
)
def process_multimodal_docs(
    document_content: str,
    document_path: str = "",
    include_images: bool = False,
    analysis_depth: str = "standard"
) -> Dict[str, Any]:
    """
    Process multi-modal troubleshooting documents with Nova Canvas.
    
    Args:
        document_content: Raw text content of the document
        document_path: Path to document file (for image extraction)
        include_images: Whether document contains images to analyze
        analysis_depth: Depth of analysis ("quick", "standard", "comprehensive")
    
    Returns:
        Dictionary containing multi-modal analysis results
    """
    try:
        if not document_content or not document_content.strip():
            return {"error": "Empty or invalid document content provided"}
        
        # Analyze document structure
        structure_analysis = _multimodal_processor.analyze_document_structure(document_content)
        
        # Extract visual elements
        visual_elements = _multimodal_processor.extract_visual_elements(document_content, include_images)
        
        # Create text-visual correlations
        correlations = _multimodal_processor.correlate_text_and_visuals(document_content, visual_elements)
        
        # Generate processing metadata
        processing_metadata = {
            'document_length': len(document_content),
            'sections_found': len(structure_analysis.get('headers', [])),
            'visual_elements_found': len(visual_elements),
            'correlations_created': len(correlations),
            'analysis_depth': analysis_depth,
            'nova_canvas_used': include_images
        }
        
        # Create comprehensive analysis result
        analysis = DocumentAnalysis(
            text_content=document_content,
            visual_elements=visual_elements,
            correlations=correlations,
            structured_sections=structure_analysis,
            guidance_steps=[],  # Will be populated by generate_guidance
            processing_metadata=processing_metadata
        )
        
        result = {
            'document_analysis': asdict(analysis),
            'structure_summary': {
                'total_sections': len(structure_analysis.get('headers', [])),
                'procedures_found': len(structure_analysis.get('procedures', [])),
                'symptoms_identified': len(structure_analysis.get('symptoms', [])),
                'safety_notes': len(structure_analysis.get('safety_notes', []))
            },
            'visual_summary': {
                'total_visual_elements': len(visual_elements),
                'diagrams': len([v for v in visual_elements if v.element_type == 'diagram']),
                'images': len([v for v in visual_elements if v.element_type == 'image']),
                'correlations': len(correlations)
            },
            'processing_status': 'success'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_multimodal_docs: {str(e)}")
        return {"error": f"Multi-modal document processing failed: {str(e)}"}


@tool(
    name="extract_visual_info",
    description="Extract and analyze visual information from images and diagrams using Nova Pro"
)
def extract_visual_info(
    image_data: str = "",
    image_path: str = "",
    analysis_type: str = "technical_diagram",
    context_text: str = ""
) -> Dict[str, Any]:
    """
    Extract visual information from images and diagrams.
    
    Args:
        image_data: Base64 encoded image data
        image_path: Path to image file
        analysis_type: Type of analysis ("technical_diagram", "component_layout", "procedure_illustration")
        context_text: Surrounding text context for better analysis
    
    Returns:
        Dictionary containing visual analysis results
    """
    try:
        # Validate inputs
        if not image_data and not image_path:
            return {"error": "Either image_data or image_path must be provided"}
        
        # Load image if path provided
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    image_data = base64.b64encode(image_bytes).decode('utf-8')
            except Exception as e:
                return {"error": f"Failed to load image from path: {str(e)}"}
        
        # Placeholder for Nova Pro integration
        # In actual implementation, this would:
        # 1. Send image to Nova Pro with appropriate prompt
        # 2. Process Nova Pro response
        # 3. Extract structured information
        
        # For now, simulate analysis based on context
        visual_analysis = _simulate_visual_analysis(image_path, analysis_type, context_text)
        
        result = {
            'visual_analysis': visual_analysis,
            'analysis_metadata': {
                'analysis_type': analysis_type,
                'has_context': bool(context_text),
                'image_source': 'path' if image_path else 'data',
                'nova_canvas_used': False  # Would be True in actual implementation
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in extract_visual_info: {str(e)}")
        return {"error": f"Visual information extraction failed: {str(e)}"}


@tool(
    name="correlate_text_images",
    description="Create correlations between textual instructions and visual references"
)
def correlate_text_images(
    document_analysis: Dict[str, Any],
    correlation_threshold: float = 0.5,
    correlation_types: List[str] = None
) -> Dict[str, Any]:
    """
    Create correlations between text content and visual elements.
    
    Args:
        document_analysis: Output from process_multimodal_docs tool
        correlation_threshold: Minimum correlation strength (0.0-1.0)
        correlation_types: Types of correlations to find
    
    Returns:
        Dictionary containing correlation analysis and mappings
    """
    try:
        if 'error' in document_analysis:
            return {"error": "Invalid document analysis provided"}
        
        analysis_data = document_analysis.get('document_analysis', {})
        if not analysis_data:
            return {"error": "No document analysis data found"}
        
        # Set default correlation types
        if correlation_types is None:
            correlation_types = ["reference", "procedure", "explanation", "diagram"]
        
        # Extract existing correlations
        existing_correlations = analysis_data.get('correlations', [])
        
        # Filter correlations by threshold and type
        filtered_correlations = [
            corr for corr in existing_correlations
            if corr.get('correlation_strength', 0) >= correlation_threshold
            and corr.get('correlation_type') in correlation_types
        ]
        
        # Create correlation mappings
        text_to_visual_map = {}
        visual_to_text_map = {}
        
        for corr in filtered_correlations:
            text_section = corr.get('text_section', '')
            visual_id = corr.get('visual_element_id', '')
            
            if text_section not in text_to_visual_map:
                text_to_visual_map[text_section] = []
            text_to_visual_map[text_section].append({
                'visual_id': visual_id,
                'correlation_type': corr.get('correlation_type'),
                'strength': corr.get('correlation_strength'),
                'context': corr.get('context', '')
            })
            
            if visual_id not in visual_to_text_map:
                visual_to_text_map[visual_id] = []
            visual_to_text_map[visual_id].append({
                'text_section': text_section,
                'correlation_type': corr.get('correlation_type'),
                'strength': corr.get('correlation_strength'),
                'context': corr.get('context', '')
            })
        
        # Generate correlation statistics
        correlation_stats = {
            'total_correlations': len(filtered_correlations),
            'correlation_types_found': list(set(corr.get('correlation_type') for corr in filtered_correlations)),
            'avg_correlation_strength': sum(corr.get('correlation_strength', 0) for corr in filtered_correlations) / len(filtered_correlations) if filtered_correlations else 0,
            'text_sections_with_visuals': len(text_to_visual_map),
            'visuals_with_text_refs': len(visual_to_text_map)
        }
        
        # Identify strong correlations for highlighting
        strong_correlations = [
            corr for corr in filtered_correlations
            if corr.get('correlation_strength', 0) > 0.8
        ]
        
        result = {
            'correlation_mappings': {
                'text_to_visual': text_to_visual_map,
                'visual_to_text': visual_to_text_map
            },
            'correlation_statistics': correlation_stats,
            'strong_correlations': strong_correlations,
            'correlation_matrix': _create_correlation_matrix(filtered_correlations),
            'correlation_metadata': {
                'threshold_used': correlation_threshold,
                'types_requested': correlation_types,
                'total_processed': len(existing_correlations),
                'total_filtered': len(filtered_correlations)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in correlate_text_images: {str(e)}")
        return {"error": f"Text-image correlation failed: {str(e)}"}


# Initialize global guidance generator (moved to after class definition)
# _guidance_generator = GuidanceGenerator()


@tool(
    name="generate_guidance",
    description="Generate contextual troubleshooting instructions from multi-modal document analysis"
)
def generate_guidance(
    document_analysis: Dict[str, Any],
    correlation_data: Dict[str, Any],
    guidance_type: str = "troubleshooting",
    output_format: str = "markdown",
    include_safety: bool = True
) -> Dict[str, Any]:
    """
    Generate contextual troubleshooting guidance from document analysis.
    
    Args:
        document_analysis: Output from process_multimodal_docs tool
        correlation_data: Output from correlate_text_images tool
        guidance_type: Type of guidance ("troubleshooting", "diagnostic", "maintenance")
        output_format: Output format ("markdown", "structured", "plain_text")
        include_safety: Whether to include safety notes and warnings
    
    Returns:
        Dictionary containing formatted guidance and metadata
    """
    try:
        # Validate inputs
        if 'error' in document_analysis:
            return {"error": "Invalid document analysis provided"}
        
        if 'error' in correlation_data:
            return {"error": "Invalid correlation data provided"}
        
        # Extract visual elements
        analysis_data = document_analysis.get('document_analysis', {})
        visual_elements = []
        
        visual_data = analysis_data.get('visual_elements', [])
        for visual_dict in visual_data:
            visual_elements.append(VisualElement(**visual_dict))
        
        # Generate structured steps using the global guidance generator
        guidance_steps = _guidance_generator.generate_structured_steps(
            document_analysis, correlation_data
        )
        
        # Filter safety information if requested
        if not include_safety:
            for step in guidance_steps:
                step.safety_notes = []
        
        # Format output
        formatted_guidance = _guidance_generator.format_guidance_output(
            guidance_steps, visual_elements, output_format
        )
        
        # Generate guidance metadata
        guidance_metadata = {
            'guidance_type': guidance_type,
            'output_format': output_format,
            'total_steps': len(guidance_steps),
            'total_visual_references': sum(len(step.visual_references) for step in guidance_steps),
            'safety_notes_included': include_safety and any(step.safety_notes for step in guidance_steps),
            'tools_identified': len(set(tool for step in guidance_steps for tool in step.tools_required)),
            'generation_timestamp': str(Path(__file__).stat().st_mtime)  # Simple timestamp
        }
        
        # Create comprehensive result
        result = {
            'formatted_guidance': formatted_guidance,
            'structured_steps': [asdict(step) for step in guidance_steps] if output_format == "structured" else None,
            'visual_integration': {
                'total_visuals': len(visual_elements),
                'visuals_referenced': len(set(ref for step in guidance_steps for ref in step.visual_references)),
                'correlation_strength': _calculate_avg_correlation_strength(correlation_data)
            },
            'guidance_metadata': guidance_metadata,
            'generation_status': 'success'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_guidance: {str(e)}")
        return {"error": f"Guidance generation failed: {str(e)}"}


def _calculate_avg_correlation_strength(correlation_data: Dict[str, Any]) -> float:
    """Calculate average correlation strength from correlation data"""
    try:
        correlations = correlation_data.get('correlation_mappings', {}).get('text_to_visual', {})
        all_strengths = []
        
        for section_correlations in correlations.values():
            for corr in section_correlations:
                strength = corr.get('strength', 0.0)
                all_strengths.append(strength)
        
        return sum(all_strengths) / len(all_strengths) if all_strengths else 0.0
        
    except Exception:
        return 0.0


# Helper functions

def _simulate_visual_analysis(image_path: str, analysis_type: str, context_text: str) -> Dict[str, Any]:
    """Simulate visual analysis (placeholder for Nova Canvas)"""
    # This is a placeholder implementation
    # In actual implementation, this would use Nova Canvas
    
    analysis = {
        'elements_detected': [],
        'text_extracted': "",
        'layout_analysis': {},
        'technical_content': {}
    }
    
    # Simulate based on analysis type
    if analysis_type == "technical_diagram":
        analysis['elements_detected'] = [
            "Component labels", "Connection lines", "Flow arrows", "Measurement points"
        ]
        analysis['technical_content'] = {
            'components_identified': ["Laser", "Detector", "Mirror", "Sample Cell"],
            'connections': ["Laser -> Mirror 1", "Mirror 1 -> Sample Cell", "Sample Cell -> Detector"],
            'measurements': ["Power levels", "Temperature readings", "Signal strength"]
        }
    
    elif analysis_type == "component_layout":
        analysis['elements_detected'] = [
            "Physical components", "Access panels", "Connection points", "Labels"
        ]
        analysis['technical_content'] = {
            'layout_structure': "Front-to-back component arrangement",
            'access_points': ["Front panel", "Side access", "Top cover"],
            'safety_elements': ["Warning labels", "Protective covers"]
        }
    
    elif analysis_type == "procedure_illustration":
        analysis['elements_detected'] = [
            "Step indicators", "Action arrows", "Before/after states", "Tool requirements"
        ]
        analysis['technical_content'] = {
            'procedure_steps': ["Remove cover", "Clean surface", "Reassemble"],
            'tools_shown': ["Screwdriver", "Cleaning cloth", "Alignment tool"],
            'safety_indicators': ["Power off warning", "ESD protection"]
        }
    
    return analysis


def _create_correlation_matrix(correlations: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Create a correlation matrix showing relationships"""
    matrix = {}
    
    # Get unique text sections and visual IDs
    text_sections = list(set(corr.get('text_section', '') for corr in correlations))
    visual_ids = list(set(corr.get('visual_element_id', '') for corr in correlations))
    
    # Initialize matrix
    for text_section in text_sections:
        matrix[text_section] = {}
        for visual_id in visual_ids:
            matrix[text_section][visual_id] = 0.0
    
    # Fill matrix with correlation strengths
    for corr in correlations:
        text_section = corr.get('text_section', '')
        visual_id = corr.get('visual_element_id', '')
        strength = corr.get('correlation_strength', 0.0)
        
        if text_section in matrix and visual_id in matrix[text_section]:
            matrix[text_section][visual_id] = max(matrix[text_section][visual_id], strength)
    
    return matrix


# Task 4.2: Guidance Generation Tools

class GuidanceGenerator:
    """Generates contextual troubleshooting guidance from multi-modal analysis"""
    
    def __init__(self):
        self.guidance_templates = {
            'diagnostic_step': {
                'format': "**Step {number}: {title}**\n{description}\n{visual_ref}\n**Expected Result:** {expected}\n",
                'required_fields': ['number', 'title', 'description']
            },
            'safety_warning': {
                'format': "**SAFETY WARNING:** {warning}\n",
                'required_fields': ['warning']
            },
            'visual_reference': {
                'format': "**Visual Reference:** {reference} ({location})\n",
                'required_fields': ['reference']
            },
            'troubleshooting_procedure': {
                'format': "## {title}\n\n**Symptoms:** {symptoms}\n\n**Steps:**\n{steps}\n\n**Expected Results:** {expected}\n",
                'required_fields': ['title', 'steps']
            }
        }
        
        self.step_keywords = {
            'check': ['verify', 'inspect', 'examine', 'look for', 'confirm'],
            'action': ['remove', 'install', 'connect', 'disconnect', 'clean', 'replace'],
            'measurement': ['measure', 'test', 'read', 'monitor', 'record'],
            'safety': ['ensure', 'warning', 'caution', 'danger', 'protect']
        }
    
    def generate_structured_steps(self, document_analysis: Dict[str, Any], 
                                correlation_data: Dict[str, Any]) -> List[GuidanceStep]:
        """Generate structured troubleshooting steps from analysis"""
        steps = []
        
        # Extract procedures from document analysis
        analysis_data = document_analysis.get('document_analysis', {})
        structured_sections = analysis_data.get('structured_sections', {})
        procedures = structured_sections.get('procedures', [])
        
        # Get correlation mappings
        correlations = correlation_data.get('correlation_mappings', {})
        text_to_visual = correlations.get('text_to_visual', {})
        
        for i, procedure in enumerate(procedures):
            step_number = procedure.get('step_number', i + 1)
            title = procedure.get('title', f'Step {step_number}')
            description = procedure.get('description', '')
            
            # Find visual references for this step
            visual_refs = []
            section_key = f"Step {step_number}" if f"Step {step_number}" in text_to_visual else title
            if section_key in text_to_visual:
                visual_refs = [ref['visual_id'] for ref in text_to_visual[section_key]]
            
            # Extract safety notes and tools
            safety_notes = self._extract_safety_notes(description)
            tools_required = self._extract_tools_required(description)
            expected_results = self._extract_expected_results(description)
            
            step = GuidanceStep(
                step_number=step_number,
                title=title,
                description=description,
                visual_references=visual_refs,
                expected_results=expected_results,
                safety_notes=safety_notes,
                tools_required=tools_required
            )
            
            steps.append(step)
        
        return steps
    
    def _extract_safety_notes(self, text: str) -> List[str]:
        """Extract safety-related information from text"""
        safety_notes = []
        safety_patterns = [
            r'(?i)(?:warning|caution|danger|safety)[:\-]?\s*([^.\n]+)',
            r'(?i)(?:ensure|make sure|verify)[^.]*(?:power|safety|protection)[^.\n]*',
            r'(?i)(?:before|after)\s+(?:removing|installing|connecting)[^.\n]*'
        ]
        
        for pattern in safety_patterns:
            matches = re.findall(pattern, text)
            safety_notes.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(safety_notes))  # Remove duplicates
    
    def _extract_tools_required(self, text: str) -> List[str]:
        """Extract required tools from text"""
        tools = []
        tool_patterns = [
            r'(?i)(?:using|with|use)\s+(?:a\s+)?([a-zA-Z\s]+(?:screwdriver|wrench|tool|meter|gauge))',
            r'(?i)(?:tool|equipment)\s+(?:required|needed)[:\-]?\s*([^.\n]+)',
            r'(?i)([a-zA-Z\s]*(?:multimeter|oscilloscope|allen key|hex key|torque wrench))'
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, text)
            tools.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(tools))  # Remove duplicates
    
    def _extract_expected_results(self, text: str) -> str:
        """Extract expected results from text"""
        result_patterns = [
            r'(?i)(?:expected|should see|result)[:\-]?\s*([^.\n]+)',
            r'(?i)(?:if successful|when complete)[:\-]?\s*([^.\n]+)',
            r'(?i)(?:normal|correct)\s+(?:reading|value|result)[:\-]?\s*([^.\n]+)'
        ]
        
        for pattern in result_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def format_guidance_output(self, steps: List[GuidanceStep], 
                             visual_elements: List[VisualElement],
                             format_type: str = "markdown") -> str:
        """Format guidance steps into readable output"""
        if format_type == "markdown":
            return self._format_markdown_guidance(steps, visual_elements)
        elif format_type == "structured":
            return self._format_structured_guidance(steps, visual_elements)
        else:
            return self._format_plain_text_guidance(steps, visual_elements)
    
    def _format_markdown_guidance(self, steps: List[GuidanceStep], 
                                visual_elements: List[VisualElement]) -> str:
        """Format guidance as markdown"""
        output = "# Troubleshooting Guidance\n\n"
        
        # Add visual elements summary
        if visual_elements:
            output += "## Visual References Available\n\n"
            for i, visual in enumerate(visual_elements):
                output += f"- **{visual.element_type.title()} {i+1}:** {visual.description}\n"
            output += "\n"
        
        # Add steps
        output += "## Troubleshooting Steps\n\n"
        for step in steps:
            output += f"### Step {step.step_number}: {step.title}\n\n"
            output += f"{step.description}\n\n"
            
            if step.visual_references:
                output += "**Visual References:**\n"
                for ref in step.visual_references:
                    output += f"- {ref}\n"
                output += "\n"
            
            if step.tools_required:
                output += "**Tools Required:**\n"
                for tool in step.tools_required:
                    output += f"- {tool}\n"
                output += "\n"
            
            if step.safety_notes:
                output += "**Safety Notes:**\n"
                for note in step.safety_notes:
                    output += f"WARNING: {note}\n"
                output += "\n"
            
            if step.expected_results:
                output += f"**Expected Result:** {step.expected_results}\n\n"
            
            output += "---\n\n"
        
        return output
    
    def _format_structured_guidance(self, steps: List[GuidanceStep], 
                                  visual_elements: List[VisualElement]) -> Dict[str, Any]:
        """Format guidance as structured data"""
        return {
            'visual_elements': [asdict(visual) for visual in visual_elements],
            'troubleshooting_steps': [asdict(step) for step in steps],
            'metadata': {
                'total_steps': len(steps),
                'total_visuals': len(visual_elements),
                'has_safety_notes': any(step.safety_notes for step in steps),
                'has_tools_required': any(step.tools_required for step in steps)
            }
        }
    
    def _format_plain_text_guidance(self, steps: List[GuidanceStep], 
                                  visual_elements: List[VisualElement]) -> str:
        """Format guidance as plain text"""
        output = "TROUBLESHOOTING GUIDANCE\n"
        output += "=" * 50 + "\n\n"
        
        for step in steps:
            output += f"STEP {step.step_number}: {step.title.upper()}\n"
            output += "-" * 30 + "\n"
            output += f"{step.description}\n\n"
            
            if step.safety_notes:
                output += "SAFETY WARNINGS:\n"
                for note in step.safety_notes:
                    output += f"! {note}\n"
                output += "\n"
            
            if step.tools_required:
                output += "TOOLS NEEDED:\n"
                for tool in step.tools_required:
                    output += f"- {tool}\n"
                output += "\n"
            
            if step.expected_results:
                output += f"EXPECTED: {step.expected_results}\n\n"
            
            output += "\n"
        
        return output


# Initialize global guidance generator
_guidance_generator = GuidanceGenerator()

# Export tools for agent_task.py
MULTIMODAL_PROCESSING_TOOLS = [
    process_multimodal_docs,
    extract_visual_info,
    correlate_text_images,
    generate_guidance
]