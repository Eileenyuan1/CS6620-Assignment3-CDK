#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { DatabaseStack } from "../lib/database-stack";
import { LambdaStack } from "../lib/lambda-stack";
import { ApiStack } from "../lib/api-stack";

const app = new cdk.App();

// 1. Database Stack (Stage 1)
const databaseStack = new DatabaseStack(app, "Assignment3DatabaseStack");

// 2. Lambda Stack (includes S3 bucket)
const lambdaStack = new LambdaStack(app, "Assignment3LambdaStack", {
  table: databaseStack.table,
  gsiName: databaseStack.gsiName,
});
lambdaStack.addDependency(databaseStack);

// 3. API Stack
const apiStack = new ApiStack(app, "Assignment3ApiStack", {
  driverLambda: lambdaStack.driverLambda,
});
apiStack.addDependency(lambdaStack);

cdk.Tags.of(app).add("Assignment", "3");

