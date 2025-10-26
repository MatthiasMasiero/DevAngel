#!/bin/bash


# QuietOps Smoke Test - Generate Error Traffic

# This script helps you test the CloudWatch monitoring by generating fake errors
# It will create enough error logs to trigger your alarm

set -e

# Configuration
LOG_GROUP="${LOG_GROUP:-/aws/lambda/checkout-api}"
ERROR_COUNT="${ERROR_COUNT:-2}"   # Generate just 2 errors (above default threshold of 1)
DELAY="${DELAY:-1}"               # 1 second between errors

echo "QuietOps Smoke Test - Generating Error Traffic"
echo "Target Log Group: $LOG_GROUP"
echo "Generating $ERROR_COUNT errors with ${DELAY}s delay"
echo "This will take approximately $((ERROR_COUNT * DELAY)) seconds"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Please install it first."
    exit 1
fi

# Check if log group exists
if ! aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$LOG_GROUP"; then
    echo "⚠️  Log group $LOG_GROUP not found."
    echo "   Creating it for testing purposes..."
    aws logs create-log-group --log-group-name "$LOG_GROUP"
    echo "✅ Log group created"
fi

# Generate error messages
echo "🚀 Starting error generation..."
for i in $(seq 1 $ERROR_COUNT); do
    # Create different types of error messages to test pattern matching
    case $((i % 4)) in
        0)
            MESSAGE="ERROR: Payment processing failed for transaction $i - Invalid card number"
            ;;
        1)
            MESSAGE="Exception in payment service: java.lang.NullPointerException at PaymentService.java:42"
            ;;
        2)
            MESSAGE="Traceback (most recent call last): File \"/app/payment.py\", line 88, in process_payment"
            ;;
        3)
            MESSAGE="ERROR: Database connection timeout in checkout-api function"
            ;;
    esac
    
    # Send log message to CloudWatch
    aws logs put-log-events \
        --log-group-name "$LOG_GROUP" \
        --log-stream-name "smoke-test-$(date +%Y%m%d)" \
        --log-events timestamp=$(date +%s000),message="$MESSAGE" \
        > /dev/null
    
    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo "📈 Generated $i/$ERROR_COUNT errors..."
    fi
    
    # Small delay to spread errors over time
    sleep $DELAY
done

echo ""
echo "Smoke test complete!"
echo "Generated $ERROR_COUNT error messages in $LOG_GROUP"
echo "Wait 1-2 minutes for CloudWatch to process the logs"
echo "Your QuietOps-ErrorSpike alarm should trigger soon"
echo ""
echo "To check alarm status:"
echo "aws cloudwatch describe-alarms --alarm-names QuietOps-ErrorSpike"
echo ""
echo "To view recent log events:"
echo "   aws logs filter-log-events --log-group-name '$LOG_GROUP' --start-time \$(date -d '5 minutes ago' +%s000)"
