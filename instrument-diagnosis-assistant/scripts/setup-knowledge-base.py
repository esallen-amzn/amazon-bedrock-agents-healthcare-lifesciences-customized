#!/usr/bin/env python3
"""
Setup script for Instrument Diagnosis Assistant Knowledge Base
Creates and configures Bedrock Knowledge Base with S3 data sources
"""

import boto3
import json
import yaml
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class KnowledgeBaseSetup:
    def __init__(self, region: str = "us-east-1", config_file: str = "config.yaml"):
        self.region = region
        self.config_file = config_file
        
        # Initialize AWS clients
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        
        # Load configuration
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            print(f"Configuration file {self.config_file} not found.")
            print("Please copy one of the template configs from deployment/ directory.")
            sys.exit(1)
            
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_s3_buckets(self, prefix: str) -> Dict[str, str]:
        """Create S3 buckets for Knowledge Base data sources"""
        buckets = {}
        
        bucket_configs = [
            ("troubleshooting-guides", "Troubleshooting guides with images and procedures"),
            ("engineering-docs", "Component specifications and system architecture"),
            ("sample-data", "Sample data for testing and validation")
        ]
        
        for bucket_suffix, description in bucket_configs:
            bucket_name = f"{prefix}-{bucket_suffix}"
            
            try:
                # Check if bucket exists
                self.s3.head_bucket(Bucket=bucket_name)
                print(f"✅ Bucket {bucket_name} already exists")
            except:
                # Create bucket
                try:
                    if self.region == 'us-east-1':
                        self.s3.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    # Add bucket policy for Bedrock access
                    self.setup_bucket_policy(bucket_name)
                    
                    print(f"✅ Created bucket: {bucket_name}")
                except Exception as e:
                    print(f"❌ Failed to create bucket {bucket_name}: {e}")
                    continue
            
            buckets[bucket_suffix] = bucket_name
        
        return buckets
    
    def setup_bucket_policy(self, bucket_name: str):
        """Setup S3 bucket policy for Bedrock Knowledge Base access"""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockKnowledgeBaseAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }
        
        try:
            self.s3.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not set bucket policy for {bucket_name}: {e}")
    
    def create_knowledge_base_role(self, prefix: str) -> str:
        """Create IAM role for Knowledge Base"""
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
                        "aoss:APIAccessAll"
                    ],
                    "Resource": [
                        f"arn:aws:aoss:{self.region}:*:collection/*"
                    ]
                }
            ]
        }
        
        try:
            # Check if role exists
            self.iam.get_role(RoleName=role_name)
            print(f"✅ IAM role {role_name} already exists")
        except:
            # Create role
            try:
                self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="IAM role for Instrument Diagnosis Assistant Knowledge Base"
                )
                
                # Attach inline policy
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=f"{prefix}-kb-policy",
                    PolicyDocument=json.dumps(permissions_policy)
                )
                
                print(f"✅ Created IAM role: {role_name}")
                
                # Wait for role to be available
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Failed to create IAM role: {e}")
                return None
        
        # Get role ARN
        role = self.iam.get_role(RoleName=role_name)
        return role['Role']['Arn']
    
    def create_opensearch_security_policies(self, collection_name: str) -> bool:
        """Create required security policies for OpenSearch Serverless"""
        try:
            opensearch_client = boto3.client('opensearchserverless', region_name=self.region)
            
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
            
            try:
                opensearch_client.create_security_policy(
                    name=encryption_policy_name,
                    type='encryption',
                    policy=json.dumps(encryption_policy)
                )
                print(f"✅ Created encryption policy: {encryption_policy_name}")
            except opensearch_client.exceptions.ConflictException:
                print(f"✅ Encryption policy {encryption_policy_name} already exists")
            
            # Create network policy (allow public access for simplicity)
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
            
            try:
                opensearch_client.create_security_policy(
                    name=network_policy_name,
                    type='network',
                    policy=json.dumps(network_policy)
                )
                print(f"✅ Created network policy: {network_policy_name}")
            except opensearch_client.exceptions.ConflictException:
                print(f"✅ Network policy {network_policy_name} already exists")
            
            # Create data access policy
            data_policy_name = f"{collection_name}-data"
            
            # Get current AWS account ID for the role ARN
            sts_client = boto3.client('sts', region_name=self.region)
            account_id = sts_client.get_caller_identity()['Account']
            role_arn = f"arn:aws:iam::{account_id}:role/instrument-diagnosis-assistant-kb-role"
            
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
                    "Principal": [role_arn]
                }
            ]
            
            try:
                opensearch_client.create_access_policy(
                    name=data_policy_name,
                    type='data',
                    policy=json.dumps(data_policy)
                )
                print(f"✅ Created data access policy: {data_policy_name}")
            except opensearch_client.exceptions.ConflictException:
                print(f"✅ Data access policy {data_policy_name} already exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create security policies: {e}")
            return False

    def create_opensearch_collection(self, prefix: str) -> Optional[str]:
        """Create OpenSearch Serverless collection"""
        # OpenSearch collection names must be <= 32 characters
        collection_name = "instrument-diag-kb"  # 18 characters, well under limit
        
        try:
            # Initialize OpenSearch Serverless client
            opensearch_client = boto3.client('opensearchserverless', region_name=self.region)
            
            # Check if collection already exists
            try:
                response = opensearch_client.list_collections()
                for collection in response.get('collectionSummaries', []):
                    if collection['name'] == collection_name:
                        collection_arn = collection['arn']
                        print(f"✅ OpenSearch collection {collection_name} already exists: {collection_arn}")
                        return collection_arn
            except Exception as e:
                print(f"⚠️  Could not list existing collections: {e}")
            
            # Create security policies first
            print(f"🔐 Creating security policies for collection: {collection_name}")
            if not self.create_opensearch_security_policies(collection_name):
                return None
            
            # Create new collection
            print(f"🔍 Creating OpenSearch Serverless collection: {collection_name}")
            response = opensearch_client.create_collection(
                name=collection_name,
                description="Vector collection for instrument diagnosis knowledge base",
                type='VECTORSEARCH'
            )
            
            collection_arn = response['createCollectionDetail']['arn']
            print(f"✅ Created OpenSearch collection: {collection_name} ({collection_arn})")
            
            # Wait for collection to be active
            print("⏳ Waiting for OpenSearch collection to be active...")
            collection_id = response['createCollectionDetail']['id']
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    collection_response = opensearch_client.batch_get_collection(ids=[collection_id])
                    collections = collection_response.get('collectionDetails', [])
                    if collections and collections[0]['status'] == 'ACTIVE':
                        print("✅ OpenSearch collection is active!")
                        break
                    else:
                        print(f"⏳ Collection status: {collections[0]['status'] if collections else 'UNKNOWN'}")
                        time.sleep(10)
                        wait_time += 10
                except Exception as e:
                    print(f"⚠️  Error checking collection status: {e}")
                    time.sleep(10)
                    wait_time += 10
            
            if wait_time >= max_wait:
                print("⚠️  Timeout waiting for collection to be active, but continuing...")
                # Don't fail here, the collection might still work
            
            return collection_arn
            
        except Exception as e:
            print(f"❌ Failed to create OpenSearch collection: {e}")
            return None

    def create_knowledge_base(self, prefix: str, role_arn: str, buckets: Dict[str, str]) -> Optional[str]:
        """Create Bedrock Knowledge Base"""
        kb_name = f"{prefix}-kb"
        
        # Check if KB already exists
        try:
            response = self.bedrock_agent.list_knowledge_bases()
            for kb in response.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    print(f"✅ Knowledge Base {kb_name} already exists: {kb['knowledgeBaseId']}")
                    return kb['knowledgeBaseId']
        except Exception as e:
            print(f"⚠️  Could not list existing knowledge bases: {e}")
        
        # Get existing OpenSearch collection ARN
        collection_arn = None
        try:
            opensearch_client = boto3.client('opensearchserverless', region_name=self.region)
            response = opensearch_client.list_collections()
            for collection in response.get('collectionSummaries', []):
                if collection['name'] == "instrument-diag-kb":
                    collection_arn = collection['arn']
                    print(f"✅ Using existing OpenSearch collection: {collection_arn}")
                    break
        except Exception as e:
            print(f"❌ Error finding OpenSearch collection: {e}")
            return None
        
        if not collection_arn:
            print("❌ OpenSearch collection not found")
            return None
        
        # Create new Knowledge Base - let Bedrock create the index automatically
        try:
            # Use a simple index name that Bedrock can create
            index_name = f"bedrock-knowledge-base-{kb_name.replace('-', '')}"
            
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
            self.wait_for_kb_ready(kb_id)
            
            return kb_id
            
        except Exception as e:
            print(f"❌ Failed to create Knowledge Base: {e}")
            return None
    
    def wait_for_kb_ready(self, kb_id: str, max_wait: int = 300):
        """Wait for Knowledge Base to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                status = response['knowledgeBase']['status']
                
                if status == 'ACTIVE':
                    print("✅ Knowledge Base is ready!")
                    return True
                elif status == 'FAILED':
                    print("❌ Knowledge Base creation failed!")
                    return False
                else:
                    print(f"⏳ Knowledge Base status: {status}")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"⚠️  Error checking KB status: {e}")
                time.sleep(10)
        
        print("⚠️  Timeout waiting for Knowledge Base to be ready")
        return False
    
    def create_data_sources(self, kb_id: str, buckets: Dict[str, str]) -> Dict[str, str]:
        """Create data sources for the Knowledge Base"""
        data_sources = {}
        
        source_configs = [
            ("troubleshooting-guides", "Troubleshooting guides with images and procedures", ["pdf", "png", "jpg", "jpeg"]),
            ("engineering-docs", "Component specifications and system architecture", ["pdf", "doc", "docx", "txt", "md"])
        ]
        
        for source_key, description, file_types in source_configs:
            if source_key not in buckets:
                print(f"⚠️  Bucket for {source_key} not found, skipping data source")
                continue
                
            bucket_name = buckets[source_key]
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
                data_sources[source_key] = ds_id
                print(f"✅ Created data source: {ds_name} ({ds_id})")
                
            except Exception as e:
                print(f"❌ Failed to create data source {ds_name}: {e}")
        
        return data_sources
    
    def update_config_file(self, kb_id: str, buckets: Dict[str, str]):
        """Update config.yaml with Knowledge Base ID and bucket names"""
        if 'knowledge_base' not in self.config:
            self.config['knowledge_base'] = {}
        
        self.config['knowledge_base']['kb_id'] = kb_id
        
        if 'deployment' not in self.config:
            self.config['deployment'] = {}
        
        self.config['deployment']['s3_buckets'] = buckets
        
        # Write updated config
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Updated {self.config_file} with Knowledge Base configuration")
    
    def setup(self, prefix: str = "instrument-diagnosis-assistant"):
        """Main setup function"""
        print(f"🚀 Setting up Instrument Diagnosis Assistant Knowledge Base")
        print(f"Region: {self.region}")
        print(f"Prefix: {prefix}")
        print()
        
        # Step 1: Create S3 buckets
        print("📦 Creating S3 buckets...")
        buckets = self.create_s3_buckets(prefix)
        if not buckets:
            print("❌ Failed to create S3 buckets")
            return False
        
        # Step 2: Create IAM role
        print("\n🔐 Creating IAM role...")
        role_arn = self.create_knowledge_base_role(prefix)
        if not role_arn:
            print("❌ Failed to create IAM role")
            return False
        
        # Step 3: Create Knowledge Base
        print("\n🧠 Creating Knowledge Base...")
        kb_id = self.create_knowledge_base(prefix, role_arn, buckets)
        if not kb_id:
            print("❌ Failed to create Knowledge Base")
            return False
        
        # Step 4: Create data sources
        print("\n📚 Creating data sources...")
        data_sources = self.create_data_sources(kb_id, buckets)
        
        # Step 5: Update configuration
        print("\n⚙️  Updating configuration...")
        self.update_config_file(kb_id, buckets)
        
        print("\n✅ Setup completed successfully!")
        print(f"\nKnowledge Base ID: {kb_id}")
        print(f"S3 Buckets: {list(buckets.values())}")
        print(f"\nNext steps:")
        print(f"1. Upload your troubleshooting guides to: s3://{buckets.get('troubleshooting-guides', 'N/A')}")
        print(f"2. Upload your engineering docs to: s3://{buckets.get('engineering-docs', 'N/A')}")
        print(f"3. Sync the data sources in the Bedrock console")
        print(f"4. Deploy your agent using: agentcore deploy")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Instrument Diagnosis Assistant Knowledge Base")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    parser.add_argument("--config", default="config.yaml", help="Configuration file")
    
    args = parser.parse_args()
    
    setup = KnowledgeBaseSetup(region=args.region, config_file=args.config)
    success = setup.setup(prefix=args.prefix)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()