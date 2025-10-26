#!/usr/bin/env python3
"""
DevAngel Pipeline Trigger
Triggers the AWS Step Functions pipeline with sample error data
"""

import boto3
import json
from datetime import datetime, timezone

def trigger_devangel_pipeline():
    """Trigger the DevAngel error processing pipeline"""
    
    # AWS Step Functions client
    stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')
    
    # Sample error data - you can modify this
    sample_errors = {
        "source": "test",
        "incident_input": {
            "logs": [
                {
                    "@timestamp": datetime.now(timezone.utc).isoformat(),
                    "@message": "[ERROR] Payment service connection failed - timeout after 5000ms",
                    "level": "ERROR"
                },
                {
                    "@timestamp": datetime.now(timezone.utc).isoformat(),
                    "@message": "Traceback (most recent call last):\n  File \"/app/payment_handler.py\", line 67, in process_payment\n    response = payment_client.charge(amount)\nConnectionError: HTTPSConnectionPool timeout",
                    "level": "ERROR"
                },
                {
                    "@timestamp": datetime.now(timezone.utc).isoformat(),
                    "@message": "[ERROR] Database query failed: connection pool exhausted",
                    "level": "ERROR"
                }
            ],
            "deploy": {
                "sha": f"test{datetime.now().strftime('%H%M%S')}",
                "message": "Fix payment processing logic",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "changed_files": ["payment_handler.py", "database_config.py", "connection_pool.py"]
            }
        }
    }
    
    # Step Functions state machine ARN
    state_machine_arn = "arn:aws:states:us-east-1:478047815638:stateMachine:DevAngelErrorPipeline"
    
    try:
        print("🚀 Triggering DevAngel pipeline...")
        print(f"📊 Processing {len(sample_errors['incident_input']['logs'])} error logs")
        
        # Start execution
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(sample_errors)
        )
        
        execution_arn = response['executionArn']
        print(f"✅ Pipeline started successfully!")
        print(f"📋 Execution ARN: {execution_arn}")
        
        # Wait a moment and check status
        import time
        time.sleep(3)
        
        status_response = stepfunctions.describe_execution(executionArn=execution_arn)
        status = status_response['status']
        
        print(f"📈 Status: {status}")
        
        if status == 'SUCCEEDED':
            output = json.loads(status_response.get('output', '{}'))
            if 'issue_url' in output:
                print(f"🎯 GitHub Issue Created: {output['issue_url']}")
                print(f"🔢 Issue Number: #{output['issue_number']}")
        elif status == 'FAILED':
            print(f"❌ Pipeline failed: {status_response.get('error', 'Unknown error')}")
        elif status == 'RUNNING':
            print("⏳ Pipeline still running... check AWS console for updates")
            
        return response
        
    except Exception as e:
        print(f"❌ Error triggering pipeline: {str(e)}")
        return None

if __name__ == "__main__":
    print("🛡️ DevAngel Pipeline Trigger")
    print("=" * 40)
    trigger_devangel_pipeline()
