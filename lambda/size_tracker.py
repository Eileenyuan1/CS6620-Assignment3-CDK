import boto3
import time
import os
import json

# --- Configuration ---
DDB_TABLE_NAME = os.environ.get('DDB_TABLE_NAME')
if not DDB_TABLE_NAME:
    raise RuntimeError('Missing env DDB_TABLE_NAME for size-tracking lambda') 
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

## Part2: construct the size-tracking lambda 
def handler(event, context):
    
    # 1. Extract Bucket Name (from the S3 event structure)
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        print(f"Triggered for bucket: {bucket_name}")
    except (KeyError, IndexError):
        # Occurs if the event structure is not a standard S3 event
        print("ERROR: Could not extract bucket name. Using fallback BUCKET_NAME if defined.")
        return {'statusCode': 400, 'body': 'Invalid S3 event structure'}


    # 2. Calculate Total Size and Object Count
    total_size = 0
    object_count = 0

    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name)

    try:
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    object_key = obj['Key']
                    
                    if not object_key.endswith('.txt'):
                        continue
                        
                    total_size += obj['Size']
                    object_count += 1
    except Exception as e:
        print(f"ERROR: Failed to list S3 objects: {e}")
        return {'statusCode': 500, 'body': f'S3 listing error: {e}'}

    print(f"Calculated: Total Size = {total_size} bytes, Object Count = {object_count}")

    # 3. Write to DynamoDB
    timestamp_ms = int(time.time() * 1000) # Milliseconds epoch time for the Sort Key

    try:
        dynamodb_client.put_item(
            TableName = DDB_TABLE_NAME,
            Item = {
                # Partition Key: Bucket Name
                'BucketName': {'S': bucket_name},
                # Sort Key: Timestamp
                'Timestamp': {'N': str(timestamp_ms)}, 
                # Attributes
                'TotalSize': {'N': str(total_size)},
                'ObjectCount': {'N': str(object_count)}
            }
        )
        print(f"Size record successfully written to DynamoDB at Timestamp: {timestamp_ms}")
    except Exception as e:
        print(f"ERROR: Failed to write to DynamoDB: {e}")
        return {'statusCode': 500, 'body': f'DynamoDB write error: {e}'}
    
    return {'statusCode': 200, 'body': json.dumps({'message': f'Total size {total_size} recorded.'})}

