#!/usr/bin/env python3
"""
List indexes in OpenSearch Serverless collection
"""

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json

def get_collection_endpoint(collection_name: str = "instrument-diag-kb") -> str:
    """Get the OpenSearch collection endpoint"""
    opensearch_client = boto3.client('opensearchserverless')
    
    response = opensearch_client.list_collections()
    for collection in response.get('collectionSummaries', []):
        if collection['name'] == collection_name:
            collection_id = collection['id']
            detail_response = opensearch_client.batch_get_collection(ids=[collection_id])
            if detail_response.get('collectionDetails'):
                return detail_response['collectionDetails'][0]['collectionEndpoint']
    
    return None

def list_indexes(collection_endpoint: str) -> list:
    """List all indexes in the collection"""
    
    session = boto3.Session()
    credentials = session.get_credentials()
    
    url = f"{collection_endpoint}/_cat/indices?format=json"
    
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
            indexes = response.json()
            return indexes
        else:
            print(f"❌ Failed to list indexes. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error listing indexes: {e}")
        return []

def main():
    collection_name = "instrument-diag-kb"
    
    print(f"📋 Listing indexes in OpenSearch collection: {collection_name}")
    
    # Get collection endpoint
    endpoint = get_collection_endpoint(collection_name)
    if not endpoint:
        print(f"❌ Collection {collection_name} not found")
        return False
    
    print(f"✅ Collection endpoint: {endpoint}")
    
    # List indexes
    indexes = list_indexes(endpoint)
    
    if indexes:
        print(f"\n📋 Found {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  - {idx.get('index', 'unknown')}")
    else:
        print("\n📋 No indexes found in collection")
        print("This is normal for a new collection - Bedrock will create indexes automatically")
    
    return True

if __name__ == "__main__":
    main()