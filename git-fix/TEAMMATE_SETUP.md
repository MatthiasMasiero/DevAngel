# Setup Instructions for Teammate

## Prerequisites
- EC2 instance running
- AWS CLI configured with admin permissions
- CloudWatch agent installed on EC2

## Step 1: Complete AWS Setup
```bash
# Run the complete setup script
chmod +x complete-setup.sh
./complete-setup.sh
```

## Step 2: Attach IAM Role to EC2
```bash
# Get your EC2 instance ID
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

# Attach the CloudWatch role
aws ec2 associate-iam-instance-profile \
  --instance-id $INSTANCE_ID \
  --iam-instance-profile Name=CloudWatchAgentServerRole
```

## Step 3: Configure CloudWatch Agent on EC2
```bash
# Copy the config file to EC2
sudo cp cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Start the agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

## Step 4: Install Amazon Q GitHub App
1. Go to: https://github.com/apps/amazon-q-developer
2. Install on MatthiasMasiero/DevAngel repository
3. Grant necessary permissions

## Step 5: Test the Complete Pipeline
```bash
# Generate test error on EC2
echo "ERROR: Test incident trigger $(date)" | sudo tee -a /var/log/nginx/error.log

# Check CloudWatch logs
aws logs filter-log-events --log-group-name /quietops/website --start-time $(date -d '5 minutes ago' +%s000)
```

## Expected Flow:
1. Error logged → CloudWatch detects → Alarm triggers
2. GitHub issue created automatically
3. Amazon Q responds to `/q plan` command
4. Team comments `/q implement` → Q creates PR with fixes

## Troubleshooting:
- Check CloudWatch agent status: `sudo systemctl status amazon-cloudwatch-agent`
- Verify IAM role attached: Check EC2 console
- Check GitHub App permissions: Repository settings
