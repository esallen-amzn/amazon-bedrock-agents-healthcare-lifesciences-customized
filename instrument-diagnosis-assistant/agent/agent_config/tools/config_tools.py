"""
Configuration management tools for the Instrument Diagnosis Assistant

These tools provide configuration validation, model information, and system status
capabilities for the diagnosis assistant.
"""

from typing import Dict, Any, List
import logging
from strands import tool
from ..config_manager import get_config_manager, ConfigurationError

logger = logging.getLogger(__name__)


@tool(
    name="Get_system_configuration",
    description="Gets current system configuration including model settings, thresholds, and deployment parameters",
)
def get_system_configuration() -> Dict[str, Any]:
    """
    Get current system configuration information.
    
    Returns:
        Dict containing current configuration settings
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        return {
            "models": {
                "text_model": config.models.text_model,
                "multimodal_model": config.models.multimodal_model,
                "temperature": config.models.temperature,
                "top_p": config.models.top_p,
                "max_tokens": config.models.max_tokens
            },
            "log_analysis": {
                "chunk_size_mb": config.log_analysis.chunk_size_mb,
                "failure_threshold": config.log_analysis.failure_threshold,
                "confidence_threshold": config.log_analysis.confidence_threshold,
                "max_file_size_mb": config.log_analysis.max_file_size_mb,
                "supported_formats": config.log_analysis.supported_formats
            },
            "component_recognition": {
                "entity_confidence": config.component_recognition.entity_confidence,
                "naming_variations": config.component_recognition.naming_variations,
                "component_types": config.component_recognition.component_types,
                "max_components_per_doc": config.component_recognition.max_components_per_doc
            },
            "deployment": {
                "aws_region": config.deployment.aws_region,
                "environment": config.deployment.environment,
                "debug_logging": config.deployment.debug_logging
            },
            "performance": {
                "max_concurrent_analyses": config.performance.max_concurrent_analyses,
                "request_timeout": config.performance.request_timeout,
                "memory_limits": config.performance.memory_limits
            }
        }
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return {"error": f"Configuration error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error getting configuration: {e}")
        return {"error": f"Unexpected error: {e}"}


@tool(
    name="Validate_configuration",
    description="Validates current configuration settings and reports any issues or warnings",
)
def validate_configuration() -> Dict[str, Any]:
    """
    Validate current configuration settings.
    
    Returns:
        Dict containing validation results and any issues found
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        validation_results = {
            "status": "valid",
            "warnings": [],
            "errors": [],
            "checks_performed": []
        }
        
        # Check required fields
        required_checks = [
            ("models.text_model", config.models.text_model),
            ("models.multimodal_model", config.models.multimodal_model),
            ("deployment.aws_region", config.deployment.aws_region)
        ]
        
        for field_name, value in required_checks:
            validation_results["checks_performed"].append(f"Required field: {field_name}")
            if not value:
                validation_results["errors"].append(f"Required field '{field_name}' is missing or empty")
                validation_results["status"] = "invalid"
        
        # Check value ranges
        range_checks = [
            ("temperature", config.models.temperature, 0.0, 1.0),
            ("top_p", config.models.top_p, 0.0, 1.0),
            ("confidence_threshold", config.log_analysis.confidence_threshold, 0.0, 1.0),
            ("failure_threshold", config.log_analysis.failure_threshold, 0.0, 1.0),
            ("entity_confidence", config.component_recognition.entity_confidence, 0.0, 1.0)
        ]
        
        for field_name, value, min_val, max_val in range_checks:
            validation_results["checks_performed"].append(f"Range check: {field_name}")
            if not (min_val <= value <= max_val):
                validation_results["errors"].append(
                    f"Field '{field_name}' value {value} is outside valid range [{min_val}, {max_val}]"
                )
                validation_results["status"] = "invalid"
        
        # Check model IDs
        validation_results["checks_performed"].append("Model ID validation")
        if not config.models.text_model.startswith("us.amazon.nova"):
            validation_results["warnings"].append(
                f"Text model '{config.models.text_model}' is not an Amazon Nova model"
            )
        
        if not config.models.multimodal_model.startswith("us.amazon.nova"):
            validation_results["warnings"].append(
                f"Multimodal model '{config.models.multimodal_model}' is not an Amazon Nova model"
            )
        
        # Check file size limits
        validation_results["checks_performed"].append("File size limits")
        if config.log_analysis.max_file_size_mb > 500:
            validation_results["warnings"].append(
                f"Maximum log file size ({config.log_analysis.max_file_size_mb}MB) is very large and may cause performance issues"
            )
        
        if config.document_processing.max_document_size_mb > 200:
            validation_results["warnings"].append(
                f"Maximum document size ({config.document_processing.max_document_size_mb}MB) is very large and may cause performance issues"
            )
        
        # Set final status
        if validation_results["warnings"] and validation_results["status"] == "valid":
            validation_results["status"] = "valid_with_warnings"
        
        return validation_results
        
    except ConfigurationError as e:
        logger.error(f"Configuration error during validation: {e}")
        return {
            "status": "error",
            "errors": [f"Configuration error: {e}"],
            "warnings": [],
            "checks_performed": []
        }
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return {
            "status": "error",
            "errors": [f"Unexpected error: {e}"],
            "warnings": [],
            "checks_performed": []
        }


