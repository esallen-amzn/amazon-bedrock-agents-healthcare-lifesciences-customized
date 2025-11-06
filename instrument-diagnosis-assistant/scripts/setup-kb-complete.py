#!/usr/bin/env python3
"""
Complete Knowledge Base setup script that handles all the complexities
This script will create everything needed for the Knowledge Base to work
"""

import boto3
import json
import time
import sys
import yaml
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from typing import Optional, Dict, Any

class KnowledgeBaseSetupComplete:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.opensearch_client = boto3.client('opensearchserverless', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Get current user info
        self.account_id = self.sts_client.get_caller_identity()['Account']
        self.current_user_arn = self.sts_client.get_caller_identity()['Arn']
        
    def setup_complete_kb(self, prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
        """Complete Knowledge Base setup"""
        
        print(f"🚀 Complete Knowledge Base Setup")
        print(f"Account: {self.account_id}")
        print(f"Region: {self.region}")
        print(f"Prefix: {prefix}")
        print(f"Current User: {self.current_user_arn}")
        print()
        
        # Step 1: Ensure IAM role exists and has correct permissions
        print("1️⃣ Setting up IAM role...")
        role_arn = self.setup_iam_role(prefix)
        if not role_arn:
            return None
        
        # Step 2: Create S3 buckets
        print("\n2️⃣ Creating S3 buckets...")
        buckets = self.create_s3_buckets(prefix)
        
        # Step 3: Set up OpenSearch collection with proper permissions
        print("\n3️⃣ Setting up OpenSearch collection...")
        collection_arn, collection_endpoint = self.setup_opensearch_collection(prefix, role_arn)
        if not collection_arn:
            return None
        
        # Step 4: Create vector index
        print("\n4️⃣ Creating vector index...")
        index_name = self.create_vector_index(collection_endpoint, prefix)
        if not index_name:
            return None
        
        # Step 5: Create Knowledge Base
        print("\n5️⃣ Creating Knowledge Base...")
        kb_id = self.create_knowledge_base(prefix, role_arn, collection_arn, index_name)
        if not kb_id:
            return None
        
        # Step 6: Create data sources
        print("\n6️⃣ Creating data sources...")
        self.create_data_sources(kb_id, prefix)
        
        # Step 7: Update configuration
        print("\n7️⃣ Updating configuration...")
        self.update_config(kb_id, prefix)
        
        print(f"\n✅ Complete setup finished!")
        print(f"Knowledge Base ID: {kb_id}")
        
        return kb_id
    
    def setup_iam_role(self, prefix: str) -> Optional[str]:
        """Set up IAM role with comprehensive permissions"""
        role_name = f"{prefix}-kb-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
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
                        f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:APIAccessAll",
                        "aoss:DashboardsAccessAll"
                    ],
                    "Resource": [
                        f"arn:aws:aoss:{self.region}:{self.account_id}:collection/*"
                    ]
                }
            ]
        }
        
        try:
            # Check if role exists
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            print(f"✅ IAM role exists: {role_arn}")
            
            # Update policy to ensure it has latest permissions
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=f"{prefix}-kb-policy",
                PolicyDocument=json.dumps(permissions_policy)
            )
            print(f"✅ Updated IAM role permissions")
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create role
            try:
                self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="IAM role for Instrument Diagnosis Assistant Knowledge Base"
                )
                
                self.iam_client.put_role_policy(
                    RoleName=role_name,
                    PolicyName=f"{prefix}-kb-policy",
                    PolicyDocument=json.dumps(permissions_policy)
                )
                
                # Get role ARN
                response = self.iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                
                print(f"✅ Created IAM role: {role_arn}")
                
                # Wait for role to propagate
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Failed to create IAM role: {e}")
                return None
        
        except Exception as e:
            print(f"❌ Error with IAM role: {e}")
            return None
        
        return role_arn
    
    def create_s3_buckets(self, prefix: str) -> Dict[str, str]:
        """Create S3 buckets for data sources"""
        buckets = {}
        
        bucket_configs = [
            ("troubleshooting-guides", "Troubleshooting guides with images and procedures"),
            ("engineering-docs", "Component specifications and system architecture")
        ]
        
        for bucket_suffix, description in bucket_configs:
            bucket_name = f"{prefix}-{bucket_suffix}"
            
            try:
                # Check if bucket exists
                self.s3_client.head_bucket(Bucket=bucket_name)
                print(f"✅ Bucket exists: {bucket_name}")
            except:
                # Create bucket
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    print(f"✅ Created bucket: {bucket_name}")
                except Exception as e:
                    print(f"⚠️  Could not create bucket {bucket_name}: {e}")
            
            buckets[bucket_suffix] = bucket_name
        
        return buckets
    
    def setup_opensearch_collection(self, prefix: str, kb_role_arn: str) -> tuple:
        """Set up OpenSearch collection with proper permissions"""
        collection_name = "instrument-diag-kb"
        
        # Delete existing policies and collection to start fresh
        self.cleanup_opensearch_resources(collection_name)
        
        # Create security policies
        if not self.create_opensearch_policies(collection_name, kb_role_arn):
            return None, None
        
        # Create collection
        collection_arn, collection_endpoint = self.create_opensearch_collection(collection_name)
        
        return collection_arn, collection_endpoint
    
    def cleanup_opensearch_resources(self, collection_name: str):
        """Clean up existing OpenSearch resources"""
        try:
            # Delete collection
            response = self.opensearch_client.list_collections()
            for collection in response.get('collectionSummaries', []):
                if collection['name'] == collection_name:
                    print(f"🗑️  Deleting existing collection: {collection_name}")
                    self.opensearch_client.delete_collection(id=collection['id'])
                    time.sleep(30)  # Wait for deletion
                    break
            
            # Delete policies
            policies = [
                (f"{collection_name}-encryption", "encryption"),
                (f"{collection_name}-network", "network"),
                (f"{collection_name}-data", "data")
            ]
            
            for policy_name, policy_type in policies:
                try:
                    if policy_type == "data":
                        self.opensearch_client.delete_access_policy(name=policy_name, type=policy_type)
                    else:
                        self.opensearch_client.delete_security_policy(name=policy_name, type=policy_type)
                    print(f"🗑️  Deleted {policy_type} policy: {policy_name}")
                except:
                    pass  # Policy might not exist
                    
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def create_opensearch_policies(self, collection_name: str, kb_role_arn: str) -> bool:
        """Create OpenSearch security policies"""
        try:
            # Encryption policy
            encryption_policy = {
                "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}],
                "AWSOwnedKey": True
            }
            
            self.opensearch_client.create_security_policy(
                name=f"{collection_name}-encryption",
                type='encryption',
                policy=json.dumps(encryption_policy)
            )
            
            # Network policy
            network_policy = [{
                "Rules": [
                    {"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]},
                    {"ResourceType": "dashboard", "Resource": [f"collection/{collection_name}"]}
                ],
                "AllowFromPublic": True
            }]
            
            self.opensearch_client.create_security_policy(
                name=f"{collection_name}-network",
                type='network',
                policy=json.dumps(network_policy)
            )
            
            # Data access policy - include both KB role and current user
            data_policy = [{
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": ["aoss:*"]
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": ["aoss:*"]
                    }
                ],
                "Principal": [kb_role_arn, self.current_user_arn]
            }]
            
            self.opensearch_client.create_access_policy(
                name=f"{collection_name}-data",
                type='data',
                policy=json.dumps(data_policy)
            )
            
            print(f"✅ Created OpenSearch security policies")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create security policies: {e}")
            return False
    
    def create_opensearch_collection(self, collection_name: str) -> tuple:
        """Create OpenSearch collection"""
        try:
            response = self.opensearch_client.create_collection(
                name=collection_name,
                description="Vector collection for instrument diagnosis knowledge base",
                type='VECTORSEARCH'
            )
            
            collection_arn = response['createCollectionDetail']['arn']
            collection_id = response['createCollectionDetail']['id']
            
            print(f"✅ Created collection: {collection_name}")
            
            # Wait for collection to be active
            print("⏳ Waiting for collection to be active...")
            max_wait = 300
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    detail_response = self.opensearch_client.batch_get_collection(ids=[collection_id])
                    collections = detail_response.get('collectionDetails', [])
                    if collections and collections[0]['status'] == 'ACTIVE':
                        endpoint = collections[0]['collectionEndpoint']
                        print(f"✅ Collection active: {endpoint}")
                        return collection_arn, endpoint
                    time.sleep(10)
                except Exception as e:
                    print(f"⚠️  Waiting for collection: {e}")
                    time.sleep(10)
            
            print("⚠️  Timeout waiting for collection")
            return None, None
            
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return None, None
    
    def create_vector_index(self, collection_endpoint: str, prefix: str) -> Optional[str]:
        """Create vector index in OpenSearch collection"""
        index_name = f"bedrock-kb-{prefix.replace('-', '')}"
        
        # Wait for permissions to propagate
        print("⏳ Waiting for permissions to propagate...")
        time.sleep(60)
        
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
                        "dimension": 1536,
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
                        "type": "object"
                    }
                }
            }
        }
        
        session = boto3.Session()
        credentials = session.get_credentials()
        
        url = f"{collection_endpoint}/{index_name}"
        
        try:
            request = AWSRequest(
                method='PUT',
                url=url,
                data=json.dumps(index_mapping),
                headers={'Content-Type': 'application/json'}
            )
            
            SigV4Auth(credentials, 'aoss', self.region).add_auth(request)
            
            response = requests.put(
                url,
                data=request.body,
                headers=dict(request.headers)
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Created vector index: {index_name}")
                return index_name
            else:
                print(f"❌ Failed to create index. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating vector index: {e}")
            return None
    
    def create_knowledge_base(self, prefix: str, role_arn: str, collection_arn: str, index_name: str) -> Optional[str]:
        """Create Bedrock Knowledge Base"""
        kb_name = f"{prefix}-kb"
        
        try:
            response = self.bedrock_agent.create_knowledge_base(
                name=kb_name,
                description="Knowledge base for instrument diagnosis troubleshooting guides and documentation",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
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
            
            # Wait for KB to be ready
            print("⏳ Waiting for Knowledge Base to be ready...")
            max_wait = 300
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    kb_response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                    status = kb_response['knowledgeBase']['status']
                    
                    if status == 'ACTIVE':
                        print("✅ Knowledge Base is ready!")
                        return kb_id
                    elif status == 'FAILED':
                        print("❌ Knowledge Base creation failed!")
                        return None
                    else:
                        print(f"⏳ Knowledge Base status: {status}")
                        time.sleep(10)
                        
                except Exception as e:
                    print(f"⚠️  Error checking KB status: {e}")
                    time.sleep(10)
            
            print("⚠️  Timeout waiting for Knowledge Base, but returning ID anyway")
            return kb_id
            
        except Exception as e:
            print(f"❌ Failed to create Knowledge Base: {e}")
            return None
    
    def create_data_sources(self, kb_id: str, prefix: str):
        """Create data sources for the Knowledge Base"""
        source_configs = [
            ("troubleshooting-guides", "Troubleshooting guides with images and procedures"),
            ("engineering-docs", "Component specifications and system architecture")
        ]
        
        for source_key, description in source_configs:
            bucket_name = f"{prefix}-{source_key}"
            ds_name = f"{source_key}-ds"
            
            try:
                response = self.bedrock_agent.create_data_source(
                    knowledgeBaseId=kb_id,
                    name=ds_name,
                    description=description,
                    dataSourceConfiguration={
                        'type': 'S3',
                        's3Configuration': {
                            'bucketArn': f"arn:aws:s3:::{bucket_name}",
                            'inclusionPrefixes': ['']
                        }
                    },
                    vectorIngestionConfiguration={
                        'chunkingConfiguration': {
                            'chunkingStrategy': 'FIXED_SIZE',
                            'fixedSizeChunkingConfiguration': {
                                'maxTokens': 512,
                                'overlapPercentage': 20
                            }
                        }
                    }
                )
                
                ds_id = response['dataSource']['dataSourceId']
                print(f"✅ Created data source: {ds_name} ({ds_id})")
                
            except Exception as e:
                print(f"❌ Failed to create data source {ds_name}: {e}")
    
    def update_config(self, kb_id: str, prefix: str):
        """Update configuration file with KB ID"""
        config_file = "config.yaml"
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'knowledge_base' not in config:
                config['knowledge_base'] = {}
            
            config['knowledge_base']['kb_id'] = kb_id
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print(f"✅ Updated {config_file} with KB ID: {kb_id}")
            
        except Exception as e:
            print(f"⚠️  Could not update config file: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Knowledge Base setup")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    
    args = parser.parse_args()
    
    setup = KnowledgeBaseSetupComplete(region=args.region)
    kb_id = setup.setup_complete_kb(prefix=args.prefix)
    
    if kb_id:
        print(f"\n🎉 Knowledge Base setup completed successfully!")
        print(f"Knowledge Base ID: {kb_id}")
        print(f"\nNext steps:")
        print(f"1. Upload documents to S3 buckets:")
        print(f"   - s3://{args.prefix}-troubleshooting-guides")
        print(f"   - s3://{args.prefix}-engineering-docs")
        print(f"2. Sync data sources in Bedrock console")
        print(f"3. Test the Knowledge Base")
        return True
    else:
        print(f"\n❌ Knowledge Base setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)