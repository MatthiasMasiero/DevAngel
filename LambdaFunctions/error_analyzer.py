import json
import boto3
from datetime import datetime
from collections import Counter

s3 = boto3.client('s3')
BUCKET_NAME = 'devangel-incident-data-1761448500'

def lambda_handler(event, context):
    """
    Error analyzer that processes source adapter output and performs detailed error analysis
    """
    
    try:
        # Get source adapter output
        source_output = event.get('source_adapter_output', {})
        error_events = source_output.get('error_events', [])
        summary = source_output.get('summary', {})
        
        # Perform error analysis
        analysis_results = {
            'error_patterns': analyze_error_patterns(error_events),
            'severity_distribution': analyze_severity_distribution(error_events),
            'source_breakdown': analyze_error_sources(error_events),
            'time_analysis': analyze_error_timing(error_events),
            'recommendations': generate_recommendations(error_events),
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_errors_analyzed': len(error_events)
        }
        
        # Create detailed error report
        error_report = {
            'summary': summary,
            'analysis': analysis_results,
            'error_events': error_events,
            'metadata': {
                'analyzer_version': '1.0',
                'processing_time': datetime.utcnow().isoformat(),
                'request_id': context.aws_request_id
            }
        }
        
        # Store analysis results in S3
        analysis_key = f"error-analysis/{datetime.utcnow().strftime('%Y/%m/%d')}/analysis-{context.aws_request_id}.json"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=analysis_key,
            Body=json.dumps(error_report, indent=2),
            ContentType='application/json'
        )
        
        # Store critical errors separately for fast access
        critical_errors = [e for e in error_events if e.get('errorType') in ['TimeoutError', 'ConnectionError']]
        if critical_errors:
            critical_key = f"critical-errors/{datetime.utcnow().strftime('%Y/%m/%d')}/critical-{context.aws_request_id}.json"
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=critical_key,
                Body=json.dumps(critical_errors, indent=2),
                ContentType='application/json'
            )
        
        return {
            'error_analyzer_output': {
                'analysis_results': analysis_results,
                'critical_errors': critical_errors,
                'error_count': len(error_events),
                'critical_issues_count': len(critical_errors),
                's3_analysis_location': f"s3://{BUCKET_NAME}/{analysis_key}",
                's3_critical_location': f"s3://{BUCKET_NAME}/{critical_key}" if critical_errors else None,
                'needs_immediate_attention': len(critical_errors) > 0,
                'error_summary': {
                    'total_errors': len(error_events),
                    'critical_count': len(critical_errors),
                    'most_common_source': get_most_common_source(error_events),
                    'most_common_error_type': get_most_common_error_type(error_events)
                }
            }
        }
        
    except Exception as e:
        print(f"Error in error analyzer: {str(e)}")
        return {
            'error_analyzer_output': {
                'analysis_results': {'error': str(e)},
                'critical_errors': [],
                'error_count': 0,
                'needs_immediate_attention': True,
                'error_summary': {'analyzer_error': str(e)}
            }
        }

def analyze_error_patterns(error_events):
    """Analyze common error patterns"""
    patterns = Counter()
    
    for error in error_events:
        message = error.get('message', '')
        error_type = error.get('errorType', 'Unknown')
        source = error.get('source', 'Unknown')
        
        # Create pattern signature
        pattern = f"{source}:{error_type}"
        patterns[pattern] += 1
    
    return {
        'most_common_patterns': patterns.most_common(5),
        'total_unique_patterns': len(patterns),
        'pattern_details': dict(patterns)
    }

def analyze_severity_distribution(error_events):
    """Analyze error severity distribution"""
    severity_map = {
        'TimeoutError': 'High',
        'ConnectionError': 'High',
        'ValidationException': 'Medium',
        'AccessDenied': 'High',
        'ThrottlingException': 'Medium',
        'InstanceUnreachable': 'High',
        'VisibilityTimeoutExceeded': 'Low'
    }
    
    severity_counts = Counter()
    
    for error in error_events:
        error_type = error.get('errorType', 'Unknown')
        severity = severity_map.get(error_type, 'Medium')
        severity_counts[severity] += 1
    
    return {
        'severity_distribution': dict(severity_counts),
        'high_severity_count': severity_counts.get('High', 0),
        'requires_immediate_action': severity_counts.get('High', 0) > 0
    }

