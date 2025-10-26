#!/bin/bash

# =============================================================================
# Comprehensive Alarm Test - Validates QuietOps alarm behavior
# =============================================================================
# This script tests:
# 1. Normal logs don't trigger alarm
# 2. Error logs DO trigger alarm
# 3. Alarm state changes are detected

set -e

# Configuration
LOG_GROUP="${LOG_GROUP:-/aws/lambda/checkout-api}"
ALARM_NAME="QuietOps-ErrorSpike"
TEST_STREAM="comprehensive-test-$(date +%Y%m%d-%H%M%S)"

echo "🧪 QuietOps Comprehensive Alarm Test"
echo "📊 Log Group: $LOG_GROUP"
echo "🚨 Alarm: $ALARM_NAME"
echo "📝 Test Stream: $TEST_STREAM"
echo ""

# Helper function to get alarm state
get_alarm_state() {
    aws cloudwatch describe-alarms \
        --alarm-names "$ALARM_NAME" \
        --query 'MetricAlarms[0].StateValue' \
        --output text 2>/dev/null || echo "NOT_FOUND"
}

# Helper function to send log message
send_log() {
    local message="$1"
    aws logs put-log-events \
        --log-group-name "$LOG_GROUP" \
        --log-stream-name "$TEST_STREAM" \
        --log-events timestamp=$(date +%s000),message="$message" \
        > /dev/null
}

# Helper function to wait and check alarm state
wait_and_check_alarm() {
    local expected_state="$1"
    local description="$2"
    local max_wait=180  # 3 minutes max wait
    local wait_time=0
    
    echo "⏳ Waiting for alarm to be $expected_state ($description)..."
    
    while [ $wait_time -lt $max_wait ]; do
        current_state=$(get_alarm_state)
        echo "   Current state: $current_state (waited ${wait_time}s)"
        
        if [ "$current_state" = "$expected_state" ]; then
            echo "✅ SUCCESS: Alarm is $expected_state"
            return 0
        fi
        
        sleep 15
        wait_time=$((wait_time + 15))
    done
    
    echo "❌ TIMEOUT: Alarm did not reach $expected_state after ${max_wait}s"
    return 1
}

# =============================================================================
# TEST SETUP
# =============================================================================

echo "🔧 Setting up test environment..."

# Check if alarm exists
if [ "$(get_alarm_state)" = "NOT_FOUND" ]; then
    echo "❌ Alarm $ALARM_NAME not found. Please deploy the CDK stack first:"
    echo "   cd infra/cdk && cdk deploy"
    exit 1
fi

# Ensure log group exists
if ! aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$LOG_GROUP"; then
    echo "📝 Creating log group $LOG_GROUP..."
    aws logs create-log-group --log-group-name "$LOG_GROUP"
fi

# Create log stream
echo "📝 Creating test log stream..."
aws logs create-log-stream --log-group-name "$LOG_GROUP" --log-stream-name "$TEST_STREAM" 2>/dev/null || true

echo "✅ Setup complete"
echo ""

# =============================================================================
# TEST 1: Normal logs should NOT trigger alarm
# =============================================================================

echo "🧪 TEST 1: Sending normal (non-error) logs..."
echo "Expected: Alarm should stay OK"

# Send various normal log messages
send_log "INFO: Application started successfully"
send_log "DEBUG: Processing user request"
send_log "WARN: High memory usage detected"
send_log "INFO: Database connection established"
send_log "DEBUG: Cache hit for user 12345"

echo "📤 Sent 5 normal log messages"

# Wait and verify alarm stays OK
if wait_and_check_alarm "OK" "normal logs should not trigger"; then
    echo "✅ TEST 1 PASSED: Normal logs did not trigger alarm"
else
    echo "❌ TEST 1 FAILED: Normal logs incorrectly triggered alarm"
    exit 1
fi

echo ""

# =============================================================================
# TEST 2: Error logs SHOULD trigger alarm
# =============================================================================

echo "🧪 TEST 2: Sending error logs..."
echo "Expected: Alarm should go to ALARM state"

# Send error log that should trigger alarm
send_log "ERROR: Payment processing failed for transaction 12345"

echo "📤 Sent 1 ERROR log message"

# Wait and verify alarm goes to ALARM
if wait_and_check_alarm "ALARM" "error log should trigger alarm"; then
    echo "✅ TEST 2 PASSED: Error log correctly triggered alarm"
else
    echo "❌ TEST 2 FAILED: Error log did not trigger alarm"
    exit 1
fi

echo ""

# =============================================================================
# TEST 3: Verify alarm details
# =============================================================================

echo "🧪 TEST 3: Checking alarm details..."

alarm_details=$(aws cloudwatch describe-alarms --alarm-names "$ALARM_NAME" --output json)
current_state=$(echo "$alarm_details" | jq -r '.MetricAlarms[0].StateValue')
state_reason=$(echo "$alarm_details" | jq -r '.MetricAlarms[0].StateReason')
threshold=$(echo "$alarm_details" | jq -r '.MetricAlarms[0].Threshold')

echo "📊 Alarm Details:"
echo "   State: $current_state"
echo "   Threshold: $threshold"
echo "   Reason: $state_reason"

if [ "$current_state" = "ALARM" ] && [ "$threshold" = "1" ]; then
    echo "✅ TEST 3 PASSED: Alarm configuration is correct"
else
    echo "❌ TEST 3 FAILED: Alarm configuration issue"
    exit 1
fi

echo ""

# =============================================================================
# TEST 4: Check metric data
# =============================================================================

echo "🧪 TEST 4: Checking metric data..."

# Get recent metric data
metric_data=$(aws cloudwatch get-metric-statistics \
    --namespace QuietOps \
    --metric-name ErrorsPerMinute \
    --start-time $(date -d '10 minutes ago' --iso-8601) \
    --end-time $(date --iso-8601) \
    --period 60 \
    --statistics Sum \
    --output json)

datapoints=$(echo "$metric_data" | jq '.Datapoints | length')
max_value=$(echo "$metric_data" | jq '.Datapoints | map(.Sum) | max // 0')

echo "📈 Metric Data:"
echo "   Datapoints found: $datapoints"
echo "   Max errors/minute: $max_value"

if [ "$datapoints" -gt 0 ] && [ "$(echo "$max_value >= 1" | bc)" = "1" ]; then
    echo "✅ TEST 4 PASSED: Metric data shows errors were recorded"
else
    echo "❌ TEST 4 FAILED: No metric data found or values too low"
    exit 1
fi

echo ""

# =============================================================================
# CLEANUP
# =============================================================================

echo "🧹 Cleaning up test stream..."
aws logs delete-log-stream --log-group-name "$LOG_GROUP" --log-stream-name "$TEST_STREAM" 2>/dev/null || true

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "🎉 ALL TESTS PASSED!"
echo ""
echo "✅ Verified behaviors:"
echo "   • Normal logs (INFO, DEBUG, WARN) do NOT trigger alarm"
echo "   • Error logs (ERROR) DO trigger alarm"
echo "   • Alarm threshold is set to 1 error/minute"
echo "   • Metric data is being recorded correctly"
echo ""
echo "🚀 Your QuietOps alarm system is working correctly!"
echo ""
echo "💡 Next steps:"
echo "   • The alarm is currently in ALARM state"
echo "   • It will return to OK state after ~10 minutes of no errors"
echo "   • EventBridge should have sent the alarm event to Step Functions"
