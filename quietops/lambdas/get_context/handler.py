"""
Get Context Lambda - Processes CloudWatch Alarm events and extracts incident context.
"""
import json
import os
from datetime import datetime, timedelta
from common.time import iso_to_epoch, epoch_to_iso


def lambda_handler(event, context):
    """
    Process CloudWatch Alarm State Change event and extract incident context.
    
    Args:
        event: EventBridge CloudWatch Alarm State Change event
        context: Lambda context
        
    Returns:
        dict: Incident context with window, service, repo info
    """
    try:
        # Extract alarm details from EventBridge event
        detail = event.get('detail', {})
        alarm_name = detail.get('alarmName', 'Unknown')
        state = detail.get('state', {}).get('value', 'UNKNOWN')
        alarm_time_str = event.get('time', datetime.utcnow().isoformat() + 'Z')
        
        # Parse alarm time and compute window
        alarm_time = datetime.fromisoformat(alarm_time_str.replace('Z', '+00:00'))
        start_time = alarm_time - timedelta(minutes=10)
        end_time = alarm_time + timedelta(minutes=2)
        
        # Convert to required formats
        start_iso = start_time.isoformat().replace('+00:00', 'Z')
        end_iso = end_time.isoformat().replace('+00:00', 'Z')
        start_epoch = int(start_time.timestamp())
        end_epoch = int(end_time.timestamp())
        
        # Get service and log group mapping
        alarm_to_loggroup = json.loads(os.environ.get('ALARM_TO_LOGGROUP', '{}'))
        log_group = alarm_to_loggroup.get(alarm_name, os.environ.get('LOG_GROUP', '/aws/lambda/checkout-api'))
        
        # Simple service inference from log group
        service = 'payment'  # Default service
        if 'checkout' in log_group:
            service = 'payment'
        elif 'user' in log_group:
            service = 'user'
        elif 'order' in log_group:
            service = 'order'
        
        # Get repo info from environment (stubbed for now)
        repo_owner = os.environ.get('REPO_OWNER')
        repo_name = os.environ.get('REPO_NAME')
        commit_sha = os.environ.get('COMMIT_SHA')
        parent_sha = os.environ.get('PARENT_SHA')
        
        repo_info = None
        if repo_owner and repo_name:
            repo_info = {
                "owner": repo_owner,
                "name": repo_name,
                "url": f"https://github.com/{repo_owner}/{repo_name}",
                "inference": "env"
            }
        
        # Build response
        response = {
            "window": {
                "start": start_iso,
                "end": end_iso,
                "start_epoch": start_epoch,
                "end_epoch": end_epoch
            },
            "service": service,
            "logGroup": log_group,
            "repo": repo_info,
            "commit_sha": commit_sha,
            "parent_sha": parent_sha,
            "files_changed": [],  # Empty for now, filled by teammate
            "alarm": {
                "name": alarm_name,
                "state": state,
                "raw_event": {
                    "time": alarm_time_str,
                    "source": event.get('source'),
                    "detail-type": event.get('detail-type'),
                    "detail": {
                        "alarmName": alarm_name,
                        "state": detail.get('state'),
                        "reason": detail.get('reason')
                    }
                }
            }
        }
        
        print(f"Generated context for alarm {alarm_name}, window: {start_iso} to {end_iso}")
        return response
        
    except Exception as e:
        print(f"Error processing alarm event: {str(e)}")
        raise
