import json
from datetime import datetime
from collections import defaultdict, Counter

def lambda_handler(event, context):
    # Read logs from JSON file
    with open('test_logs.json', 'r') as f:
        log_data = json.load(f)
    
    logs = log_data.get('logs', [])
    deploy = log_data.get('deploy', {})
    
    # Process logs
    series = generate_error_series(logs)
    exemplars = extract_exemplars(logs)
    file_hits = count_file_hits(logs)
    
    return {
        'source_adapter_output': {
            'series': series,
            'exemplars': exemplars,
            'file_hits': file_hits,
            'deploy': deploy
        }
    }

def generate_error_series(logs):
    error_counts = defaultdict(int)
    for log in logs:
        if is_error_log(log):
            timestamp = extract_timestamp(log)
            if timestamp:
                minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
                error_counts[minute_key] += 1
    return [[k, v] for k, v in sorted(error_counts.items())]

def extract_exemplars(logs, max_exemplars=5):
    error_logs = [log for log in logs if is_error_log(log)]
    return error_logs[:max_exemplars]

def count_file_hits(logs):
    file_counter = Counter()
    for log in logs:
        message = log.get('@message', '') or log.get('message', '')
        if '.py' in message:
            files = [word for word in message.split() if '.py' in word]
            for file_path in files:
                file_counter[file_path] += 1
    return dict(file_counter)

def is_error_log(log):
    if isinstance(log, dict):
        level = log.get('level', '').lower()
        message = (log.get('@message') or log.get('message', '')).lower()
        return level in ['error', 'fatal'] or 'error' in message
    return False

def extract_timestamp(log):
    timestamp_str = log.get('@timestamp') or log.get('timestamp')
    if timestamp_str:
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            pass
    return datetime.now()
