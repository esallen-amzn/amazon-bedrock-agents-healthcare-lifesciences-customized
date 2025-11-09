"""
Tools package for Instrument Diagnosis Assistant

This package contains all the specialized tools for log analysis,
diagnosis generation, and instrument troubleshooting.
"""

from .sample_tools import SAMPLE_TOOLS
from .log_analysis_tools import LOG_ANALYSIS_TOOLS
from .s3_storage_tools import S3_STORAGE_TOOLS
from .s3_log_analysis_tools import S3_LOG_ANALYSIS_TOOLS
from .diagnosis_tools import DIAGNOSIS_TOOLS

# Export all available tools
ALL_TOOLS = (
    SAMPLE_TOOLS + 
    LOG_ANALYSIS_TOOLS + 
    S3_STORAGE_TOOLS + 
    S3_LOG_ANALYSIS_TOOLS + 
    DIAGNOSIS_TOOLS
)

__all__ = [
    'SAMPLE_TOOLS',
    'LOG_ANALYSIS_TOOLS',
    'S3_STORAGE_TOOLS',
    'S3_LOG_ANALYSIS_TOOLS',
    'DIAGNOSIS_TOOLS',
    'ALL_TOOLS'
]