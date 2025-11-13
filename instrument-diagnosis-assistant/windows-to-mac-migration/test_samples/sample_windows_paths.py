"""
Sample file with Windows-specific path patterns for testing.

This file intentionally contains Windows-specific patterns that should be
detected by the path checker.
"""

import os
import subprocess

# Example 1: Windows drive letter (CRITICAL)
config_path = "C:/Users/Admin/config.yaml"
data_dir = "D:\\Data\\Projects"

# Example 2: Hardcoded backslashes (WARNING)
log_file = "logs\\application.log"
temp_path = "temp\\cache\\data.txt"

# Example 3: Windows executable (CRITICAL)
subprocess.run(["notepad.exe", "file.txt"])
os.system("cmd.exe /c dir")

# Example 4: Path concatenation with + (WARNING)
base_path = "/home/user"
full_path = base_path + "/documents"

# Example 5: os.sep usage (INFO)
separator = os.sep
path_with_sep = "folder" + os.sep + "file.txt"

# Example 6: subprocess with shell=True (INFO)
subprocess.run("ls -la", shell=True)

# Correct examples (should not trigger warnings):
from pathlib import Path

# Good: Using pathlib
config = Path.home() / "config" / "settings.yaml"
data = Path("/data/projects")

# Good: Using os.path.join
log_path = os.path.join("logs", "application.log")

# Good: Forward slashes (work on all platforms)
resource = "resources/images/logo.png"
