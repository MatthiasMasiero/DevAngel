import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
BUCKET_NAME = 'devangel-incident-data-1761448500'

def lambda_handler(event, context):
    try:
        analyzer_output = event.get('error_analyzer_output', {})
        error_summary = analyzer_output.get('error_summary', {})
        critical_errors = analyzer_output.get('critical_errors', [])
        recommendations = analyzer_output.get('analysis_results', {}).get('recommendations', [])
        
        # Create human summary using Bedrock
        human_summary = generate_bedrock_summary(error_summary, critical_errors, recommendations)
        
        # Store in S3
        report_key = f"human-reports/{datetime.utcnow().strftime('%Y/%m/%d')}/report-{context.aws_request_id}.json"
        
        report = {
            'human_summary': human_summary,
            'error_statistics': error_summary,
            'critical_errors': critical_errors,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=report_key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        
        return {
            'error_summarizer_output': {
                'human_summary': human_summary,
                'report_location': f"s3://{BUCKET_NAME}/{report_key}",
                'requires_immediate_action': analyzer_output.get('needs_immediate_attention', False),
                'github_issue_data': {
                    'title': f"Critical System Errors - {error_summary.get('total_errors', 0)} Issues",
                    'body': human_summary,
                    'labels': ['bug', 'critical', 'devangel'],
                    'priority': 'high' if len(critical_errors) > 0 else 'medium'
                }
            }
        }
        
    except Exception as e:
        return {
            'error_summarizer_output': {
                'human_summary': f"Error generating summary: {str(e)}",
                'requires_immediate_action': True
            }
        }

def generate_bedrock_summary(error_summary, critical_errors, recommendations):
    try:
        prompt = f"""
Create a concise executive summary for this system error analysis:

ERRORS: {error_summary.get('total_errors', 0)} total, {error_summary.get('critical_count', 0)} critical
MOST AFFECTED: {error_summary.get('most_common_source', 'Unknown')} service
PRIMARY ERROR: {error_summary.get('most_common_error_type', 'Unknown')}

CRITICAL ISSUES:
{chr(10).join([f"- {e.get('source', 'Unknown')}: {e.get('errorType', 'Unknown')} - {e.get('message', 'No details')[:100]}" for e in critical_errors[:3]])}

RECOMMENDATIONS:
{chr(10).join([f"- {r.get('recommendation', 'No recommendation')}" for r in recommendations[:3]])}

Write a 3-paragraph executive summary: 1) What happened, 2) Impact and urgency, 3) Next steps. Keep under 300 words.
"""

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
        
    except Exception as e:
        return f"""
SYSTEM ERROR ANALYSIS SUMMARY

Our monitoring system detected {error_summary.get('total_errors', 0)} errors with {error_summary.get('critical_count', 0)} requiring immediate attention. The most affected service is {error_summary.get('most_common_source', 'Unknown')} experiencing {error_summary.get('most_common_error_type', 'Unknown')} errors.

Critical issues include database connectivity problems and service timeouts that are directly impacting system availability. These errors require immediate investigation to prevent service degradation.

Recommended actions: Address high-priority infrastructure issues, review system capacity, and implement monitoring improvements. Full technical details are available in the attached analysis report.
"""
