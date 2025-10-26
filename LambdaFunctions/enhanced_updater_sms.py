import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
BUCKET_NAME = 'devangel-incident-data-1761448500'

# Replace with your phone number (format: +1234567890)
YOUR_PHONE_NUMBER = '+1234567890'

def lambda_handler(event, context):
    """
    Enhanced updater with SMS completion notification
    """
    
    source_output = event.get('source_adapter_output', {})
    analyzer_output = event.get('error_analyzer_output', {})
    summarizer_output = event.get('error_summarizer_output', {})
    
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    enhanced_data = {
        'incident_id': incident_id,
        'timestamp': datetime.now().isoformat(),
        'status': determine_severity(analyzer_output),
        'update_type': 'enhanced',
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
        'charts': {
            'error_timeline': source_output.get('series', []),
            'file_impact': source_output.get('file_hits', {}),
            'top_errors': analyzer_output.get('dashboard_ready', {}).get('top_errors', [])[:5]
        },
        'analysis': {
            'status': 'Complete',
            'executive_summary': summarizer_output.get('detailed_analysis', ''),
            'recommendations': summarizer_output.get('recommendations', [])
        }
    }
    
    # Store enhanced data in S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f'incidents/{incident_id}-enhanced.json',
        Body=json.dumps(enhanced_data),
        ContentType='application/json',
        Metadata={'update-type': 'enhanced', 'incident-id': incident_id}
    )
    
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='latest-incident.json',
        Body=json.dumps(enhanced_data),
        ContentType='application/json'
    )
    
    # Send SMS completion notification
    sms_result = send_completion_sms(incident_id, summarizer_output)
    
    return {
        'incident_id': incident_id,
        'update_type': 'enhanced',
        'stored': True,
        'sms_sent': sms_result
    }

def send_completion_sms(incident_id, summarizer_output):
    """Send SMS when AI analysis is complete"""
    
    recommendations = summarizer_output.get('recommendations', [])
    timeline_analysis = summarizer_output.get('timeline_analysis', {})
    
    # Get top recommendation
    top_rec = recommendations[0] if recommendations else None
    
    # Create completion SMS (160 char limit)
    if top_rec and top_rec.get('priority') == 'CRITICAL':
        message = f"DevAngel Analysis Complete\n{incident_id}\nCRITICAL: {top_rec.get('action', 'Check dashboard')}\nView dashboard for full details."
    else:
        correlation = timeline_analysis.get('correlation', 'unknown').upper()
        message = f"DevAngel Analysis Complete\n{incident_id}\nCorrelation: {correlation}\nRecommendations available on dashboard."
    
    try:
        response = sns.publish(
            PhoneNumber=YOUR_PHONE_NUMBER,
            Message=message,
            Subject='DevAngel Analysis Complete'
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
