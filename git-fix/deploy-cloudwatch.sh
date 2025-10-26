#!/bin/bash

# Deploy CloudWatch monitoring setup
echo "Setting up CloudWatch monitoring..."

# Create IAM role for EC2 CloudWatch access
aws iam create-role \
  --role-name CloudWatchAgentServerRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach CloudWatch policy
aws iam attach-role-policy \
  --role-name CloudWatchAgentServerRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name CloudWatchAgentServerRole

aws iam add-role-to-instance-profile \
  --instance-profile-name CloudWatchAgentServerRole \
  --role-name CloudWatchAgentServerRole

# Create metric filter for ERROR logs
aws logs put-metric-filter \
  --log-group-name "/quietops/website" \
  --filter-name "ErrorFilter" \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=QuietOps/Website,metricValue=1

echo "CloudWatch setup complete!"
echo "Attach the CloudWatchAgentServerRole to your EC2 instance"
