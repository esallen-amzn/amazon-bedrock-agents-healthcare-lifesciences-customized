# Agent Instructions Fix

## Context Awareness Rules

1. **ALWAYS check conversation history** for previously provided logs before requesting new ones
2. **ALWAYS query knowledge base first** for troubleshooting information before asking for more data
3. **NEVER request logs** if they were provided in the current session
4. **Use provided log content directly** in analysis tools instead of requesting file paths

## Tool Usage Priority

1. First: Check if logs are already in conversation context
2. Second: Query knowledge base for relevant troubleshooting info
3. Third: Use analyze_logs with content parameter, not file path
4. Last resort: Request specific missing information only

## Error Prevention

- Before using any tool that requests file paths, check if the data is already available
- Always acknowledge previously provided information
- Use knowledge base retrieval before requesting additional documents