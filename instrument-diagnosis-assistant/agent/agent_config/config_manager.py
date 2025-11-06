"""
Configuration Management System for Instrument Diagnosis Assistant

This module handles loading, validation, and management of all system configuration
parameters from the config.yaml file.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for Amazon Nova models"""
    text_model: str = "us.amazon.nova-pro-v1:0"
    multimodal_model: str = "us.amazon.nova-canvas-v1:0"
    embedding_model: str = "amazon.titan-embed-text-v2:0"
    temperature: float = 0.3
    top_p: float = 0.9
    max_tokens: int = 8192


@dataclass
class KnowledgeBaseConfig:
    """Configuration for Bedrock Knowledge Base"""
    kb_id: str = ""
    retrieval_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_results": 10,
        "score_threshold": 0.7,
        "reranking_enabled": True
    })


@dataclass
class LogAnalysisConfig:
    """Configuration for log analysis functionality"""
    chunk_size_mb: int = 50
    failure_threshold: float = 0.8
    confidence_threshold: float = 0.75
    max_file_size_mb: int = 250
    supported_formats: List[str] = field(default_factory=lambda: ["txt", "log", "csv"])


@dataclass
class ComponentRecognitionConfig:
    """Configuration for component recognition"""
    entity_confidence: float = 0.6
    naming_variations: bool = True
    component_types: List[str] = field(default_factory=lambda: ["hardware", "software", "firmware"])
    max_components_per_doc: int = 100


@dataclass
class DocumentProcessingConfig:
    """Configuration for multi-modal document processing"""
    supported_formats: List[str] = field(default_factory=lambda: ["pdf", "docx", "txt", "png", "jpg", "jpeg"])
    max_document_size_mb: int = 100
    image_processing: Dict[str, Any] = field(default_factory=lambda: {
        "max_width": 2048,
        "max_height": 2048,
        "quality": 85
    })


@dataclass
class CorrelationConfig:
    """Configuration for cross-source correlation"""
    component_similarity_threshold: float = 0.8
    max_correlation_distance: int = 3
    fuzzy_matching: bool = True


@dataclass
class DeploymentConfig:
    """Configuration for deployment settings"""
    aws_region: str = "us-east-1"
    auth_mode: str = "oauth"
    environment: str = "development"
    debug_logging: bool = False
    session_timeout: int = 30


@dataclass
class UIConfig:
    """Configuration for user interface"""
    max_upload_size_mb: int = 250
    allowed_upload_types: List[str] = field(default_factory=lambda: ["txt", "log", "csv", "pdf", "docx", "png", "jpg", "jpeg"])
    results_display: Dict[str, Any] = field(default_factory=lambda: {
        "max_results_per_page": 20,
        "show_confidence_scores": True,
        "show_detailed_analysis": True
    })


@dataclass
class PerformanceConfig:
    """Configuration for performance settings"""
    max_concurrent_analyses: int = 5
    request_timeout: int = 300
    memory_limits: Dict[str, int] = field(default_factory=lambda: {
        "max_memory_mb": 2048,
        "gc_threshold": 1024
    })


@dataclass
class ValidationConfig:
    """Configuration validation rules"""
    required_fields: List[str] = field(default_factory=lambda: [
        "models.text_model",
        "models.multimodal_model",
        "deployment.aws_region"
    ])
    constraints: Dict[str, List[float]] = field(default_factory=lambda: {
        "temperature": [0.0, 1.0],
        "top_p": [0.0, 1.0],
        "confidence_threshold": [0.0, 1.0],
        "failure_threshold": [0.0, 1.0]
    })


