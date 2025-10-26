# QuietOps CloudWatch Signals Runbook

## Overview

This system monitors your application logs for error spikes and automatically triggers incident response. Here's how it works:

```
Log Errors → Metric Filter → CloudWatch Alarm → EventBridge → Step Functions
```

## Components

### 1. Metric Filter
- **What it does**: Scans log messages for error patterns
- **Patterns it looks for**: `ERROR`, `Exception`, `Traceback`
- **Output**: Creates a metric `QuietOps/ErrorsPerMinute`

### 2. CloudWatch Alarm
- **Name**: `QuietOps-ErrorSpike`
- **Triggers when**: Error count ≥ threshold in 1 minute
- **Default threshold**: 50 errors/minute
- **States**: OK (normal) → ALARM (problem detected)

### 3. EventBridge Rule
- **Listens for**: CloudWatch Alarm State Changes
- **Filters**: Only `QuietOps-ErrorSpike` going to `ALARM` state
- **Action**: Forwards event to Step Functions

## Deployment

### Prerequisites
```bash
# Install CDK CLI
npm install -g aws-cdk

# Navigate to infrastructure directory
cd infra/cdk

# Install dependencies
npm install
```

### Deploy with Defaults
```bash
# Bootstrap (first time only)
cdk bootstrap

# Deploy
cdk deploy
```

### Deploy with Custom Settings
```bash
# Monitor different log group with custom threshold
cdk deploy \
  -c logGroup=/aws/lambda/user-service \
  -c errorsThreshold=25

# Set Step Functions ARN
export INCIDENT_SM_ARN=arn:aws:states:us-west-2:123456789012:stateMachine:IncidentSM
cdk deploy
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INCIDENT_SM_ARN` | Step Functions ARN for incident handling | None (required) |

## Testing

### Run Smoke Test
```bash
# Generate 60 errors to trigger alarm
./scripts/smoke_generate_errors.sh

# Custom test
LOG_GROUP=/aws/lambda/my-service ERROR_COUNT=100 ./scripts/smoke_generate_errors.sh
```

### Check Alarm Status
```bash
aws cloudwatch describe-alarms --alarm-names QuietOps-ErrorSpike
```

### View Recent Logs
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/checkout-api \
  --start-time $(date -d '10 minutes ago' +%s000) \
  --filter-pattern "ERROR Exception Traceback"
```

## Example EventBridge Event

When the alarm triggers, EventBridge sends this event to Step Functions:

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "account": "123456789012",
  "time": "2025-10-25T15:30:00Z",
  "region": "us-west-2",
  "detail": {
    "alarmName": "QuietOps-ErrorSpike",
    "state": {
      "value": "ALARM",
      "reason": "Threshold Crossed: 1 out of the last 1 datapoints [75.0 (25/10/25 15:30:00)] was greater than the threshold (50.0)."
    },
    "previousState": {
      "value": "OK"
    }
  }
}
```

## Troubleshooting

### Alarm Not Firing

1. **Check log group exists**:
   ```bash
   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/checkout-api
   ```

2. **Verify error patterns in logs**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/checkout-api \
     --filter-pattern "ERROR Exception Traceback" \
     --start-time $(date -d '1 hour ago' +%s000)
   ```

3. **Check metric data**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace QuietOps \
     --metric-name ErrorsPerMinute \
     --start-time $(date -d '1 hour ago' --iso-8601) \
     --end-time $(date --iso-8601) \
     --period 300 \
     --statistics Sum
   ```

### Empty Results from Queries

1. **Log group name mismatch**: Verify the exact log group name
2. **Time window too narrow**: Errors might be outside the query window
3. **Pattern not matching**: Check if your error messages contain the expected keywords

### Regex Patterns Not Matching

The system looks for these patterns in log messages:
- **Python**: `File "path/file.py", line 123`
- **Java**: `(ClassName.java:123)`
- **JavaScript**: `(file.js:123:45)`

If your logs use different formats, the file extraction might miss them.

## Monitoring the Monitor

### Key Metrics to Watch
- `QuietOps/ErrorsPerMinute`: Your error rate
- Alarm state: Should be OK most of the time
- EventBridge rule invocations: Should match alarm state changes

### Alerts on the Alerts
Consider setting up notifications when:
- The alarm stays in ALARM state for too long
- The Step Functions workflow fails
- No error data for extended periods (might indicate logging issues)
