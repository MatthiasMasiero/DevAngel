import json
import boto3
import re
from datetime import datetime
from collections import defaultdict, Counter

s3 = boto3.client('s3')
BUCKET_NAME = 'devangel-incident-data-1761448500'

def lambda_handler(event, context):
    """
    Source adapter that processes CloudWatch logs and extracts relevant data
    """
    
    try:
        # Load simulated CloudWatch logs from event or use embedded default
        log_data = event.get('logData', {})
        
        # If no log data in event, use embedded simulated data
        if not log_data:
            log_data = get_embedded_simulated_logs()
        
        # Process log events
        processed_events = []
        error_events = []
        
        for log_event in log_data.get('logEvents', []):
            processed_event = {
                'timestamp': log_event.get('timestamp'),
                'message': log_event.get('message'),
                'logLevel': log_event.get('logLevel', 'INFO'),
                'requestId': log_event.get('requestId'),
                'source': log_event.get('source'),
                'errorType': log_event.get('errorType'),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            processed_events.append(processed_event)
            
            # Collect error events for analysis
            if processed_event['logLevel'] in ['ERROR', 'WARN']:
                error_events.append(processed_event)
        
        # Generate analysis using existing functions
        series = generate_error_series(processed_events)
        exemplars = extract_exemplars(error_events)
        file_hits = count_file_hits(processed_events)
        
        # Create summary
        summary = {
            'total_events': len(processed_events),
            'error_count': len([e for e in processed_events if e['logLevel'] == 'ERROR']),
            'warning_count': len([e for e in processed_events if e['logLevel'] == 'WARN']),
            'info_count': len([e for e in processed_events if e['logLevel'] == 'INFO']),
            'processing_timestamp': datetime.utcnow().isoformat(),
            'log_group': log_data.get('logGroupName', '/aws/lambda/devangel-functions')
        }
        
        # Store raw processed data in S3
        raw_data_key = f"raw-logs/{datetime.utcnow().strftime('%Y/%m/%d')}/processed-{context.aws_request_id}.json"
        
        raw_data = {
            'summary': summary,
            'events': processed_events,
            'error_events': error_events,
            'analysis': {
                'series': series,
                'exemplars': exemplars,
                'file_hits': file_hits
            }
        }
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=raw_data_key,
            Body=json.dumps(raw_data, indent=2),
            ContentType='application/json'
        )
        
        print(f"Processed {len(processed_events)} events, found {len(error_events)} errors")
        
        return {
            'source_adapter_output': {
                'series': series,
                'exemplars': exemplars,
                'file_hits': file_hits,
                'summary': summary,
                'error_events': error_events,
                's3_location': f"s3://{BUCKET_NAME}/{raw_data_key}"
            }
        }
        
    except Exception as e:
        print(f"Error in source adapter: {str(e)}")
        return {
            'source_adapter_output': {
                'series': [],
                'exemplars': [],
                'file_hits': {},
                'summary': {'error': str(e)},
                'error_events': []
            }
        }

def get_embedded_simulated_logs():
    """Embedded simulated CloudWatch logs for testing"""
    return {
        "logEvents": [
            {
                "timestamp": 1698345600000,
                "message": "2023-10-26T12:00:00.000Z INFO [RequestId: abc123] Lambda function started successfully",
                "logLevel": "INFO",
                "requestId": "abc123",
                "source": "lambda"
            },
            {
                "timestamp": 1698345605000,
                "message": "2023-10-26T12:00:05.000Z ERROR [RequestId: def456] DynamoDB operation failed: The provided key element does not match the schema",
                "logLevel": "ERROR",
                "requestId": "def456",
                "source": "dynamodb",
                "errorType": "ValidationException"
            },
            {
                "timestamp": 1698345610000,
                "message": "2023-10-26T12:00:10.000Z INFO [RequestId: ghi789] S3 object uploaded successfully to bucket: devangel-data",
                "logLevel": "INFO",
                "requestId": "ghi789",
                "source": "s3"
            },
            {
                "timestamp": 1698345615000,
                "message": "2023-10-26T12:00:15.000Z WARN [RequestId: jkl012] API Gateway throttling detected: Rate exceeded",
                "logLevel": "WARN",
                "requestId": "jkl012",
                "source": "apigateway",
                "errorType": "ThrottlingException"
            },
            {
                "timestamp": 1698345620000,
                "message": "2023-10-26T12:00:20.000Z ERROR [RequestId: mno345] Lambda timeout: Task timed out after 30.00 seconds",
                "logLevel": "ERROR",
                "requestId": "mno345",
                "source": "lambda",
                "errorType": "TimeoutError"
            },
            {
                "timestamp": 1698345630000,
                "message": "2023-10-26T12:00:30.000Z ERROR [RequestId: stu901] RDS connection failed: Could not connect to database instance",
                "logLevel": "ERROR",
                "requestId": "stu901",
                "source": "rds",
                "errorType": "ConnectionError"
            },
            {
                "timestamp": 1698345640000,
                "message": "2023-10-26T12:00:40.000Z ERROR [RequestId: yza567] IAM permission denied: User is not authorized to perform action",
                "logLevel": "ERROR",
                "requestId": "yza567",
                "source": "iam",
                "errorType": "AccessDenied"
            },
            {
                "timestamp": 1698345650000,
                "message": "2023-10-26T12:00:50.000Z ERROR [RequestId: efg123] EC2 instance health check failed: Instance i-1234567890abcdef0 is unreachable",
                "logLevel": "ERROR",
                "requestId": "efg123",
                "source": "ec2",
                "errorType": "InstanceUnreachable"
            }
        ],
        "logGroupName": "/aws/lambda/devangel-functions"
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

def extract_exemplars(logs, max_exemplars=10):
    error_logs = [log for log in logs if is_error_log(log)]
    error_groups = defaultdict(list)
    for log in error_logs:
        error_signature = get_error_signature(log)
        error_groups[error_signature].append(log)
    exemplars = []
    for signature, group in error_groups.items():
        exemplars.append(group[0])
        if len(exemplars) >= max_exemplars:
            break
    return exemplars[:max_exemplars]

def count_file_hits(logs):
    file_counter = Counter()
    for log in logs:
        files = extract_files_from_stacktrace(log)
        for file_path in files:
            file_counter[file_path] += 1
    return dict(file_counter)

def is_error_log(log):
    if isinstance(log, dict):
        level = log.get('logLevel', '').upper()
        message = log.get('message', '').lower()
        return level in ['ERROR', 'FATAL'] or 'error' in message or 'exception' in message
    return False

def extract_timestamp(log):
    if isinstance(log, dict):
        timestamp = log.get('timestamp')
        if timestamp:
            try:
                return datetime.fromtimestamp(timestamp / 1000)
            except:
                pass
    return datetime.now()

def get_error_signature(log):
    if isinstance(log, dict):
        message = log.get('message', '')
    else:
        message = str(log)
    signature = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', message)
    signature = re.sub(r'\[RequestId: [^\]]+\]', '[REQUEST_ID]', signature)
    signature = re.sub(r'\b\d+\b', '[NUMBER]', signature)
    return signature[:200]

def extract_files_from_stacktrace(log):
    files = []
    if isinstance(log, dict):
        message = log.get('message', '')
    else:
        message = str(log)
    
    patterns = [
        r'File\s+"([^"]+\.(?:py|js|java|rb|php|go|rs|cpp|c|h))"',
        r'([/\w.-]+\.(?:py|js|java|rb|php|go|rs|cpp|c|h)):\d+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, message)
        files.extend(matches)
    return list(set(files))
