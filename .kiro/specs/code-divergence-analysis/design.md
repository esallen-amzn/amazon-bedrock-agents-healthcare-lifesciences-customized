# Design Document: Code Divergence Analysis

## Overview

This document provides a comprehensive analysis of how the `instrument-diagnosis-assistant` project has diverged from the original `agentcore_template`. The analysis reveals significant customization while maintaining the core AgentCore framework structure.

## Executive Summary

**Divergence Level: HIGH (70-80% custom implementation)**

The instrument-diagnosis-assistant has evolved significantly from the template, with extensive custom tooling, modified core files, and specialized workflows. However, it still relies on the core AgentCore/Strands framework and maintains the basic architectural patterns.

## Detailed Analysis

### 1. Structural Divergence

#### Files Added (Not in Template)
```
instrument-diagnosis-assistant/
├── s3_integration.py                    # NEW: S3 file upload/management
├── process_uploaded_files_new.py        # NEW: File processing logic
├── invoke_agent_fixed.py                # NEW: Custom invocation
├── app_local.py                         # NEW: Local development variant
├── app_cli_invoke.py                    # NEW: CLI invocation
├── app_temp.py                          # NEW: Temporary/test app
├── run_app.py                           # NEW: Application launcher
├── config.yaml                          # NEW: Runtime configuration
├── agentcore-invoke-policy.json         # NEW: IAM policy
├── setup_aws_credentials.md             # NEW: Setup documentation
├── set_creds.bat                        # NEW: Windows credential setup
├── start.bat                            # NEW: Windows launcher
├── start.sh                             # NEW: Unix launcher
├── deployment/                          # NEW: Environment configs
│   ├── dev-config.yaml
│   ├── test-config.yaml
│   └── prod-config.yaml
└── agent/agent_config/
    ├── config_manager.py                # NEW: Configuration management
    └── tools/                           # HEAVILY EXTENDED
        ├── diagnosis_tools.py           # NEW: Diagnosis logic
        ├── log_analysis_tools.py        # NEW: Log analysis
        ├── component_recognition_tools.py # NEW: Component extraction
        ├── s3_storage_tools.py          # NEW: S3 operations
        ├── s3_log_analysis_tools.py     # NEW: S3-based log analysis
        ├── s3_log_sampling_tools.py     # NEW: Large file sampling
        ├── multimodal_processing_tools.py # NEW: Image/doc processing
        ├── cross_source_correlation_tools.py # NEW: Data correlation
        ├── guidance_generation.py       # NEW: Troubleshooting guidance
        ├── consistency_management_tools.py # NEW: Data consistency
        └── config_tools.py              # NEW: Config tools
```

#### Files Modified (From Template)

**main.py** - MODERATE modifications:
- ✅ Still uses template structure (BedrockAgentCoreApp, entrypoint decorator)
- ❌ Removed SSM parameter lookup for KB_ID (uses config.yaml instead)
- ❌ Removed gateway token retrieval (uses fallback mode)
- ✅ Added extensive debug logging
- **Assessment**: Core structure intact, but configuration mechanism changed

**app.py** - MAJOR modifications:
- ✅ Still uses Streamlit and boto3 bedrock-agentcore client
- ❌ Completely redesigned UI (removed sidebar, added file upload tabs)
- ❌ Added S3 integration for file handling
- ❌ Added custom file processing logic
- ❌ Changed from agent selection dropdown to auto-fetch latest
- ❌ Added diagnosis results display section
- ❌ Added Unicode handling and ASCII-only response requirements
- **Assessment**: ~60% rewritten, fundamentally different UX

**agent.py** - MAJOR modifications:
- ✅ Still uses Strands Agent, BedrockModel, MCPClient
- ❌ Renamed class from TemplateAgent to InstrumentDiagnosisAgent
- ❌ Added ConfigManager integration
- ❌ Added multimodal model support
- ❌ Completely rewritten system prompt (10x longer, specialized)
- ❌ Added 13 custom local tools
- ❌ Added S3-aware workflow instructions
- ❌ Made gateway optional (template requires it)
- **Assessment**: ~70% rewritten, highly specialized

