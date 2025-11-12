def analyze_logs(log_content=None, log_file_path=None, gold_standard_path=None):
    """
    Analyze logs - accepts either content directly or file path
    """
    if log_content:
        # Process provided log content directly
        return process_log_content(log_content)
    elif log_file_path:
        # Fallback to file path if content not provided
        return process_log_file(log_file_path)
    else:
        return {"error": "No log data provided"}

def process_log_content(content):
    """Process log content that's already provided"""
    # Your existing analysis logic here
    pass