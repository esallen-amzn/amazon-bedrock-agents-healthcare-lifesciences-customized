# Component Recognition Tools

## Overview

The `component_recognition_tools.py` module provides intelligent component extraction and inventory management from engineering documentation. It identifies hardware and software components, builds component inventories, maps functions, and manages component-function relationships.

## Purpose

This module enables:
- Extraction of hardware and software components from technical documents
- Building comprehensive component inventories with specifications
- Mapping components to their functions and categories
- Resolving component name aliases and variations
- Creating searchable component databases
- Identifying component relationships and dependencies

## Key Components

### SystemComponent (Dataclass)

Represents a system component with comprehensive metadata:

- `name`: Component name
- `component_type`: Type ("hardware", "software", "firmware")
- `function`: Primary function description
- `specifications`: Dictionary of technical specifications
- `related_components`: List of related component names
- `aliases`: List of alternative names/abbreviations
- `failure_indicators`: List of known failure indicators
- `confidence`: Extraction confidence score (0.0-1.0)

### ComponentExtractor (Class)

Core extraction engine with pattern-based component identification.

**Component Identification Patterns**:

#### Hardware Patterns
- Module pattern: `(\w+\s+(?:module|unit|system|array|sensor|detector))\s*\(([^)]+)\)`
- Device pattern: `(\w+(?:\s+\w+)*)\s*-\s*([A-Z0-9-]+)`
- Spec pattern: `(laser|detector|sensor|pump|valve|motor|controller|power|temperature)`
- Model pattern: `([A-Z]{2,}-[A-Z0-9]+|[A-Z]+\d+[A-Z]*|\w+-\d+)`

#### Software Patterns
- Software pattern: `(\w+(?:\s+\w+)*\s+(?:software|system|module|application))\s*\(([^)]+)\)`
- Version pattern: `(v\d+\.\d+(?:\.\d+)?|\d+\.\d+(?:\.\d+)?)`
- Module pattern: `(\w+\s+(?:module|interface|manager|processor|controller))`
- Framework pattern: `(\.NET\s+Framework|Windows|Linux|SQLite|USB|Ethernet)`

### Inventory Building and Naming Resolution

The module uses intelligent naming resolution to handle:

1. **Abbreviation Expansion**: Expands common abbreviations (temp → temperature, ctrl → control)
2. **Alias Generation**: Creates acronyms and variations for component names
3. **Canonical Naming**: Establishes primary names for components with multiple references
4. **Relationship Mapping**: Tracks dependencies and interfaces between components

**Naming Resolution Process**:
```
1. Extract component name from document
2. Generate normalized form (lowercase, remove common words)
3. Create aliases (acronyms, variations)
4. Map to canonical name
5. Store in inventory with all aliases
```

## Available Tools

### 1. extract_components

**Description**: Parse engineering documents to identify and extract hardware and software components.

**Parameters**:
- `document_content` (str): Raw text content of the engineering document
- `document_type` (str): Type of document ("engineering", "specification", "manual")
- `component_types` (List[str]): List of component types to extract (["hardware", "software"])

**Returns**: Dictionary containing extracted components and metadata

**Usage Example**:
```python
with open("engineering_doc.md", "r") as f:
    content = f.read()

result = extract_components(
    document_content=content,
    document_type="engineering",
    component_types=["hardware", "software"]
)
```

**Output Structure**:
```json
{
  "components": {
    "Laser Module": {
      "name": "Laser Module",
      "component_type": "hardware",
      "function": "Generates coherent light for sample excitation",
      "specifications": {
        "wavelength": "532 nm",
        "power": "50 mW",
        "stability": "±0.1%"
      },
      "related_components": ["Optical System", "Detector Array"],
      "aliases": ["LM", "Laser"],
      "failure_indicators": ["Power fluctuation", "Beam instability"],
      "confidence": 0.9
    }
  },
  "component_list": [...],
  "statistics": {
    "total_components": 15,
    "hardware_components": 10,
    "software_components": 5,
    "avg_confidence": 0.85
  },
  "extraction_metadata": {
    "document_type": "engineering",
    "requested_types": ["hardware", "software"],
    "extraction_timestamp": "...",
    "confidence_threshold": 0.5
  }
}
```

### 2. map_functions

**Description**: Associate components with their functions and create function-component mappings.

**Parameters**:
- `components_data` (Dict[str, Any]): Output from extract_components tool
- `function_categories` (List[str]): List of function categories to organize by

**Returns**: Dictionary containing function mappings and analysis

**Default Function Categories**:
- control
- detection
- processing
- communication
- storage
- analysis
- monitoring
- interface

**Usage Example**:
```python
# First extract components
components = extract_components(document_content=content)

# Then map functions
result = map_functions(
    components_data=components,
    function_categories=["control", "detection", "processing"]
)
```