#### Files Unchanged (Still Using Template Code)

**Core Infrastructure** - MOSTLY UNCHANGED:
- ✅ `agent/agent_config/context.py` - Context management
- ✅ `agent/agent_config/streaming_queue.py` - Response streaming
- ✅ `agent/agent_config/memory_hook_provider.py` - Memory integration
- ✅ `agent/agent_config/access_token.py` - Token management
- ✅ `agent/agent_config/utils.py` - SSM parameter utilities
- ✅ `app_modules/` - OAuth UI components (auth.py, chat.py, main.py, styles.py, utils.py)
- ✅ `prerequisite/` - Infrastructure templates (infrastructure.yaml, cognito.yaml)
- ✅ `scripts/` - Deployment scripts (mostly unchanged, some additions)
- ✅ `static/` - UI assets (unchanged)
- ✅ `tests/` - Test scripts (unchanged)

**Assessment**: Core AgentCore framework components remain intact (~30-40% of codebase)

### 2. Architecture Analysis

#### What's Still Template-Based

```
┌─────────────────────────────────────────────────────────┐
│         TEMPLATE ARCHITECTURE (STILL USED)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Streamlit   │──────│  AgentCore   │                │
│  │     UI       │      │   Runtime    │                │
│  └──────────────┘      └──────────────┘                │
│         │                      │                        │
│         │                      │                        │
│  ┌──────▼──────────────────────▼──────┐                │
│  │      Strands Agent Framework       │                │
│  │  - BedrockModel                    │                │
│  │  - Agent orchestration             │                │
│  │  - Tool execution                  │                │
│  │  - Memory hooks                    │                │
│  └────────────────────────────────────┘                │
│         │                      │                        │
│  ┌──────▼──────┐      ┌───────▼──────┐                │
│  │   Memory    │      │   Gateway    │                │
│  │   Service   │      │   (MCP)      │                │
│  └─────────────┘      └──────────────┘                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### What's Custom Implementation

```
┌─────────────────────────────────────────────────────────┐
│       CUSTOM IMPLEMENTATION (NEW CODE)                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────┐              │
│  │   Custom Streamlit UI                │              │
│  │  - File upload tabs                  │              │
│  │  - S3 integration                    │              │
│  │  - Diagnosis results display         │              │
│  │  - Quick action buttons              │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                        │
│  ┌──────────────▼───────────────────────┐              │
│  │   S3 File Management Layer           │              │
│  │  - Upload to S3                      │              │
│  │  - Session-based organization        │              │
│  │  - File metadata tracking            │              │
│  │  - Presigned URL generation          │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                        │
│  ┌──────────────▼───────────────────────┐              │
│  │   Specialized Agent Tools (13)       │              │
│  │  - Log analysis                      │              │
│  │  - S3 log sampling (MCP strategy)    │              │
│  │  - Component recognition             │              │
│  │  - Diagnosis generation              │              │
│  │  - Multimodal processing             │              │
│  │  - Cross-source correlation          │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                        │
│  ┌──────────────▼───────────────────────┐              │
│  │   Configuration Management           │              │
│  │  - YAML-based config                 │              │
│  │  - Environment-specific settings     │              │
│  │  - Model configuration               │              │
│  │  - Analysis thresholds               │              │
│  └──────────────────────────────────────┘              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Key Divergence Points

#### 3.1 Configuration Management

**Template Approach:**
- Uses SSM Parameter Store for all configuration
- Hardcoded parameter paths (`/app/myapp/...`)
- Runtime configuration via agentcore CLI

**Custom Approach:**
- Uses YAML configuration files (config.yaml)
- Environment-specific configs (dev/test/prod)
- ConfigManager class for dynamic config loading
- Fallback values when config unavailable

**Impact**: Medium - Makes deployment more flexible but diverges from AWS-native approach

#### 3.2 File Handling

**Template Approach:**
- No file upload capability
- Assumes data in Knowledge Base
- Simple text-based interactions

**Custom Approach:**
- Full S3 integration for file uploads
- Session-based file organization
- Support for large files (up to 500MB)
- Multi-format support (logs, PDFs, images)
- Smart file sampling for large files (MCP strategy)

