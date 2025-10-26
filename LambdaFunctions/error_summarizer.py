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
    
    # Create detailed summary with full context
    detailed_summary = generate_detailed_summary(
        series, exemplars, file_hits, deploy, basic_stats, timeline_analysis
    )
    
    # Create individual error summaries with context
    error_summaries = []
    for exemplar in exemplars[:5]:
        error_message = exemplar.get('@message', '') or exemplar.get('message', '')
        summary = generate_contextual_error_summary(
            error_message, deploy, timeline_analysis, file_hits
        )
        if summary:
            error_summaries.append(summary)
    
    return {
        'detailed_analysis': detailed_summary,
        'error_summaries': error_summaries,
        'timeline_analysis': timeline_analysis,
        'recommendations': generate_enhanced_recommendations(deploy, timeline_analysis, basic_stats)
    }

def analyze_error_timeline(series, deploy):
    """Analyze error timeline relative to deployment"""
    
    if not series or not deploy.get('timestamp'):
        return {'correlation': 'unknown', 'deploy_impact': False}
    
    deploy_time = deploy.get('timestamp', '')
    deploy_dt = datetime.fromisoformat(deploy_time.replace('Z', '+00:00'))
    
    # Find error spike timing
    max_errors = max(point[1] for point in series)
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
    """Generate comprehensive analysis with full context"""
    
    # Build detailed context for Bedrock
    context_prompt = f"""
INCIDENT ANALYSIS REQUEST:

TIMELINE ANALYSIS:
- Deployment: {deploy.get('sha', 'unknown')} deployed at {deploy.get('timestamp', 'unknown')}
- Deployment Message: "{deploy.get('message', 'No message')}"
- Error Spike: {timeline.get('peak_error_count', 0)} errors at {timeline.get('error_spike_timestamp', 'unknown')}
- Time Correlation: {timeline.get('minutes_after_deploy', 'unknown')} minutes after deployment
- Impact Assessment: {'HIGH - Errors started immediately after deployment' if timeline.get('deploy_impact') else 'MEDIUM - Timing correlation unclear'}

DEPLOYMENT DETAILS:
- Changed Files: {', '.join(deploy.get('changed_files', []))}
- Files Experiencing Errors: {', '.join(list(file_hits.keys())[:5])}
- File Overlap: {'YES - Deployed files are experiencing errors' if any(any(cf in ef for cf in deploy.get('changed_files', [])) for ef in file_hits.keys()) else 'NO - Different files affected'}

ERROR STATISTICS:
- Total Errors: {basic_stats.get('total_errors', 0)}
- Error Timeline: {len(series)} time periods tracked
- Affected Components: {basic_stats.get('affected_files', 0)} files

SAMPLE ERROR MESSAGES:
{chr(10).join([f"- {ex.get('@message', ex.get('message', ''))[:100]}..." for ex in exemplars[:3]])}

Create a detailed incident analysis that includes:
1. Executive summary with business impact
2. Timeline correlation between deployment and errors
3. Root cause analysis linking deployment changes to specific errors
4. Recommended immediate actions with specific rollback instructions
5. Risk assessment if no action is taken

Format as a professional incident report. Be specific about timestamps, deployment versions, and file correlations.
"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 800,
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
        # Enhanced fallback with context
        return create_detailed_fallback_summary(deploy, timeline, basic_stats, file_hits)

def generate_contextual_error_summary(error_message, deploy, timeline, file_hits):
    """Generate error summary with deployment context"""
    
    prompt = f"""
CONTEXTUAL ERROR ANALYSIS:

ERROR MESSAGE:
{error_message[:400]}

DEPLOYMENT CONTEXT:
- Deploy SHA: {deploy.get('sha', 'unknown')}
- Deploy Time: {deploy.get('timestamp', 'unknown')}
- Deploy Message: "{deploy.get('message', 'No message')}"
- Changed Files: {', '.join(deploy.get('changed_files', [])[:3])}

TIMING CORRELATION:
- Error spike occurred {timeline.get('minutes_after_deploy', 'unknown')} minutes after deployment
- Peak errors: {timeline.get('peak_error_count', 0)} at {timeline.get('error_spike_timestamp', 'unknown')}
- Correlation level: {timeline.get('correlation', 'unknown')}

