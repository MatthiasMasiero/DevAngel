"""
Query Logs Lambda - Executes CloudWatch Logs Insights queries and parses results.
"""
import json
import re
from datetime import datetime
from common.aws import run_logs_insights_query
from common.time import epoch_to_iso


def extract_files_from_message(message):
    """
    Extract file paths and line numbers from error messages.
    
    Args:
        message (str): Log message
        
    Returns:
        list: List of dicts with 'path' and 'line' keys
    """
    files = []
    
    # Python: File "path/to/file.py", line 123
    python_pattern = r'File "([^"]+)", line (\d+)'
    for match in re.finditer(python_pattern, message):
        files.append({"path": match.group(1), "line": int(match.group(2))})
    
    # Java: (ClassName.java:123)
    java_pattern = r'\(([^:]+\.java):(\d+)\)'
    for match in re.finditer(java_pattern, message):
        files.append({"path": match.group(1), "line": int(match.group(2))})
    
    # JavaScript: (file.js:123:45)
    js_pattern = r'\(([^:]+\.js):(\d+):\d+\)'
    for match in re.finditer(js_pattern, message):
        files.append({"path": match.group(1), "line": int(match.group(2))})
    
    return files


def build_file_hits(exemplars):
    """
    Build file hits summary from exemplars.
    
    Args:
        exemplars (list): List of exemplar dicts
        
    Returns:
        list: List of file hit summaries sorted by hit count
    """
    file_counts = {}
    
    for exemplar in exemplars:
        for file_info in exemplar.get('files', []):
            path = file_info['path']
            if path not in file_counts:
                file_counts[path] = {
                    'path': path,
                    'hits': 0,
                    'first_ts': exemplar['ts']
                }
            file_counts[path]['hits'] += 1
            # Keep earliest timestamp
            if exemplar['ts'] < file_counts[path]['first_ts']:
                file_counts[path]['first_ts'] = exemplar['ts']
    
    # Sort by hits descending
    return sorted(file_counts.values(), key=lambda x: x['hits'], reverse=True)


def lambda_handler(event, context):
    """
    Query CloudWatch Logs for error patterns and extract file information.
    
    Args:
        event: Context from get-context Lambda
        context: Lambda context
        
    Returns:
        dict: Enhanced context with series, exemplars, and file_hits
    """
    try:
        log_group = event['logGroup']
        start_epoch = event['window']['start_epoch']
        end_epoch = event['window']['end_epoch']
        
        print(f"Querying {log_group} from {start_epoch} to {end_epoch}")
        
        # Query 1: Time series data
        series_query = """
        fields @timestamp, @message
        | filter @message like /ERROR|Exception|Traceback/
        | stats count() as errors by bin(60s)
        """
        
        series_results = run_logs_insights_query(
            log_group, start_epoch, end_epoch, series_query
        )
        
        # Query 2: Error exemplars
        exemplars_query = """
        fields @timestamp, @message
        | filter @message like /ERROR|Exception|Traceback/
        | sort @timestamp desc
        | limit 200
        """
        
        exemplars_results = run_logs_insights_query(
            log_group, start_epoch, end_epoch, exemplars_query
        )
        
        # Process series data
        series = []
        for result in series_results:
            timestamp = result.get('@timestamp')
            errors = int(result.get('errors', 0))
            if timestamp:
                # Convert to ISO minute format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                iso_minute = dt.replace(second=0, microsecond=0).isoformat().replace('+00:00', 'Z')
                series.append([iso_minute, errors])
        
        series.sort(key=lambda x: x[0])  # Sort by timestamp
        
        # Process exemplars (limit to 50)
        exemplars = []
        for result in exemplars_results[:50]:
            timestamp = result.get('@timestamp')
            message = result.get('@message', '')
            if timestamp and message:
                files = extract_files_from_message(message)
                exemplars.append({
                    'ts': timestamp,
                    'message': message,
                    'files': files
                })
        
        # Build file hits summary
        file_hits = build_file_hits(exemplars)
        
        # Merge with input event
        response = event.copy()
        response.update({
            'series': series,
            'exemplars': exemplars,
            'file_hits': file_hits
        })
        
        print(f"Found {len(series)} time points, {len(exemplars)} exemplars, {len(file_hits)} unique files")
        return response
        
    except Exception as e:
        print(f"Error querying logs: {str(e)}")
        raise
