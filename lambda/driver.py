import boto3
import time
import json
import os 

# --- Configuration ---
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
PLOT_LAMBDA_ARN = os.environ.get('PLOT_LAMBDA_ARN')

if not BUCKET_NAME:
    raise RuntimeError('Missing env S3_BUCKET_NAME for driver lambda')
if not PLOT_LAMBDA_ARN:
    raise RuntimeError('Missing env PLOT_LAMBDA_ARN for driver lambda')

s3_client = boto3.client('s3')

## Part4: construct the driver lambda 
# Helper function to pause execution
def pause(seconds):
    print(f"Pausing for {seconds} seconds...")
    time.sleep(seconds)

# Function to perform S3 operations, trigger size tracking and call the plotting API.
def handler(event, context):

    print(f"--- Starting Driver Operations on Bucket: {BUCKET_NAME} ---")
    
    # Setup
    key_1 = 'assignment1.txt'
    key_2 = 'assignment2.txt'
    content_1 = "Empty Assignment 1".encode('ascii')           # 18 bytes
    content_2 = "Empty Assignment 2222222222".encode('ascii')   # 27 bytes
    content_3 = "33".encode('ascii')        

    # 1. Create object assignment1.txt (18 bytes)
    print(f"1. Creating {key_1} (18 bytes)...")
    s3_client.put_object(
        Bucket=BUCKET_NAME, 
        Key=key_1, 
        Body=content_1,
        ContentLength=len(content_1)
    )
    pause(2) 

    # 2. Update object assignment1.txt (27 bytes)
    print(f"2. Updating {key_1} (27 bytes)...")
    s3_client.put_object(
        Bucket=BUCKET_NAME, 
        Key=key_1, 
        Body=content_2,
        ContentLength=len(content_2)
    )
    pause(2) 

    # 3. Delete object assignment1.txt (Size: 0)
    print(f"3. Deleting {key_1} (Size: 0)...")
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=key_1)
    pause(2) 

    # 4. Create object assignment2.txt (2 bytes)
    print(f"4. Creating {key_2} (2 bytes)...")
    s3_client.put_object(
        Bucket=BUCKET_NAME, 
        Key=key_2, 
        Body=content_3,
        ContentLength=len(content_3)
    )
    pause(2) 

    #5. Call the Plotting Lambda directly
    print(f"5. Calling Plotting Lambda...")
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=PLOT_LAMBDA_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps({'bucket': BUCKET_NAME})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Plotting Lambda Response: {result}")

    except Exception as e:
        print(f"ERROR: Failed to call plotting lambda: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'Lambda Call Failed: {e}'})}
    
    print("--- Driver Operations Complete ---")
    return {'statusCode': 200, 'body': json.dumps({'message': 'S3 operations and plotting API call completed successfully.'})}

# --- Main execution block ---
if __name__ == "__main__":
    print("\n--- Starting Local Test for Driver Lambda (Part 4) ---")
    
    response = handler(event={}, context=None)
    
    print("--- Local Test Complete ---")
    print("Final API Call Status:", response)