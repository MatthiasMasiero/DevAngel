#!/bin/bash

# CloudWatch Agent Installation Script
echo "Installing CloudWatch Agent..."

# Update system
sudo yum update -y

# Download and install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create config directory if it doesn't exist
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/

# Copy the config file
sudo cp cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Start CloudWatch Agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Enable auto-start
sudo systemctl enable amazon-cloudwatch-agent

echo "CloudWatch Agent setup complete!"
echo "Testing error log generation..."

# Test error generation
echo "ERROR: Test incident trigger $(date)" | sudo tee -a /var/log/nginx/error.log

echo "Check CloudWatch Logs in AWS Console: /quietops/website log group"
