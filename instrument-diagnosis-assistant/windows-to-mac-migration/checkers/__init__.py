"""Checker modules for Windows-to-Mac migration testing."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import TestResult


class BaseChecker(ABC):
    """Base class for all migration checkers."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
    
    @abstractmethod
    def check(self):
        """Run the checker and return results."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this checker."""
        pass


# Import checkers for easy access
from .permissions_checker import PermissionsChecker
from .line_endings_checker_adapter import LineEndingsChecker
from .path_checker_adapter import PathCheckerAdapter
from .dependency_checker_adapter import DependencyCheckerAdapter
from .aws_checker_adapter import AWSCheckerAdapter

__all__ = ['BaseChecker', 'PermissionsChecker', 'LineEndingsChecker', 'PathCheckerAdapter', 'DependencyCheckerAdapter', 'AWSCheckerAdapter']
