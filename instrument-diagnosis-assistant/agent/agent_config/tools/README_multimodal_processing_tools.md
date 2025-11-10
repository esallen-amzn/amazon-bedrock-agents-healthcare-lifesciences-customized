# Multimodal Processing Tools

## Overview

The `multimodal_processing_tools.py` module provides multimodal document processing capabilities for troubleshooting guides containing text, images, and diagrams. It uses Amazon Nova Pro for visual analysis and creates correlations between textual instructions and visual references.

## Purpose

This module enables:
- Processing troubleshooting guides with text and images
- Extracting visual elements (diagrams, images, charts)
- Correlating text sections with visual references
- Generating structured troubleshooting guidance
- Analyzing technical diagrams and component layouts
- Creating actionable step-by-step procedures

## Key Components

### VisualElement (Dataclass)

Represents a visual element extracted from a document:

- `element_type`: Type ("diagram", "image", "chart", "table")
- `description`: Description of the visual element
- `location`: Position or reference in document
- `content_analysis`: Analysis of visual content
- `related_text`: List of related text sections
- `confidence`: Extraction confidence score (0.0-1.0)

### TextImageCorrelation (Dataclass)

Represents correlation between text and visual elements:

- `text_section`: Text section title
- `visual_element_id`: Unique visual element identifier
- `correlation_type`: Type ("reference", "explanation", "procedure", "diagram")
- `correlation_strength`: Strength score (0.0-1.0)
- `context`: Contextual information

### MultiModalProcessor (Class)

Core multimodal document processing engine.

**Visual Element Detection Patterns**:
- Diagram references: `(?i)(?:see\s+)?(?:diagram|figure|image|chart)\s*[:\-]?\s*([^.\n]+)`
- Step references: `(?i)(?:step\s+\d+|procedure\s+\d+|figure\s+\d+)`
- Visual indicators: `(?i)(?:shown\s+(?:in|below)|illustrated|depicted|see\s+(?:above|below))`
- Location references: `(?i)(?:front|back|left|right|top|bottom|side)\s+(?:panel|cover|access)`

### Visual Analysis Capabilities

The module provides visual analysis for:

1. **Technical Diagrams**: Component layouts, connections, flow diagrams
2. **Component Layouts**: Physical arrangements, access points, labels
3. **Procedure Illustrations**: Step-by-step visual guides, tool requirements

## Available Tools

### 1. process_multimodal_docs

**Description**: Process troubleshooting guides containing text, images, and diagrams using Nova Pro.

**Parameters**:
- `document_content` (str): Raw text content of the document
- `document_path` (str): Path to document file (for image extraction)
- `include_images` (bool): Whether document contains images to analyze
- `analysis_depth` (str): Depth of analysis ("quick", "standard", "comprehensive")

**Returns**: Dictionary containing multimodal analysis results

**Usage Example**:
```python
with open("troubleshooting_guide.md", "r") as f:
    content = f.read()

result = process_multimodal_docs(
    document_content=content,
    document_path="troubleshooting_guide.md",
    include_images=True,
    analysis_depth="comprehensive"
)
```

**Output Structure**:
```json
{
  "document_analysis": {
    "text_content": "...",
    "visual_elements": [
      {
        "element_type": "diagram",
        "description": "System component layout",
        "location": "Referenced at position 1234",
        "content_analysis": "Shows laser, detector, and optical path",
        "related_text": ["Check optical alignment", "Verify laser power"],
        "confidence": 0.9
      }
    ],
    "correlations": [
      {
        "text_section": "Optical Alignment Procedure",
        "visual_element_id": "visual_1234",
        "correlation_type": "procedure",
        "correlation_strength": 0.9,
        "context": "Procedural context in Optical Alignment Procedure"
      }
    ],
    "structured_sections": {
      "headers": [...],
      "procedures": [...],
      "symptoms": [...],
      "troubleshooting_steps": [...]
    },
    "guidance_steps": [],
    "processing_metadata": {
      "document_length": 50000,
      "sections_found": 15,
      "visual_elements_found": 8,
      "correlations_created": 12,
      "analysis_depth": "comprehensive",
      "nova_canvas_used": true
    }
  },
  "structure_summary": {
    "total_sections": 15,
    "procedures_found": 8,
    "symptoms_identified": 5,
    "safety_notes": 3
  },
  "visual_summary": {
    "total_visual_elements": 8,
    "diagrams": 5,
    "images": 3,
    "correlations": 12
  },
  "processing_status": "success"
}
```

