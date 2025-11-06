#!/usr/bin/env python3
"""
Fix OpenSearch Serverless security policies for Knowledge Base access
This script updates the data access policy to allow the Knowledge Base role to access the collection
"""

import boto3
import json
import sys
from typing import Optional

def get_account_id() -> str:
    """Get current AWS account ID"""
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()['Account']

def get_kb_role_arn(prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Get the Knowledge Base IAM role ARN"""
    iam_client = boto3.client('iam')
    role_name = f"{prefix}-kb-role"
    
    try:
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        print(f"❌ IAM role {role_name} not found")
        return None
    except Exception as e:
        print(f"❌ Error getting IAM role: {e}")
        return None

def update_data_access_policy(collection_name: str = "instrument-diag-kb", 
                            prefix: str = "instrument-diagnosis-assistant") -> bool:
    """Update the data access policy for the OpenSearch collection"""
    
    opensearch_client = boto3.client('opensearchserverless')
    policy_name = f"{collection_name}-data"
    
    # Get the Knowledge Base role ARN
    kb_role_arn = get_kb_role_arn(prefix)
    if not kb_role_arn:
        return False
    
    # Get current user ARN for administrative access
    sts_client = boto3.client('sts')
    current_user_arn = sts_client.get_caller_identity()['Arn']
    
    print(f"🔐 Updating data access policy: {policy_name}")
    print(f"📋 Knowledge Base role: {kb_role_arn}")
    print(f"👤 Current user: {current_user_arn}")
    
    # Create the updated data access policy with both KB role and current user
    data_policy = [
        {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems", 
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ]
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ]
                }
            ],
            "Principal": [kb_role_arn, current_user_arn]
        }
    ]
    
    try:
        # Check if policy exists
        try:
            response = opensearch_client.get_access_policy(
                name=policy_name,
                type='data'
            )
            print(f"✅ Found existing data access policy")
            
            # Update existing policy
            opensearch_client.update_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(data_policy),
                policyVersion=response['accessPolicyDetail']['policyVersion']
            )
            print(f"✅ Updated data access policy: {policy_name}")
            
        except opensearch_client.exceptions.ResourceNotFoundException:
            # Create new policy
            opensearch_client.create_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(data_policy)
            )
            print(f"✅ Created data access policy: {policy_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update data access policy: {e}")
        return False

def verify_collection_access(collection_name: str = "instrument-diag-kb") -> bool:
    """Verify that the collection is accessible"""
    opensearch_client = boto3.client('opensearchserverless')
    
    try:
        response = opensearch_client.list_collections()
        for collection in response.get('collectionSummaries', []):
            if collection['name'] == collection_name:
                status = collection['status']
                print(f"✅ Collection {collection_name} status: {status}")
                return status == 'ACTIVE'
        
        print(f"❌ Collection {collection_name} not found")
        return False
        
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
        return False

def update_kb_role_permissions(prefix: str = "instrument-diagnosis-assistant") -> bool:
    """Update the Knowledge Base IAM role permissions"""
    iam_client = boto3.client('iam')
    role_name = f"{prefix}-kb-role"
    policy_name = f"{prefix}-kb-policy"
    
    # Enhanced permissions policy
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{prefix}-*",
                    f"arn:aws:s3:::{prefix}-*/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll",
                    "aoss:DashboardsAccessAll"
                ],
                "Resource": [
                    "arn:aws:aoss:*:*:collection/*"
                ]
            }
        ]
    }
    
    try:
        # Update the role policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy)
        )
        print(f"✅ Updated IAM role permissions: {role_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update IAM role permissions: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix OpenSearch security policies for Knowledge Base")
    parser.add_argument("--collection", default="instrument-diag-kb", help="OpenSearch collection name")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    
    args = parser.parse_args()
    
    print(f"🔧 Fixing OpenSearch security policies for Knowledge Base")
    print(f"Collection: {args.collection}")
    print(f"Prefix: {args.prefix}")
    print()
    
    # Step 1: Verify collection exists and is active
    print("1️⃣ Verifying OpenSearch collection...")
    if not verify_collection_access(args.collection):
        print("❌ Collection is not accessible or not active")
        return False
    
    # Step 2: Update IAM role permissions
    print("\n2️⃣ Updating IAM role permissions...")
    if not update_kb_role_permissions(args.prefix):
        print("❌ Failed to update IAM role permissions")
        return False
    
    # Step 3: Update data access policy
    print("\n3️⃣ Updating data access policy...")
    if not update_data_access_policy(args.collection, args.prefix):
        print("❌ Failed to update data access policy")
        return False
    
    print("\n✅ Security policies updated successfully!")
    print("\nNext steps:")
    print("1. Wait 1-2 minutes for policy changes to propagate")
    print("2. Retry creating the Knowledge Base")
    print("3. Run: python scripts/setup-knowledge-base.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)