def process_uploaded_files(uploaded_files, max_content_length: int = 2000) -> str:
    """
    Process uploaded files by uploading to S3 and returning S3 URI information for the agent.
    
    Args:
        uploaded_files: List of Streamlit uploaded file objects
        max_content_length: Unused (kept for compatibility)
    
    Returns:
        Formatted string with S3 file information and agent instructions
    """
    # Note: st is already imported at module level
    if not uploaded_files:
        # Check if we have files from previous uploads in this session
        session_context = get_session_context(st.session_state)
        if session_context:
            return session_context
        
        # Try to load existing S3 files for this session
        if 'runtime_session_id' in st.session_state:
            load_existing_s3_files_for_session(st.session_state, st.session_state.runtime_session_id)
            session_context = get_session_context(st.session_state)
            if session_context:
                return session_context
        
        return ""
    
    # Get session ID from Streamlit session state
    if 'runtime_session_id' not in st.session_state:
        st.session_state.runtime_session_id = str(uuid.uuid4())
    session_id = st.session_state.runtime_session_id
    
    # Create progress callback for upload status
    progress_placeholder = st.empty()
    
    def show_progress(current, total, filename):
        progress_placeholder.info(f"⬆️ Uploading to S3: {filename} ({current}/{total})")
    
    # Upload files to S3 and get metadata
    file_metadata = upload_files_to_s3(uploaded_files, session_id, progress_callback=show_progress)
    
    # Clear progress message
    progress_placeholder.empty()
    
    if not file_metadata:
        return "\n=== NO FILES SUCCESSFULLY UPLOADED TO S3 ===\n"
    
    # Update session registry
    update_session_file_registry(st.session_state, file_metadata)
    
    # Create action summary with S3 file information
    action_summary = []
    action_summary.append("\n" + "="*60)
    action_summary.append("CRITICAL INSTRUCTION: FILES ARE ALREADY UPLOADED TO S3")
    action_summary.append("DO NOT ASK FOR FILES - USE S3 TOOLS IMMEDIATELY")
    action_summary.append("="*60)
    action_summary.append(f"AGENT ACTION REQUIRED: {len(file_metadata)} S3 FILES READY")
    action_summary.append("="*60)
    
    # Sort files by size (largest first) and type (errors first)
    sorted_files = sorted(file_metadata.items(), key=lambda x: (
        'error' not in x[0].lower(),  # Error files first
        -x[1]['file_size']  # Then by size (largest first)
    ))
    
    total_size = sum(meta['file_size'] for meta in file_metadata.values())
    action_summary.append(f"TOTAL SIZE: {total_size / (1024*1024):.2f} MB")
    action_summary.append(f"S3 STORAGE: Files stored with session-based organization")
    action_summary.append("")
    
    # Handle multiple files intelligently
    if len(file_metadata) > 3:
        action_summary.append("MULTIPLE FILES DETECTED - CRITICAL: Process ONE file at a time to avoid token limits")
        action_summary.append("PRIORITY ORDER: Error logs first, then by size")
        action_summary.append("STRATEGY: Analyze first file only, provide diagnosis, then user can request next file")
        action_summary.append("")
    
    files_processed = 0
    # CRITICAL: For multiple large files, only show the FIRST file to avoid token limits
    max_files_to_show = 1 if len(file_metadata) > 2 and any(m['file_size'] > 500*1024 for m in file_metadata.values()) else 3
    
    for original_name, metadata in sorted_files:
        file_size = metadata['file_size']
        s3_uri = metadata['s3_uri']
        s3_key = metadata['key']
        
        action_summary.append(f"\n📁 FILE {files_processed + 1}: {original_name}")
        action_summary.append(f"   S3_URI: {s3_uri}")
        action_summary.append(f"   SIZE: {file_size / (1024*1024):.2f} MB")
        
        # Provide S3-based analysis instructions - use summary for files >500KB
        if file_size > 500 * 1024:  # Files > 500KB
            action_summary.append(f"   ⚡ ACTION: extract_s3_log_summary(s3_uri='{s3_uri}')")
            action_summary.append(f"   REASON: File >{file_size / (1024*1024):.1f}MB - MUST use summary for speed")
        else:
            action_summary.append(f"   ⚡ ACTION: get_s3_file_content(s3_uri='{s3_uri}')")
            action_summary.append(f"   REASON: Small file - can retrieve full content")
        
        action_summary.append("")
        
        files_processed += 1
        # CRITICAL: Limit to avoid token limits with multiple large files
        if files_processed >= max_files_to_show:
            remaining_files = len(file_metadata) - files_processed
            if remaining_files > 0:
                action_summary.append(f"[{remaining_files} additional files available - process one at a time]")
                action_summary.append(f"IMPORTANT: Analyze the first file above, then user can request next file")
                action_summary.append(f"Use list_session_logs(session_id='{session_id}') to see all files")
            break
    
    # Add appropriate action based on file count
    action_summary.append("\n" + "="*60)
    action_summary.append("⚡ IMMEDIATE NEXT STEPS:")
    action_summary.append("="*60)
    
    if len(file_metadata) == 1:
        first_file = list(file_metadata.values())[0]
        if first_file['file_size'] > 500 * 1024:  # 500KB threshold
            action_summary.append(f"1. Call: extract_s3_log_summary(s3_uri='{first_file['s3_uri']}')")
            action_summary.append(f"2. Call: analyze_log_content(summary_from_step_1, '')")
            action_summary.append(f"3. Provide diagnosis results")
            action_summary.append(f"CRITICAL: File is {first_file['file_size'] / (1024*1024):.1f}MB - MUST use extract_s3_log_summary")
        else:
            action_summary.append(f"1. Call: get_s3_file_content(s3_uri='{first_file['s3_uri']}')")
            action_summary.append(f"2. Call: analyze_log_content(content_from_step_1, '')")
            action_summary.append(f"3. Provide diagnosis results")
    elif len(file_metadata) <= 3:
        action_summary.append("CRITICAL: Process files ONE AT A TIME to avoid token limits")
        action_summary.append("1. Analyze ONLY the first file listed above")
        action_summary.append("2. If file >500KB: Call extract_s3_log_summary(s3_uri='...') - REQUIRED FOR SPEED")
        action_summary.append("   If file <500KB: Call get_s3_file_content(s3_uri='...')")
        action_summary.append("3. Call: analyze_log_content(content_or_summary, '')")
        action_summary.append("4. Provide diagnosis for this file")
        action_summary.append("5. User can then request analysis of next file if needed")
    else:
        action_summary.append("CRITICAL: MANY FILES DETECTED - Process ONE file at a time")
        action_summary.append(f"1. Analyze ONLY the first file listed above")
        action_summary.append("2. If file >500KB: extract_s3_log_summary(s3_uri='...') - REQUIRED")
        action_summary.append("   If file <500KB: get_s3_file_content(s3_uri='...')")
        action_summary.append("3. Provide diagnosis for this ONE file")
        action_summary.append("4. DO NOT process additional files in same response - token limit will be exceeded")
        action_summary.append(f"5. User can request next file analysis separately")
        action_summary.append(f"Available: list_session_logs(session_id='{session_id}') to see all files")
    
    action_summary.append("")
    action_summary.append("🚫 DO NOT ASK USER TO UPLOAD FILES - THEY ARE ALREADY IN S3")
    action_summary.append("="*60)
    
    return '\n'.join(action_summary)
