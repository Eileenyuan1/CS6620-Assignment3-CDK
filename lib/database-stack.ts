import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class DatabaseStack extends cdk.Stack {
  // Expose the table for reference by other stacks (LambdaStack)
  public readonly table: dynamodb.Table; 
  public readonly gsiName: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // 1. Create DynamoDB Table for S3 size tracking
    this.table = new dynamodb.Table(this, 'S3ObjectSizeHistory', {
      partitionKey: { name: 'BucketName', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'Timestamp', type: dynamodb.AttributeType.NUMBER },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, 
      removalPolicy: cdk.RemovalPolicy.DESTROY, 
    });

    // 2. Add GSI for querying by max TotalSize per bucket
    this.gsiName = 'BucketSizeGSI';
    this.table.addGlobalSecondaryIndex({
      indexName: this.gsiName,
      partitionKey: { name: 'BucketName', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'TotalSize', type: dynamodb.AttributeType.NUMBER },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Output the Table Name
    new cdk.CfnOutput(this, 'DynamoDBTableName', {
      value: this.table.tableName,
    });

    new cdk.CfnOutput(this, 'DynamoDBGsiName', { value: this.gsiName });
  }
}