@dataclass
class DiagnosisConfig:
    """Main configuration class containing all sub-configurations"""
    models: ModelConfig = field(default_factory=ModelConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    log_analysis: LogAnalysisConfig = field(default_factory=LogAnalysisConfig)
    component_recognition: ComponentRecognitionConfig = field(default_factory=ComponentRecognitionConfig)
    document_processing: DocumentProcessingConfig = field(default_factory=DocumentProcessingConfig)
    correlation: CorrelationConfig = field(default_factory=CorrelationConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class ConfigManager:
    """
    Configuration Manager for the Instrument Diagnosis Assistant
    
    Handles loading, validation, and access to configuration parameters
    from the config.yaml file.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[DiagnosisConfig] = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path"""
        # Look for config.yaml in the project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # Go up to project root
        config_path = project_root / "config.yaml"
        
        if not config_path.exists():
            # Fallback to current directory
            config_path = Path("config.yaml")
        
        return str(config_path)
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file not found at {self.config_path}. Using default configuration.")
                self.config = DiagnosisConfig()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            if not config_data:
                logger.warning("Configuration file is empty. Using default configuration.")
                self.config = DiagnosisConfig()
                return
            
            # Parse configuration sections
            self.config = self._parse_config(config_data)
            
            # Validate configuration
            self._validate_config()
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> DiagnosisConfig:
        """Parse configuration data into structured objects"""
        try:
            # Parse each configuration section
            models_config = ModelConfig(**config_data.get('models', {}))
            kb_config = KnowledgeBaseConfig(**config_data.get('knowledge_base', {}))
            log_config = LogAnalysisConfig(**config_data.get('log_analysis', {}))
            component_config = ComponentRecognitionConfig(**config_data.get('component_recognition', {}))
            doc_config = DocumentProcessingConfig(**config_data.get('document_processing', {}))
            correlation_config = CorrelationConfig(**config_data.get('correlation', {}))
            deployment_config = DeploymentConfig(**config_data.get('deployment', {}))
            ui_config = UIConfig(**config_data.get('ui', {}))
            performance_config = PerformanceConfig(**config_data.get('performance', {}))
            validation_config = ValidationConfig(**config_data.get('validation', {}))
            
            return DiagnosisConfig(
                models=models_config,
                knowledge_base=kb_config,
                log_analysis=log_config,
                component_recognition=component_config,
                document_processing=doc_config,
                correlation=correlation_config,
                deployment=deployment_config,
                ui=ui_config,
                performance=performance_config,
                validation=validation_config
            )
            
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration structure: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        # Check required fields
        for field_path in self.config.validation.required_fields:
            if not self._get_nested_value(field_path):
                raise ConfigurationError(f"Required configuration field missing: {field_path}")
        
        # Check value constraints
        for field_name, (min_val, max_val) in self.config.validation.constraints.items():
            value = self._get_config_value(field_name)
            if value is not None and not (min_val <= value <= max_val):
                raise ConfigurationError(
                    f"Configuration value '{field_name}' ({value}) must be between {min_val} and {max_val}"
                )
        
        # Validate model IDs
        if not self.config.models.text_model.startswith("us.amazon.nova"):
            logger.warning(f"Text model '{self.config.models.text_model}' is not an Amazon Nova model")
        
        if not self.config.models.multimodal_model.startswith("us.amazon.nova"):
            logger.warning(f"Multimodal model '{self.config.models.multimodal_model}' is not an Amazon Nova model")
        
        logger.info("Configuration validation completed successfully")
    
    def _get_nested_value(self, field_path: str) -> Any:
        """Get a nested configuration value using dot notation"""
        parts = field_path.split('.')
        value = self.config
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def _get_config_value(self, field_name: str) -> Any:
        """Get configuration value by field name"""
        # Map field names to actual config paths
        field_mapping = {
            'temperature': self.config.models.temperature,
            'top_p': self.config.models.top_p,
            'confidence_threshold': self.config.log_analysis.confidence_threshold,
            'failure_threshold': self.config.log_analysis.failure_threshold
        }
        
        return field_mapping.get(field_name)
    
    def get_config(self) -> DiagnosisConfig:
        """Get the complete configuration object"""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        return self.config
    
    def get_model_config(self) -> ModelConfig:
        """Get model configuration"""
        return self.get_config().models
    
    def get_knowledge_base_config(self) -> KnowledgeBaseConfig:
        """Get knowledge base configuration"""
        return self.get_config().knowledge_base
    
    def get_log_analysis_config(self) -> LogAnalysisConfig:
        """Get log analysis configuration"""
        return self.get_config().log_analysis
    
    def get_component_recognition_config(self) -> ComponentRecognitionConfig:
        """Get component recognition configuration"""
        return self.get_config().component_recognition
    
    def get_document_processing_config(self) -> DocumentProcessingConfig:
        """Get document processing configuration"""
        return self.get_config().document_processing
    
    def get_correlation_config(self) -> CorrelationConfig:
        """Get correlation configuration"""
        return self.get_config().correlation
    
    def get_deployment_config(self) -> DeploymentConfig:
        """Get deployment configuration"""
        return self.get_config().deployment
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return self.get_config().ui
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        return self.get_config().performance
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self._load_config()
        logger.info("Configuration reloaded")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration values dynamically
        
        Args:
            updates: Dictionary of configuration updates using dot notation
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        for field_path, value in updates.items():
            self._set_nested_value(field_path, value)
        
        # Re-validate after updates
        self._validate_config()
        logger.info(f"Configuration updated: {list(updates.keys())}")
    
    def _set_nested_value(self, field_path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation"""
        parts = field_path.split('.')
        obj = self.config
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise ConfigurationError(f"Invalid configuration path: {field_path}")
        
        # Set the final value
        final_part = parts[-1]
        if hasattr(obj, final_part):
            setattr(obj, final_part, value)
        else:
            raise ConfigurationError(f"Invalid configuration field: {field_path}")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> DiagnosisConfig:
    """Get the current configuration"""
    return get_config_manager().get_config()


def reload_config() -> None:
    """Reload the configuration from file"""
    get_config_manager().reload_config()