@tool(
    name="Get_model_information",
    description="Gets information about the currently configured Amazon Nova models and their capabilities",
)
def get_model_information() -> Dict[str, Any]:
    """
    Get information about configured models.
    
    Returns:
        Dict containing model information and capabilities
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        model_info = {
            "text_model": {
                "model_id": config.models.text_model,
                "type": "text_analysis",
                "capabilities": [
                    "Log analysis and pattern recognition",
                    "Component identification from text",
                    "Failure diagnosis and reasoning",
                    "Cross-source correlation analysis"
                ],
                "parameters": {
                    "temperature": config.models.temperature,
                    "top_p": config.models.top_p,
                    "max_tokens": config.models.max_tokens
                }
            },
            "multimodal_model": {
                "model_id": config.models.multimodal_model,
                "type": "multimodal_analysis",
                "capabilities": [
                    "Document processing with images and diagrams",
                    "Visual troubleshooting guide analysis",
                    "Text-image correlation",
                    "Multi-modal content understanding"
                ],
                "parameters": {
                    "temperature": config.models.temperature,
                    "top_p": config.models.top_p,
                    "max_tokens": config.models.max_tokens
                }
            }
        }
        
        # Add model family information
        for model_key, model_data in model_info.items():
            model_id = model_data["model_id"]
            if "nova-pro" in model_id:
                model_data["family"] = "Nova Pro"
                model_data["description"] = "High-performance text model for complex reasoning and analysis"
            elif "nova-canvas" in model_id:
                model_data["family"] = "Nova Canvas"
                model_data["description"] = "Multi-modal model for processing text, images, and documents"
            elif "nova-lite" in model_id:
                model_data["family"] = "Nova Lite"
                model_data["description"] = "Lightweight model for basic text processing"
            else:
                model_data["family"] = "Unknown"
                model_data["description"] = "Model family not recognized"
        
        return model_info
        
    except ConfigurationError as e:
        logger.error(f"Configuration error getting model information: {e}")
        return {"error": f"Configuration error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error getting model information: {e}")
        return {"error": f"Unexpected error: {e}"}


@tool(
    name="Update_configuration_parameter",
    description="Updates a specific configuration parameter. Use dot notation for nested parameters (e.g., 'models.temperature')",
)
def update_configuration_parameter(parameter_path: str, new_value: Any) -> Dict[str, Any]:
    """
    Update a specific configuration parameter.
    
    Args:
        parameter_path: Dot-notation path to the parameter (e.g., 'models.temperature')
        new_value: New value for the parameter
    
    Returns:
        Dict containing update result
    """
    try:
        config_manager = get_config_manager()
        
        # Update the configuration
        config_manager.update_config({parameter_path: new_value})
        
        return {
            "status": "success",
            "message": f"Successfully updated {parameter_path} to {new_value}",
            "parameter_path": parameter_path,
            "new_value": new_value
        }
        
    except ConfigurationError as e:
        logger.error(f"Configuration error updating parameter: {e}")
        return {
            "status": "error",
            "message": f"Configuration error: {e}",
            "parameter_path": parameter_path,
            "new_value": new_value
        }
    except Exception as e:
        logger.error(f"Unexpected error updating parameter: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}",
            "parameter_path": parameter_path,
            "new_value": new_value
        }


@tool(
    name="Reload_configuration",
    description="Reloads configuration from the config.yaml file, useful after manual file changes",
)
def reload_configuration() -> Dict[str, Any]:
    """
    Reload configuration from file.
    
    Returns:
        Dict containing reload result
    """
    try:
        config_manager = get_config_manager()
        config_manager.reload_config()
        
        return {
            "status": "success",
            "message": "Configuration reloaded successfully from config.yaml"
        }
        
    except ConfigurationError as e:
        logger.error(f"Configuration error during reload: {e}")
        return {
            "status": "error",
            "message": f"Configuration error: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during reload: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}"
        }