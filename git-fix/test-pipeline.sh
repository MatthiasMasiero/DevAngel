#!/bin/bash

echo "🔍 Testing AWS Connection..."
aws sts get-caller-identity

echo "🔍 Checking Existing Resources..."
echo "API Gateways:"
aws apigateway get-rest-apis --query 'items[].name' --output table

echo "Lambda Functions:"
aws lambda list-functions --query 'Functions[].FunctionName' --output table

echo "CloudWatch Log Groups:"
aws logs describe-log-groups --query 'logGroups[].logGroupName' --output table

echo "✅ Test complete. Ready for next steps."
