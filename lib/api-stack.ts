import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';

// Interface to receive the Driver Lambda reference
interface ApiStackProps extends cdk.StackProps {
  readonly driverLambda: lambda.IFunction;
}

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    // 1. Create REST API
    const api = new apigw.RestApi(this, 'MyAssignmentRestAPI', {
      deployOptions: {
        stageName: 'dev',
      },
    });

    // 2. Integrate with Driver Lambda
    const driverIntegration = new apigw.LambdaIntegration(props.driverLambda);

    // 3. Configure API Route: POST /trigger
    const triggerResource = api.root.addResource('trigger');
    triggerResource.addMethod('POST', driverIntegration);

    // 4. Output API URL
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url + 'trigger',
    });
  }
}
