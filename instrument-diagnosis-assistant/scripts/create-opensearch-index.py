#!/usr/bin/env python3
"""
Create the required vector index in OpenSearch Serverless collection
This script creates the vector index that the Knowledge Base needs
"""

import boto3
import json
import requests
from requests.auth import HTTPBasicAuth
import time
import sys
from typing import Optional

def get_collection_endpoint(collection_name: str = "instrument-diag-kb") -> Optional[str]:
    """Get the OpenSearch collection endpoint"""
    opensearch_client = boto3.client('opensearchserverless')
    
    try:
        response = opensearch_client.list_collections()
        for collection in response.get('collectionSummaries', []):
            if collection['name'] == collection_name:
                collection_id = collection['id']
                # Get collection details to get the endpoint
                detail_response = opensearch_client.batch_get_collection(ids=[collection_id])
                if detail_response.get('collectionDetails'):
                    endpoint = detail_response['collectionDetails'][0]['collectionEndpoint']
                    return endpoint
        
        print(f"❌ Collection {collection_name} not found")
        return None
        
    except Exception as e:
        print(f"❌ Error getting collection endpoint: {e}")
        return None

def get_aws_credentials():
    """Get AWS credentials for signing requests"""
    session = boto3.Session()
    credentials = session.get_credentials()
    return credentials

def create_vector_index(collection_endpoint: str, index_name: str = "bedrock-knowledge-base-instrumentdiagnosisassistantkb") -> bool:
    """Create the vector index in OpenSearch"""
    
    # Index mapping for Knowledge Base - using simple field names
    index_mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,  # Amazon Titan Embed Text v2 dimension
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "text": {
                    "type": "text"
                },
                "metadata": {
                    "type": "object",
                    "enabled": True
                }
            }
        }
    }
    
    # Use AWS SigV4 authentication
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    
    credentials = get_aws_credentials()
    
    # Create the index
    url = f"{collection_endpoint}/{index_name}"
    
    try:
        # Prepare the request
        request = AWSRequest(
            method='PUT',
            url=url,
            data=json.dumps(index_mapping),
            headers={'Content-Type': 'application/json'}
        )
        
        # Sign the request
        SigV4Auth(credentials, 'aoss', 'us-east-1').add_auth(request)
        
        # Make the request using requests
        response = requests.put(
            url,
            data=request.body,
            headers=dict(request.headers)
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Created vector index: {index_name}")
            return True
        else:
            print(f"❌ Failed to create index. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating vector index: {e}")
        return False

def check_index_exists(collection_endpoint: str, index_name: str = "bedrock-knowledge-base-instrumentdiagnosisassistantkb") -> bool:
    """Check if the vector index already exists"""
    
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    
    credentials = get_aws_credentials()
    url = f"{collection_endpoint}/{index_name}"
    
    try:
        # Prepare the request
        request = AWSRequest(
            method='GET',
            url=url,
            headers={'Content-Type': 'application/json'}
        )
        
        # Sign the request
        SigV4Auth(credentials, 'aoss', 'us-east-1').add_auth(request)
        
        # Make the request
        response = requests.get(
            url,
            headers=dict(request.headers)
        )
        
        if response.status_code == 200:
            print(f"✅ Index {index_name} already exists")
            return True
        elif response.status_code == 404:
            print(f"📋 Index {index_name} does not exist")
            return False
        else:
            print(f"⚠️  Unexpected response checking index: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking index: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create OpenSearch vector index for Knowledge Base")
    parser.add_argument("--collection", default="instrument-diag-kb", help="OpenSearch collection name")
    parser.add_argument("--index", default="bedrock-knowledge-base-instrumentdiagnosisassistantkb", help="Vector index name")
    
    args = parser.parse_args()
    
    print(f"🔍 Creating OpenSearch vector index")
    print(f"Collection: {args.collection}")
    print(f"Index: {args.index}")
    print()
    
    # Step 1: Get collection endpoint
    print("1️⃣ Getting collection endpoint...")
    endpoint = get_collection_endpoint(args.collection)
    if not endpoint:
        return False
    
    print(f"✅ Collection endpoint: {endpoint}")
    
    # Step 2: Check if index already exists
    print("\n2️⃣ Checking if index exists...")
    if check_index_exists(endpoint, args.index):
        print("✅ Index already exists, no action needed")
        return True
    
    # Step 3: Create the vector index
    print("\n3️⃣ Creating vector index...")
    if not create_vector_index(endpoint, args.index):
        return False
    
    # Step 4: Wait for index to be ready
    print("\n4️⃣ Waiting for index to be ready...")
    time.sleep(5)
    
    if check_index_exists(endpoint, args.index):
        print("✅ Vector index created successfully!")
        print("\nNext steps:")
        print("1. Retry creating the Knowledge Base")
        print("2. Run: python scripts/setup-knowledge-base.py")
        return True
    else:
        print("❌ Index creation may have failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)