# Sample Data for Instrument Diagnosis Assistant

This directory contains sample data for testing and validating the Instrument Diagnosis Assistant system. The data is organized to support all major diagnostic capabilities and test scenarios.

## Directory Structure

```
sample_data/
├── gold_standard_logs/          # Reference logs from properly functioning instruments
├── failed_unit_logs/           # Logs from instruments with various failures
├── engineering_docs/           # Technical documentation and component specifications
├── troubleshooting_guides/     # Multi-modal troubleshooting procedures
├── test_scenarios_config.yaml  # Configuration for automated testing scenarios
└── README.md                   # This file
```

## Data Contents

### Gold Standard Logs
- **system_log_good_001.txt**: Normal system operation log showing healthy instrument behavior
- **pc_log_good_001.txt**: Normal PC system log with proper software operation

These logs establish baseline patterns for:
- Normal startup sequences
- Successful sample analysis workflows
- Proper component status indicators
- Expected performance metrics

### Failed Unit Logs
- **system_log_fail_001.txt**: System log showing multiple hardware failures
- **pc_log_fail_001.txt**: PC log showing software and communication issues

These logs contain examples of:
- Laser power degradation
- Temperature control instability
- Fluid system pressure problems
- USB communication timeouts
- Memory usage issues
- Software module failures

### Engineering Documentation
- **component_specifications.md**: Detailed specifications for all hardware and software components
- **system_architecture.md**: System architecture overview and component relationships

These documents provide:
- Component identification information
- Functional specifications and operating ranges
- Failure indicators and thresholds
- System integration details
- Performance specifications

### Troubleshooting Guides
- **optical_system_troubleshooting.md**: Comprehensive guide for optical system issues
- **software_communication_guide.md**: Guide for software and communication problems

These guides include:
- Step-by-step troubleshooting procedures
- Visual diagrams and reference information
- Safety notes and precautions
- Preventive maintenance schedules
- When to escalate to technical support

## Test Scenarios

The `test_scenarios_config.yaml` file defines five comprehensive test scenarios:

1. **Normal Operation Validation**: Verify recognition of healthy system operation
2. **Multiple System Failures**: Test detection of simultaneous failures across multiple subsystems
3. **Component Recognition**: Validate identification and mapping of hardware/software components
4. **Multi-modal Document Processing**: Test processing of guides with text and visual elements
5. **Cross-source Correlation**: Test correlation of information across logs, documentation, and guides

## Usage Instructions

### For Development Testing
1. Use the gold standard logs to establish baseline behavior patterns
2. Test failure detection using the failed unit logs
3. Validate component recognition against the engineering documentation
4. Test troubleshooting guidance generation using the guides

### For System Validation
1. Run the automated test scenarios defined in `test_scenarios_config.yaml`
2. Verify expected results match actual system output
3. Test performance with the large file processing scenarios
4. Validate multi-modal processing capabilities

### For Customer Demonstration
1. Use the complete workflow: analyze failed logs against gold standards
2. Demonstrate component identification from engineering docs
3. Show troubleshooting guidance generation from the guides
4. Highlight cross-source correlation capabilities

## Data Characteristics

### Log File Formats
- Plain text format with timestamp prefixes
- Structured entries with component status indicators
- Error messages and failure indicators clearly marked
- Realistic timing and operational sequences

### Documentation Formats
- Markdown format for easy processing and display
- Structured sections with clear headings
- Technical specifications in tabular format
- Visual diagrams using ASCII art and text descriptions

### File Sizes
- Log files: 1-5 KB (representative samples)
- Documentation: 5-15 KB per file
- Total sample data: <100 KB for easy distribution

## Extending the Sample Data

To add new test scenarios:

1. **New Log Files**: Add to appropriate subdirectory with descriptive names
2. **Additional Documentation**: Place in `engineering_docs/` with clear naming
3. **New Troubleshooting Guides**: Add to `troubleshooting_guides/` directory
4. **Test Scenarios**: Update `test_scenarios_config.yaml` with new test cases

### Naming Conventions
- Log files: `{type}_log_{status}_{sequence}.txt`
- Documentation: `{topic}_{type}.md`
- Guides: `{system}_{purpose}_guide.md`

## Integration with System

The sample data is designed to work seamlessly with:
- Amazon Nova models for text and multi-modal analysis
- Bedrock Knowledge Base for document retrieval
- AgentCore template structure and tools
- Configuration-driven test execution

## Quality Assurance

All sample data has been:
- Validated for realistic content and formatting
- Tested with the diagnostic system components
- Reviewed for completeness and accuracy
- Designed to cover edge cases and common scenarios

This sample data provides a comprehensive foundation for testing, validation, and demonstration of the Instrument Diagnosis Assistant capabilities.