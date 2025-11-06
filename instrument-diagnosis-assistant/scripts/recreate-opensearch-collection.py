#!/usr/bin/env python3
"""
Recreate OpenSearch Serverless collection with proper permissions
This script deletes and recreates the collection to fix permission issues
"""

import boto3
import json
import time
import sys
from typing import Optional

def get_account_id() -> str:
    """Get current AWS account ID"""
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()['Account']

def get_current_user_arn() -> str:
    """Get current user ARN"""
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()['Arn']

def get_kb_role_arn(prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Get the Knowledge Base IAM role ARN"""
    iam_client = boto3.client('iam')
    role_name = f"{prefix}-kb-role"
    
    try:
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']
    except Exception as e:
        print(f"❌ Error getting IAM role: {e}")
        return None

def delete_collection(collection_name: str = "instrument-diag-kb") -> bool:
    """Delete the existing OpenSearch collection"""
    opensearch_client = boto3.client('opensearchserverless')
    
    try:
        # Get collection ID first
        response = opensearch_client.list_collections()
        collection_id = None
        
        for collection in response.get('collectionSummaries', []):
            if collection['name'] == collection_name:
                collection_id = collection['id']
                break
        
        if not collection_id:
            print(f"✅ Collection {collection_name} does not exist")
            return True
        
        print(f"🗑️  Deleting collection: {collection_name}")
        opensearch_client.delete_collection(id=collection_id)
        
        # Wait for deletion
        print("⏳ Waiting for collection to be deleted...")
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                response = opensearch_client.list_collections()
                found = False
                for collection in response.get('collectionSummaries', []):
                    if collection['name'] == collection_name:
                        found = True
                        break
                
                if not found:
                    print("✅ Collection deleted successfully!")
                    return True
                
                time.sleep(10)
                wait_time += 10
                
            except Exception as e:
                print(f"⚠️  Error checking deletion status: {e}")
                time.sleep(10)
                wait_time += 10
        
        print("⚠️  Timeout waiting for deletion, but continuing...")
        return True
        
    except Exception as e:
        print(f"❌ Failed to delete collection: {e}")
        return False

def delete_security_policies(collection_name: str = "instrument-diag-kb") -> bool:
    """Delete existing security policies"""
    opensearch_client = boto3.client('opensearchserverless')
    
    policies = [
        (f"{collection_name}-encryption", "encryption"),
        (f"{collection_name}-network", "network"),
        (f"{collection_name}-data", "data")
    ]
    
    for policy_name, policy_type in policies:
        try:
            if policy_type == "data":
                opensearch_client.delete_access_policy(name=policy_name, type=policy_type)
            else:
                opensearch_client.delete_security_policy(name=policy_name, type=policy_type)
            print(f"✅ Deleted {policy_type} policy: {policy_name}")
        except opensearch_client.exceptions.ResourceNotFoundException:
            print(f"✅ Policy {policy_name} does not exist")
        except Exception as e:
            print(f"⚠️  Could not delete policy {policy_name}: {e}")
    
    return True

def create_security_policies(collection_name: str = "instrument-diag-kb", 
                           kb_role_arn: str = None, current_user_arn: str = None) -> bool:
    """Create security policies with proper permissions"""
    opensearch_client = boto3.client('opensearchserverless')
    
    try:
        # Create encryption policy
        encryption_policy_name = f"{collection_name}-encryption"
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AWSOwnedKey": True
        }
        
        opensearch_client.create_security_policy(
            name=encryption_policy_name,
            type='encryption',
            policy=json.dumps(encryption_policy)
        )
        print(f"✅ Created encryption policy: {encryption_policy_name}")
        
        # Create network policy (allow public access)
        network_policy_name = f"{collection_name}-network"
        network_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    },
                    {
                        "ResourceType": "dashboard",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AllowFromPublic": True
            }
        ]
        
        opensearch_client.create_security_policy(
            name=network_policy_name,
            type='network',
            policy=json.dumps(network_policy)
        )
        print(f"✅ Created network policy: {network_policy_name}")
        
        # Create data access policy with both KB role and current user
        data_policy_name = f"{collection_name}-data"
        principals = []
        
        if kb_role_arn:
            principals.append(kb_role_arn)
        if current_user_arn:
            principals.append(current_user_arn)
        
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
                "Principal": principals
            }
        ]
        
        opensearch_client.create_access_policy(
            name=data_policy_name,
            type='data',
            policy=json.dumps(data_policy)
        )
        print(f"✅ Created data access policy: {data_policy_name}")
        print(f"📋 Principals: {principals}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create security policies: {e}")
        return False

def create_collection(collection_name: str = "instrument-diag-kb") -> Optional[str]:
    """Create new OpenSearch Serverless collection"""
    opensearch_client = boto3.client('opensearchserverless')
    
    try:
        print(f"🔍 Creating OpenSearch Serverless collection: {collection_name}")
        response = opensearch_client.create_collection(
            name=collection_name,
            description="Vector collection for instrument diagnosis knowledge base",
            type='VECTORSEARCH'
        )
        
        collection_arn = response['createCollectionDetail']['arn']
        collection_id = response['createCollectionDetail']['id']
        print(f"✅ Created OpenSearch collection: {collection_name} ({collection_arn})")
        
        # Wait for collection to be active
        print("⏳ Waiting for OpenSearch collection to be active...")
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                collection_response = opensearch_client.batch_get_collection(ids=[collection_id])
                collections = collection_response.get('collectionDetails', [])
                if collections and collections[0]['status'] == 'ACTIVE':
                    print("✅ OpenSearch collection is active!")
                    return collection_arn
                else:
                    status = collections[0]['status'] if collections else 'UNKNOWN'
                    print(f"⏳ Collection status: {status}")
                    time.sleep(10)
                    wait_time += 10
            except Exception as e:
                print(f"⚠️  Error checking collection status: {e}")
                time.sleep(10)
                wait_time += 10
        
        print("⚠️  Timeout waiting for collection to be active")
        return collection_arn
        
    except Exception as e:
        print(f"❌ Failed to create OpenSearch collection: {e}")
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Recreate OpenSearch collection with proper permissions")
    parser.add_argument("--collection", default="instrument-diag-kb", help="OpenSearch collection name")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    
    args = parser.parse_args()
    
    print(f"🔄 Recreating OpenSearch collection with proper permissions")
    print(f"Collection: {args.collection}")
    print(f"Prefix: {args.prefix}")
    print()
    
    # Get required ARNs
    kb_role_arn = get_kb_role_arn(args.prefix)
    current_user_arn = get_current_user_arn()
    
    print(f"📋 Knowledge Base role: {kb_role_arn}")
    print(f"👤 Current user: {current_user_arn}")
    print()
    
    # Step 1: Delete existing collection
    print("1️⃣ Deleting existing collection...")
    if not delete_collection(args.collection):
        return False
    
    # Step 2: Delete existing security policies
    print("\n2️⃣ Deleting existing security policies...")
    delete_security_policies(args.collection)
    
    # Step 3: Create new security policies
    print("\n3️⃣ Creating new security policies...")
    if not create_security_policies(args.collection, kb_role_arn, current_user_arn):
        return False
    
    # Step 4: Create new collection
    print("\n4️⃣ Creating new collection...")
    collection_arn = create_collection(args.collection)
    if not collection_arn:
        return False
    
    print(f"\n✅ Collection recreated successfully!")
    print(f"Collection ARN: {collection_arn}")
    print("\nNext steps:")
    print("1. Wait 1-2 minutes for policies to propagate")
    print("2. Create the vector index")
    print("3. Create the Knowledge Base")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)