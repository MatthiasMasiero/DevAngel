import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { Construct } from 'constructs';

export class QuietOpsCloudWatchStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // =============================================================================
    // CONFIGURATION - These are the settings you can customize
    // =============================================================================
    
    // Which log group to monitor (default: checkout API Lambda logs)
    const logGroupName = this.node.tryGetContext('logGroup') || '/aws/lambda/checkout-api';
    
    // How many errors per minute trigger the alarm (default: 1 for hackathon testing)
    const errorsThreshold = Number(this.node.tryGetContext('errorsThreshold')) || 1;
    
    // Step Functions ARN that handles incidents (your teammates will provide this)
    const incidentSmArn = this.node.tryGetContext('incidentSmArn') || process.env.INCIDENT_SM_ARN;

    // =============================================================================
    // STEP 1: CREATE METRIC FILTER
    // This watches your log files and counts ERROR messages
    // =============================================================================
    
    const metricFilter = new logs.MetricFilter(this, 'ErrorMetricFilter', {
      // Reference the existing log group (we don't create it, just reference it)
      logGroup: logs.LogGroup.fromLogGroupName(this, 'TargetLogGroup', logGroupName),
      
      // Create a custom metric in CloudWatch
      metricNamespace: 'QuietOps',  // This groups our metrics together
      metricName: 'ErrorsPerMinute', // The name of our error count metric
      
      // This pattern looks for ERROR, Exception, or Traceback in log messages
      filterPattern: logs.FilterPattern.anyTerm('ERROR', 'Exception', 'Traceback'),
      
      // Each matching log line counts as 1 error
      metricValue: '1',
      defaultValue: 0, // When no errors, the metric value is 0
    });

    // =============================================================================
    // STEP 2: CREATE CLOUDWATCH ALARM
    // This monitors the error metric and triggers when errors spike
    // =============================================================================
    
    const alarm = new cloudwatch.Alarm(this, 'ErrorSpike', {
      alarmName: 'QuietOps-ErrorSpike', // This exact name is important for EventBridge
      
      // Define what metric to monitor
      metric: new cloudwatch.Metric({
        namespace: 'QuietOps',
        metricName: 'ErrorsPerMinute',
        statistic: 'Sum', // Add up all errors in the time period
        period: cdk.Duration.minutes(1), // Check every 1 minute
      }),
      
      // Alarm triggers when errors >= threshold in 1 evaluation period
      threshold: errorsThreshold,
      evaluationPeriods: 1, // Only need 1 minute of high errors to trigger
      
      // If no data, don't trigger alarm (service might be down)
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // =============================================================================
    // STEP 3: CREATE EVENTBRIDGE RULE
    // This listens for alarm state changes and forwards them to Step Functions
    // =============================================================================
    
    const rule = new events.Rule(this, 'AlarmStateChangeRule', {
      // This rule triggers when CloudWatch alarms change state
      eventPattern: {
        source: ['aws.cloudwatch'], // Only CloudWatch events
        detailType: ['CloudWatch Alarm State Change'], // Only alarm state changes
        detail: {
          state: {
            value: ['ALARM'], // Only when alarm goes into ALARM state (not OK)
          },
          alarmName: [alarm.alarmName], // Only our specific alarm
        },
      },
    });

    // =============================================================================
    // STEP 4: ADD STEP FUNCTIONS TARGET (if provided)
    // This sends the alarm event to your teammates' Step Functions workflow
    // =============================================================================
    
    if (incidentSmArn) {
      // Reference the existing Step Functions state machine
      const stateMachine = cdk.aws_stepfunctions.StateMachine.fromStateMachineArn(
        this, 
        'IncidentSM', 
        incidentSmArn
      );
      
      // Add it as a target for our EventBridge rule
      rule.addTarget(new targets.SfnStateMachine(stateMachine));
    } else {
      // If no Step Functions ARN provided, just log a warning
      console.warn('No INCIDENT_SM_ARN provided - EventBridge rule created but has no target');
    }

    // =============================================================================
    // OUTPUTS - These values can be used by other stacks or for reference
    // =============================================================================
    
    new cdk.CfnOutput(this, 'AlarmName', {
      value: alarm.alarmName,
      description: 'Name of the CloudWatch alarm that detects error spikes',
    });

    new cdk.CfnOutput(this, 'RuleArn', {
      value: rule.ruleArn,
      description: 'ARN of the EventBridge rule that forwards alarm events',
    });

    new cdk.CfnOutput(this, 'LogGroupName', {
      value: logGroupName,
      description: 'Log group being monitored for errors',
    });
  }
}
