#!/usr/bin/env python3
"""
Create Knowledge Base using Bedrock's managed vector store
This should work without external dependencies
"""

import boto3
import json
import time
import sys
import yaml
from typing import Optional, Dict, Any

def load_config(config_file: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️  Could not load config file {config_file}: {e}")
        return {}

def create_knowledge_base_managed(prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Create Knowledge Base using Bedrock's managed vector store"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    iam_client = boto3.client('iam')
    
    kb_name = f"{prefix}-kb"
    role_name = f"{prefix}-kb-role"
    
    # Get role ARN
    try:
        role_response = iam_client.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
        print(f"✅ Using IAM role: {role_arn}")
    except Exception as e:
        print(f"❌ Error getting IAM role: {e}")
        return None
    
    # Check if KB already exists
    try:
        response = bedrock_agent.list_knowledge_bases()
        for kb in response.get('knowledgeBaseSummaries', []):
            if kb['name'] == kb_name:
                print(f"✅ Knowledge Base {kb_name} already exists: {kb['knowledgeBaseId']}")
                return kb['knowledgeBaseId']
    except Exception as e:
        print(f"⚠️  Could not list existing knowledge bases: {e}")
    
    # Try different storage configurations
    storage_configs = [
        # Option 1: No storage configuration (let Bedrock manage)
        {
            'name': 'Bedrock Managed',
            'config': None
        },
        # Option 2: Try with minimal OpenSearch config
        {
            'name': 'OpenSearch Serverless (minimal)',
            'config': {
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': 'arn:aws:aoss:us-east-1:390402579286:collection/et0w0nl0hjap3m12i1n9',
                    'vectorIndexName': 'bedrock-default-index',
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        }
    ]
    
    for storage_option in storage_configs:
        try:
            print(f"🧠 Trying to create Knowledge Base with {storage_option['name']}...")
            
            kb_config = {
                'name': kb_name,
                'description': "Knowledge base for instrument diagnosis troubleshooting guides and documentation",
                'roleArn': role_arn,
                'knowledgeBaseConfiguration': {
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
                    }
                }
            }
            
            # Add storage configuration if provided
            if storage_option['config']:
                kb_config['storageConfiguration'] = storage_option['config']
            
            response = bedrock_agent.create_knowledge_base(**kb_config)
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base with {storage_option['name']}: {kb_name} ({kb_id})")
            
            # Wait for KB to be ready
            print("⏳ Waiting for Knowledge Base to be ready...")
            if wait_for_kb_ready(bedrock_agent, kb_id):
                return kb_id
            else:
                print(f"⚠️  Knowledge Base created but not ready, continuing anyway...")
                return kb_id
            
        except Exception as e:
            print(f"❌ Failed to create Knowledge Base with {storage_option['name']}: {e}")
            continue
    
    print("❌ All storage options failed")
    return None

def wait_for_kb_ready(bedrock_agent, kb_id: str, max_wait: int = 300) -> bool:
    """Wait for Knowledge Base to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
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

def create_data_sources(kb_id: str, prefix: str = "instrument-diagnosis-assistant") -> bool:
    """Create data sources for the Knowledge Base"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    
    source_configs = [
        ("troubleshooting-guides", "Troubleshooting guides with images and procedures"),
        ("engineering-docs", "Component specifications and system architecture")
    ]
    
    success = True
    
    for source_key, description in source_configs:
        bucket_name = f"{prefix}-{source_key}"
        ds_name = f"{source_key}-ds"
        
        try:
            print(f"📚 Creating data source: {ds_name}")
            response = bedrock_agent.create_data_source(
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
            success = False
    
    return success

def update_config_file(kb_id: str, config_file: str = "config.yaml") -> bool:
    """Update config.yaml with Knowledge Base ID"""
    try:
        config = load_config(config_file)
        
        if 'knowledge_base' not in config:
            config['knowledge_base'] = {}
        
        config['knowledge_base']['kb_id'] = kb_id
        
        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"✅ Updated {config_file} with Knowledge Base ID: {kb_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update config file: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Knowledge Base with managed vector store")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    parser.add_argument("--config", default="config.yaml", help="Configuration file to update")
    
    args = parser.parse_args()
    
    print(f"🚀 Creating Knowledge Base with managed vector store")
    print(f"Prefix: {args.prefix}")
    print()
    
    # Step 1: Create Knowledge Base
    kb_id = create_knowledge_base_managed(args.prefix)
    if not kb_id:
        print("❌ Failed to create Knowledge Base")
        return False
    
    # Step 2: Create data sources
    print("\n📚 Creating data sources...")
    create_data_sources(kb_id, args.prefix)
    
    # Step 3: Update configuration
    print("\n⚙️  Updating configuration...")
    update_config_file(kb_id, args.config)
    
    print(f"\n✅ Setup completed!")
    print(f"Knowledge Base ID: {kb_id}")
    print(f"\nNext steps:")
    print(f"1. Upload your troubleshooting guides to: s3://{args.prefix}-troubleshooting-guides")
    print(f"2. Upload your engineering docs to: s3://{args.prefix}-engineering-docs")
    print(f"3. Sync the data sources in the Bedrock console")
    print(f"4. Test the Knowledge Base with queries")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)