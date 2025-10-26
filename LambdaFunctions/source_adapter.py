import json
from datetime import datetime
from collections import defaultdict, Counter

def lambda_handler(event, context):
    # Extract CloudWatch Logs events
    log_events = []
    if 'detail' in event and 'logEvents' in event['detail']:
        log_events = event['detail']['logEvents']
    
    # Process the log events
    series = generate_error_series(log_events)
    exemplars = extract_exemplars(log_events)
    file_hits = count_file_hits(log_events)
    
    # Add source adapter output to the original event (fix double nesting)
    event['source_adapter_output'] = {
        'series': series,
        'exemplars': exemplars,
        'file_hits': file_hits,
        'deploy': {}
    }
    
    return event

def generate_error_series(log_events):
    error_counts = defaultdict(int)
    for log_event in log_events:
        if is_error_log(log_event):
            timestamp = datetime.fromtimestamp(log_event['timestamp'] / 1000)
            minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
            error_counts[minute_key] += 1
    return [[k, v] for k, v in sorted(error_counts.items())]

def extract_exemplars(log_events, max_exemplars=5):
    error_logs = [log for log in log_events if is_error_log(log)]
    return error_logs[:max_exemplars]

def count_file_hits(log_events):
    file_counter = Counter()
    for log_event in log_events:
        message = log_event.get('message', '')
        # Look for file patterns like .py, .js, etc.
        words = message.split()
        for word in words:
            if any(ext in word for ext in ['.py', '.js', '.java']):
                # Clean up the file name
                clean_word = word.strip('.,():')
                file_counter[clean_word] += 1
    return dict(file_counter)

def is_error_log(log_event):
    message = log_event.get('message', '').upper()
    return any(level in message for level in ['[ERROR]', '[CRITICAL]', '[FATAL]', 'ERROR:', 'CRITICAL:'])