**Impact**: HIGH - Completely new capability, major architectural addition

#### 3.3 Agent Specialization

**Template Approach:**
- Generic assistant agent
- Simple system prompt (~200 words)
- Basic tools (retrieve, current_time, gateway tools)
- General-purpose responses

**Custom Approach:**
- Specialized instrument diagnosis agent
- Extensive system prompt (~1000+ words)
- 13 custom tools for specific workflows
- Domain-specific response formatting
- S3-aware workflow instructions
- MCP sampling strategy for large files

**Impact**: VERY HIGH - Fundamentally different agent purpose and capabilities

#### 3.4 UI/UX Design

**Template Approach:**
- Sidebar-based configuration
- Agent selection dropdown
- Manual session ID management
- Simple chat interface
- Raw response display options

**Custom Approach:**
- Collapsed sidebar (auto-configuration)
- File upload tabs (logs vs documentation)
- Auto-fetch latest agent
- Diagnosis results display section
- Quick action buttons
- ASCII-only response enforcement
- Unicode handling for Windows compatibility

**Impact**: HIGH - Completely redesigned user experience

#### 3.5 Gateway Integration

**Template Approach:**
- Gateway is REQUIRED
- M2M authentication mandatory
- SSM-based gateway URL lookup
- Gateway tools always loaded

**Custom Approach:**
- Gateway is OPTIONAL
- Fallback mode when gateway unavailable
- Graceful degradation
- Focus on local tools over gateway tools

**Impact**: MEDIUM - More resilient but less integrated with gateway services

### 4. Code Reuse Assessment

#### Template Code Still in Use (30-40%)

**Core Framework Components:**
- ✅ BedrockAgentCoreApp and entrypoint pattern
- ✅ Strands Agent, BedrockModel, MCPClient
- ✅ Memory hook integration
- ✅ Streaming queue mechanism
- ✅ Context management
- ✅ OAuth UI components (app_modules/)
- ✅ Infrastructure templates (CloudFormation)
- ✅ Deployment scripts (mostly)
- ✅ Test scripts

**Assessment**: The core AgentCore/Strands framework is fully utilized

#### Custom Code (60-70%)

**New Implementations:**
- ❌ S3 integration layer (s3_integration.py, s3_storage_tools.py)
- ❌ 13 specialized agent tools
- ❌ Configuration management system
- ❌ File processing logic
- ❌ Custom UI components
- ❌ Diagnosis workflow
- ❌ Large file handling (MCP sampling strategy)
- ❌ Multimodal processing
- ❌ Component recognition
- ❌ Cross-source correlation

**Assessment**: Majority of business logic is custom

### 5. Template Dependency Analysis

#### Strong Dependencies (Cannot Remove)

```python
# These template components are ESSENTIAL
from bedrock_agentcore.runtime import BedrockAgentCoreApp  # REQUIRED
from strands import Agent                                   # REQUIRED
from strands.models import BedrockModel                     # REQUIRED
from strands_tools import current_time, retrieve            # REQUIRED
from agent.agent_config.memory_hook_provider import MemoryHook  # REQUIRED
from agent.agent_config.streaming_queue import StreamingQueue   # REQUIRED
from agent.agent_config.context import TemplateContext          # REQUIRED
```

**Assessment**: Core framework dependencies are non-negotiable

#### Weak Dependencies (Could Be Replaced)

```python
# These template components could be replaced
from agent.agent_config.utils import get_ssm_parameter     # REPLACED with config.yaml
from agent.agent_config.access_token import get_gateway_access_token  # BYPASSED with fallback
from strands.tools.mcp import MCPClient                    # OPTIONAL (graceful degradation)
```

**Assessment**: Configuration and gateway integration have been loosened

#### No Dependencies (Fully Custom)

```python
# These are completely custom implementations
from s3_integration import upload_files_to_s3              # CUSTOM
from agent.agent_config.config_manager import ConfigManager # CUSTOM
from agent.agent_config.tools.diagnosis_tools import *     # CUSTOM
from agent.agent_config.tools.log_analysis_tools import *  # CUSTOM
from agent.agent_config.tools.s3_storage_tools import *    # CUSTOM
# ... and 10 more custom tool modules
```

