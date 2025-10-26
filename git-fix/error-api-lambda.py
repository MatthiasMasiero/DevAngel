import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Get bucket and key from query parameters or path
        bucket = event.get('queryStringParameters', {}).get('bucket')
        key = event.get('queryStringParameters', {}).get('key')
        
        if not bucket or not key:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing bucket or key parameter'})
            }
        
        # Retrieve JSON from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        error_data = json.loads(response['Body'].read())
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(error_data)
        }
        
    except ClientError as e:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'S3 error: {str(e)}'})
        }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in S3 object'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
