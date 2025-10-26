#!/bin/bash

# Create Lambda function
zip -j function.zip error-api-lambda.py

aws lambda create-function \
  --function-name error-api-function \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-s3-role \
  --handler error-api-lambda.lambda_handler \
  --zip-file fileb://function.zip

# Create API Gateway
aws apigateway create-rest-api --name error-retrieval-api

echo "Update the role ARN and deploy the CloudFormation template for complete setup"