### 2. extract_visual_info

**Description**: Extract and analyze visual information from images and diagrams using Nova Pro.

**Parameters**:
- `image_data` (str): Base64 encoded image data
- `image_path` (str): Path to image file
- `analysis_type` (str): Type of analysis ("technical_diagram", "component_layout", "procedure_illustration")
- `context_text` (str): Surrounding text context for better analysis

**Returns**: Dictionary containing visual analysis results

**Usage Example**:
```python
# Analyze from file path
result = extract_visual_info(
    image_path="diagrams/component_layout.png",
    analysis_type="component_layout",
    context_text="This diagram shows the internal component arrangement..."
)

# Analyze from base64 data
result = extract_visual_info(
    image_data="iVBORw0KGgoAAAANSUhEUgAA...",
    analysis_type="technical_diagram",
    context_text="System optical path diagram"
)
```

**Output Structure**:
```json
{
  "visual_analysis": {
    "elements_detected": [
      "Component labels",
      "Connection lines",
      "Flow arrows",
      "Measurement points"
    ],
    "text_extracted": "Laser, Detector, Mirror, Sample Cell",
    "layout_analysis": {
      "layout_structure": "Front-to-back component arrangement",
      "access_points": ["Front panel", "Side access", "Top cover"],
      "safety_elements": ["Warning labels", "Protective covers"]
    },
    "technical_content": {
      "components_identified": ["Laser", "Detector", "Mirror", "Sample Cell"],
      "connections": ["Laser -> Mirror 1", "Mirror 1 -> Sample Cell"],
      "measurements": ["Power levels", "Temperature readings"]
    }
  },
  "analysis_metadata": {
    "analysis_type": "component_layout",
    "has_context": true,
    "image_source": "path",
    "nova_canvas_used": true
  }
}
```

### 3. correlate_text_images

**Description**: Create correlations between textual instructions and visual references.

**Parameters**:
- `document_analysis` (Dict[str, Any]): Output from process_multimodal_docs tool
- `correlation_threshold` (float): Minimum correlation strength (0.0-1.0) - default: 0.5
- `correlation_types` (List[str]): Types of correlations to find - default: ["reference", "procedure", "explanation", "diagram"]

**Returns**: Dictionary containing correlation analysis and mappings

**Usage Example**:
```python
# First process document
doc_analysis = process_multimodal_docs(document_content=content)

# Then create correlations
result = correlate_text_images(
    document_analysis=doc_analysis,
    correlation_threshold=0.6,
    correlation_types=["reference", "procedure", "diagram"]
)
```

**Output Structure**:
```json
{
  "correlation_mappings": {
    "text_to_visual": {
      "Optical Alignment Procedure": [
        {
          "visual_id": "visual_1234",
          "correlation_type": "procedure",
          "strength": 0.9,
          "context": "Procedural context"
        }
      ]
    },
    "visual_to_text": {
      "visual_1234": [
        {
          "text_section": "Optical Alignment Procedure",
          "correlation_type": "procedure",
          "strength": 0.9,
          "context": "Procedural context"
        }
      ]
    }
  },
  "correlation_statistics": {
    "total_correlations": 12,
    "correlation_types_found": ["reference", "procedure", "diagram"],
    "avg_correlation_strength": 0.85,
    "text_sections_with_visuals": 8,
    "visuals_with_text_refs": 6
  },
  "strong_correlations": [
    {
      "text_section": "Optical Alignment Procedure",
      "visual_element_id": "visual_1234",
      "correlation_type": "procedure",
      "correlation_strength": 0.9,
      "context": "Procedural context"
    }
  ],
  "correlation_matrix": {...}
}
```

### 4. generate_guidance

**Description**: Generate contextual troubleshooting instructions from multimodal document analysis.

