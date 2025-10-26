import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = 'devangel-incident-data-1761448500'

def lambda_handler(event, context):
    """
    API for dashboard to get incident data
    """
    
    # Handle CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Get latest incident data from S3
        if event.get('httpMethod') == 'GET':
            return get_latest_incident(headers)
        
        # Store new incident data (called by Step Functions)
        elif event.get('httpMethod') == 'POST':
            return store_incident_data(event, headers)
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def get_latest_incident(headers):
    """Get latest incident for dashboard"""
    
    try:
        # Get latest incident from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key='latest-incident.json')
        incident_data = json.loads(response['Body'].read())
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'success',
                'data': incident_data
            })
        }
        
    except s3.exceptions.NoSuchKey:
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({
                'status': 'no_incidents',
                'message': 'No incidents found'
            })
        }

def store_incident_data(event, headers):
    """Store incident data from Step Functions"""
    
    # Parse Step Functions output
    body = event.get('body', '{}')
    if isinstance(body, str):
        step_functions_data = json.loads(body)
    else:
        step_functions_data = body
    
    # Format for dashboard
    dashboard_data = format_for_dashboard(step_functions_data)
    
    # Store in S3
    incident_id = dashboard_data['incident_id']
    
    # Store specific incident
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f'incidents/{incident_id}.json',
        Body=json.dumps(dashboard_data),
        ContentType='application/json'
    )
    
    # Store as latest
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='latest-incident.json',
        Body=json.dumps(dashboard_data),
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'status': 'stored',
            'incident_id': incident_id
        })
    }

def format_for_dashboard(step_output):
    """Format Step Functions output for dashboard"""
    
    source_output = step_output.get('source_adapter_output', {})
    analyzer_output = step_output.get('error_analyzer_output', {})
    summarizer_output = step_output.get('error_summarizer_output', {})
    
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return {
        'incident_id': incident_id,
        'timestamp': datetime.now().isoformat(),
        'status': determine_severity(analyzer_output),
        'summary': {
            'total_errors': analyzer_output.get('basic_stats', {}).get('total_errors', 0),
            'deploy_sha': analyzer_output.get('basic_stats', {}).get('deploy_sha'),
            'deploy_message': analyzer_output.get('basic_stats', {}).get('deploy_message'),
            'affected_files': analyzer_output.get('basic_stats', {}).get('affected_files', 0)
        },
        'timeline': {
            'error_series': source_output.get('series', []),
            'deploy_correlation': summarizer_output.get('timeline_analysis', {})
        },
        'analysis': {
            'executive_summary': summarizer_output.get('detailed_analysis', ''),
            'recommendations': summarizer_output.get('recommendations', [])
        },
        'charts': {
            'error_timeline': source_output.get('series', []),
            'file_impact': source_output.get('file_hits', {}),
            'top_errors': analyzer_output.get('dashboard_ready', {}).get('top_errors', [])[:5]
        }
    }

def determine_severity(analyzer_output):
    """Determine incident severity"""
    total_errors = analyzer_output.get('basic_stats', {}).get('total_errors', 0)
    
    if total_errors >= 10:
        return 'critical'
    elif total_errors >= 5:
        return 'high'
    elif total_errors >= 1:
        return 'medium'
    else:
        return 'low'
