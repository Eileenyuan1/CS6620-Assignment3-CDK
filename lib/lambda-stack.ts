import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3'; 
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

interface LambdaStackProps extends cdk.StackProps {
  readonly table: dynamodb.ITable;
  readonly gsiName: string;
}

export class LambdaStack extends cdk.Stack {
  public readonly driverLambda: lambda.Function; 
  public readonly sizeTrackingLambda: lambda.Function; 
  public readonly plottingLambda: lambda.Function;
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: LambdaStackProps) {
    super(scope, id, props);

    const codePath = 'lambda';

    // Create S3 Bucket
    this.bucket = new s3.Bucket(this, "TestBucket", {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    }); 

    const matplotlibLayer = lambda.LayerVersion.fromLayerVersionArn(
      this, 
      'MatplotlibLayer',
      'arn:aws:lambda:us-east-1:647066518468:layer:Matplotlib-For-Plotting:1'
    );

    // --- 1. Plotting Lambda ---
    this.plottingLambda = new lambda.Function(this, 'PlottingLambda', {
      runtime: lambda.Runtime.PYTHON_3_9, 
      handler: 'plotting.handler',         
      code: lambda.Code.fromAsset(codePath),
      timeout: cdk.Duration.seconds(30),
      layers: [matplotlibLayer],
      environment: {
        DDB_TABLE_NAME: props.table.tableName,
        S3_BUCKET_NAME: this.bucket.bucketName,
        DDB_GSI_NAME: props.gsiName,
      },
    });
    props.table.grantReadData(this.plottingLambda); 
    this.bucket.grantReadWrite(this.plottingLambda); 

    // --- 2. Size-Tracking Lambda ---
    this.sizeTrackingLambda = new lambda.Function(this, 'SizeTrackingLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'size_tracker.handler',    
      code: lambda.Code.fromAsset(codePath),
      environment: {
        DDB_TABLE_NAME: props.table.tableName,
        S3_BUCKET_NAME: this.bucket.bucketName,
      },
    });
    props.table.grantReadWriteData(this.sizeTrackingLambda);
    this.bucket.grantRead(this.sizeTrackingLambda);

    // --- 3. Driver Lambda ---
    this.driverLambda = new lambda.Function(this, 'DriverLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'driver.handler',          
      code: lambda.Code.fromAsset(codePath),
      timeout: cdk.Duration.minutes(5),
      environment: {
        S3_BUCKET_NAME: this.bucket.bucketName,
        PLOT_LAMBDA_ARN: this.plottingLambda.functionArn,
      },
    });
    this.plottingLambda.grantInvoke(this.driverLambda);
    this.bucket.grantReadWrite(this.driverLambda);

    // --- 4. Add S3 Notification ---
    this.bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(this.sizeTrackingLambda)
    );
    this.bucket.addEventNotification(
      s3.EventType.OBJECT_REMOVED,
      new s3n.LambdaDestination(this.sizeTrackingLambda)
    );

    // --- 5. Output ---
    new cdk.CfnOutput(this, "S3BucketName", {
      value: this.bucket.bucketName,
    });
  }
}