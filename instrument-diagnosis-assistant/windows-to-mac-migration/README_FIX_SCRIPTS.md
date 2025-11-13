# Automated Fix Scripts

This directory contains automated fix scripts for resolving Windows-to-Mac migration issues. These scripts are designed to be safe, with validation, backup options, and detailed logging.

## Available Scripts

### 1. fix_permissions.sh

Fixes execute permissions on shell scripts that were migrated from Windows.

**Features:**
- ✅ Validates files exist before modification
- ✅ Checks current permissions and skips already-executable files
- ✅ Optional backup of permission states
- ✅ Dry-run mode to preview changes
- ✅ Colored output with detailed status
- ✅ Summary statistics

**Usage:**

```bash
# Preview what would be fixed (recommended first step)
./windows-to-mac-migration/fix_permissions.sh --dry-run

# Fix permissions without backup
./windows-to-mac-migration/fix_permissions.sh

# Fix permissions with backup
./windows-to-mac-migration/fix_permissions.sh --backup

# Show help
./windows-to-mac-migration/fix_permissions.sh --help
```

**What it fixes:**
- `scripts/cleanup.sh`
- `scripts/deploy.sh`
- `scripts/list_ssm_parameters.sh`
- `scripts/prereq.sh`
- `start.sh`

**Restore from backup:**
```bash
# If you created a backup, you can restore with:
while IFS=: read -r file perms; do chmod $perms $file; done < backups/permissions_TIMESTAMP/permissions.log
```

### 2. fix_line_endings.sh

Converts Windows line endings (CRLF) to Unix line endings (LF) across the project.

**Features:**
- ✅ Scans multiple file types (.sh, .py, .yaml, .json, .md, .txt)
- ✅ Validates files before modification
- ✅ Skips files that already have correct line endings
- ✅ Optional backup of original files
- ✅ Dry-run mode to preview changes
- ✅ Supports both dos2unix and sed (automatic fallback)
- ✅ Colored output with detailed status
- ✅ Summary statistics

**Usage:**

```bash
# Preview what would be fixed (recommended first step)
./windows-to-mac-migration/fix_line_endings.sh --dry-run

# Fix line endings without backup
./windows-to-mac-migration/fix_line_endings.sh

# Fix line endings with backup
./windows-to-mac-migration/fix_line_endings.sh --backup

# Show help
./windows-to-mac-migration/fix_line_endings.sh --help
```

**What it fixes:**
- Shell scripts (*.sh) - CRITICAL
- Python files (*.py) - CRITICAL
- YAML files (*.yaml, *.yml) - WARNING
- JSON files (*.json) - WARNING
- Markdown files (*.md) - WARNING
- Text files (*.txt) - WARNING

**Restore from backup:**
```bash
# If you created a backup, you can restore with:
while IFS=' -> ' read -r original backup; do cp "$backup" "$original"; done < backups/line_endings_TIMESTAMP/backup.log
```

**Installing dos2unix (optional but recommended):**
```bash
# macOS
brew install dos2unix

# The script will automatically use dos2unix if available,
# otherwise it falls back to sed
```

## Generator Scripts

These scripts automatically generate fix scripts based on detected issues:

### generate_fix_script.py

Generates a fix script for permission issues by scanning the project.

```bash
python windows-to-mac-migration/generate_fix_script.py
```

### generate_line_endings_fix.py

Generates a fix script for line ending issues by scanning the project.

```bash
python windows-to-mac-migration/generate_line_endings_fix.py
```

## Safety Features

Both fix scripts include multiple safety features:

1. **Validation**: Files are checked before modification
2. **Dry-run mode**: Preview changes without applying them
3. **Backup option**: Create backups before making changes
4. **Skip logic**: Already-correct files are skipped
5. **Error handling**: Failed operations are reported
6. **Detailed logging**: See exactly what was changed
7. **Restore instructions**: Easy rollback if needed

## Recommended Workflow

1. **Run dry-run first** to see what would be changed:
   ```bash
   ./windows-to-mac-migration/fix_permissions.sh --dry-run
   ./windows-to-mac-migration/fix_line_endings.sh --dry-run
   ```

2. **Review the output** to ensure changes are expected

3. **Run with backup** for safety:
   ```bash
   ./windows-to-mac-migration/fix_permissions.sh --backup
   ./windows-to-mac-migration/fix_line_endings.sh --backup
   ```

4. **Test the application** to ensure everything works

5. **Remove backups** once confirmed working:
   ```bash
   rm -rf backups/
   ```

## Exit Codes

Both scripts use standard exit codes:
- `0`: Success (all files fixed or already correct)
- `1`: Failure (one or more files failed to fix)

## Output Colors

- 🟢 **Green**: Successfully fixed
- 🟡 **Yellow**: Already correct / skipped / warnings
- 🔴 **Red**: Failed to fix
- 🔵 **Blue**: Informational messages

## Requirements

### fix_permissions.sh
- Bash shell
- `chmod` command (standard on macOS/Linux)
- `stat` command (standard on macOS/Linux)

### fix_line_endings.sh
- Bash shell
- `sed` command (standard on macOS/Linux)
- `dos2unix` command (optional, recommended)
- `find` and `grep` commands (standard on macOS/Linux)

## Troubleshooting

### Permission denied when running scripts

Make sure the scripts are executable:
```bash
chmod +x windows-to-mac-migration/fix_permissions.sh
chmod +x windows-to-mac-migration/fix_line_endings.sh
```

### dos2unix not found

This is not an error - the script will automatically fall back to using `sed`. However, for better performance, you can install dos2unix:
```bash
brew install dos2unix
```

### Backup directory already exists

The backup directory includes a timestamp, so this should rarely happen. If it does, either:
- Wait a minute and try again (timestamp will be different)
- Manually remove the old backup directory
- Run without `--backup` flag

### Script reports files as "already correct"

This is normal and means those files don't need fixing. The script only modifies files that actually have issues.

## Integration with Migration Testing

These fix scripts are designed to work with the migration testing framework:

1. Run the migration test to identify issues:
   ```bash
   python windows-to-mac-migration/test_migration.py
   ```

2. Use the fix scripts to resolve issues:
   ```bash
   ./windows-to-mac-migration/fix_permissions.sh
   ./windows-to-mac-migration/fix_line_endings.sh
   ```

3. Re-run the migration test to verify fixes:
   ```bash
   python windows-to-mac-migration/test_migration.py
   ```

## Requirements Addressed

These scripts address the following requirements from the migration specification:

- **Requirement 2.1**: Set execute permissions on all .sh files
- **Requirement 2.2**: Set execute permissions on start.sh
- **Requirement 1.2**: Detect and fix files with Windows line endings (CRLF)

## License

These scripts are part of the Instrument Diagnosis Assistant project and follow the same license.
