import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
BUCKET_NAME = 'devangel-incident-data-1761448500'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:478047815638:DevAngelAlerts'

def lambda_handler(event, context):
    source_output = event.get('source_adapter_output', {})
    analyzer_output = event.get('error_analyzer_output', {})
    
    # Get error count from the correct location
    error_summary = analyzer_output.get('error_summary', {})
    total_errors = error_summary.get('total_errors', 0)
    critical_count = error_summary.get('critical_count', 0)
    
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Create email message
    if total_errors > 0:
        subject = f"🚨 DevAngel Alert: {total_errors} Errors Detected ({critical_count} Critical)"
        message = f"""
DevAngel Error Analysis Report

INCIDENT ID: {incident_id}
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

ERROR SUMMARY:
- Total Errors: {total_errors}
- Critical Errors: {critical_count}
- Most Common Source: {error_summary.get('most_common_source', 'Unknown')}
- Most Common Error Type: {error_summary.get('most_common_error_type', 'Unknown')}

CRITICAL ERRORS:
"""
        critical_errors = analyzer_output.get('critical_errors', [])
        for i, error in enumerate(critical_errors[:3], 1):
            message += f"{i}. {error.get('source', 'Unknown')}: {error.get('errorType', 'Unknown')} - {error.get('message', 'No message')[:100]}...\n"
        
        if analyzer_output.get('needs_immediate_attention'):
            message += "\n⚠️  IMMEDIATE ACTION REQUIRED ⚠️"
        
        message += f"\n\nView full analysis: s3://{BUCKET_NAME}/error-analysis/"
    else:
        subject = "✅ DevAngel: No Critical Errors Detected"
        message = f"DevAngel monitoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. No errors detected."
    
    # Send SNS notification
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        email_status = "sent"
    except Exception as e:
        print(f"SNS error: {e}")
        email_status = "failed"
    
    return {
        'incident_id': incident_id,
        'update_type': 'enhanced',
        'stored': True,
        'email_sent': {'status': email_status, 'message_id': 'enhanced-notification'},
        'total_errors': total_errors
    }
