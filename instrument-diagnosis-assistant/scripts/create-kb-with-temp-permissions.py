#!/usr/bin/env python3
"""
Create Knowledge Base by temporarily adding admin permissions to OpenSearch
"""

import boto3
import json
import time
import sys
from typing import Optional

def add_admin_to_opensearch_policy(collection_name: str = "instrument-diag-kb") -> bool:
    """Temporarily add admin permissions to OpenSearch data policy"""
    
    opensearch_client = boto3.client('opensearchserverless')
    sts_client = boto3.client('sts')
    
    policy_name = f"{collection_name}-data"
    
    # Get current user ARN
    current_user_arn = sts_client.get_caller_identity()['Arn']
    
    # Get KB role ARN
    iam_client = boto3.client('iam')
    try:
        role_response = iam_client.get_role(RoleName="instrument-diagnosis-assistant-kb-role")
        kb_role_arn = role_response['Role']['Arn']
    except Exception as e:
        print(f"❌ Error getting KB role: {e}")
        return False
    
    # Create comprehensive data access policy
    data_policy = [
        {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:*"  # Full permissions
                    ]
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:*"  # Full permissions
                    ]
                }
            ],
            "Principal": [kb_role_arn, current_user_arn]
        }
    ]
    
    try:
        # Get existing policy
        response = opensearch_client.get_access_policy(
            name=policy_name,
            type='data'
        )
        
        # Update with full permissions
        opensearch_client.update_access_policy(
            name=policy_name,
            type='data',
            policy=json.dumps(data_policy),
            policyVersion=response['accessPolicyDetail']['policyVersion']
        )
        
        print(f"✅ Updated data access policy with admin permissions")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update data access policy: {e}")
        return False

def create_index_and_kb(collection_name: str = "instrument-diag-kb", 
                       prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Create the index and Knowledge Base"""
    
    # First, create the index
    opensearch_client = boto3.client('opensearchserverless')
    
    # Get collection endpoint
    response = opensearch_client.list_collections()
    collection_endpoint = None
    
    for collection in response.get('collectionSummaries', []):
        if collection['name'] == collection_name:
            collection_id = collection['id']
            detail_response = opensearch_client.batch_get_collection(ids=[collection_id])
            if detail_response.get('collectionDetails'):
                collection_endpoint = detail_response['collectionDetails'][0]['collectionEndpoint']
                collection_arn = collection['arn']
                break
    
    if not collection_endpoint:
        print(f"❌ Collection {collection_name} not found")
        return None
    
    print(f"✅ Collection endpoint: {collection_endpoint}")
    
    # Create the vector index using direct API call
    import requests
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    
    session = boto3.Session()
    credentials = session.get_credentials()
    
    index_name = f"bedrock-knowledge-base-{prefix.replace('-', '')}"
    
    # Simple index mapping
    index_mapping = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib"
                    }
                },
                "text": {
                    "type": "text"
                },
                "metadata": {
                    "type": "object"
                }
            }
        }
    }
    
    url = f"{collection_endpoint}/{index_name}"
    
    try:
        # Create index
        request = AWSRequest(
            method='PUT',
            url=url,
            data=json.dumps(index_mapping),
            headers={'Content-Type': 'application/json'}
        )
        
        SigV4Auth(credentials, 'aoss', 'us-east-1').add_auth(request)
        
        response = requests.put(
            url,
            data=request.body,
            headers=dict(request.headers)
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Created vector index: {index_name}")
        else:
            print(f"❌ Failed to create index. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return None
    
    # Now create the Knowledge Base
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    iam_client = boto3.client('iam')
    
    kb_name = f"{prefix}-kb"
    
    # Get role ARN
    try:
        role_response = iam_client.get_role(RoleName=f"{prefix}-kb-role")
        role_arn = role_response['Role']['Arn']
    except Exception as e:
        print(f"❌ Error getting IAM role: {e}")
        return None
    
    try:
        print(f"🧠 Creating Knowledge Base: {kb_name}")
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description="Knowledge base for instrument diagnosis troubleshooting guides and documentation",
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': index_name,
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_name} ({kb_id})")
        return kb_id
        
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def main():
    collection_name = "instrument-diag-kb"
    prefix = "instrument-diagnosis-assistant"
    
    print(f"🚀 Creating Knowledge Base with temporary admin permissions")
    print(f"Collection: {collection_name}")
    print(f"Prefix: {prefix}")
    print()
    
    # Step 1: Add admin permissions
    print("1️⃣ Adding admin permissions to OpenSearch...")
    if not add_admin_to_opensearch_policy(collection_name):
        return False
    
    # Step 2: Wait for permissions to propagate
    print("\n2️⃣ Waiting for permissions to propagate...")
    time.sleep(30)
    
    # Step 3: Create index and Knowledge Base
    print("\n3️⃣ Creating index and Knowledge Base...")
    kb_id = create_index_and_kb(collection_name, prefix)
    
    if kb_id:
        print(f"\n✅ Knowledge Base created successfully!")
        print(f"Knowledge Base ID: {kb_id}")
        print("\nNext steps:")
        print("1. Create data sources")
        print("2. Upload documents to S3 buckets")
        print("3. Sync data sources")
        return True
    else:
        print(f"\n❌ Failed to create Knowledge Base")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)