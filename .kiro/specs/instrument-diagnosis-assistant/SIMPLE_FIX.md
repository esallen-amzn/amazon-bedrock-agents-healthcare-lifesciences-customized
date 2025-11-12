# Simple Fix for S3 URI Detection Issue

## Problem
Agent receives user message without S3 file information, so it asks for file uploads instead of using existing S3 files.

## Root Cause
The Streamlit app uploads files to S3 but doesn't include the S3 URIs in the message sent to the agent.

## Fix
Modify the Streamlit app to include S3 file information in the user message.

## Implementation

### 1. Find the message construction in app.py
Look for where user messages are sent to the agent (around line 1000+ in the chat input section).

### 2. Add S3 context to user messages
Before sending the message to the agent, prepend S3 file information:

```python
# In app.py, modify the chat input section:
if prompt := st.chat_input("Ask about instrument diagnosis..."):
    # Get S3 file context
    s3_context = get_session_s3_context()  # Create this function
    
    # Prepend S3 context to user message
    full_message = s3_context + "\n\n" + prompt if s3_context else prompt
    
    # Send full_message to agent instead of just prompt
```

### 3. Create S3 context function
Add this function to app.py:

```python
def get_session_s3_context():
    """Get S3 file context for current session"""
    if 'uploaded_s3_files' not in st.session_state:
        return ""
    
    files = st.session_state.uploaded_s3_files
    if not files:
        return ""
    
    context = ["S3 FILES READY FOR ANALYSIS:"]
    for filename, metadata in files.items():
        context.append(f"S3 URI: {metadata['s3_uri']}")
        context.append(f"FILE: {filename}")
        context.append(f"SIZE: {metadata['file_size']} bytes")
    
    context.append("USE: get_s3_file_content(s3_uri='...') to retrieve files")
    return "\n".join(context)
```

### 4. Store S3 metadata in session state
When files are uploaded to S3, store the metadata:

```python
# After successful S3 upload:
if 'uploaded_s3_files' not in st.session_state:
    st.session_state.uploaded_s3_files = {}

st.session_state.uploaded_s3_files[filename] = {
    's3_uri': s3_uri,
    'file_size': file_size,
    'upload_time': datetime.now()
}
```

## Result
Agent will receive messages like:
```
S3 FILES READY FOR ANALYSIS:
S3 URI: s3://bucket/sessions/abc123/logs/error.log
FILE: error.log
SIZE: 5242032 bytes
USE: get_s3_file_content(s3_uri='...') to retrieve files

Please analyze my log files for errors.
```

This ensures the agent sees the S3 URIs and uses the S3 tools instead of asking for file uploads.