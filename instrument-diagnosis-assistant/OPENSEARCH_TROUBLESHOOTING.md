# OpenSearch Serverless Troubleshooting Guide

## Issue Summary
We're encountering persistent 403 Forbidden errors when trying to create vector indexes in the OpenSearch Serverless collection, even after setting up comprehensive data access policies.

## Root Cause Analysis
The issue appears to be related to how AWS STS assumed role ARNs are handled in OpenSearch Serverless data access policies. The current user ARN format `arn:aws:sts::390402579286:assumed-role/Admin/esallen-Isengard` may not be compatible with OpenSearch access policies.

## Attempted Solutions

### 1. ✅ Collection and Policy Recreation
- Successfully deleted and recreated the OpenSearch collection
- Successfully created encryption, network, and data access policies
- Collection is active and accessible

### 2. ❌ Vector Index Creation
- Consistently fails with 403 Forbidden errors
- Tried multiple index names and configurations
- Tried different field mappings (Bedrock standard vs custom)

### 3. ❌ Permission Variations
- Added both Knowledge Base role and current user to data access policy
- Tried wildcard permissions (`aoss:*`)
- Waited for policy propagation (30-60 seconds)

## Alternative Solutions

### Option 1: Use IAM User Instead of Assumed Role
Create a dedicated IAM user for Knowledge Base setup instead of using assumed role credentials.

### Option 2: Use AWS CLI with Different Credentials
Switch to using IAM user credentials or a different role that might work better with OpenSearch.

### Option 3: Manual Index Creation via AWS Console
Create the vector index manually through the AWS OpenSearch console, then proceed with Knowledge Base creation.

### Option 4: Use Alternative Vector Store
Consider using Amazon RDS with pgvector or Pinecone instead of OpenSearch Serverless.

## Recommended Next Steps

1. **Try Manual Console Creation**: 
   - Go to AWS OpenSearch Serverless console
   - Navigate to the `instrument-diag-kb` collection
   - Manually create a vector index with the required specifications
   - Then run the Knowledge Base creation script

2. **Use Different Credentials**:
   - Create a dedicated IAM user for this setup
   - Use those credentials instead of assumed role

3. **Simplify the Architecture**:
   - Consider using a simpler vector store solution
   - Or proceed without Knowledge Base for now and add it later

## Vector Index Specifications Needed

When creating manually, use these specifications:

```json
{
  "settings": {
    "index": {
      "knn": true,
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
```

Index name: `bedrock-kb-instrumentdiagnosisassistant`

## Current Status
- ✅ OpenSearch collection created and active
- ✅ Security policies configured
- ✅ IAM roles and S3 buckets ready
- ❌ Vector index creation blocked by permissions
- ❌ Knowledge Base creation pending index creation

The infrastructure is 90% ready - only the vector index creation is blocking completion.