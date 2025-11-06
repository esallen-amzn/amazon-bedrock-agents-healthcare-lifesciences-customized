# 📖 User Guide - Instrument Diagnosis Assistant

Welcome to the Instrument Diagnosis Assistant! This guide will help you effectively use the system to diagnose instrument issues and get troubleshooting guidance.

## 🎯 Overview

The Instrument Diagnosis Assistant is an AI-powered system that helps technicians diagnose instrument failures by:
- Analyzing log files from problem instruments (primary function)
- Optionally comparing against gold standard patterns when available
- Identifying system components from documentation
- Processing troubleshooting guides with images and diagrams
- Providing pass/fail determinations with confidence levels

## 🚀 Getting Started

### Accessing the System

1. **Open the Application**
   - Navigate to your deployment URL (provided by your administrator)
   - Log in using your credentials (if authentication is enabled)

2. **Main Interface Overview**
   - **File Upload Area**: Upload logs, documentation, and guides
   - **Quick Actions**: Pre-configured analysis buttons
   - **Chat Interface**: Interactive conversation with the AI
   - **Results Display**: Structured diagnosis results

### First Time Setup

1. **Upload Sample Data** (recommended for first-time users)
   - Use the provided sample files to test the system
   - Verify all features work correctly
   - Familiarize yourself with the interface

## 📁 File Upload and Management

### Supported File Types

#### Log Files
- **Formats**: `.txt`, `.log`, `.csv`
- **Size Limit**: Up to 500MB per file
- **Types**:
  - **Gold Standard Logs (Optional)**: Reference logs from working instruments for comparison analysis
  - **Problem Unit Logs (Required)**: Primary logs from instruments experiencing issues

#### Documentation
- **Formats**: `.pdf`, `.doc`, `.docx`, `.txt`, `.md`
- **Content**: Component specifications, system architecture, engineering docs
- **Best Practices**: Use clear headings and structured content

#### Troubleshooting Guides
- **Formats**: `.pdf`, `.doc`, `.docx`, `.png`, `.jpg`, `.jpeg`
- **Content**: Multi-modal guides with text, images, and diagrams
- **Optimization**: High-resolution images work best for analysis

### Upload Process

1. **Select File Type Tab**
   - Choose the appropriate tab (Log Files, Documentation, or Troubleshooting Guides)

2. **Upload Files**
   - Click "Browse files" or drag and drop
   - Select multiple files if needed
   - Wait for upload confirmation

3. **Verify Upload**
   - Check the file count indicator
   - Ensure all files are listed correctly

## 🔍 Analysis Features

### Quick Actions

#### 🔍 Analyze Logs
- **Purpose**: Compare failed logs against gold standards
- **Input**: Requires both gold standard and failed unit logs
- **Output**: Pass/fail determination with confidence level
- **Use Case**: Primary diagnostic function

#### 🔧 Identify Components
- **Purpose**: Extract component information from documentation
- **Input**: Engineering documents and specifications
- **Output**: Component inventory with functions and relationships
- **Use Case**: Understanding system architecture

#### 📚 Process Guides
- **Purpose**: Analyze troubleshooting guides with visual content
- **Input**: Multi-modal troubleshooting documentation
- **Output**: Structured procedures and visual references
- **Use Case**: Extracting repair procedures

#### 🎯 Full Diagnosis
- **Purpose**: Comprehensive analysis using all uploaded files
- **Input**: All file types (logs, docs, guides)
- **Output**: Complete diagnostic report with recommendations
- **Use Case**: Thorough instrument evaluation

### Analysis Modes

#### Comprehensive Analysis
- **Description**: Detailed analysis of all aspects
- **Time**: Longer processing time
- **Accuracy**: Highest accuracy and detail
- **Best For**: Critical diagnoses, complex issues

#### Quick Diagnosis
- **Description**: Faster analysis focusing on key indicators
- **Time**: Shorter processing time
- **Accuracy**: Good accuracy for common issues
- **Best For**: Routine checks, initial screening

#### Component Focus
- **Description**: Emphasis on component identification and relationships
- **Time**: Moderate processing time
- **Accuracy**: Specialized for component analysis
- **Best For**: System understanding, component issues

#### Log Comparison Only
- **Description**: Focus solely on log file analysis
- **Time**: Fast processing
- **Accuracy**: High for log-based issues
- **Best For**: Known log patterns, quick checks

## 📊 Understanding Results

### Diagnosis Status

#### ✅ PASS
- **Meaning**: Instrument appears to be functioning correctly
- **Confidence**: Shows how certain the system is (0-100%)
- **Action**: Monitor for changes, routine maintenance

#### ❌ FAIL
- **Meaning**: Instrument has identified issues or failures
- **Confidence**: Shows certainty of the failure determination
- **Action**: Review failure indicators and recommendations

#### ⚠️ UNCERTAIN
- **Meaning**: System cannot make a definitive determination
- **Confidence**: Usually indicates low confidence or conflicting data
- **Action**: Gather more data, manual inspection recommended

### Result Components

#### Failure Indicators
- **Description**: Specific patterns or anomalies found in logs
- **Format**: List of technical indicators
- **Use**: Helps understand what went wrong

#### Recommendations
- **Description**: Suggested next steps and actions
- **Format**: Prioritized list of recommendations
- **Use**: Guides troubleshooting and repair efforts