**Parameters**:
- `document_analysis` (Dict[str, Any]): Output from process_multimodal_docs tool
- `correlation_data` (Dict[str, Any]): Output from correlate_text_images tool
- `guidance_type` (str): Type of guidance ("troubleshooting", "diagnostic", "maintenance")
- `output_format` (str): Output format ("markdown", "structured", "plain_text")
- `include_safety` (bool): Whether to include safety notes and warnings

**Returns**: Dictionary containing formatted guidance and metadata

**Usage Example**:
```python
# Process document and create correlations
doc_analysis = process_multimodal_docs(document_content=content)
correlations = correlate_text_images(document_analysis=doc_analysis)

# Generate guidance
result = generate_guidance(
    document_analysis=doc_analysis,
    correlation_data=correlations,
    guidance_type="troubleshooting",
    output_format="markdown",
    include_safety=True
)
```

**Output Structure**:
```json
{
  "formatted_guidance": "# Troubleshooting Guide\n\n## Step 1: Check Optical Alignment\n\n**Description**: Verify laser beam alignment...\n\n**Visual Reference**: See Diagram 1 (Component Layout)\n\n**Expected Result**: Beam centered on detector\n\n**Safety Notes**:\n- Power off laser before adjustment\n- Wear appropriate eye protection\n\n**Tools Required**:\n- Alignment tool\n- Power meter\n\n---\n\n## Step 2: Verify Power Levels\n...",
  "structured_steps": [
    {
      "step_number": 1,
      "title": "Check Optical Alignment",
      "description": "Verify laser beam alignment through optical path",
      "visual_references": ["Diagram 1", "Figure 2"],
      "expected_results": "Beam centered on detector with <1mm deviation",
      "safety_notes": [
        "Power off laser before adjustment",
        "Wear appropriate eye protection"
      ],
      "tools_required": ["Alignment tool", "Power meter"]
    }
  ],
  "visual_integration": {
    "total_visuals": 8,
    "visuals_referenced": 6,
    "correlation_strength": 0.85
  },
  "guidance_metadata": {
    "guidance_type": "troubleshooting",
    "output_format": "markdown",
    "total_steps": 5,
    "total_visual_references": 12,
    "safety_notes_included": true,
    "tools_identified": 8,
    "generation_timestamp": "..."
  },
  "generation_status": "success"
}
```

## Document Structure Analysis

The module analyzes document structure to extract:

### 1. Headers and Hierarchy
- Markdown headers (# ## ###)
- Section titles and levels
- Content organization

### 2. Procedural Sections
- Numbered steps
- Step titles and descriptions
- Visual references in steps

### 3. Structured Content
- Symptoms
- Troubleshooting steps
- Expected results
- Safety notes
- When to escalate

## Correlation Types

### 1. Reference Correlation
- Direct mentions of visual elements in text
- "See Figure 1", "Refer to diagram"
- Strength: 0.9 (high confidence)

### 2. Procedure Correlation
- Visual elements supporting procedural steps
- Diagrams showing step-by-step actions
- Strength: 0.7 (medium-high confidence)

### 3. Explanation Correlation
- Visuals explaining concepts
- Diagrams illustrating principles
- Strength: 0.6 (medium confidence)

### 4. Diagram Correlation
- Technical diagrams with component details
- System architecture visuals
- Strength: 0.8 (high confidence)

## Dependencies

- `strands`: Tool decorator for agent integration
- `re`: Regular expression pattern matching
- `json`: JSON data handling
- `base64`: Image encoding/decoding
- `mimetypes`: MIME type detection
- `dataclasses`: Structured data representation
- `pathlib`: File path operations
- `logging`: Error and info logging

## Error Handling

- Empty document content returns descriptive error messages
- Invalid image paths trigger clear error responses
- Missing visual elements are handled gracefully
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Include context**: Provide surrounding text for better visual analysis
2. **Use appropriate analysis types**: Match analysis type to visual content
3. **Set correlation thresholds**: Adjust based on desired precision
4. **Include safety notes**: Always enable safety information in guidance
5. **Use structured output**: Structured format for programmatic processing
6. **Review correlations**: Verify strong correlations for accuracy
7. **Combine with text analysis**: Use alongside log analysis for complete diagnosis
8. **Leverage visual references**: Include visual references in troubleshooting steps
