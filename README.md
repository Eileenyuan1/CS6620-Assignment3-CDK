# CS6620 - Assignment 3: use CDK to deploy the resources in Assignment 2

## Project Overview

This repository contains the **AWS Cloud Development Kit (CDK)** solution for CS6620 Programming Assignment 3. The goal is to automatically deploy and manage the complete serverless data pipeline required in Assignment 2. The pipeline tracks object changes in an **S3 bucket**, persists the history to **DynamoDB**, and generates a time-series plot.

## Deployed AWS Resources

The infrastructure is provisioned across **three CDK stacks**:

1.  **Database Stack:** DynamoDB Table (`S3ObjectSizeHistory`) and its Global Secondary Index (GSI).
2.  **Lambda Stack:** Three Python Lambda Functions (`Driver`, `Size Tracker`, `Plotting`), the S3 Bucket (`TestBucket`), and S3 event triggers.
3.  **API Stack:** REST API Gateway integrated with the `Driver` Lambda.

---

## Useful Commands

### CDK Commands
```bash
npm run build                          # Compile TypeScript
cdk deploy --all                       # Deploy all stacks
cdk deploy <stack-name>                # Deploy single stack
cdk destroy --all                      # Delete all stacks
cdk diff                               # Compare with deployed state
cdk synth                              # Generate CloudFormation templates
```

### S3 Bucket Cleanup
```bash
# Delete all objects recursively
aws s3 rm s3://<bucket-name> --recursive
```

---

## Deployment and Demo Instructions

### 1. Pre-Demo Cleanup
```bash
cdk destroy --all
```

### 2. Deploy Stacks
```bash
cdk deploy --all
```

### 3. Test
1. Go to AWS Lambda Console
2. Find and invoke `Assignment3LambdaStack-DriverLambda*`
3. Check DynamoDB table for records
4. Check S3 bucket for `plot.png`

---

## Project Structure

```
assignment3/
├── bin/assignment3.ts              # App entry
├── lib/
│   ├── api-stack.ts                # API Gateway
│   ├── database-stack.ts           # DynamoDB
│   └── lambda-stack.ts             # Lambdas + S3
├── lambda/
│   ├── driver.py                   # Driver Lambda
│   ├── plotting.py                 # Plotting Lambda
│   ├── size_tracker.py             # Size Tracking Lambda
│   └── requirements.txt            # Python dependencies
├── package.json
├── tsconfig.json
└── cdk.json
```
