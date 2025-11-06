"""
Guidance Generation Tool for Multi-modal Document Processing

This module provides guidance generation functionality that works with
the multi-modal document processing tools to create structured troubleshooting guidance.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from strands import tool

logger = logging.getLogger(__name__)


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


def extract_safety_notes(text: str) -> List[str]:
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


def extract_tools_required(text: str) -> List[str]:
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


def extract_expected_results(text: str) -> str:
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


def format_guidance_as_markdown(steps: List[GuidanceStep], visual_elements: List[Dict]) -> str:
    """Format guidance steps as markdown"""
    output = "# Troubleshooting Guidance\n\n"
    
    # Add visual elements summary
    if visual_elements:
        output += "## Visual References Available\n\n"
        for i, visual in enumerate(visual_elements):
            element_type = visual.get('element_type', 'element').title()
            description = visual.get('description', f'Visual element {i+1}')
            output += f"- **{element_type} {i+1}:** {description}\n"
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
        
        # Extract data from document analysis
        analysis_data = document_analysis.get('document_analysis', {})
        structured_sections = analysis_data.get('structured_sections', {})
        procedures = structured_sections.get('procedures', [])
        visual_elements = analysis_data.get('visual_elements', [])
        
        # Get correlation mappings
        correlations = correlation_data.get('correlation_mappings', {})
        text_to_visual = correlations.get('text_to_visual', {})
        
        # Generate structured steps
        guidance_steps = []
        
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
            safety_notes = extract_safety_notes(description) if include_safety else []
            tools_required = extract_tools_required(description)
            expected_results = extract_expected_results(description)
            
            step = GuidanceStep(
                step_number=step_number,
                title=title,
                description=description,
                visual_references=visual_refs,
                expected_results=expected_results,
                safety_notes=safety_notes,
                tools_required=tools_required
            )
            
            guidance_steps.append(step)
        
        # Format output based on requested format
        if output_format == "markdown":
            formatted_guidance = format_guidance_as_markdown(guidance_steps, visual_elements)
        elif output_format == "structured":
            formatted_guidance = {
                'visual_elements': visual_elements,
                'troubleshooting_steps': [asdict(step) for step in guidance_steps]
            }
        else:  # plain_text
            formatted_guidance = "TROUBLESHOOTING GUIDANCE\n" + "=" * 50 + "\n\n"
            for step in guidance_steps:
                formatted_guidance += f"STEP {step.step_number}: {step.title.upper()}\n"
                formatted_guidance += f"{step.description}\n\n"
        
        # Generate guidance metadata
        guidance_metadata = {
            'guidance_type': guidance_type,
            'output_format': output_format,
            'total_steps': len(guidance_steps),
            'total_visual_references': sum(len(step.visual_references) for step in guidance_steps),
            'safety_notes_included': include_safety and any(step.safety_notes for step in guidance_steps),
            'tools_identified': len(set(tool for step in guidance_steps for tool in step.tools_required)),
        }
        
        # Calculate average correlation strength
        all_strengths = []
        for section_correlations in text_to_visual.values():
            for corr in section_correlations:
                strength = corr.get('strength', 0.0)
                all_strengths.append(strength)
        avg_correlation_strength = sum(all_strengths) / len(all_strengths) if all_strengths else 0.0
        
        # Create comprehensive result
        result = {
            'formatted_guidance': formatted_guidance,
            'structured_steps': [asdict(step) for step in guidance_steps] if output_format == "structured" else None,
            'visual_integration': {
                'total_visuals': len(visual_elements),
                'visuals_referenced': len(set(ref for step in guidance_steps for ref in step.visual_references)),
                'correlation_strength': avg_correlation_strength
            },
            'guidance_metadata': guidance_metadata,
            'generation_status': 'success'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_guidance: {str(e)}")
        return {"error": f"Guidance generation failed: {str(e)}"}