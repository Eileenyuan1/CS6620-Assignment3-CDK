import boto3
import json
import time
import os
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from decimal import Decimal

# --- Configuration ---
REGION_NAME = os.environ.get('AWS_REGION', 'us-east-1') 
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
DDB_TABLE_NAME = os.environ.get('DDB_TABLE_NAME')
DDB_GSI_NAME = os.environ.get('DDB_GSI_NAME')

if not BUCKET_NAME:
    raise RuntimeError('Missing env S3_BUCKET_NAME for plotting lambda')
if not DDB_TABLE_NAME:
    raise RuntimeError('Missing env DDB_TABLE_NAME for plotting lambda')
if not DDB_GSI_NAME:
    raise RuntimeError('Missing env DDB_GSI_NAME for plotting lambda')

## Part3: constrcut the plotting lambda
# Use query on PK to get max size
def get_max_size_overall(table, target_bucket):
    # Query GSI with PK=BucketName, order by TotalSize descending, take top 1
    response = table.query(
        IndexName=DDB_GSI_NAME,
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(target_bucket),
        ScanIndexForward=False,  # descending by sort key (TotalSize)
        Limit=1,
    )

    items = response.get('Items', [])
    if not items:
        return 0
    return int(items[0]['TotalSize'])

# Query data points from the Last 10 Seconds
def get_recent_data(table, target_bucket):
    
    # Calculate the timestamp boundaries in milliseconds
    current_time_ms = int(time.time() * 1000)
    time_limit_ms = current_time_ms - (10 * 1000) # 10 seconds ago

    # Use the Query API for efficient retrieval
    response = table.query(
        KeyConditionExpression=(
            # 1. Partition Key must match the target bucket
            boto3.dynamodb.conditions.Key('BucketName').eq(target_bucket) &
            # 2. Sort Key (Timestamp) must be greater than the 10-second limit
            boto3.dynamodb.conditions.Key('Timestamp').gt(time_limit_ms)
        )
    )

    # Extract X and Y axis data
    timestamps = []
    sizes = []
    
    if 'Items' in response:
        # Sort items by timestamp to ensure correct plotting order
        items_sorted = sorted(response['Items'], key=lambda x: int(x['Timestamp']))
        
        for item in items_sorted:
            # Convert millisecond timestamp to seconds for plotting
            timestamps.append(int(item['Timestamp']) / 1000) 
            sizes.append(int(item['TotalSize']))

    return timestamps, sizes

# Plot S3 bucket size change and upload the graph to S3
def handler(event, context):

    s3_client = boto3.client('s3', region_name = REGION_NAME)
    dynamodb_resource = boto3.resource('dynamodb', region_name = REGION_NAME)
    table = dynamodb_resource.Table(DDB_TABLE_NAME)
    target_bucket = BUCKET_NAME 
    
    # Get data points from the last 10 seconds
    timestamps, sizes = get_recent_data(table, target_bucket)
    
    # Get the historical maximum size
    max_size_overall = get_max_size_overall(table, target_bucket)
    
    if not timestamps:
        print("No data points found in the last 10 seconds.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'No recent data for plotting.'})}

    # Start plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the size change curve
    ax.plot(timestamps, sizes, marker='o', linestyle='-', color='blue', linewidth=2, markersize=6)
    
    # Plot the maximum size as a horizontal line
    ax.axhline(y=max_size_overall, color='red', linestyle='--', linewidth=2, label=f'Max Size: {max_size_overall} bytes')
    
    # Set chart titles and labels
    ax.set_title(f'{target_bucket} Size Change (Last 10s)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Timestamp (Seconds since Epoch)', fontsize=12)
    ax.set_ylabel('Total Bucket Size (Bytes)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add data point annotations
    for i, (ts, size) in enumerate(zip(timestamps, sizes)):
        ax.annotate(f'{size}B', (ts, size), textcoords="offset points", xytext=(0,10), ha='center')
    
    plt.tight_layout()
    
    # Save the plot to an in-memory buffer (BytesIO)
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', dpi=150, bbox_inches='tight')
    img_data.seek(0)
    plt.close(fig)

    # Upload the image to S3
    plot_key = 'plot.png' 
    try:
        s3_client.put_object(
            Bucket=target_bucket,
            Key=plot_key,
            Body=img_data,
            ContentType='image/png'
        )
        print(f"Successfully uploaded plot to s3://{target_bucket}/{plot_key}")
    except Exception as e:
        print(f"ERROR: Failed to upload plot to S3: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to upload plot.'})}
        
    return {'statusCode': 200, 'body': json.dumps({'message': f'Plot generated and saved to {target_bucket}/{plot_key}'})}


# --- Main execution block ---
if __name__ == "__main__":
    print("--- Starting Plotting Lambda ---")
    
    mock_event = {} 
    
    # Running the Lambda handler locally
    response = handler(mock_event, None)
    
    print("--- Local Test Complete ---")
    print("API Response:", response)