**Output Structure**:
```json
{
  "function_mappings": {
    "control": [
      {
        "component": "Temperature Controller",
        "function": "Regulates sample temperature",
        "type": "hardware",
        "confidence": 0.9
      }
    ],
    "detection": [
      {
        "component": "Detector Array",
        "function": "Captures optical signals",
        "type": "hardware",
        "confidence": 0.95
      }
    ]
  },
  "component_functions": {
    "Temperature Controller": {
      "primary_function": "Regulates sample temperature",
      "function_category": "control",
      "related_functions": ["monitoring", "thermal management"]
    }
  },
  "function_analysis": {
    "total_functions": 15,
    "function_distribution": {
      "control": 4,
      "detection": 3,
      "processing": 5
    },
    "most_common_category": "processing",
    "coverage_analysis": {...}
  }
}
```

### 3. build_inventory

**Description**: Create comprehensive component database with relationships and specifications.

**Parameters**:
- `components_data` (Dict[str, Any]): Output from extract_components tool
- `function_mappings` (Dict[str, Any]): Output from map_functions tool (optional)
- `include_relationships` (bool): Whether to include component relationships

**Returns**: Dictionary containing complete component inventory

**Usage Example**:
```python
# Extract and map components
components = extract_components(document_content=content)
functions = map_functions(components_data=components)

# Build comprehensive inventory
inventory = build_inventory(
    components_data=components,
    function_mappings=functions,
    include_relationships=True
)
```

**Output Structure**:
```json
{
  "inventory": {
    "components": {
      "Laser Module": {
        "name": "Laser Module",
        "type": "hardware",
        "function": "Generates coherent light",
        "confidence": 0.9,
        "aliases": ["LM", "Laser"],
        "function_category": "detection"
      }
    },
    "relationships": {
      "Laser Module": ["Optical System", "Detector Array"]
    },
    "specifications": {
      "Laser Module": {
        "wavelength": "532 nm",
        "power": "50 mW"
      }
    },
    "failure_indicators": {
      "Laser Module": ["Power fluctuation", "Beam instability"]
    },
    "aliases": {
      "LM": "Laser Module",
      "Laser": "Laser Module"
    }
  },
  "statistics": {
    "total_components": 15,
    "component_types": {
      "hardware": 10,
      "software": 5
    },
    "components_with_specs": 12,
    "components_with_failures": 8,
    "total_relationships": 25,
    "total_aliases": 30
  },
  "lookup_indices": {
    "by_type": {
      "hardware": ["Laser Module", "Detector Array", ...],
      "software": ["Control Software", "Analysis Module", ...]
    },
    "by_function_category": {
      "control": ["Temperature Controller", ...],
      "detection": ["Laser Module", "Detector Array", ...]
    },
    "by_confidence": {
      "high": ["Laser Module", ...],
      "medium": [...],
      "low": [...]
    }
  },
  "search_capabilities": {
    "component_search": true,
    "alias_resolution": true,
    "relationship_traversal": true,
    "specification_lookup": true,
    "failure_indicator_lookup": true
  }
}
```

## Extraction Process

### 1. Document Structure Analysis
- Split document into sections based on headers
- Identify component-related sections
- Extract component blocks from each section

### 2. Component Parsing
- Apply pattern matching to identify components
- Extract component name and model/version
- Parse function descriptions
- Extract technical specifications
- Identify related components
- Extract failure indicators

### 3. Metadata Generation
- Generate aliases (acronyms, variations)
- Calculate extraction confidence
- Normalize component names
- Create relationships

### 4. Inventory Building
- Organize components by type
- Create lookup indices
- Map functions to categories
- Build relationship graph

## Confidence Scoring

Confidence scores are calculated based on:
- **Name clarity**: +0.2 for clear, descriptive names
- **Function description**: +0.2 for detailed function descriptions
- **Specifications**: +0.05 per specification (max +0.3)
- **Base confidence**: 0.5

**Confidence Levels**:
- High: 0.8-1.0 (clear identification with specifications)
- Medium: 0.6-0.8 (good identification, some details)
- Low: 0.5-0.6 (basic identification, minimal details)

## Dependencies

- `strands`: Tool decorator for agent integration
- `re`: Regular expression pattern matching
- `json`: JSON data handling
- `dataclasses`: Structured data representation
- `pathlib`: File path operations
- `logging`: Error and info logging

## Error Handling

- Empty document content returns descriptive error messages
- Invalid component data triggers validation errors
- Missing required fields are handled gracefully
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Use structured documents**: Markdown or well-formatted text works best
2. **Include specifications**: More details improve extraction accuracy
3. **Map functions**: Use map_functions for better organization
4. **Build complete inventory**: Include relationships for comprehensive view
5. **Review confidence scores**: Focus on high-confidence components first
6. **Use aliases**: Leverage alias resolution for flexible component lookup
7. **Check relationships**: Verify component dependencies and interfaces
