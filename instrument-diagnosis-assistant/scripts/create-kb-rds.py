#!/usr/bin/env python3
"""
Create Knowledge Base using Amazon RDS with pgvector
This avoids the OpenSearch permission issues
"""

import boto3
import json
import time
import sys
from typing import Optional

def create_knowledge_base_rds(prefix: str = "instrument-diagnosis-assistant") -> Optional[str]:
    """Create Knowledge Base using RDS PostgreSQL with pgvector"""
    
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
    
    # Create Knowledge Base with RDS storage
    try:
        print(f"🧠 Creating Knowledge Base with RDS storage: {kb_name}")
        
        # For now, let's try without storage configuration to see if Bedrock has a default
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
                'type': 'RDS',
                'rdsConfiguration': {
                    'resourceArn': 'arn:aws:rds:us-east-1:390402579286:cluster:bedrock-kb-cluster',  # We'll need to create this
                    'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:390402579286:secret:bedrock-kb-secret',  # We'll need to create this
                    'databaseName': 'bedrock_kb',
                    'tableName': 'bedrock_kb_table',
                    'fieldMapping': {
                        'primaryKeyField': 'id',
                        'vectorField': 'embedding',
                        'textField': 'chunks',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✅ Created Knowledge Base: {kb_name} ({kb_id})")
        return kb_id
        
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base with RDS: {e}")
        
        # Try with Pinecone instead
        try:
            print(f"🔄 Trying with Pinecone storage...")
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
                    'type': 'PINECONE',
                    'pineconeConfiguration': {
                        'connectionString': 'https://your-index.pinecone.io',  # Would need real Pinecone setup
                        'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:390402579286:secret:pinecone-api-key',
                        'namespace': 'instrument-diagnosis',
                        'fieldMapping': {
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            print(f"✅ Created Knowledge Base with Pinecone: {kb_name} ({kb_id})")
            return kb_id
            
        except Exception as e2:
            print(f"❌ Failed to create Knowledge Base with Pinecone: {e2}")
            return None

def main():
    print("🚀 Creating Knowledge Base with alternative storage")
    print("This avoids OpenSearch permission issues")
    print()
    
    kb_id = create_knowledge_base_rds()
    if kb_id:
        print(f"\n✅ Knowledge Base created successfully!")
        print(f"Knowledge Base ID: {kb_id}")
    else:
        print(f"\n❌ Failed to create Knowledge Base")
        print("You may need to set up RDS or Pinecone storage first")
    
    return kb_id is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)