import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    # Get data from previous Lambdas
    source_output = event.get('source_adapter_output', {})
    analyzer_output = event.get('error_analyzer_output', {})
    
    # Extract key data
    series = source_output.get('series', [])
    exemplars = source_output.get('exemplars', [])
    file_hits = source_output.get('file_hits', {})
    deploy = source_output.get('deploy', {})
    basic_stats = analyzer_output.get('basic_stats', {})
    
    # Analyze timeline and deployment correlation
    timeline_analysis = analyze_error_timeline(series, deploy)
    
    # Create detailed summary
    detailed_summary = generate_detailed_summary(
        series, exemplars, file_hits, deploy, basic_stats, timeline_analysis
    )
    
    # Create individual error summaries
    error_summaries = []
    for exemplar in exemplars[:5]:
        if isinstance(exemplar, dict):
            error_message = exemplar.get('message', '')
        else:
            error_message = str(exemplar)
        
        summary = generate_contextual_error_summary(
            error_message, deploy, timeline_analysis, file_hits
        )
        if summary:
            error_summaries.append(summary)
    
    # Generate recommendations
    recommendations = generate_enhanced_recommendations(deploy, timeline_analysis, basic_stats)
    
    # Determine if immediate action is required
    total_errors = basic_stats.get('total_errors', 0)
    requires_immediate_action = (
        total_errors >= 5 or 
        timeline_analysis.get('deploy_impact', False) or
        any(rec.get('priority') == 'CRITICAL' for rec in recommendations)
    )
    
    return {
        'error_summarizer_output': {
            'detailed_analysis': detailed_summary,
            'error_summaries': error_summaries,
            'timeline_analysis': timeline_analysis,
            'recommendations': recommendations,
            'requires_immediate_action': requires_immediate_action,
            'total_errors': total_errors
        }
    }

def analyze_error_timeline(series, deploy):
    """Analyze error timeline relative to deployment"""
    
    if not series or not deploy.get('timestamp'):
        return {'correlation': 'unknown', 'deploy_impact': False}
    
    deploy_time = deploy.get('timestamp', '')
    try:
        deploy_dt = datetime.fromisoformat(deploy_time.replace('Z', '+00:00'))
    except:
        return {'correlation': 'unknown', 'deploy_impact': False}
    
    # Find error spike timing
    max_errors = max(point[1] for point in series) if series else 0
    peak_time = None
    for timestamp_str, count in series:
        if count == max_errors:
            peak_time = timestamp_str
            break
    
    # Calculate time difference
    if peak_time:
        try:
            peak_dt = datetime.fromisoformat(peak_time.replace(' ', 'T') + ':00+00:00')
            time_diff = (peak_dt - deploy_dt).total_seconds() / 60  # minutes
            
            return {
                'deploy_timestamp': deploy_time,
                'error_spike_timestamp': peak_time,
                'minutes_after_deploy': int(time_diff),
                'peak_error_count': max_errors,
                'correlation': 'high' if 0 <= time_diff <= 30 else 'medium' if time_diff <= 60 else 'low',
                'deploy_impact': 0 <= time_diff <= 30
            }
        except:
            pass
    
    return {
        'deploy_timestamp': deploy_time,
        'error_spike_timestamp': peak_time,
        'peak_error_count': max_errors,
        'correlation': 'medium',
        'deploy_impact': True
    }

def generate_detailed_summary(series, exemplars, file_hits, deploy, basic_stats, timeline):
    """Generate comprehensive analysis"""
    
    # Try Bedrock first
    try:
        context_prompt = f"""
Analyze this incident:

ERRORS: {basic_stats.get('total_errors', 0)} total errors
TIMELINE: {len(series)} time periods
FILES AFFECTED: {list(file_hits.keys())[:3]}
DEPLOYMENT: {deploy.get('sha', 'unknown')} - {deploy.get('message', 'No message')}

Create a brief incident analysis focusing on:
1. What happened
2. Likely cause
3. Immediate action needed

Keep response under 300 words.
"""

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 400,
                'messages': [
                    {
                        'role': 'user',
                        'content': context_prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()
        
    except Exception as e:
        # Fallback analysis
        return create_fallback_summary(deploy, timeline, basic_stats, file_hits)

def generate_contextual_error_summary(error_message, deploy, timeline, file_hits):
    """Generate error summary with deployment context"""
    
    if not error_message:
        return None
        
    # Simple contextual analysis without Bedrock for reliability
    if 'timeout' in error_message.lower():
        return f"Timeout error detected. May be related to deployment {deploy.get('sha', 'unknown')}."
    elif 'connection' in error_message.lower():
        return f"Connection failure. Check if deployment {deploy.get('sha', 'unknown')} affected connectivity."
    elif 'memory' in error_message.lower():
        return f"Memory issue detected. Recent deployment may have introduced memory leak."
    else:
        return f"Error occurred after deployment {deploy.get('sha', 'unknown')}. Investigation needed."

def generate_enhanced_recommendations(deploy, timeline, basic_stats):
    """Generate specific recommendations"""
    
    recommendations = []
    
    total_errors = basic_stats.get('total_errors', 0)
    
    if timeline.get('deploy_impact') and total_errors > 0:
        recommendations.append({
            'priority': 'CRITICAL',
            'action': f'Consider rollback of deployment {deploy.get("sha", "unknown")}',
            'reason': f'Errors detected after deployment with {timeline.get("correlation", "unknown")} correlation',
            'timeline': 'Immediate'
        })
    
    if total_errors >= 5:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'Activate incident response team',
            'reason': f'{total_errors} errors detected',
            'timeline': 'Within 15 minutes'
        })
    
    return recommendations

def create_fallback_summary(deploy, timeline, basic_stats, file_hits):
    """Fallback analysis when Bedrock fails"""
    
    total_errors = basic_stats.get('total_errors', 0)
    
    return f"""
INCIDENT ANALYSIS REPORT

EXECUTIVE SUMMARY:
System incident detected with {total_errors} errors affecting {basic_stats.get('affected_files', 0)} components.

DEPLOYMENT CORRELATION:
- Deployment: {deploy.get('sha', 'unknown')}
- Message: "{deploy.get('message', 'No message')}"
- Correlation: {timeline.get('correlation', 'unknown')}

RECOMMENDATION:
{'Investigate deployment impact and consider rollback if errors persist.' if total_errors > 0 else 'Monitor system for additional issues.'}
"""
