#!/usr/bin/env python3
"""
AgentCore Project Generator

This script creates a new AgentCore application project based on the agentcore_template.
It copies the template structure and allows customization of project name and configuration.
"""

import os
import shutil
import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml
from config_models import (
    ProjectConfig, AgentConfig, DeploymentConfig, ToolDefinition,
    ConfigurationManager, validate_configuration
)


class ProjectGenerator:
    """Generates new AgentCore projects based on the template."""
    
    def __init__(self, template_path: str = "agentcore_template"):
        """
        Initialize the project generator.
        
        Args:
            template_path: Path to the agentcore_template directory
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")
    
    def validate_project_name(self, name: str) -> str:
        """
        Validate and sanitize project name.
        
        Args:
            name: Raw project name input
            
        Returns:
            Sanitized project name
            
        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError("Project name cannot be empty")
        
        # Remove invalid characters and convert to lowercase
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name.strip())
        sanitized = sanitized.lower()
        
        # Ensure it starts with a letter or underscore
        if not re.match(r'^[a-zA-Z_]', sanitized):
            sanitized = f"agent-{sanitized}"
        
        # Remove consecutive dashes/underscores
        sanitized = re.sub(r'[-_]+', '-', sanitized)
        
        # Remove leading/trailing dashes
        sanitized = sanitized.strip('-')
        
        if len(sanitized) < 3:
            raise ValueError("Project name must be at least 3 characters long")
        
        if len(sanitized) > 50:
            raise ValueError("Project name must be less than 50 characters")
        
        return sanitized
    
    def substitute_variables(self, content: str, variables: Dict[str, str]) -> str:
        """
        Substitute template variables in file content.
        
        Args:
            content: File content with template variables
            variables: Dictionary of variable substitutions
            
        Returns:
            Content with variables substituted
        """
        for key, value in variables.items():
            # Replace various template patterns
            patterns = [
                f"{{{{{key}}}}}",  # {{variable}}
                f"${{{key}}}",     # ${variable}
                f"<{key}>",        # <variable>
            ]
            
            for pattern in patterns:
                content = content.replace(pattern, value)
        
        return content
    
    def copy_template_file(self, src_path: Path, dest_path: Path, variables: Dict[str, str]):
        """
        Copy a template file with variable substitution.
        
        Args:
            src_path: Source file path
            dest_path: Destination file path
            variables: Variables for substitution
        """
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Binary files that should be copied without modification
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.ttf', '.woff', '.woff2'}
        
        if src_path.suffix.lower() in binary_extensions:
            # Copy binary files as-is
            shutil.copy2(src_path, dest_path)
        else:
            # Text files - read, substitute, and write
            try:
                with open(src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Perform variable substitution
                content = self.substitute_variables(content, variables)
                
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except UnicodeDecodeError:
                # If we can't decode as text, copy as binary
                shutil.copy2(src_path, dest_path)
    
    def get_template_variables(self, project_name: str, **kwargs) -> Dict[str, str]:
        """
        Generate template variables for substitution.
        
        Args:
            project_name: Sanitized project name
            **kwargs: Additional configuration options
            
        Returns:
            Dictionary of template variables
        """
        # Convert project name variations
        project_title = project_name.replace('-', ' ').replace('_', ' ').title()
        project_class = ''.join(word.capitalize() for word in project_name.replace('-', '_').split('_'))
        project_upper = project_name.upper().replace('-', '_')
        
        variables = {
            'PROJECT_NAME': project_name,
            'PROJECT_TITLE': project_title,
            'PROJECT_CLASS': project_class,
            'PROJECT_UPPER': project_upper,
            'project_name': project_name,
            'project_title': project_title,
            'project_class': project_class,
            'project_upper': project_upper,
        }
        
        # Add any additional variables from kwargs
        variables.update(kwargs)
        
        return variables
    
    def create_project(self, project_name: str, output_dir: str = ".", **config) -> Path:
        """
        Create a new project based on the template.
        
        Args:
            project_name: Name of the new project
            output_dir: Directory where the project should be created
            **config: Additional configuration options
            
        Returns:
            Path to the created project directory
        """
        # Validate and sanitize project name
        sanitized_name = self.validate_project_name(project_name)
        
        # Create output directory
        output_path = Path(output_dir)
        project_path = output_path / sanitized_name
        
        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")
        
        print(f"Creating project '{sanitized_name}' at {project_path}")
        
        # Generate template variables
        variables = self.get_template_variables(sanitized_name, **config)
        
        # Copy template structure
        self._copy_directory_structure(self.template_path, project_path, variables)
        
        # Create additional project-specific files
        self._create_project_config(project_path, sanitized_name, variables, **config)
        
        print(f"✅ Project '{sanitized_name}' created successfully!")
        print(f"📁 Location: {project_path.absolute()}")
        print(f"🚀 Next steps:")
        print(f"   cd {sanitized_name}")
        print(f"   pip install -r dev-requirements.txt")
        print(f"   ./scripts/prereq.sh")
        
        return project_path
    
    def _copy_directory_structure(self, src_dir: Path, dest_dir: Path, variables: Dict[str, str]):
        """
        Recursively copy directory structure with variable substitution.
        
        Args:
            src_dir: Source directory
            dest_dir: Destination directory
            variables: Variables for substitution
        """
        for item in src_dir.iterdir():
            src_path = src_dir / item.name
            dest_path = dest_dir / item.name
            
            if item.is_dir():
                # Recursively copy directories
                dest_path.mkdir(parents=True, exist_ok=True)
                self._copy_directory_structure(src_path, dest_path, variables)
            else:
                # Copy files with variable substitution
                self.copy_template_file(src_path, dest_path, variables)
    
    def _create_project_config(self, project_path: Path, project_name: str, variables: Dict[str, str], **config_options):
        """
        Create project-specific configuration files using configuration models.
        
        Args:
            project_path: Path to the project directory
            project_name: Project name
            variables: Template variables
            **config_options: Additional configuration options
        """
        # Create configuration using the configuration models
        project_config = ConfigurationManager.create_default_config(
            project_name=project_name,
            description=f'Custom AgentCore application: {variables["PROJECT_TITLE"]}',
            **config_options
        )
        
        # Validate the configuration
        errors = validate_configuration(project_config)
        if errors:
            print("⚠️  Configuration validation warnings:")
            for error in errors:
                print(f"   - {error}")
        
        # Save configuration to .agentcore.yaml
        config_path = project_path / '.agentcore.yaml'
        ConfigurationManager.save_to_file(project_config, config_path, format='yaml')
        
        # Create project-specific README
        readme_content = f"""# {variables['PROJECT_TITLE']}

A custom AgentCore application built from the healthcare and life sciences template.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r dev-requirements.txt
   ```

2. **Set up AWS infrastructure:**
   ```bash
   ./scripts/prereq.sh
   ```

3. **Deploy AgentCore components:**
   ```bash
   python scripts/agentcore_gateway.py
   python scripts/agentcore_memory.py
   python scripts/agentcore_agent_runtime.py
   ```

4. **Run the application:**
   ```bash
   streamlit run app_oauth.py  # For OAuth authentication
   # OR
   streamlit run app.py        # For IAM authentication
   ```

## Configuration

Edit `.agentcore.yaml` to customize your agent's behavior, tools, and deployment settings.

## Project Structure

- `agent/` - Agent configuration and custom tools
- `app_modules/` - Streamlit UI components
- `scripts/` - Deployment and management scripts
- `prerequisite/` - Infrastructure setup files
- `tests/` - Test files

## Documentation

See the original [AgentCore Template README](../agentcore_template/README.md) for detailed documentation.
"""
        
        readme_path = project_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a new AgentCore application project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project_generator.py my-healthcare-agent
  python project_generator.py "Financial Analysis Agent" --output-dir ./projects
  python project_generator.py research-assistant --auth-mode iam --region us-west-2
        """
    )
    
    parser.add_argument(
        'project_name',
        help='Name of the new project'
    )
    
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory where the project should be created (default: current directory)'
    )
    
    parser.add_argument(
        '--template-path',
        default='agentcore_template',
        help='Path to the agentcore_template directory (default: agentcore_template)'
    )
    
    parser.add_argument(
        '--auth-mode',
        choices=['oauth', 'iam'],
        default='oauth',
        help='Authentication mode (default: oauth)'
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for deployment (default: us-east-1)'
    )
    
    parser.add_argument(
        '--model-id',
        default='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        help='Bedrock model ID to use (default: Claude 3.5 Sonnet)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create project generator
        generator = ProjectGenerator(args.template_path)
        
        # Generate project
        project_path = generator.create_project(
            project_name=args.project_name,
            output_dir=args.output_dir,
            auth_mode=args.auth_mode,
            aws_region=args.region,
            model_id=args.model_id
        )
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())