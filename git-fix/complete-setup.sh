#!/bin/bash

echo "🚀 Setting up complete incident response system..."

# Create CloudWatch Log Group
aws logs create-log-group --log-group-name /quietops/website

# Create metric filter for ERROR logs
aws logs put-metric-filter \
  --log-group-name "/quietops/website" \
  --filter-name "ErrorLogFilter" \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=QuietOps/Website,metricValue=1

# Create CloudWatch Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "ErrorSpikeAlarm" \
  --alarm-description "Triggers when ERROR logs spike" \
  --metric-name ErrorCount \
  --namespace QuietOps/Website \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 3 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions "arn:aws:sns:us-east-1:478047815638:error-notifications"

# Create SNS Topic
aws sns create-topic --name error-notifications

echo "✅ Setup complete! Your teammate can now:"
echo "1. Attach IAM role to EC2"
echo "2. Configure CloudWatch agent"
echo "3. Test with error logs"
