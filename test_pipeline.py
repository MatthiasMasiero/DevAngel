#!/usr/bin/env python3
"""
Test script to verify the DevAngel pipeline works end-to-end
"""

import json
import sys
import os
from datetime import datetime

# Add the LambdaFunctions directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'LambdaFunctions'))

# Import the Lambda functions
import source_adapter
import error_analyzer

class MockContext:
    """Mock AWS Lambda context for testing"""
    def __init__(self):
        self.aws_request_id = f"test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

def test_source_adapter():
    """Test the source adapter with simulated logs"""
    print("🔍 Testing Source Adapter...")
    
    context = MockContext()
    
    # Test with empty event (should use embedded logs)
    event = {}
    
    try:
        result = source_adapter.lambda_handler(event, context)
        
        print(f"✅ Source Adapter Success!")
        print(f"   - Processed {len(result['source_adapter_output']['error_events'])} error events")
        print(f"   - Generated {len(result['source_adapter_output']['series'])} time series points")
        print(f"   - Found {len(result['source_adapter_output']['exemplars'])} error exemplars")
        
        return result
        
    except Exception as e:
        print(f"❌ Source Adapter Failed: {str(e)}")
        return None

def test_error_analyzer(source_output):
    """Test the error analyzer with source adapter output"""
    print("\n🔍 Testing Error Analyzer...")
    
    context = MockContext()
    
    # Create event with source adapter output
    event = {
        'source_adapter_output': source_output['source_adapter_output']
    }
    
    try:
        result = error_analyzer.lambda_handler(event, context)
        
        print(f"✅ Error Analyzer Success!")
        print(f"   - Analyzed {result['error_analyzer_output']['error_count']} errors")
        print(f"   - Found {result['error_analyzer_output']['critical_issues_count']} critical issues")
        print(f"   - Needs attention: {result['error_analyzer_output']['needs_immediate_attention']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error Analyzer Failed: {str(e)}")
        return None

def test_pipeline():
    """Test the complete pipeline"""
    print("🚀 Starting DevAngel Pipeline Test\n")
    
    # Step 1: Test Source Adapter
    source_result = test_source_adapter()
    if not source_result:
        print("❌ Pipeline failed at Source Adapter")
        return False
    
    # Step 2: Test Error Analyzer
    analyzer_result = test_error_analyzer(source_result)
    if not analyzer_result:
        print("❌ Pipeline failed at Error Analyzer")
        return False
    
    # Step 3: Show summary
    print("\n📊 Pipeline Test Summary:")
    print("=" * 50)
    
    source_summary = source_result['source_adapter_output']['summary']
    analyzer_summary = analyzer_result['error_analyzer_output']['error_summary']
    
    print(f"Total Events Processed: {source_summary['total_events']}")
    print(f"Error Events Found: {source_summary['error_count']}")
    print(f"Warning Events Found: {source_summary['warning_count']}")
    print(f"Critical Issues: {analyzer_result['error_analyzer_output']['critical_issues_count']}")
    print(f"Most Common Source: {analyzer_summary.get('most_common_source', 'N/A')}")
    print(f"Most Common Error Type: {analyzer_summary.get('most_common_error_type', 'N/A')}")
    
    # Show recommendations
    recommendations = analyzer_result['error_analyzer_output']['analysis_results'].get('recommendations', [])
    if recommendations:
        print(f"\n📋 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. [{rec.get('priority', 'Medium')}] {rec.get('recommendation', 'No recommendation')}")
    
    print("\n✅ Pipeline test completed successfully!")
    return True

def main():
    """Main test function"""
    try:
        success = test_pipeline()
        if success:
            print("\n🎉 All tests passed! The pipeline is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Tests failed! Check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
