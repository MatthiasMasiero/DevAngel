# QuietOps CloudWatch Infrastructure

This CDK project creates **only the CloudWatch monitoring components** for QuietOps:

## What This Creates

1. **Metric Filter** - Watches your Lambda logs for ERROR/Exception/Traceback patterns
2. **CloudWatch Alarm** - Triggers when error count exceeds threshold (default: 50/minute)  
3. **EventBridge Rule** - Forwards alarm events to your Step Functions workflow

## Prerequisites

- AWS CLI configured with your credentials
- Node.js 18+ installed
- CDK CLI: `npm install -g aws-cdk`

## Quick Setup

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy with defaults (monitors /aws/lambda/checkout-api, threshold=50)
cdk deploy

# Deploy with custom settings
cdk deploy -c logGroup=/aws/lambda/my-service -c errorsThreshold=25
```

## Configuration Options

You can customize these settings:

- `logGroup`: Which log group to monitor (default: `/aws/lambda/checkout-api`)
- `errorsThreshold`: How many errors/minute trigger alarm (default: 50)
- `incidentSmArn`: Step Functions ARN for incident handling (set via env var `INCIDENT_SM_ARN`)

## Example with Custom Settings

```bash
# Monitor a different service with lower threshold
cdk deploy -c logGroup=/aws/lambda/user-service -c errorsThreshold=10

# Set Step Functions ARN via environment variable
export INCIDENT_SM_ARN=arn:aws:states:us-west-2:123456789012:stateMachine:IncidentSM
cdk deploy
```

## What Happens When Deployed

1. **Normal Operation**: Metric filter quietly counts errors, alarm stays in OK state
2. **Error Spike**: When errors exceed threshold, alarm goes to ALARM state
3. **Event Forwarding**: EventBridge rule catches alarm state change and sends event to Step Functions
4. **Your Teammates' Code**: Step Functions workflow processes the incident (not part of this stack)

## Useful Commands

```bash
# See what will be created
cdk synth

# Compare with deployed version
cdk diff

# Remove everything
cdk destroy
```
