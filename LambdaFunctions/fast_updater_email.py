import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
BUCKET_NAME = 'devangel-incident-data-1761448500'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:478047815638:DevAngelAlerts'

def lambda_handler(event, context):
    # Create incident ID with exact timestamp format from working version
    incident_id = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Get data from previous steps
    analyzer_output = event.get('error_analyzer_output', {})
    basic_stats = analyzer_output.get('basic_stats', {})
    
    # Extract info for email
    total_errors = basic_stats.get('total_errors', 0)
    log_group = event.get('detail', {}).get('logGroup', 'Unknown')
    
    # Create initial incident data for S3
    incident_data = {
        'incident_id': incident_id,
        'timestamp': datetime.now().isoformat(),
        'update_type': 'initial',
        'log_group': log_group,
        'total_errors': total_errors,
        'status': 'processing'
    }
    
    # Store in S3
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f'incidents/{incident_id}-initial.json',
            Body=json.dumps(incident_data),
            ContentType='application/json'
        )
        stored = True
    except:
        stored = False
    
    # Send email
    subject = f"DevAngel Alert - {total_errors} Errors in {log_group}"
    message = f"""DevAngel Quick Alert

LOG GROUP: {log_group}
TOTAL ERRORS: {total_errors}
INCIDENT ID: {incident_id}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Errors detected in your application logs.
"""
    
    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        
        email_sent = {
            'status': 'sent',
            'message_id': response['MessageId']
        }
    except Exception as e:
        email_sent = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Return exact format from working version
    return {
        'incident_id': incident_id,
        'update_type': 'initial',
        'stored': stored,
        'email_sent': email_sent
    }
