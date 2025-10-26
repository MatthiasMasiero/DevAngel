#!/bin/bash

# DevAngel AWS Deployment Script
set -e

echo "🚀 Deploying DevAngel Pipeline to AWS..."

# Variables
REGION="us-east-1"
BUCKET="devangel-incident-data-1761448500"
ROLE_ARN="arn:aws:iam::478047815638:role/lambda-execution-role"

# Create S3 bucket if it doesn't exist
echo "📦 Creating S3 bucket..."
aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || echo "Bucket already exists"

# Package and deploy Lambda functions
cd LambdaFunctions

echo "📤 Deploying Source Adapter..."
zip -q source_adapter.zip source_adapter.py
aws lambda create-function \
  --function-name SourceAdapter \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler source_adapter.lambda_handler \
  --zip-file fileb://source_adapter.zip \
  --timeout 60 \
  --region $REGION 2>/dev/null || \
aws lambda update-function-code \
  --function-name SourceAdapter \
  --zip-file fileb://source_adapter.zip \
  --region $REGION

echo "📤 Deploying Error Analyzer..."
zip -q error_analyzer.zip error_analyzer.py
aws lambda create-function \
  --function-name ErrorAnalyzer \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler error_analyzer.lambda_handler \
  --zip-file fileb://error_analyzer.zip \
  --timeout 60 \
  --region $REGION 2>/dev/null || \
aws lambda update-function-code \
  --function-name ErrorAnalyzer \
  --zip-file fileb://error_analyzer.zip \
  --region $REGION

echo "📤 Deploying Error Summarizer..."
zip -q error_summarizer.zip error_summarizer.py
aws lambda create-function \
  --function-name ErrorSummarizer \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler error_summarizer.lambda_handler \
  --zip-file fileb://error_summarizer.zip \
  --timeout 120 \
  --region $REGION 2>/dev/null || \
aws lambda update-function-code \
  --function-name ErrorSummarizer \
  --zip-file fileb://error_summarizer.zip \
  --region $REGION

cd ..

echo "📤 Deploying GitHub Issue Creator..."
zip -q CreateIssueForQ.zip CreateIssueForQ.py
aws lambda create-function \
  --function-name CreateIssueForQ \
  --runtime python3.9 \
  --role $ROLE_ARN \
  --handler CreateIssueForQ.lambda_handler \
  --zip-file fileb://CreateIssueForQ.zip \
  --timeout 30 \
  --region $REGION 2>/dev/null || \
aws lambda update-function-code \
  --function-name CreateIssueForQ \
  --zip-file fileb://CreateIssueForQ.zip \
  --region $REGION

echo "🔧 Creating Step Functions State Machine..."
aws stepfunctions create-state-machine \
  --name DevAngelPipeline \
  --definition file://LambdaFunctions/state_machine_complete.json \
  --role-arn arn:aws:iam::478047815638:role/stepfunctions-execution-role \
  --region $REGION 2>/dev/null || \
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:$REGION:478047815638:stateMachine:DevAngelPipeline \
  --definition file://LambdaFunctions/state_machine_complete.json \
  --region $REGION

echo "✅ Deployment complete!"
echo "🔗 Test the pipeline:"
echo "aws stepfunctions start-execution --state-machine-arn arn:aws:states:$REGION:478047815638:stateMachine:DevAngelPipeline --input '{}'"
