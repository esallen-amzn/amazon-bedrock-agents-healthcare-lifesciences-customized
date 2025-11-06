#!/usr/bin/env python3
"""
Simple Knowledge Base creation script that works with Bedrock's automatic index management
"""

import boto3
import json
import time
import sys
from typing import Optional

def create_knowledge_base_simple(prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Create Knowledge Base using Pinecone (simpler alternative)"""
    
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
    
    # Create Knowledge Base with in-memory vector store (simplest option)
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
            }
            # No storage configuration - uses default in-memory vector store
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_name} ({kb_id})")
        
        # Wait for KB to be ready
        print("⏳ Waiting for Knowledge Base to be ready...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
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
        
        print("⚠️  Timeout waiting for Knowledge Base to be ready")
        return kb_id  # Return anyway, might still work
        
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        return None

def create_data_sources(kb_id: str, prefix: str = "instrument-diagnosis-assistant") -> bool:
    """Create data sources for the Knowledge Base"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    
    source_configs = [
        ("troubleshooting-guides", "Troubleshooting guides with images and procedures"),
        ("engineering-docs", "Component specifications and system architecture")
    ]
    
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
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Knowledge Base with simple configuration")
    parser.add_argument("--prefix", default="instrument-diagnosis-assistant", help="Resource prefix")
    
    args = parser.parse_args()
    
    print(f"🚀 Creating Knowledge Base with simple configuration")
    print(f"Prefix: {args.prefix}")
    print()
    
    # Step 1: Create Knowledge Base
    kb_id = create_knowledge_base_simple(args.prefix)
    if not kb_id:
        print("❌ Failed to create Knowledge Base")
        return False
    
    # Step 2: Create data sources
    print("\n📚 Creating data sources...")
    create_data_sources(kb_id, args.prefix)
    
    print(f"\n✅ Setup completed!")
    print(f"Knowledge Base ID: {kb_id}")
    print(f"\nNext steps:")
    print(f"1. Upload your troubleshooting guides to: s3://{args.prefix}-troubleshooting-guides")
    print(f"2. Upload your engineering docs to: s3://{args.prefix}-engineering-docs")
    print(f"3. Sync the data sources in the Bedrock console")
    print(f"4. Update your config.yaml with the Knowledge Base ID")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)