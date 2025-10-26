import json

def lambda_handler(event, context):
    # Get source adapter output
    source_output = event.get('source_adapter_output', {})
    series = source_output.get('series', [])
    exemplars = source_output.get('exemplars', [])
    file_hits = source_output.get('file_hits', {})
    deploy = source_output.get('deploy', {})
    
    # Add error analyzer output to event
    event['error_analyzer_output'] = {
        'basic_stats': {
            'total_errors': sum(point[1] for point in series) if series else 0,
            'total_error_points': len(series),
            'unique_exemplars': len(exemplars),
            'affected_files': len(file_hits),
            'deploy_sha': deploy.get('sha'),
            'deploy_message': deploy.get('message')
        },
        'dashboard_ready': {
            'error_timeline': series,
            'top_errors': exemplars[:5],
            'file_impact': file_hits,
            'deployment_info': deploy
        }
    }
    
    return event
