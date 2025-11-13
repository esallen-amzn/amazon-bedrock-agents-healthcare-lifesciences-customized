"""Test CRLF detection capability."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from checkers.line_endings_checker import LineEndingsChecker

# Create a test file with CRLF
test_file = Path('instrument-diagnosis-assistant/test_crlf_temp.sh')
test_file.write_bytes(b'#!/bin/bash\r\necho "test"\r\n')

# Run checker
checker = LineEndingsChecker('instrument-diagnosis-assistant')
result = checker.check()

print(f'Status: {result.status}')
print(f'Issues found: {len(result.issues)}')

# Find our test file
for issue in result.issues:
    if 'test_crlf_temp.sh' in issue.file_path:
        print(f'✓ Detected CRLF in test file')
        print(f'  Type: {issue.line_ending_type}')
        print(f'  CRLF count: {issue.crlf_count}')
        print(f'  Fix: {issue.fix_command}')
        break
else:
    print('✗ Failed to detect CRLF in test file')

# Cleanup
test_file.unlink()
print('Test completed!')
