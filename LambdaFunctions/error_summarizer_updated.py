import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
BUCKET_NAME = 'devangel-incident-data-1761448500'

def lambda_handler(event, context):
    try:
        analyzer_output = event.get('error_analyzer_output', {})
        analysis_results = analyzer_output.get('analysis_results', {})
        critical_errors = analyzer_output.get('critical_errors', [])
        error_summary = analyzer_output.get('error_summary', {})
        
        llm_input = prepare_llm_input(analysis_results, critical_errors, error_summary)
        human_summary = generate_human_summary(llm_input)
        
        final_report = {
            'executive_summary': human_summary,
            'technical_analysis': analysis_results,
            'critical_errors': critical_errors,
            'error_statistics': error_summary,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        report_key = f"human-reports/{datetime.utcnow().strftime('%Y/%m/%d')}/report-{context.aws_request_id}.json"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=report_key,
            Body=json.dumps(final_report, indent=2),
            ContentType='application/json'
        )
        
        return {
            'error_summarizer_output': {
                'human_summary': human_summary,
                'report_location': f"s3://{BUCKET_NAME}/{report_key}",
                'critical_issues_count': len(critical_errors),
                'requires_immediate_action': analyzer_output.get('needs_immediate_attention', False),
                'github_issue_data': {
                    'title': f"Critical System Errors Detected - {len(critical_errors)} Issues",
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
                'error': str(e),
                'requires_immediate_action': True
            }
        }

def prepare_llm_input(analysis_results, critical_errors, error_summary):
    return {
        'error_statistics': {
            'total_errors': error_summary.get('total_errors', 0),
            'critical_count': len(critical_errors),
            'most_common_source': error_summary.get('most_common_source'),
            'most_common_error_type': error_summary.get('most_common_error_type')
        },
        'error_patterns': analysis_results.get('error_patterns', {}),
        'recommendations': analysis_results.get('recommendations', []),
        'critical_errors_sample': critical_errors[:3] if critical_errors else []
    }

def generate_human_summary(llm_input):
    try:
        prompt = create_summary_prompt(llm_input)
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 800,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        return generate_fallback_summary(llm_input)

def create_summary_prompt(llm_input):
    stats = llm_input['error_statistics']
    recommendations = llm_input['recommendations']
    
    return f"""
Analyze these AWS infrastructure errors and create an executive summary:

STATISTICS:
- Total Errors: {stats.get('total_errors', 0)}
- Critical Errors: {stats.get('critical_count', 0)}
- Most Affected Service: {stats.get('most_common_source', 'Unknown')}
- Primary Error Type: {stats.get('most_common_error_type', 'Unknown')}

RECOMMENDATIONS:
{json.dumps(recommendations, indent=2)}

Provide:
1. Executive summary (2-3 sentences)
2. Critical issues requiring immediate attention
3. Recommended actions
4. System health assessment

Keep under 400 words, professional tone.
"""

def generate_fallback_summary(llm_input):
    stats = llm_input['error_statistics']
    recommendations = llm_input['recommendations']
    
    summary = f"""SYSTEM ERROR ANALYSIS

Overview: Detected {stats.get('total_errors', 0)} errors with {stats.get('critical_count', 0)} critical issues.
Most Affected: {stats.get('most_common_source', 'Unknown')} service
Primary Error: {stats.get('most_common_error_type', 'Unknown')}

Critical Issues:"""
    
    high_priority = [r for r in recommendations if r.get('priority') == 'High']
    for rec in high_priority[:3]:
        summary += f"\n- {rec.get('issue', 'Issue')}: {rec.get('recommendation', 'Action needed')}"
    
    summary += f"\n\nSystem Health: {'CRITICAL' if stats.get('critical_count', 0) > 0 else 'STABLE'}"
    return summary