#### Detailed Analysis Summary
- **Description**: Comprehensive explanation of findings
- **Format**: Structured text with technical details
- **Use**: In-depth understanding of the diagnosis

### Confidence Levels

- **90-100%**: Very High - Strong evidence for the determination
- **75-89%**: High - Good evidence, reliable result
- **60-74%**: Moderate - Some uncertainty, consider additional data
- **Below 60%**: Low - Uncertain result, manual verification recommended

## 💬 Interactive Chat

### Using the Chat Interface

1. **Ask Questions**
   - Type specific questions about your instrument
   - Request clarification on results
   - Ask for additional analysis

2. **Request Specific Analysis**
   - "Analyze the optical system components"
   - "Compare the latest logs with baseline"
   - "What troubleshooting steps are recommended?"

3. **Get Explanations**
   - "Explain the failure indicators"
   - "Why is the confidence level low?"
   - "What does this error pattern mean?"

### Effective Prompts

#### Good Examples
- "Compare the failed unit logs from today with the gold standard and focus on the optical system"
- "Identify all motor components from the engineering documentation"
- "What troubleshooting steps are shown in the uploaded guides for communication errors?"

#### Less Effective Examples
- "Fix my instrument" (too vague)
- "What's wrong?" (no context)
- "Help" (not specific)

## ⚙️ Configuration Options

### Analysis Settings

#### Confidence Threshold
- **Range**: 50-95%
- **Default**: 75%
- **Effect**: Higher values = more conservative diagnoses
- **Recommendation**: Start with default, adjust based on experience

#### Analysis Mode
- **Options**: Comprehensive, Quick, Component Focus, Log Comparison
- **Default**: Comprehensive
- **Effect**: Changes processing time and focus areas

#### Visual Analysis
- **Option**: Include/exclude image analysis
- **Default**: Included
- **Effect**: Processes diagrams and images in troubleshooting guides
- **Note**: Requires Nova Canvas model access

### Display Options

#### Auto-format Responses
- **Effect**: Cleans and structures AI responses
- **Recommendation**: Keep enabled for better readability

#### Show Tools
- **Effect**: Displays which AI tools are being used
- **Use**: Helpful for understanding the analysis process

#### Show Thinking
- **Effect**: Shows AI reasoning process
- **Use**: Useful for debugging or understanding decisions

## 📈 Best Practices

### File Organization

1. **Consistent Naming**
   - Use descriptive filenames
   - Include dates and instrument IDs
   - Example: `instrument_001_system_log_2024_11_15.txt`

2. **File Quality**
   - Ensure logs are complete and untruncated
   - Use high-resolution images for guides
   - Keep documentation up-to-date

3. **Logical Grouping**
   - Upload related files together
   - Separate different analysis sessions
   - Maintain version control for documents

### Analysis Workflow

1. **Start with Quick Diagnosis**
   - Get initial assessment quickly
   - Identify obvious issues early
   - Decide if deeper analysis is needed

2. **Use Comprehensive Analysis for Complex Issues**
   - When quick diagnosis is uncertain
   - For critical instruments
   - When detailed documentation is needed

3. **Leverage Component Analysis**
   - When unfamiliar with system architecture
   - For component-specific issues
   - To understand system relationships

### Interpreting Results

1. **Consider Confidence Levels**
   - High confidence results are more reliable
   - Low confidence may indicate need for more data
   - Very high confidence in PASS results is reassuring

2. **Review Failure Indicators**
   - Look for patterns across multiple indicators
   - Cross-reference with known issues
   - Consider temporal relationships

3. **Follow Recommendations**
   - Start with highest priority recommendations
   - Document actions taken
   - Re-analyze after making changes

## 🔧 Troubleshooting Common Issues

### Upload Problems

**Issue**: Files won't upload
- **Check**: File size limits (500MB max)
- **Check**: Supported file formats
- **Solution**: Split large files or convert formats

**Issue**: Upload appears successful but files not recognized
- **Check**: File content is readable
- **Check**: File isn't corrupted
- **Solution**: Re-upload or use different format

### Analysis Issues

**Issue**: Low confidence results
- **Cause**: Insufficient or poor quality data
- **Solution**: Upload more reference data, check file quality

**Issue**: Analysis takes too long
- **Cause**: Large files or complex analysis
- **Solution**: Use Quick Diagnosis mode, split large files

**Issue**: Unexpected results
- **Cause**: Data quality, system configuration
- **Solution**: Review uploaded files, check analysis mode

### Interface Issues

**Issue**: Page won't load
- **Check**: Internet connection
- **Check**: Browser compatibility
- **Solution**: Refresh page, try different browser

**Issue**: Authentication problems
- **Check**: Login credentials
- **Check**: Session timeout
- **Solution**: Re-login, contact administrator

## 📞 Getting Help

### Self-Service Resources
1. **This User Guide**: Comprehensive usage instructions
2. **FAQ Section**: Common questions and answers
3. **Sample Data**: Practice with provided examples
4. **Troubleshooting Guide**: Technical issue resolution

### Support Channels
1. **Administrator**: For system access and configuration issues
2. **Technical Support**: For application problems and bugs
3. **Training**: For additional user training needs

### Providing Feedback
- Report bugs or issues with specific error messages
- Suggest improvements or new features
- Share successful use cases and workflows

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**For Technical Support**: Contact your system administrator