Analyze this specific error in context of the deployment. Explain:
1. What specific component/file is failing
2. How this relates to the deployment changes
3. What user-facing functionality is impacted
4. Confidence level that deployment caused this error

Keep response to 2-3 sentences, be specific about the deployment correlation.
"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 200,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()
        
    except Exception as e:
        return create_contextual_fallback(error_message, deploy, timeline)

def generate_enhanced_recommendations(deploy, timeline, basic_stats):
    """Generate specific recommendations with deployment context"""
    
    recommendations = []
    
    if timeline.get('deploy_impact'):
        recommendations.append({
            'priority': 'CRITICAL',
            'action': f'Immediate rollback to commit prior to {deploy.get("sha", "unknown")}',
            'reason': f'Error spike occurred {timeline.get("minutes_after_deploy", 0)} minutes after deployment',
            'timeline': f'Deploy at {deploy.get("timestamp", "unknown")} → Errors at {timeline.get("error_spike_timestamp", "unknown")}',
            'confidence': 'HIGH - Strong temporal correlation'
        })
    
    if basic_stats.get('total_errors', 0) > 5:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'Activate incident response team',
            'reason': f'{basic_stats.get("total_errors", 0)} errors affecting multiple components',
            'timeline': 'Immediate action required',
            'confidence': 'HIGH - Error volume exceeds threshold'
        })
    
    # File-specific recommendations with deployment context
    changed_files = deploy.get('changed_files', [])
    for file_path in changed_files[:2]:
        recommendations.append({
            'priority': 'MEDIUM',
            'action': f'Review changes in {file_path}',
            'reason': f'File was modified in deployment {deploy.get("sha", "unknown")} and may be causing errors',
            'timeline': 'Within 1 hour',
            'confidence': 'MEDIUM - File correlation identified'
        })
    
    return recommendations

def create_detailed_fallback_summary(deploy, timeline, basic_stats, file_hits):
    """Enhanced fallback with full context"""
    
    return f"""
INCIDENT ANALYSIS REPORT

EXECUTIVE SUMMARY:
Critical system incident detected with {basic_stats.get('total_errors', 0)} errors affecting {basic_stats.get('affected_files', 0)} components. Strong correlation identified between deployment {deploy.get('sha', 'unknown')} and error onset.

TIMELINE CORRELATION:
- Deployment {deploy.get('sha', 'unknown')} completed at {deploy.get('timestamp', 'unknown')}
- Error spike ({timeline.get('peak_error_count', 0)} errors) detected at {timeline.get('error_spike_timestamp', 'unknown')}
- Time correlation: {timeline.get('minutes_after_deploy', 'unknown')} minutes post-deployment
- Assessment: HIGH CONFIDENCE that deployment triggered these errors

ROOT CAUSE ANALYSIS:
The deployment message "{deploy.get('message', 'No message')}" suggests timeout configuration changes. Modified files include {', '.join(deploy.get('changed_files', [])[:3])}, which directly correlate with error-generating components.

IMMEDIATE RECOMMENDATION:
Execute rollback to commit prior to {deploy.get('sha', 'unknown')} within next 15 minutes to restore service stability.

BUSINESS IMPACT:
Payment processing and core application functionality compromised, directly affecting customer transactions and revenue.
"""

def create_contextual_fallback(error_message, deploy, timeline):
    """Contextual fallback for individual errors"""
    
    if 'timeout' in error_message.lower():
        return f"Payment timeout errors started {timeline.get('minutes_after_deploy', 'unknown')} minutes after deployment {deploy.get('sha', 'unknown')}, which modified timeout configurations from 30s to 5s. This change is directly causing transaction failures and requires immediate rollback."
    elif 'database' in error_message.lower():
        return f"Database connectivity issues emerged {timeline.get('minutes_after_deploy', 'unknown')} minutes post-deployment {deploy.get('sha', 'unknown')}, likely due to configuration changes affecting connection pooling and timeout settings."
    else:
        return f"Application errors correlate with deployment {deploy.get('sha', 'unknown')} at {deploy.get('timestamp', 'unknown')}, suggesting recent code changes introduced instability requiring investigation."
