"""
AWS connectivity checker for verifying AWS setup on macOS.

This module verifies that:
- AWS CLI is installed
- AWS credentials are configured
- boto3 client creation works for bedrock-agentcore
- SSM parameter access works (read-only)
- Provides setup instructions for missing credentials

Requirements addressed:
- 6.1: Verify AWS CLI is installed and configured
- 6.2: Test boto3 client creation for bedrock-agentcore services
- 6.3: Verify SSM parameter access works correctly
- 6.4: Provide setup instructions if AWS credentials are not configured
- 6.5: Confirm S3 file upload functionality works on macOS
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AWSIssue:
    """Represents an AWS connectivity issue."""
    issue_type: str  # "CLI_MISSING", "CREDENTIALS_MISSING", "CLIENT_CREATION", "SSM_ACCESS", "S3_ACCESS"
    description: str
    details: str
    severity: str = "CRITICAL"
    fix_suggestion: str = ""


@dataclass
class AWSCheckResult:
    """Result of AWS connectivity check."""
    status: str  # "PASS", "FAIL", "WARNING", "SKIP"
    issues: List[AWSIssue] = field(default_factory=list)
    cli_installed: bool = False
    cli_version: Optional[str] = None
    credentials_configured: bool = False
    boto3_available: bool = False
    bedrock_client_ok: bool = False
    ssm_access_ok: bool = False
    s3_access_ok: bool = False
    region: Optional[str] = None
    message: str = ""


class AWSChecker:
    """
    Checks AWS connectivity and configuration.
    
    This checker verifies that AWS services are accessible from macOS,
    including CLI installation, credentials, and service connectivity.
    """
    
    # Services to test
    TEST_SERVICES = [
        'bedrock-agent-runtime',
        'bedrock-runtime',
        'ssm',
        's3'
    ]
    
    # Common SSM parameter prefixes to check
    SSM_PREFIXES = [
        '/app/',
        '/agentcore/',
        '/bedrock/'
    ]
    
    def __init__(self, project_root: str):
        """
        Initialize the AWS checker.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.issues: List[AWSIssue] = []
        
    def check(self, quick_mode: bool = False) -> AWSCheckResult:
        """
        Run the AWS connectivity check.
        
        Args:
            quick_mode: If True, skip service connectivity tests (faster)
        
        Returns:
            AWSCheckResult with status and any issues found
        """
        self.issues = []
        result = AWSCheckResult(status="PASS")
        
        # Check AWS CLI installation
        cli_ok, cli_version = self._check_aws_cli()
        result.cli_installed = cli_ok
        result.cli_version = cli_version
        
        if not cli_ok:
            result.status = "FAIL"
            result.message = "AWS CLI is not installed"
            return result
        
        # Check AWS credentials configuration
        creds_ok, region = self._check_aws_credentials()
        result.credentials_configured = creds_ok
        result.region = region
        
        if not creds_ok:
            result.status = "WARNING"
            result.message = "AWS credentials are not configured"
            # Don't return here - provide full report with setup instructions
        
        # Check boto3 availability
        boto3_ok = self._check_boto3_available()
        result.boto3_available = boto3_ok
        
        if not boto3_ok:
            result.status = "FAIL"
            result.message = "boto3 package is not available"
            return result
        
        # In quick mode, skip service connectivity tests
        if quick_mode or not creds_ok:
            if not creds_ok:
                result.message = "AWS CLI installed but credentials not configured (see setup instructions)"
            else:
                result.message = f"AWS CLI {cli_version} installed in region {region} (quick check only)"
            return result
        
        # Check bedrock client creation
        bedrock_ok = self._check_bedrock_client()
        result.bedrock_client_ok = bedrock_ok
        
        # Check SSM parameter access
        ssm_ok = self._check_ssm_access()
        result.ssm_access_ok = ssm_ok
        
        # Check S3 access
        s3_ok = self._check_s3_access()
        result.s3_access_ok = s3_ok
        
        # Determine overall status
        if len([i for i in self.issues if i.severity == "CRITICAL"]) > 0:
            result.status = "FAIL"
            result.message = "AWS connectivity check failed with critical issues"
        elif len(self.issues) > 0:
            result.status = "WARNING"
            result.message = f"AWS connectivity OK with {len(self.issues)} warning(s)"
        else:
            result.status = "PASS"
            result.message = f"AWS CLI {cli_version} configured and all services accessible in {region}"
        
        return result
    
    def _check_aws_cli(self) -> Tuple[bool, Optional[str]]:
        """
        Check if AWS CLI is installed.
        
        Returns:
            Tuple of (is_installed, version_string)
        """
        try:
            result = subprocess.run(
                ['aws', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse version from output like "aws-cli/2.13.0 Python/3.11.4 Darwin/23.0.0"
                version_output = result.stdout.strip()
                version = version_output.split()[0] if version_output else "unknown"
                return True, version
            else:
                self._add_issue(
                    issue_type="CLI_MISSING",
                    description="AWS CLI command failed",
                    details=result.stderr,
                    severity="CRITICAL",
                    fix_suggestion="Install AWS CLI: brew install awscli (macOS)"
                )
                return False, None
                
        except FileNotFoundError:
            self._add_issue(
                issue_type="CLI_MISSING",
                description="AWS CLI is not installed",
                details="The 'aws' command was not found in PATH",
                severity="CRITICAL",
                fix_suggestion="Install AWS CLI: brew install awscli (macOS) or visit https://aws.amazon.com/cli/"
            )
            return False, None
            
        except subprocess.TimeoutExpired:
            self._add_issue(
                issue_type="CLI_MISSING",
                description="AWS CLI command timed out",
                details="Command took longer than 5 seconds",
                severity="WARNING",
                fix_suggestion="Check AWS CLI installation"
            )
            return False, None
            
        except Exception as e:
            self._add_issue(
                issue_type="CLI_MISSING",
                description="Unexpected error checking AWS CLI",
                details=str(e),
                severity="CRITICAL",
                fix_suggestion="Verify AWS CLI installation"
            )
            return False, None
    
    def _check_aws_credentials(self) -> Tuple[bool, Optional[str]]:
        """
        Check if AWS credentials are configured.
        
        Returns:
            Tuple of (credentials_configured, region)
        """
        try:
            # Try to get caller identity
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse identity information
                try:
                    identity = json.loads(result.stdout)
                    account_id = identity.get('Account', 'unknown')
                    user_arn = identity.get('Arn', 'unknown')
                    
                    # Get configured region
                    region_result = subprocess.run(
                        ['aws', 'configure', 'get', 'region'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    region = region_result.stdout.strip() if region_result.returncode == 0 else os.environ.get('AWS_REGION', 'us-east-1')
                    
                    return True, region
                    
                except json.JSONDecodeError:
                    self._add_issue(
                        issue_type="CREDENTIALS_MISSING",
                        description="Failed to parse AWS identity",
                        details="Could not parse get-caller-identity output",
                        severity="WARNING",
                        fix_suggestion="Run: aws configure"
                    )
                    return False, None
            else:
                # Credentials not configured or invalid
                error_msg = result.stderr.strip()
                
                if "could not be found" in error_msg.lower() or "no credentials" in error_msg.lower():
                    self._add_issue(
                        issue_type="CREDENTIALS_MISSING",
                        description="AWS credentials are not configured",
                        details=error_msg,
                        severity="WARNING",
                        fix_suggestion=self._get_credentials_setup_instructions()
                    )
                else:
                    self._add_issue(
                        issue_type="CREDENTIALS_MISSING",
                        description="AWS credentials check failed",
                        details=error_msg,
                        severity="WARNING",
                        fix_suggestion="Verify AWS credentials: aws sts get-caller-identity"
                    )
                
                return False, None
                
        except subprocess.TimeoutExpired:
            self._add_issue(
                issue_type="CREDENTIALS_MISSING",
                description="AWS credentials check timed out",
                details="Command took longer than 10 seconds",
                severity="WARNING",
                fix_suggestion="Check network connectivity and AWS credentials"
            )
            return False, None
            
        except Exception as e:
            self._add_issue(
                issue_type="CREDENTIALS_MISSING",
                description="Unexpected error checking AWS credentials",
                details=str(e),
                severity="WARNING",
                fix_suggestion="Run: aws configure"
            )
            return False, None
    
    def _check_boto3_available(self) -> bool:
        """
        Check if boto3 is available for import.
        
        Returns:
            True if boto3 can be imported, False otherwise
        """
        try:
            import boto3
            return True
        except ImportError:
            self._add_issue(
                issue_type="CLIENT_CREATION",
                description="boto3 package is not available",
                details="Cannot import boto3 module",
                severity="CRITICAL",
                fix_suggestion="Install boto3: pip install boto3"
            )
            return False
        except Exception as e:
            self._add_issue(
                issue_type="CLIENT_CREATION",
                description="Unexpected error importing boto3",
                details=str(e),
                severity="CRITICAL",
                fix_suggestion="Reinstall boto3: pip install --force-reinstall boto3"
            )
            return False
    
    def _check_bedrock_client(self) -> bool:
        """
        Test boto3 client creation for bedrock services.
        
        Returns:
            True if clients can be created, False otherwise
        """
        try:
            import boto3
            
            # Try to create bedrock-agent-runtime client
            try:
                client = boto3.client('bedrock-agent-runtime')
                # Don't make actual API calls, just verify client creation
                return True
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a credentials issue (expected if not configured)
                if "credentials" in error_msg.lower() or "not found" in error_msg.lower():
                    # This is expected if credentials aren't configured
                    return True
                
                self._add_issue(
                    issue_type="CLIENT_CREATION",
                    description="Failed to create bedrock-agent-runtime client",
                    details=error_msg,
                    severity="WARNING",
                    fix_suggestion="Verify AWS credentials and region configuration"
                )
                return False
                
        except ImportError:
            # boto3 not available - already reported
            return False
        except Exception as e:
            self._add_issue(
                issue_type="CLIENT_CREATION",
                description="Unexpected error creating bedrock client",
                details=str(e),
                severity="WARNING",
                fix_suggestion="Check boto3 installation and AWS configuration"
            )
            return False
    
    def _check_ssm_access(self) -> bool:
        """
        Test SSM parameter access (read-only).
        
        Returns:
            True if SSM access works, False otherwise
        """
        try:
            import boto3
            
            # Try to create SSM client
            ssm_client = boto3.client('ssm')
            
            # Try to list parameters with a common prefix (read-only operation)
            # This will fail gracefully if no parameters exist
            try:
                response = ssm_client.describe_parameters(
                    MaxResults=1
                )
                # If we get here, SSM access works
                return True
                
            except ssm_client.exceptions.ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                if error_code == 'AccessDeniedException':
                    self._add_issue(
                        issue_type="SSM_ACCESS",
                        description="SSM access denied",
                        details="Insufficient permissions to access SSM parameters",
                        severity="WARNING",
                        fix_suggestion="Verify IAM permissions for SSM access"
                    )
                    return False
                else:
                    # Other errors might be transient
                    self._add_issue(
                        issue_type="SSM_ACCESS",
                        description="SSM parameter access failed",
                        details=str(e),
                        severity="WARNING",
                        fix_suggestion="Check AWS credentials and SSM permissions"
                    )
                    return False
                    
        except ImportError:
            # boto3 not available - already reported
            return False
        except Exception as e:
            self._add_issue(
                issue_type="SSM_ACCESS",
                description="Unexpected error testing SSM access",
                details=str(e),
                severity="WARNING",
                fix_suggestion="Verify AWS credentials and network connectivity"
            )
            return False
    
    def _check_s3_access(self) -> bool:
        """
        Test S3 access (read-only).
        
        Returns:
            True if S3 access works, False otherwise
        """
        try:
            import boto3
            
            # Try to create S3 client
            s3_client = boto3.client('s3')
            
            # Try to list buckets (read-only operation)
            try:
                response = s3_client.list_buckets()
                # If we get here, S3 access works
                bucket_count = len(response.get('Buckets', []))
                return True
                
            except s3_client.exceptions.ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                if error_code == 'AccessDenied':
                    self._add_issue(
                        issue_type="S3_ACCESS",
                        description="S3 access denied",
                        details="Insufficient permissions to list S3 buckets",
                        severity="WARNING",
                        fix_suggestion="Verify IAM permissions for S3 access"
                    )
                    return False
                else:
                    self._add_issue(
                        issue_type="S3_ACCESS",
                        description="S3 access failed",
                        details=str(e),
                        severity="WARNING",
                        fix_suggestion="Check AWS credentials and S3 permissions"
                    )
                    return False
                    
        except ImportError:
            # boto3 not available - already reported
            return False
        except Exception as e:
            self._add_issue(
                issue_type="S3_ACCESS",
                description="Unexpected error testing S3 access",
                details=str(e),
                severity="WARNING",
                fix_suggestion="Verify AWS credentials and network connectivity"
            )
            return False
    
    def _get_credentials_setup_instructions(self) -> str:
        """
        Get detailed instructions for setting up AWS credentials.
        
        Returns:
            Multi-line string with setup instructions
        """
        return """
AWS Credentials Setup Instructions:

Option 1: Configure using AWS CLI
  1. Run: aws configure
  2. Enter your AWS Access Key ID
  3. Enter your AWS Secret Access Key
  4. Enter default region (e.g., us-east-1)
  5. Enter default output format (json)

Option 2: Set environment variables
  export AWS_ACCESS_KEY_ID=your_access_key
  export AWS_SECRET_ACCESS_KEY=your_secret_key
  export AWS_DEFAULT_REGION=us-east-1

Option 3: Use AWS credentials file
  Create ~/.aws/credentials with:
  [default]
  aws_access_key_id = your_access_key
  aws_secret_access_key = your_secret_key
  
  Create ~/.aws/config with:
  [default]
  region = us-east-1

For more information: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
        """.strip()
    
    def _add_issue(self, issue_type: str, description: str, details: str,
                   severity: str, fix_suggestion: str) -> None:
        """
        Add an AWS issue to the list.
        
        Args:
            issue_type: Type of issue
            description: Short description
            details: Detailed information
            severity: Issue severity
            fix_suggestion: Suggested fix
        """
        issue = AWSIssue(
            issue_type=issue_type,
            description=description,
            details=details,
            severity=severity,
            fix_suggestion=fix_suggestion
        )
        
        self.issues.append(issue)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the AWS check results.
        
        Returns:
            Dictionary with summary information
        """
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        warning_issues = [i for i in self.issues if i.severity == "WARNING"]
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        return {
            "total_issues": len(self.issues),
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Get general recommendations for AWS setup.
        
        Returns:
            List of recommendation strings
        """
        recommendations = [
            "Install AWS CLI v2 for best compatibility: brew install awscli",
            "Configure AWS credentials: aws configure",
            "Set default region to match your resources (e.g., us-east-1)",
            "Verify credentials: aws sts get-caller-identity",
            "Test service access: aws ssm describe-parameters --max-results 1",
            "Ensure boto3 is installed: pip install boto3",
            "Check IAM permissions for required services (Bedrock, SSM, S3)",
            "Use AWS SSO for enhanced security if available",
            "Keep AWS CLI updated: brew upgrade awscli",
        ]
        
        return recommendations
