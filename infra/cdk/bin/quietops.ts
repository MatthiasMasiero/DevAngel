#!/usr/bin/env node

// This is the main entry point for our CDK app
// It creates and configures our CloudWatch monitoring stack

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { QuietOpsCloudWatchStack } from '../lib/cloudwatch-stack';

// Create the CDK app - this is the container for all our AWS resources
const app = new cdk.App();

// Create our CloudWatch monitoring stack
// This stack will contain ONLY the CloudWatch components:
// 1. Metric filter (watches log files for ERROR patterns)
// 2. CloudWatch alarm (triggers when too many errors occur)
// 3. EventBridge rule (sends alarm events to Step Functions)
new QuietOpsCloudWatchStack(app, 'QuietOpsCloudWatchStack', {
  env: {
    // Use your default AWS account and region (us-west-2 by default)
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-west-2',
  },
});
