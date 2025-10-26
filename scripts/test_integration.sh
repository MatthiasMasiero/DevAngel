#!/bin/bash

# =============================================================================
# Integration Test - Verify handoff points for teammates
# =============================================================================

set -e

LOG_GROUP="/aws/lambda/checkout-api"
ALARM_NAME="QuietOps-ErrorSpike"

echo "🔗 QuietOps Integration Test"
echo "Testing handoff points for teammates..."
echo ""

# =============================================================================
# TEST 1: Generate error and capture alarm event format
# =============================================================================

echo "📤 Sending error to trigger alarm..."
aws logs put-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "integration-test-$(date +%s)" \
    --log-events timestamp=$(date +%s000),message="ERROR: Integration test - payment service crashed"

echo "⏳ Waiting 90 seconds for alarm to trigger..."
sleep 90

# Get alarm details
alarm_info=$(aws cloudwatch describe-alarms --alarm-names "$ALARM_NAME" --output json)
alarm_state=$(echo "$alarm_info" | jq -r '.MetricAlarms[0].StateValue')
state_reason=$(echo "$alarm_info" | jq -r '.MetricAlarms[0].StateReason')

echo ""
echo "🚨 ALARM STATUS:"
echo "   State: $alarm_state"
echo "   Reason: $state_reason"
echo ""

# =============================================================================
# TEST 2: Show EventBridge event format teammates will receive
# =============================================================================

echo "📋 EVENTBRIDGE EVENT FORMAT (what your teammates receive):"
cat << 'EOF'
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "account": "478047815638",
  "time": "2025-10-25T22:00:00Z",
  "region": "us-east-1",
  "detail": {
    "alarmName": "QuietOps-ErrorSpike",
    "state": {
      "value": "ALARM",
      "reason": "Threshold Crossed: 1 datapoint [1.0] was greater than or equal to the threshold (1.0)."
    },
    "previousState": {
      "value": "OK"
    }
  }
}
EOF

echo ""

# =============================================================================
# TEST 3: Show log query format for Lambda functions
# =============================================================================

echo "📊 LOG QUERY FORMAT (for teammate's Lambda functions):"
echo ""
echo "To query logs around incident time:"
cat << 'EOF'
aws logs start-query \
  --log-group-name "/aws/lambda/checkout-api" \
  --start-time ALARM_EPOCH_TIME_MINUS_10_MIN \
  --end-time ALARM_EPOCH_TIME_PLUS_2_MIN \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR|Exception|Traceback/ | sort @timestamp desc | limit 100'
EOF

echo ""

# =============================================================================
# TEST 4: Integration points summary
# =============================================================================

echo "✅ INTEGRATION POINTS FOR TEAMMATES:"
echo ""
echo "1. 📥 INPUT: EventBridge sends alarm event to Step Functions"
echo "   - Event format: CloudWatch Alarm State Change (shown above)"
echo "   - Trigger: When QuietOps-ErrorSpike goes to ALARM"
echo ""
echo "2. 📊 LOG ACCESS: Lambda functions can query CloudWatch Logs"
echo "   - Log Group: $LOG_GROUP"
echo "   - Query: Use CloudWatch Logs Insights API"
echo "   - Time Window: Extract from alarm event timestamp"
echo ""
echo "3. 🔧 CONFIGURATION:"
echo "   - Alarm Name: $ALARM_NAME"
echo "   - Threshold: 1 error/minute"
echo "   - Evaluation: 1 minute window"
echo ""
echo "4. 🎯 OUTPUTS AVAILABLE:"
aws cloudformation describe-stacks \
  --stack-name QuietOpsCloudWatchStack \
  --query 'Stacks[0].Outputs' \
  --output table

echo ""
echo "🚀 READY FOR INTEGRATION!"
echo "Your CloudWatch layer is working and ready for teammate handoff."
