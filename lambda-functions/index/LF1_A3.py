from opensearchpy import OpenSearch, RequestsHttpConnection
import json
import boto3
from datetime import datetime
from requests_aws4auth import AWS4Auth
import base64

# Initialize clients for S3 and Rekognition - haha
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

#Connect to OpenSearch  
region = 'us-east-1'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# Initialize the OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': 'search-photos-m74gu5wpz62gg5csfse24gurki.us-east-1.es.amazonaws.com', 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
    connection_class=RequestsHttpConnection
)

def lambda_handler(event, context):
    print(event)
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        #print(bucket_name, object_key)

        # Step 1: Detect labels in the image using Rekognition
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
            MaxLabels=3  # Adjust the maximum number of labels as needed
        )
        rekognition_labels = [label['Name'].lower() for label in response['Labels']]
        
        # Step 2: Retrieve metadata from the S3 object
        metadata = s3_client.head_object(Bucket=bucket_name, Key=object_key).get('Metadata', {})
        print(metadata)
        custom_labels = metadata.get('customlabels', '').split(',')
        
        # Combine custom labels and detected labels
        labels = list(set(custom_labels + rekognition_labels))  # Remove duplicates if any
        print(labels)
        # Step 3: Prepare the JSON object for indexing in OpenSearch
        photo_data = {
            "objectKey": object_key,
            "bucket": bucket_name,
            "createdTimestamp": datetime.now().isoformat(),
            "labels": labels
        }

        # Step 4: Store the JSON object in the "photos" index in OpenSearch
        opensearch_client.index(
            index='photos',
            id=object_key,
            body=photo_data
        )

    return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                },
            'body': json.dumps('Image indexed successfully!')
            }
