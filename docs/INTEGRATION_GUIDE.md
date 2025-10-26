# QuietOps Integration Guide

## For Teammates: How to Connect to CloudWatch Layer

### 🎯 What You Get From CloudWatch Layer

**Input**: EventBridge event when errors spike
**Access**: Query CloudWatch Logs for actual error details
**Trigger**: Automatic when ≥1 error/minute detected

---

## 📥 Step Functions Integration

### EventBridge Event Format
```json
{
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "time": "2025-10-25T22:00:00Z",
  "detail": {
    "alarmName": "QuietOps-ErrorSpike",
    "state": { "value": "ALARM" },
    "previousState": { "value": "OK" }
  }
}
```

### Step Functions State Machine Input
```json
{
  "alarmName": "QuietOps-ErrorSpike",
  "alarmTime": "2025-10-25T22:00:00Z",
  "logGroup": "/aws/lambda/checkout-api"
}
```

---

## 📊 Lambda Functions: Query Logs

### Get Error Logs Around Incident
```python
import boto3
from datetime import datetime, timedelta

def get_incident_logs(alarm_time_str, log_group):
    logs_client = boto3.client('logs')
    
    # Parse alarm time and create window
    alarm_time = datetime.fromisoformat(alarm_time_str.replace('Z', '+00:00'))
    start_time = alarm_time - timedelta(minutes=10)
    end_time = alarm_time + timedelta(minutes=2)
    
    # Query for errors
    query = """
    fields @timestamp, @message
    | filter @message like /ERROR|Exception|Traceback/
    | sort @timestamp desc
    | limit 100
    """
    
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int(start_time.timestamp()),
        endTime=int(end_time.timestamp()),
        queryString=query
    )
    
    # Poll for results
    query_id = response['queryId']
    while True:
        result = logs_client.get_query_results(queryId=query_id)
        if result['status'] == 'Complete':
            return result['results']
        time.sleep(1)
```

---

## 🔧 Configuration Values

| Item | Value | Usage |
|------|-------|-------|
| Alarm Name | `QuietOps-ErrorSpike` | Filter EventBridge events |
| Log Group | `/aws/lambda/checkout-api` | Query logs |
| Threshold | 1 error/minute | Incident sensitivity |
| Region | `us-east-1` | AWS API calls |

---

## 🧪 Testing Integration

### Test 1: Trigger Alarm
```bash
./scripts/test_integration.sh
```

### Test 2: Manual Error
```bash
aws logs put-log-events \
  --log-group-name /aws/lambda/checkout-api \
  --log-stream-name test \
  --log-events timestamp=$(date +%s000),message="ERROR: Test incident"
```

### Test 3: Verify EventBridge
```bash
# Check if rule exists and has targets
aws events list-targets-by-rule --rule QuietOpsCloudWatchStack-AlarmStateChangeRule*
```

---

## 🚀 Deployment Dependencies

### Required Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name QuietOpsCloudWatchStack \
  --query 'Stacks[0].Outputs'
```

### Environment Variables for Your Lambdas
```bash
ALARM_NAME=QuietOps-ErrorSpike
LOG_GROUP=/aws/lambda/checkout-api
AWS_REGION=us-east-1
```

---

## 🔍 Troubleshooting

### Alarm Not Triggering
1. Check log group exists: `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/checkout-api`
2. Verify error patterns: Must contain "ERROR", "Exception", or "Traceback"
3. Check threshold: Currently set to 1 error/minute

### No EventBridge Events
1. Verify Step Functions ARN is set: `export INCIDENT_SM_ARN=your-arn`
2. Redeploy: `cdk deploy`
3. Check rule targets: `aws events list-targets-by-rule --rule [rule-name]`

### Empty Log Queries
1. Time window too narrow
2. Log group name mismatch
3. No errors in specified time range

---

## ✅ Integration Checklist

- [ ] CloudWatch stack deployed (`QuietOpsCloudWatchStack`)
- [ ] Step Functions ARN configured (`INCIDENT_SM_ARN`)
- [ ] EventBridge rule has Step Functions target
- [ ] Lambda functions have CloudWatch Logs permissions
- [ ] Test alarm triggers correctly
- [ ] Test log queries return data

**Ready for handoff!** 🎉
