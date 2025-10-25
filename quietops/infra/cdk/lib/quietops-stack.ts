import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class QuietOpsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const logGroupName = this.node.tryGetContext('logGroup') || '/aws/lambda/checkout-api';
    const errorsThreshold = Number(this.node.tryGetContext('errorsThreshold')) || 50;
    const incidentSmArn = this.node.tryGetContext('incidentSmArn') || process.env.INCIDENT_SM_ARN;

    // Metric Filter
    const metricFilter = new logs.MetricFilter(this, 'ErrorMetricFilter', {
      logGroup: logs.LogGroup.fromLogGroupName(this, 'TargetLogGroup', logGroupName),
      metricNamespace: 'QuietOps',
      metricName: 'ErrorsPerMinute',
      filterPattern: logs.FilterPattern.anyTerm('ERROR', 'Exception', 'Traceback'),
      metricValue: '1',
      defaultValue: 0,
    });

    // CloudWatch Alarm
    const alarm = new cloudwatch.Alarm(this, 'ErrorSpike', {
      alarmName: 'QuietOps-ErrorSpike',
      metric: new cloudwatch.Metric({
        namespace: 'QuietOps',
        metricName: 'ErrorsPerMinute',
        statistic: 'Sum',
        period: cdk.Duration.minutes(1),
      }),
      threshold: errorsThreshold,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // Lambda execution role with logs permissions
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      inlinePolicies: {
        LogsInsights: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'logs:StartQuery',
                'logs:GetQueryResults',
              ],
              resources: ['*'],
            }),
            // Commented for future GitHub integration
            // new iam.PolicyStatement({
            //   effect: iam.Effect.ALLOW,
            //   actions: ['secretsmanager:GetSecretValue'],
            //   resources: ['arn:aws:secretsmanager:*:*:secret:github-token-*'],
            // }),
          ],
        }),
      },
    });

    // Get Context Lambda
    const getContextLambda = new lambda.Function(this, 'GetContextFunction', {
      functionName: 'get-context',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../../lambdas/get_context'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        LOG_GROUP: logGroupName,
        REPO_OWNER: process.env.REPO_OWNER || '',
        REPO_NAME: process.env.REPO_NAME || '',
        COMMIT_SHA: process.env.COMMIT_SHA || '',
        PARENT_SHA: process.env.PARENT_SHA || '',
        ALARM_TO_LOGGROUP: process.env.ALARM_TO_LOGGROUP || '{}',
      },
    });

    // Query Logs Lambda
    const queryLogsLambda = new lambda.Function(this, 'QueryLogsFunction', {
      functionName: 'query-logs',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('../../lambdas/query_logs'),
      role: lambdaRole,
      timeout: cdk.Duration.minutes(5),
    });

    // EventBridge Rule
    const rule = new events.Rule(this, 'AlarmStateChangeRule', {
      eventPattern: {
        source: ['aws.cloudwatch'],
        detailType: ['CloudWatch Alarm State Change'],
        detail: {
          state: {
            value: ['ALARM'],
          },
          alarmName: [alarm.alarmName],
        },
      },
    });

    // Add Step Functions target if ARN provided
    if (incidentSmArn) {
      rule.addTarget(new targets.SfnStateMachine(
        cdk.aws_stepfunctions.StateMachine.fromStateMachineArn(this, 'IncidentSM', incidentSmArn)
      ));
    }

    // Stack Outputs
    new cdk.CfnOutput(this, 'AlarmName', {
      value: alarm.alarmName,
      exportName: 'QuietOps-AlarmName',
    });

    new cdk.CfnOutput(this, 'RuleArn', {
      value: rule.ruleArn,
      exportName: 'QuietOps-RuleArn',
    });

    new cdk.CfnOutput(this, 'GetContextLambdaArn', {
      value: getContextLambda.functionArn,
      exportName: 'QuietOps-GetContextLambdaArn',
    });

    new cdk.CfnOutput(this, 'QueryLogsLambdaArn', {
      value: queryLogsLambda.functionArn,
      exportName: 'QuietOps-QueryLogsLambdaArn',
    });
  }
}