**Assessment**: Business logic is independent of template

### 6. Upgrade Path Analysis

#### Safe to Upgrade (Low Risk)

These template components can be updated without breaking custom code:

1. **Infrastructure templates** (prerequisite/*.yaml)
   - Risk: LOW
   - Impact: Infrastructure improvements
   - Action: Review and merge changes

2. **Deployment scripts** (scripts/*.py)
   - Risk: LOW
   - Impact: Better deployment automation
   - Action: Review and merge changes

3. **OAuth UI components** (app_modules/)
   - Risk: LOW (not heavily used in custom app.py)
   - Impact: Better OAuth experience
   - Action: Review and merge if using app_oauth.py

4. **Test scripts** (tests/)
   - Risk: LOW
   - Impact: Better testing capabilities
   - Action: Review and merge changes

#### Risky to Upgrade (Medium Risk)

These template components have been modified and need careful review:

1. **main.py**
   - Risk: MEDIUM
   - Modifications: Config loading, gateway token handling
   - Action: Manual merge, preserve custom config logic

2. **agent.py**
   - Risk: MEDIUM-HIGH
   - Modifications: Extensive - class rename, tools, system prompt
   - Action: Review template improvements, selectively merge

3. **app.py**
   - Risk: HIGH
   - Modifications: Complete UI redesign
   - Action: Keep custom version, review template for useful patterns

#### Cannot Upgrade (Breaking Changes)

These template components cannot be updated without major refactoring:

1. **System prompt** in agent.py
   - Reason: Completely specialized for instrument diagnosis
   - Action: Keep custom version

2. **File handling** in app.py
   - Reason: S3 integration is core to custom implementation
   - Action: Keep custom version

3. **Configuration system**
   - Reason: YAML-based vs SSM-based
   - Action: Keep custom version

### 7. Recommendations

#### Immediate Actions

1. **Document Custom Code**
   - Create README for each custom tool module
   - Document S3 integration architecture
   - Document configuration system

2. **Separate Custom from Template**
   - Move custom tools to clearly marked directories
   - Add comments indicating template vs custom code
   - Create a CUSTOMIZATIONS.md file

3. **Version Control**
   - Tag current state as "pre-template-sync"
   - Create branch for template updates
   - Document merge strategy

#### Short-term Actions (1-3 months)

1. **Selective Template Updates**
   - Update infrastructure templates
   - Update deployment scripts
   - Update test scripts
   - Review agent.py for useful patterns

2. **Refactor for Maintainability**
   - Extract S3 logic into separate package
   - Create plugin architecture for custom tools
   - Standardize configuration approach

3. **Testing**
   - Add tests for custom tools
   - Add integration tests for S3 workflow
   - Add tests for configuration management

#### Long-term Actions (3-6 months)

1. **Consider Contributing Back**
   - S3 integration could be useful for template
   - Large file handling (MCP sampling) could be contributed
   - Configuration management improvements

2. **Maintain Template Alignment**
   - Set up automated template sync checks
   - Review template updates quarterly
   - Maintain compatibility layer

3. **Architecture Evolution**
   - Consider microservices for S3 handling
   - Consider separate service for file processing
   - Consider plugin system for domain-specific tools

## Conclusion

The instrument-diagnosis-assistant has diverged significantly from the template (70-80% custom code), but maintains the core AgentCore/Strands framework. The divergence is intentional and necessary for the specialized use case.

**Key Findings:**
- ✅ Core framework is intact and well-utilized
- ✅ Custom code is well-organized and purposeful
- ✅ Template updates are possible but require careful review
- ⚠️ Configuration approach has diverged (YAML vs SSM)
- ⚠️ Gateway integration is optional (template assumes required)
- ⚠️ UI/UX is completely custom

**Overall Assessment**: The project successfully extends the template for a specialized use case while maintaining framework compatibility. Template updates should be selective and carefully reviewed.