def analyze_error_sources(error_events):
    """Analyze error sources"""
    source_counts = Counter()
    source_errors = {}
    
    for error in error_events:
        source = error.get('source', 'Unknown')
        source_counts[source] += 1
        
        if source not in source_errors:
            source_errors[source] = []
        source_errors[source].append(error.get('errorType', 'Unknown'))
    
    return {
        'source_distribution': dict(source_counts),
        'most_problematic_source': source_counts.most_common(1)[0] if source_counts else None,
        'source_error_types': {k: Counter(v).most_common() for k, v in source_errors.items()}
    }

def analyze_error_timing(error_events):
    """Analyze error timing patterns"""
    if not error_events:
        return {'no_errors': True}
    
    timestamps = [error.get('timestamp', 0) for error in error_events]
    timestamps = [t for t in timestamps if t > 0]
    
    if not timestamps:
        return {'no_valid_timestamps': True}
    
    time_diffs = []
    for i in range(1, len(timestamps)):
        diff = timestamps[i] - timestamps[i-1]
        time_diffs.append(diff / 1000)  # Convert to seconds
    
    return {
        'error_frequency': len(error_events),
        'time_span_seconds': (max(timestamps) - min(timestamps)) / 1000 if len(timestamps) > 1 else 0,
        'average_interval_seconds': sum(time_diffs) / len(time_diffs) if time_diffs else 0,
        'burst_detected': any(diff < 5 for diff in time_diffs) if time_diffs else False
    }

def generate_recommendations(error_events):
    """Generate recommendations based on error analysis"""
    recommendations = []
    
    # Analyze error types and generate specific recommendations
    error_types = Counter(error.get('errorType', 'Unknown') for error in error_events)
    sources = Counter(error.get('source', 'Unknown') for error in error_events)
    
    # Timeout recommendations
    if error_types.get('TimeoutError', 0) > 0:
        recommendations.append({
            'priority': 'High',
            'category': 'Performance',
            'issue': 'Lambda timeout errors detected',
            'recommendation': 'Increase Lambda timeout settings or optimize function performance',
            'affected_count': error_types['TimeoutError']
        })
    
    # Connection error recommendations
    if error_types.get('ConnectionError', 0) > 0:
        recommendations.append({
            'priority': 'High',
            'category': 'Infrastructure',
            'issue': 'Database connection failures',
            'recommendation': 'Check RDS instance health and connection pool settings',
            'affected_count': error_types['ConnectionError']
        })
    
    # Access denied recommendations
    if error_types.get('AccessDenied', 0) > 0:
        recommendations.append({
            'priority': 'High',
            'category': 'Security',
            'issue': 'IAM permission errors',
            'recommendation': 'Review and update IAM policies for affected resources',
            'affected_count': error_types['AccessDenied']
        })
    
    # Throttling recommendations
    if error_types.get('ThrottlingException', 0) > 0:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Scaling',
            'issue': 'API throttling detected',
            'recommendation': 'Implement exponential backoff or increase API limits',
            'affected_count': error_types['ThrottlingException']
        })
    
    return recommendations

def get_most_common_source(error_events):
    """Get the most common error source"""
    if not error_events:
        return None
    
    sources = Counter(error.get('source', 'Unknown') for error in error_events)
    return sources.most_common(1)[0][0] if sources else None

def get_most_common_error_type(error_events):
    """Get the most common error type"""
    if not error_events:
        return None
    
    error_types = Counter(error.get('errorType', 'Unknown') for error in error_events)
    return error_types.most_common(1)[0][0] if error_types else None
