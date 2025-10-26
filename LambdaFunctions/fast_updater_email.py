import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
BUCKET_NAME = 'devangel-incident-data-1761448500'

# SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:478047815638:DevAngelAlerts'

def lambda_handler(event, context):
    """
    Fast updater with email notifications
    """
    
    source_output = event.get('source_adapter_output', {})
    analyzer_output = event.get('error_analyzer_output', {})
    
    # Create fast dashboard data
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    severity = determine_severity(analyzer_output)
    total_errors = analyzer_output.get('basic_stats', {}).get('total_errors', 0)
    deploy_sha = analyzer_output.get('basic_stats', {}).get('deploy_sha', 'unknown')
    
    fast_data = {
        'incident_id': incident_id,
        'timestamp': datetime.now().isoformat(),
        'status': severity,
        'update_type': 'initial',
        'summary': {
            'total_errors': total_errors,
            'deploy_sha': deploy_sha,
            'deploy_message': analyzer_output.get('basic_stats', {}).get('deploy_message'),
            'affected_files': analyzer_output.get('basic_stats', {}).get('affected_files', 0)
        },
        'charts': {
            'error_timeline': source_output.get('series', []),
            'file_impact': source_output.get('file_hits', {}),
            'top_errors': analyzer_output.get('dashboard_ready', {}).get('top_errors', [])[:5]
        },
        'analysis': {
            'status': 'Processing AI analysis...',
            'executive_summary': 'Incident detected. AI analysis in progress...',
            'recommendations': [{
                'priority': 'HIGH',
                'action': 'Monitor system while analysis completes',
                'reason': 'Initial incident response'
            }]
        }
    }
    
    # Store in S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f'incidents/{incident_id}-initial.json',
        Body=json.dumps(fast_data),
        ContentType='application/json',
        Metadata={'update-type': 'initial', 'incident-id': incident_id}
    )
    
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='latest-incident.json',
        Body=json.dumps(fast_data),
        ContentType='application/json'
    )
    
    # Send email notification
    email_result = send_email_notification(incident_id, severity, total_errors, deploy_sha, source_output)
    
    return {
        'incident_id': incident_id,
        'update_type': 'initial',
        'stored': True,
        'email_sent': email_result
    }

def send_email_notification(incident_id, severity, total_errors, deploy_sha, source_output):
    """Send email notification about the incident"""
    
    # Create error timeline summary
    timeline = source_output.get('series', [])
    timeline_text = '\n'.join([f"  {point[0]}: {point[1]} errors" for point in timeline])
    
    # Create email subject
    subject = f"DevAngel Alert - {severity.upper()} - {total_errors} Errors Detected"
    
    # Create email message
    message = f"""DevAngel Incident Alert

SEVERITY: {severity.upper()}
INCIDENT ID: {incident_id}
TOTAL ERRORS: {total_errors}
DEPLOY SHA: {deploy_sha}
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ERROR TIMELINE:
{timeline_text}

STATUS: AI analysis in progress...

Next steps:
1. Check your dashboard for real-time updates
2. Full AI analysis will be available in ~30 seconds
3. You'll receive another email when analysis is complete

Dashboard URL: https://your-amplify-dashboard-url.com

This is an automated alert from DevAngel incident detection system.
"""
    
    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        
        return {
            'status': 'sent',
            'message_id': response['MessageId']
        }
        
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
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
