import json
import boto3
from datetime import datetime

sns = boto3.client('sns')
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:478047815638:DevAngelAlerts'

def lambda_handler(event, context):
    analyzer_output = event.get('error_analyzer_output', {})
    summarizer_output = event.get('error_summarizer_output', {})
    
    error_summary = analyzer_output.get('error_summary', {})
    total_errors = error_summary.get('total_errors', 0)
    critical_count = error_summary.get('critical_count', 0)
    human_summary = summarizer_output.get('human_summary', 'No summary available')
    
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    if total_errors > 0:
        subject = f"🚨 DevAngel CRITICAL Alert: {total_errors} Errors ({critical_count} Critical)"
        message = f"""
DevAngel AI-Powered Error Analysis

INCIDENT ID: {incident_id}
TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

AI EXECUTIVE SUMMARY:
{human_summary}

TECHNICAL DETAILS:
- Total Errors: {total_errors}
- Critical Errors: {critical_count}
- Most Affected Service: {error_summary.get('most_common_source', 'Unknown')}
- Primary Error Type: {error_summary.get('most_common_error_type', 'Unknown')}

CRITICAL ISSUES:
"""
        critical_errors = analyzer_output.get('critical_errors', [])
        for i, error in enumerate(critical_errors[:3], 1):
            message += f"{i}. {error.get('source', 'Unknown')}: {error.get('message', 'No details')[:100]}...\n"
        
        message += f"\nReport Location: {summarizer_output.get('report_location', 'N/A')}"
        message += f"\nGitHub Issue: Will be created automatically for critical errors"
        
    else:
        subject = "✅ DevAngel: System Monitoring Complete"
        message = f"DevAngel monitoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. No critical errors detected."
    
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
        email_status = "sent"
    except Exception as e:
        email_status = "failed"
    
    # Pass through all data for next step
    result = event.copy()
    result['email_notification'] = {
        'incident_id': incident_id,
        'email_sent': {'status': email_status},
        'total_errors': total_errors
    }
    
    return result
